#!/usr/bin/env python3
"""OpenAI-compatible local proxy for IBM Bob via litellm-ibm-bob."""
import json
import os
import time
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


@app.get("/health")
def health() -> dict[str, Any]:
    return {"ok": True, "models": BOB_MODELS, "aliases": MODEL_ALIASES}


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

    # LiteLLM accepts most OpenAI params directly. Drop OpenAI-only stream_options;
    # the Bob provider may not understand it.
    body.pop("stream_options", None)

    try:
        if not stream:
            resp = await litellm.acompletion(model=model, messages=messages, stream=False, **body)
            return JSONResponse(json.loads(resp.model_dump_json()))

        async def event_stream():
            chunks = await litellm.acompletion(model=model, messages=messages, stream=True, **body)
            async for chunk in chunks:
                yield "data: " + chunk.model_dump_json() + "\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
