# PR 3 — WebSocket Server

**Branch:** `feat/websocket-server` → base `feat/fault-detection` (PR 2)
**Goal:** Serve the readings live. A FastAPI app polls the reader and pushes each
reading to all connected browsers over `/ws`, attaching PR 2's fault details to DTCs.

## Why this PR exists
The browser can't touch a serial port — it needs a backend to read the adapter and
push data. This is the bridge between PR 1's reader and PR 4's dashboard, and it's
where fault meaning (PR 2) gets attached so the frontend stays dumb.

## Review guide — click through the changes

| # | File | What it adds & why |
|---|------|--------------------|
| 1 | [`obd_reader/server.py`](../../backend-OBD-reader/obd_reader/server.py) | FastAPI `app`, the `/ws` endpoint, and `_broadcast_loop` that polls `make_reader()` and fans readings out. `_enrich` attaches `faults` to DTC messages. |
| 2 | [`main.py`](../../backend-OBD-reader/main.py) | One-command entry point (`python3 backend-OBD-reader/main.py`); fixes `sys.path` so the import string resolves. |
| 3 | [`README.md`](../../backend-OBD-reader/README.md) | Install/run, env vars, and a copy-paste WS client to watch the stream. |

## Design notes
- **`asyncio.to_thread(reader.poll_once)`** — the serial read is blocking; running it
  off-thread keeps the event loop (and the WebSockets) responsive.
- **FastAPI `lifespan`** starts/stops the poll loop with the app (current API; not the
  deprecated `on_event`).
- **Reuses** `make_reader()`, `Reading.to_dict()`, and `faults.describe()` — no new
  decode or fault logic here.

## How to verify
```bash
pip install -r requirements.txt
python3 backend-OBD-reader/main.py         # fixture mode
# then, in another shell, run the client snippet from backend-OBD-reader/README.md
```
You should see JSON readings stream, with an enriched `faults` list on DTC messages.

## Not in this PR
- PR 4 `feat/web-dashboard` — the browser page that renders this feed
