# PR 4 — Web Dashboard

**Branch:** `feat/web-dashboard` → base `feat/websocket-server` (PR 3)
**Goal:** Make it visible. A vanilla page the FastAPI server serves, updating gauges
live from the WebSocket and showing a colored fault banner.

## Why this PR exists
PR 3 streams JSON, but nobody's watching it. This is the human-facing end of Phase 1:
open a browser, see your car's data move in real time, and get a colored banner the
moment a fault appears. No build toolchain — plain HTML/CSS/JS served by the same
backend.

## Review guide — click through the changes

| # | File | What it adds & why |
|---|------|--------------------|
| 1 | [`frontend-web/index.html`](../../frontend-web/index.html) | Sensor cards (keyed by `data-name` to match reading names) + fault banner + status pill. |
| 2 | [`frontend-web/app.js`](../../frontend-web/app.js) | Connects to `/ws`, updates cards on `pid` messages, renders the fault banner on `dtc` messages (colored by worst severity), auto-reconnects. |
| 3 | [`frontend-web/style.css`](../../frontend-web/style.css) | Grid layout + severity colors + status styling. |
| 4 | [`obd_reader/server.py`](../../backend-OBD-reader/obd_reader/server.py) | Mounts `StaticFiles` at `/` so the same server serves the page and the feed (no CORS, one command). |

## How to verify
```bash
pip install -r requirements.txt
python3 backend-OBD-reader/main.py
# open http://localhost:8000
```
Because the fixture cycles through the overheating spike + DTCs, you'll see values
change and a colored fault banner appear (e.g. P0217 in red).

## That completes Phase 1
Reader (PR 1) → fault meaning (PR 2) → live server (PR 3) → dashboard (PR 4).
Deferred next: storage (`feat/storage`), then the agent phase.
