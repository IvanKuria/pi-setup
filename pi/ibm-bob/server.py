#!/usr/bin/env python3
"""OpenAI-compatible local proxy for IBM Bob via litellm-ibm-bob."""
import json
import os
import time
import uuid
from typing import Any

import litellm
import litellm_ibm_bob  # noqa: F401 - side effect registers the ibm-bob provider
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from litellm_ibm_bob import _auth, provider as bob_provider
from litellm_ibm_bob._transport import AsyncBobTransport

# Comma-separated Bob model/tier names to expose through /v1/models.
BOB_MODELS = [
    m.strip()
    for m in os.getenv("BOB_MODELS", "premium,best,java-optim,python,opus,gpt,fast").split(",")
    if m.strip()
]
LOCAL_API_KEY = os.getenv("PI_BOB_PROXY_KEY", "pi-bob-local")
# Bob's public shell/API docs expose Bob Shell tools and MCP, but the inference
# endpoint used by litellm-ibm-bob is not a reliable OpenAI tool-calling backend
# across Bob's routed model groups (Bedrock/Mistral fallbacks are especially
# strict). Default to chat-only for pi reliability. Set BOB_ENABLE_TOOLS=1 to
# experiment with tool calling.
ENABLE_TOOLS = os.getenv("BOB_ENABLE_TOOLS", "0").lower() in {"1", "true", "yes", "on"}

# User-facing pi aliases. Values are the model/tier string passed to IBM Bob.
# Override with BOB_MODEL_ALIASES='{"best":"premium","opus":"claude-opus"}'.
DEFAULT_MODEL_ALIASES: dict[str, str] = {
    "best": "premium",
    "java-optim": "premium",
    "python": "premium",
    "premium": "premium",
    "fast": "fast",
    # These only work if your Bob subscription/backend exposes them. They are
    # included so you can test direct routing with /bob/model-info or a prompt.
    "opus": "opus",
    "gpt": "gpt",
}
try:
    MODEL_ALIASES = {**DEFAULT_MODEL_ALIASES, **json.loads(os.getenv("BOB_MODEL_ALIASES", "{}"))}
except json.JSONDecodeError:
    MODEL_ALIASES = DEFAULT_MODEL_ALIASES

ALIAS_METADATA: dict[str, dict[str, Any]] = {
    "best": {
        "mode": "advanced",
        "tags": ["pi", "highest-capability", "prefer-opus-gpt-class", "terminal-first"],
        "routingPreference": "Use the strongest available coding/reasoning model route.",
    },
    "java-optim": {
        "mode": "advanced",
        "tags": ["pi", "enterprise-java", "ibm-optim", "data-archiving", "prefer-opus-gpt-class"],
        "routingPreference": "Prioritize strongest reasoning for enterprise Java and data archiving safety.",
    },
    "python": {
        "mode": "advanced",
        "tags": ["pi", "python", "data-pipeline", "prefer-opus-gpt-class"],
        "routingPreference": "Prioritize strong Python coding and data-pipeline reasoning.",
    },
    "opus": {"mode": "advanced", "tags": ["pi", "prefer-opus"]},
    "gpt": {"mode": "advanced", "tags": ["pi", "prefer-gpt"]},
}

app = FastAPI(title="pi IBM Bob connector", version="1.0.0")


def _check_local_auth(authorization: str | None) -> None:
    if not LOCAL_API_KEY:
        return
    if authorization != f"Bearer {LOCAL_API_KEY}":
        raise HTTPException(status_code=401, detail="bad local proxy token")


def _alias_name(model: str) -> str:
    if model.startswith("ibm-bob/"):
        model = model[len("ibm-bob/") :]
    if model.startswith("bob-"):
        model = model[4:]
    return model


def _bob_model_and_metadata(model: str) -> tuple[str, dict[str, Any]]:
    # pi can send "bob-best", "bob-premium", "premium", or "ibm-bob/premium".
    alias = _alias_name(model)
    target = MODEL_ALIASES.get(alias, alias)
    return f"ibm-bob/{target}", ALIAS_METADATA.get(alias, {})


def _merge_metadata(body: dict[str, Any], alias_metadata: dict[str, Any]) -> None:
    if not alias_metadata:
        return
    metadata = dict(body.get("metadata") or {})
    tags = list(metadata.get("tags") or [])
    for tag in alias_metadata.get("tags") or []:
        if tag not in tags:
            tags.append(tag)
    metadata.update({k: v for k, v in alias_metadata.items() if k != "tags"})
    metadata["tags"] = tags
    body["metadata"] = metadata


def _strip_cache_control(value: Any) -> Any:
    """Remove Anthropic/OpenAI cache-control annotations some backends reject."""
    if isinstance(value, dict):
        return {k: _strip_cache_control(v) for k, v in value.items() if k != "cache_control"}
    if isinstance(value, list):
        return [_strip_cache_control(v) for v in value]
    return value


def _sanitize_tools_for_bob(body: dict[str, Any]) -> None:
    """Normalize pi/OpenAI tool definitions for Bob's LiteLLM/Bedrock routes.

    pi's OpenAI-compatible provider can send `strict` and cache-control fields.
    Bedrock/LiteLLM routes are stricter and public LiteLLM issues show tool
    conversion failures around OpenAI tool metadata and tool-result messages.
    """
    tools = body.get("tools")
    if isinstance(tools, list):
        for tool in tools:
            if not isinstance(tool, dict):
                continue
            tool.pop("cache_control", None)
            function = tool.get("function")
            if isinstance(function, dict):
                function.pop("strict", None)
                # Bedrock tool names must be alphanumeric/underscore/hyphen.
                name = function.get("name")
                if isinstance(name, str):
                    cleaned = "".join(ch if ch.isalnum() or ch in "_-" else "_" for ch in name)[:64]
                    function["name"] = cleaned or "tool"
                parameters = function.get("parameters")
                if isinstance(parameters, dict):
                    function["parameters"] = _strip_cache_control(parameters)
    body["messages"] = _strip_cache_control(body.get("messages", []))


def _maybe_disable_tools(body: dict[str, Any]) -> None:
    if ENABLE_TOOLS:
        return
    body.pop("tools", None)
    body.pop("tool_choice", None)
    body.pop("parallel_tool_calls", None)


def _debug_payload(label: str, payload: dict[str, Any]) -> None:
    if os.getenv("BOB_DEBUG_REQUESTS") != "1":
        return
    def scrub(v: Any) -> Any:
        if isinstance(v, str):
            return f"<str len={len(v)}>" if len(v) > 120 else v
        if isinstance(v, list):
            return [scrub(x) for x in v[:10]]
        if isinstance(v, dict):
            return {k: scrub(val) for k, val in v.items() if k.lower() not in {"authorization", "api_key"}}
        return v
    print(f"[pi-bob] {label}: " + json.dumps(scrub(payload), ensure_ascii=False), flush=True)


@app.get("/health")
def health() -> dict[str, Any]:
    return {"ok": True, "models": BOB_MODELS, "aliases": MODEL_ALIASES, "tools_enabled": ENABLE_TOOLS}


@app.get("/v1/models")
def models(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    _check_local_auth(authorization)
    now = int(time.time())
    return {
        "object": "list",
        "data": [
            {"id": f"bob-{m}", "object": "model", "created": now, "owned_by": "ibm-bob"}
            for m in BOB_MODELS
        ],
    }


@app.get("/bob/model-info")
async def bob_model_info(authorization: str | None = Header(default=None)) -> JSONResponse:
    """Diagnostic: call IBM Bob's native model-info endpoint with Bob auth/signing.

    Requires BOBSHELL_API_KEY in this process. This reveals what the Bob backend
    exposes to your subscription, which is the source of truth for whether direct
    IDs like opus/gpt are available.
    """
    _check_local_auth(authorization)
    try:
        cfg = bob_provider._resolve_config(api_key=None, api_base=None, optional_params={})
        async with AsyncBobTransport(cfg) as transport:
            await bob_provider._apply_identity_async(cfg, transport)
            kind = _auth.classify_key(cfg.api_key)
            authn = _auth.is_authn_backend(cfg.resolved_base_url(), kind=kind)
            response = await transport.request("GET", _auth.models_info_path(authn=authn))
            response.raise_for_status()
            return JSONResponse(response.json())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/v1/chat/completions")
async def chat_completions(request: Request, authorization: str | None = Header(default=None)):
    _check_local_auth(authorization)
    body = await request.json()
    model, alias_metadata = _bob_model_and_metadata(body.pop("model", "best"))
    _merge_metadata(body, alias_metadata)
    messages = body.pop("messages", [])
    stream = bool(body.pop("stream", False))
    body["messages"] = messages
    _sanitize_tools_for_bob(body)
    _maybe_disable_tools(body)
    messages = body.pop("messages", [])
    _debug_payload("request", {"model": model, "stream": stream, "messages": messages, **body})

    # LiteLLM accepts most OpenAI params directly. Drop OpenAI-only/OpenAI-cache
    # fields the Bob provider or underlying Bedrock routes may not understand.
    for unsupported in ("stream_options", "prompt_cache_key", "prompt_cache_retention", "store"):
        body.pop(unsupported, None)

    try:
        if not stream:
            resp = await litellm.acompletion(model=model, messages=messages, stream=False, **body)
            return JSONResponse(json.loads(resp.model_dump_json()))

        # pi uses OpenAI streaming. IBM Bob/LiteLLM streaming can terminate on
        # some Bob routes, so use a robust compatibility bridge: perform a
        # normal Bob completion first, then stream the final assistant message
        # back as OpenAI-compatible SSE chunks. Importantly, the Bob call is
        # awaited before creating StreamingResponse, so failures are returned as
        # normal JSON errors instead of ASGI TaskGroup crashes.
        resp = await litellm.acompletion(model=model, messages=messages, stream=False, **body)
        payload = json.loads(resp.model_dump_json())
        chunk_id = payload.get("id") or f"chatcmpl-{uuid.uuid4().hex}"
        created = payload.get("created") or int(time.time())
        response_model = payload.get("model") or model
        choices = payload.get("choices") or []
        message = (choices[0].get("message") if choices else {}) or {}
        content = message.get("content") or ""
        tool_calls = message.get("tool_calls") or []
        finish_reason = (choices[0].get("finish_reason") if choices else None) or "stop"
        usage = payload.get("usage")

        def send(obj: dict[str, Any]) -> str:
            return "data: " + json.dumps(obj, separators=(",", ":"), ensure_ascii=False) + "\n\n"

        chunks: list[str] = []
        chunks.append(send({
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": response_model,
            "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}],
        }))
        if content:
            chunks.append(send({
                "id": chunk_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": response_model,
                "choices": [{"index": 0, "delta": {"content": content}, "finish_reason": None}],
            }))
        for i, tool_call in enumerate(tool_calls):
            function = tool_call.get("function") or {}
            chunks.append(send({
                "id": chunk_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": response_model,
                "choices": [{
                    "index": 0,
                    "delta": {
                        "tool_calls": [{
                            "index": i,
                            "id": tool_call.get("id") or f"call_{i}",
                            "type": tool_call.get("type") or "function",
                            "function": {
                                "name": function.get("name") or "",
                                "arguments": function.get("arguments") or "{}",
                            },
                        }]
                    },
                    "finish_reason": None,
                }],
            }))
        done: dict[str, Any] = {
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": response_model,
            "choices": [{"index": 0, "delta": {}, "finish_reason": finish_reason}],
        }
        if usage:
            done["usage"] = usage
        chunks.append(send(done))
        chunks.append("data: [DONE]\n\n")

        async def event_stream():
            for chunk in chunks:
                yield chunk

        return StreamingResponse(event_stream(), media_type="text/event-stream")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
