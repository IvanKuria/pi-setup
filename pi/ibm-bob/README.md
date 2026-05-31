# pi IBM Bob connector

This runs a local OpenAI-compatible proxy for IBM Bob using your Bob API key.
pi talks to `http://127.0.0.1:4010/v1`; the proxy signs/routes requests to Bob.

## Install

Requires Python 3.11+. On macOS, install with `brew install python@3.12` if needed.

```bash
~/.pi/ibm-bob/setup.sh
```

## Start

```bash
export BOBSHELL_API_KEY='<your_bob_api_key>'   # or your IBM Bob inference API key
~/.pi/ibm-bob/start.sh
```

Optional:

```bash
export BOB_MODELS='premium,best,java-optim,python,opus,gpt,fast'
export PI_BOB_PROXY_KEY='pi-bob-local'   # local token pi sends to this proxy
export PI_BOB_PROXY_PORT=4010

# Override pi alias -> Bob model/tier mapping if /bob/model-info shows concrete IDs.
# Example only; use the exact IDs returned for your subscription.
export BOB_MODEL_ALIASES='{"best":"premium","opus":"claude-opus","gpt":"gpt-5"}'
```

Default aliases exposed to pi:

- `bob-best` -> `premium` with strongest-route metadata
- `bob-java-optim` -> `premium` with enterprise Java / IBM Optim / data-archiving metadata
- `bob-python` -> `premium` with Python data-pipeline metadata
- `bob-premium` -> `premium`
- `bob-opus` -> `opus` direct preference, only works if Bob exposes that ID or you remap it
- `bob-gpt` -> `gpt` direct preference, only works if Bob exposes that ID or you remap it
- `bob-fast` -> `fast`

## Test

```bash
curl http://127.0.0.1:4010/health
curl -s http://127.0.0.1:4010/v1/models -H 'Authorization: Bearer pi-bob-local'

# Native Bob model-info diagnostic. Use this to discover whether direct Opus/GPT IDs exist.
curl -s http://127.0.0.1:4010/bob/model-info -H 'Authorization: Bearer pi-bob-local'

curl -s http://127.0.0.1:4010/v1/chat/completions \
  -H 'Authorization: Bearer pi-bob-local' -H 'Content-Type: application/json' \
  -d '{"model":"bob-best","messages":[{"role":"user","content":"Say hello"}]}'
```

## Copy to another laptop

Copy this directory and the pi model config:

```bash
rsync -a ~/.pi/ibm-bob other-laptop:~/.pi/
rsync -a ~/.pi/agent/models.json other-laptop:~/.pi/agent/models.json
```

On the other laptop install pi, run `~/.pi/ibm-bob/setup.sh`, set `BOBSHELL_API_KEY`, start the connector, then run pi.
