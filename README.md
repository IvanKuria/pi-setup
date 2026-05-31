# pi setup

Portable pi configuration for using pi as the harness with IBM Bob as the default model backend, plus enterprise Java / IBM Optim / Python workflow customizations.

## What is included

- IBM Bob local OpenAI-compatible connector: `pi/ibm-bob/`
- pi model config: `pi/agent/models.json`
- pi default settings: `pi/agent/settings.json`
- prompt templates:
  - `/terminal-plan`
  - `/java-investigate`
  - `/optim-archive-plan`
  - `/python-pipeline`
  - `/review-risk`
  - `/bob-best`
- skill: `enterprise-java-optim`
- project starter template for enterprise Java / Optim repos

## Install on a laptop

Requires Python 3.11+. On macOS, install with `brew install python@3.12` if needed.

```bash
git clone https://github.com/IvanKuria/pi-setup.git
cd pi-setup
./install.sh
```

Then install connector dependencies:

```bash
~/.pi/ibm-bob/setup.sh
```

Start the connector:

```bash
export BOBSHELL_API_KEY='<your_bob_api_key>'
~/.pi/ibm-bob/start.sh
```

Run pi normally. Default model is `ibm-bob/bob-best`.

## Optional Bob routing aliases

The connector exposes these pi models:

- `bob-best`
- `bob-java-optim`
- `bob-python`
- `bob-premium`
- `bob-opus`
- `bob-gpt`
- `bob-fast`

Discover native Bob model info:

```bash
curl -s http://127.0.0.1:4010/bob/model-info \
  -H 'Authorization: Bearer pi-bob-local'
```

If Bob exposes concrete model IDs, remap aliases before starting the connector:

```bash
export BOB_MODEL_ALIASES='{"best":"premium","opus":"actual-opus-id","gpt":"actual-gpt-id"}'
```

## Install project template into a repo

```bash
cd /path/to/project
~/.pi/agent/project-templates/enterprise-java-optim/install-into-project.sh
```

This adds:

- `AGENTS.md`
- `.pi/knowledge/`
- `scripts/pi-context/`

## Security notes

This repo intentionally does **not** include:

- `~/.pi/agent/auth.json`
- IBM Bob API keys
- virtual environments
- session history
