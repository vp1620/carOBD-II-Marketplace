# PR 2 — Fault Detection

**Branch:** `feat/fault-detection` → base `phase1-start-site` (PR 1)
**Goal:** Translate a raw DTC code into meaning the UI and future agent can present:
description, severity, "can it wait?", and a body zone. Pure logic, fully tested.

## Why this PR exists
PR 1 can decode `43 02 17` into `P0217`, but `P0217` still means nothing to a driver.
This PR is the thin interpretation layer that makes a code human-readable and
triage-able ("critical, engine, don't ignore"), which PR 4's dashboard and the later
agent both consume via one call.

## Review guide — click through the changes

| # | File | What it adds & why |
|---|------|--------------------|
| 1 | [`obd_reader/faults.py`](../../backend-OBD-reader/obd_reader/faults.py) | `DTC_DESCRIPTIONS` map + `severity_for` / `zone_for` / `describe`. `describe()` is the one safe call the UI/agent uses; it never raises on unknown codes. |
| 2 | [`tests/test_faults.py`](../../backend-OBD-reader/tests/test_faults.py) | Covers a known critical code, graceful handling of an unknown code, zone-prefix mapping, and severity levels. |

## Design notes
- **Prefix-based zones**, not a per-code table — so `zone_for` works on codes we
  haven't catalogued and feeds the future "highlight the area on the car" view.
- **`deferrable = severity != "critical"`** — the enthusiast "what can wait" signal.
- **Graceful unknowns** — an unmapped code returns a generic entry, keeping the live
  feed robust.

## How to verify
```bash
cd backend-OBD-reader
python3 tests/test_faults.py     # -> all pass
```

## Not in this PR
- PR 3 `feat/websocket-server` streams readings (and attaches these fault details to DTC messages)
- PR 4 `feat/web-dashboard` shows the colored fault banner
