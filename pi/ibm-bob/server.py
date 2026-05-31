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
# Emulate OpenAI tool-calling over plain Bob chat. pi sends tools -> proxy injects
# a text protocol -> Bob emits JSON -> proxy converts that to OpenAI tool_calls.
TOOL_BRIDGE = os.getenv("BOB_TOOL_BRIDGE", "1").lower() in {"1", "true", "yes", "on"}

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


def _content_to_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    parts.append(str(item.get("text", "")))
                elif item.get("type") == "image_url":
                    parts.append("[image omitted]")
                else:
                    parts.append(json.dumps(item, ensure_ascii=False))
            else:
                parts.append(str(item))
        return "\n".join(p for p in parts if p)
    return json.dumps(content, ensure_ascii=False)


def _tool_specs_for_prompt(tools: list[Any]) -> str:
    specs: list[str] = []
    for tool in tools:
        if not isinstance(tool, dict):
            continue
        fn = tool.get("function") or {}
        if not isinstance(fn, dict):
            continue
        specs.append(json.dumps({
            "name": fn.get("name"),
            "description": fn.get("description", ""),
            "parameters": fn.get("parameters", {}),
        }, ensure_ascii=False))
    return "\n".join(specs)


def _bridge_tool_messages(messages: list[dict[str, Any]], tools: list[Any]) -> list[dict[str, str]]:
    tool_instruction = (
        "You are running behind a compatibility adapter. You do not have native tool access.\n"
        "When you need to use a tool, output ONLY compact JSON with this exact shape and no markdown:\n"
        '{"tool_call":{"name":"tool_name","arguments":{}}}\n\n'
        "Rules:\n"
        "- Call at most one tool at a time.\n"
        "- Use tools only when needed to answer or modify files.\n"
        "- If no tool is needed, answer normally in plain text.\n"
        "- After a tool result is provided, continue normally or request the next tool using the same JSON format.\n\n"
        "Available tools as JSON schemas:\n" + _tool_specs_for_prompt(tools)
    )

    out: list[dict[str, str]] = []
    inserted = False
    for msg in messages:
        role = msg.get("role")
        if role in {"system", "developer"}:
            content = _content_to_text(msg.get("content"))
            if not inserted:
                out.append({"role": "system", "content": content + "\n\n" + tool_instruction})
                inserted = True
            else:
                out.append({"role": "system", "content": content})
        elif role == "tool":
            name = msg.get("name") or "tool"
            tool_call_id = msg.get("tool_call_id") or ""
            out.append({
                "role": "user",
                "content": f"Tool result for {name} (id {tool_call_id}):\n{_content_to_text(msg.get('content'))}",
            })
        elif role == "assistant":
            tool_calls = msg.get("tool_calls") or []
            if tool_calls:
                out.append({"role": "assistant", "content": "Requested tool call(s): " + json.dumps(tool_calls, ensure_ascii=False)})
            else:
                out.append({"role": "assistant", "content": _content_to_text(msg.get("content"))})
        else:
            out.append({"role": "user", "content": _content_to_text(msg.get("content"))})
    if not inserted:
        out.insert(0, {"role": "system", "content": tool_instruction})
    return out


def _extract_json_tool_payload(text: str) -> dict[str, Any] | None:
    raw = text.strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        raw = "\n".join(lines).strip()
    candidates = [raw]
    if "{" in raw and "}" in raw:
        candidates.append(raw[raw.find("{"): raw.rfind("}") + 1])
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except Exception:
            continue
        if isinstance(parsed, dict) and ("tool_call" in parsed or "tool_calls" in parsed or "final" in parsed):
            return parsed
    return None


def _normalize_bridge_tool_calls(parsed: dict[str, Any]) -> list[dict[str, Any]]:
    raw_calls = parsed.get("tool_calls")
    if raw_calls is None and parsed.get("tool_call") is not None:
        raw_calls = [parsed["tool_call"]]
    if not isinstance(raw_calls, list):
        return []
    calls: list[dict[str, Any]] = []
    for call in raw_calls[:1]:
        if not isinstance(call, dict):
            continue
        fn = call.get("function") if isinstance(call.get("function"), dict) else call
        name = fn.get("name") if isinstance(fn, dict) else None
        args = fn.get("arguments", {}) if isinstance(fn, dict) else {}
        if isinstance(args, str):
            try:
                args_obj = json.loads(args)
            except Exception:
                args_obj = {}
        elif isinstance(args, dict):
            args_obj = args
        else:
            args_obj = {}
        if isinstance(name, str) and name:
            calls.append({
                "id": f"call_{uuid.uuid4().hex[:24]}",
                "type": "function",
                "function": {"name": name, "arguments": json.dumps(args_obj, ensure_ascii=False)},
            })
    return calls


def _apply_bridge_parse(payload: dict[str, Any], bridge_active: bool) -> dict[str, Any]:
    if not bridge_active:
        return payload
    choices = payload.get("choices") or []
    if not choices:
        return payload
    message = choices[0].get("message") or {}
    content = message.get("content") or ""
    if not isinstance(content, str) or not content.strip():
        return payload
    parsed = _extract_json_tool_payload(content)
    if not parsed:
        return payload
    tool_calls = _normalize_bridge_tool_calls(parsed)
    if tool_calls:
        message["content"] = None
        message["tool_calls"] = tool_calls
        choices[0]["message"] = message
        choices[0]["finish_reason"] = "tool_calls"
    elif isinstance(parsed.get("final"), str):
        message["content"] = parsed["final"]
        choices[0]["message"] = message
    return payload


def _prepare_for_bob(messages: list[dict[str, Any]], body: dict[str, Any]) -> tuple[list[dict[str, Any]], bool]:
    tools = body.get("tools")
    if TOOL_BRIDGE and isinstance(tools, list) and tools:
        bridged_messages = _bridge_tool_messages(messages, tools)
        body.pop("tools", None)
        body.pop("tool_choice", None)
        body.pop("parallel_tool_calls", None)
        return bridged_messages, True
    _maybe_disable_tools(body)
    return messages, False


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "models": BOB_MODELS,
        "aliases": MODEL_ALIASES,
        "native_tools_enabled": ENABLE_TOOLS,
        "tool_bridge_enabled": TOOL_BRIDGE,
    }


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
    messages = body.pop("messages", [])
    messages, bridge_active = _prepare_for_bob(messages, body)
    _debug_payload("request", {"model": model, "stream": stream, "bridge_active": bridge_active, "messages": messages, **body})

    # LiteLLM accepts most OpenAI params directly. Drop OpenAI-only/OpenAI-cache
    # fields the Bob provider or underlying Bedrock routes may not understand.
    for unsupported in ("stream_options", "prompt_cache_key", "prompt_cache_retention", "store"):
        body.pop(unsupported, None)

    try:
        if not stream:
            resp = await litellm.acompletion(model=model, messages=messages, stream=False, **body)
            payload = _apply_bridge_parse(json.loads(resp.model_dump_json()), bridge_active)
            return JSONResponse(payload)

        # pi uses OpenAI streaming. IBM Bob/LiteLLM streaming can terminate on
        # some Bob routes, so use a robust compatibility bridge: perform a
        # normal Bob completion first, then stream the final assistant message
        # back as OpenAI-compatible SSE chunks. Importantly, the Bob call is
        # awaited before creating StreamingResponse, so failures are returned as
        # normal JSON errors instead of ASGI TaskGroup crashes.
        resp = await litellm.acompletion(model=model, messages=messages, stream=False, **body)
        payload = _apply_bridge_parse(json.loads(resp.model_dump_json()), bridge_active)
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
