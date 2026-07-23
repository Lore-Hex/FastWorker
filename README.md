<p align="center">
  <img src="surfaces/gui/assets/fastworker-logo.svg" width="88" height="88" alt="FastWorker logo">
</p>

<h1 align="center">FastWorker</h1>

<p align="center">
  An open-source desktop AI worker powered by
  <a href="https://trustedrouter.com">TrustedRouter</a>.
</p>

<p align="center">
  <a href="https://github.com/Lore-Hex/FastWorker/actions/workflows/ci.yml"><img src="https://github.com/Lore-Hex/FastWorker/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-0a0e0b.svg" alt="MIT license"></a>
</p>

FastWorker is an AI coworker that lives on your desktop and produces finished
work, not just chat. It can prepare documents, analyze local files, update
connected tools, run scheduled work, and ask for approval before consequential
actions.

TrustedRouter is the default provider and `trustedrouter/fast` is the default
model. One key gives FastWorker a low-latency route across current models while
keeping the desktop app provider-independent.

## Why FastWorker

- **Gets work done:** creates files, reports, spreadsheets, messages, and other
  concrete deliverables.
- **Fast by default:** starts with `trustedrouter/fast`, TrustedRouter's
  low-latency multi-model route.
- **Local first:** the agent loop, conversations, connector tokens, and model
  keys stay on your computer.
- **Model freedom:** switch among TrustedRouter, OpenAI, Anthropic, Gemini,
  open-weight providers, or local Ollama models.
- **Approval gates:** sending messages, changing calendars, and running commands
  require approval unless you explicitly allow them.
- **Open source:** the desktop UI, Python agent server, packaging, and release
  automation are all available in this repository.

## Quick start

Prerequisites: Python 3.10+, Node 20+, and a
[TrustedRouter API key](https://trustedrouter.com/console/api-keys).

```shell
git clone https://github.com/Lore-Hex/FastWorker.git
cd FastWorker

bash packaging/setup_dev_env.sh
export TRUSTEDROUTER_API_KEY="sk-tr-..."

# Terminal 1: local agent server
.venv/bin/fastworker-server --cwd ~/FastWorker --port 8765

# Terminal 2: web UI
cd surfaces/gui
npm install
npm run dev
```

Open the Vite URL shown in the second terminal. You can also leave the
environment variable unset and add the key during onboarding.

For the native desktop shell, install the Rust toolchain with
[rustup](https://rustup.rs/), then run:

```shell
cd surfaces/gui
npm run tauri dev
```

## Default model

FastWorker routes its initial model as:

```text
provider: TrustedRouter
model:    trustedrouter/fast
endpoint: https://api.trustedrouter.com/v1
```

The internal routed identifier is
`trustedrouter:trustedrouter/fast`: the first prefix selects FastWorker's
TrustedRouter adapter, and the remaining model ID is sent to the
OpenAI-compatible API.

You can change the default model or add provider keys under **Settings > Models**.
FastWorker includes first-class setup for TrustedRouter, OpenAI, Anthropic,
Gemini, Z.ai, DeepSeek, Moonshot, MiniMax, Qwen, xAI, Mistral, Together,
Fireworks, and Ollama.

## How it works

```text
+------------------------------------------------+
|              FastWorker desktop app            |
+------------------------------------------------+
|            local Python agent server           |
|       engine | tools | approvals | schedules   |
+----------------+---------------+---------------+
|  local files   |  connectors   |  model API    |
|  and terminal  |  and MCP      |  of choice    |
+----------------+---------------+---------------+
```

1. Describe the outcome you want.
2. FastWorker plans and performs the work with the tools you allow.
3. It pauses for approval before sensitive actions.
4. It returns the completed result and any generated files.

FastWorker supports local files and shell tools, more than 20 connectors,
Model Context Protocol servers, recurring automations, Slack-triggered work,
and local voice transcription.

## Privacy

FastWorker stores its local state and secrets on your computer. Model requests
leave the computer only through the provider you configure. With the default
route, requests go through TrustedRouter's attested API gateway, which does not
store prompt or output content. Downstream model-provider policies still apply.
See the [TrustedRouter trust center](https://trustedrouter.com/trust) for the
current architecture, source, provider, and retention details.

## Tests

```shell
# Backend
uv run --extra dev --extra messaging pytest -q

# Frontend
cd surfaces/gui
NODE_OPTIONS=--no-experimental-webstorage npm test
npm run build
npm run e2e

# Native shell
cd src-tauri
cargo check
```

## Repository layout

| Directory | Contents |
| --- | --- |
| `coworker/` | Python agent engine, providers, tools, connectors, and API |
| `surfaces/gui/` | React UI and Tauri desktop shell |
| `stt/` | Local speech-to-text sidecar |
| `packaging/` | Development bootstrap and desktop release builds |
| `docs/` | Product, architecture, and design decisions |
| `tests/` | Backend test suite |

## Project history

FastWorker is a fork of
[Andrew Ng's OpenWorker](https://github.com/andrewyng/openworker), built on
[aisuite](https://github.com/andrewyng/aisuite). The fork preserves the MIT
license and upstream attribution while making TrustedRouter and
`trustedrouter/fast` the default model path.

## Contributing

Issues and pull requests are welcome in
[Lore-Hex/FastWorker](https://github.com/Lore-Hex/FastWorker). Include tests and
screenshots for user-interface changes.

## License

MIT. See [LICENSE](LICENSE).
