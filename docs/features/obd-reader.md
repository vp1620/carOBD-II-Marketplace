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
