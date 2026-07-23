# FastWorker GUI (React + Tauri)

A thin client of the local FastWorker server (REST API + WebSocket event and
approval stream). The same codebase runs in a browser during development and in
the FastWorker desktop app.

## First time: bootstrap the Python backend

A fresh checkout has no server to run. From the repository root, create the
virtual environment both flows below expect:

```bash
bash packaging/setup_dev_env.sh
```

## Run it (browser, two terminals)

1. **Start the server** with `TRUSTEDROUTER_API_KEY` in the environment, or add
   a key later in FastWorker:
   ```bash
   ./.venv/bin/fastworker-server --cwd /path/to/your/project --port 8765
   ```
2. **Start the UI:**
   ```bash
   cd surfaces/gui
   npm install      # first time
   npm run dev      # → http://localhost:5173
   ```

Open http://localhost:5173. The UI talks to `http://127.0.0.1:8765` (override with
`VITE_COWORKER_HTTP` / `VITE_COWORKER_WS`).

## Run the desktop app from source

The Tauri shell wraps the same UI and supervises the Python server itself — no separate
terminal. It needs the Rust toolchain (`rustup`) plus the venv from the bootstrap step;
in development it finds the server at `.venv/bin/fastworker-server`
automatically. Packaged builds retain an internal compatibility sidecar filename.

```bash
cd surfaces/gui
npm install        # first time
npm run tauri dev  # builds the shell, launches the window, starts the server
```

## Tests

```bash
npx tsc --noEmit && npx vitest run   # typecheck + unit
npx playwright test                  # hermetic e2e (mocked /v1 + WS, no Python needed)
```
