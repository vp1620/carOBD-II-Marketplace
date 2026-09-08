---
id: OBD
name: OBD reader
status: shipped
stories: [OBD-1, OBD-2, OBD-3, OBD-4]
prs: [1]
key_files:
  - backend-OBD-reader/obd_reader/reader.py
  - backend-OBD-reader/obd_reader/decoder.py
  - backend-OBD-reader/obd_reader/pids.py
  - backend-OBD-reader/obd_reader/models.py
  - test_files/sample_obd_output.json
---

# OBD reader

## What it does

Talks to an **ELM327** — a cheap Bluetooth adapter that plugs into a car's diagnostic
port — and turns the ASCII hex it sends back into typed records.

```
request  "010C"                      (a PID: "give me engine RPM")
response "41 0C 1A F8"
record   {"type": "pid", "pid": "010C", "name": "engine_rpm",
          "value": 1726.0, "unit": "rpm"}
```

A **PID** is the code you send to ask for one sensor value. Each has its own decode
formula from the OBD-II standard — RPM is `(A*256+B)/4`, coolant temp is `A-40`.

## How it works

```
ELM327 adapter → reader.py (request a PID, read until the ">" prompt)
               → decoder.py (validate the frame, split the data bytes)
               → pids.py (formula lookup) → models.py (Reading) → downstream
```

`pids.py` is a lookup *called by* the decoder, not a stage of its own. Fault codes
(Mode 03) skip it entirely — they have no formula.

**The one non-obvious choice:** `SerialReader` takes an injected `transport` — anything
exposing `write()` and `read_until()`. Real use passes a pyserial port; tests pass a
`FakeSerial` that replays a recorded capture. So the test drives **the same code a real
car drives**, and the two cannot drift apart.

That replaced an earlier `stream.py` which held a second copy of the parse logic used
only by tests. Three copies of the decode path existed at one point; a test that passes
against a parallel implementation proves nothing about the real one.

## History

| PR | What it did |
|---|---|
| [#1](https://github.com/vp1620/carOBD-II-Marketplace/pull/1) | The reader package — `SerialReader`, `FixtureReader`, decoder, PID registry, `Reading` model, and the golden-file test. |

## Gotchas

**`test_files/sample_obd_output.json` cannot move under `tests/`.** It is the golden
expected output *and* the replay source `FixtureReader` loads at runtime for offline
development. It is production input as well as test data, and production code must not
depend on a test directory. `test_files/README.md` says so next to the file.

**Responses end with `>`, not a newline.** Framing reads until that prompt. A reader that
waits for `\n` hangs forever.

**Unsupported PIDs are normal.** Not every car answers every PID; the ECU replies
`NO DATA`, and the poll loop skips it. That is expected behaviour, not an error.

**Decode failures are currently swallowed.** `poll_once()` does
`except (NoData, ValueError): continue`, discarding both the exception and the raw
bytes — so a misbehaving PID shows up only as a missing gauge. Tracked as **OBD-5**.

## Related

- **OBD-5 / OBD-6** in `BACKLOG.md` — capture undecodable frames, then replay them as
  fixtures.
- [Fault detection](fault-detection.md) — consumes the codes this produces.
- [`decisions`](../../DECISIONS.md) — "The test must exercise the REAL code path, not a
  parallel copy".

---

## Architecture & data flow

*(moved from README, 2026-09-08 — the README keeps a short summary and links here.)*

The reader package (`backend-OBD-reader/obd_reader/`) turns raw adapter bytes into
clean records. At runtime, data flows like this:

```
Live path (real adapter):
  ELM327 adapter → reader.py (SerialReader: request PID, read response)
                 → decoder.py (parse/validate hex) → pids.py (formula lookup)
                 → models.py (Reading record) → server.py → /ws → browser

Fixture/test path (offline, no car):
  sample_obd_raw_stream.txt → FakeSerial (replays the capture in place of a real
  serial port) → reader.py (the SAME SerialReader code) → decoder.py + pids.py
                            → Reading records → compared against sample_obd_output.json
```

- `pids.py` is a lookup *called by* the decoder (which sensor a code means + its
  formula), not a separate stage. DTCs (fault codes) skip it entirely.
- The test path runs the **exact same reader code** as the live path. The only swap is
  the serial *port*: a `FakeSerial` (defined in the test) replays a recorded capture
  byte-for-byte instead of talking to hardware. This is *dependency injection* — pass in
  a fake instead of the real thing — and it's why the test can never drift from the code
  a real car actually drives. (An earlier `stream.py` had a *second* copy of the parsing
  logic just for tests; it was deleted because this fake exercises the real path instead.)
- Note the module *reading order* (foundations first: `pids` → `decoder` → `models` →
  `reader`) is **not** the runtime data path above — don't confuse the two.

### Serving it to the browser

`server.py` is the layer that turns records into something a page can render. A
**WebSocket** is a connection the browser opens once and holds open, so the server can
push new data down it without the page asking again — the right shape for a live gauge.

```
reader.poll_once()  ──►  _broadcast_loop()  ──►  _clients (open sockets)  ──►  /ws
   (blocking serial)         background task        fan-out, drops dead ones
```

- The poll runs inside `asyncio.to_thread`, so waiting on the adapter never stalls the
  event loop serving the sockets. This is the load-bearing detail: without it, one slow
  serial read freezes every connected browser.
- Fault readings are enriched **at the edge** — a DTC is passed through
  `faults.describe()` before being sent, so the browser receives
  `{code, description, severity, zone, deferrable}` and never has to understand fault
  codes itself.
- The loop's lifetime is tied to the app's via `lifespan`, so it cannot outlive the
  server that started it.
- Readings are broadcast and discarded. There is no persistence yet (STORE-1), so a
  client that connects late has missed everything before it.

---

- **Adapter:** Bluetooth ELM327 (serial-over-Bluetooth / RFCOMM SPP)
- **Baud:** 9600–38400
- **Init sequence:** `ATZ` → `ATE0` → `ATL0` → `ATSP0`
- **Read a PID:** e.g. `010C` (RPM) → response `41 0C 1A F8`
- Responses terminate with the `>` prompt, not a newline

**Common PIDs:**

| PID | Name | Formula |
|---|---|---|
| `010C` | Engine RPM | `(A*256+B)/4` |
| `010D` | Vehicle speed | `A` km/h |
| `0105` | Coolant temp | `A-40` °C |
| `0111` | Throttle position | `A*100/255` % |
| `012F` | Fuel level | `A*100/255` % |
| `0104` | Engine load | `A*100/255` % |
| `0110` | MAF air flow | `(A*256+B)/100` g/s |
| `0114` | O2 sensor voltage | `A/200` V |
| `0142` | Battery/module voltage | `(A*256+B)/1000` V |
| `010F` | Intake air temp | `A-40` °C |

---
