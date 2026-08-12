# Archive — Parked / Future Work

Nothing here is part of the Phase 1 build. It's kept ready for when the project
gets to the **Go migration** (see `../DEVELOPMENT_PLAN.md` → Tech Stack → Backend).

Don't let this distract from Phase 1 (the Python website). Revisit when you
actually sit down to learn Go.

## Contents

- **`parser-fixtures/`** — byte-accurate ELM327 capture + generator, for writing
  an OBD parser from scratch in Go (no library). Test your Go read-loop and
  decoder against these bytes without needing a car.
  - `generate_raw_stream.py` — derives the capture from `testing/sample_obd_output.json` (single source of truth)
  - `sample_obd_raw_stream.bin` — real framing: `\r` (0x0D) line terminators, `>` (0x3E) prompt, **no** line feeds
  - `RAW_STREAM_FORMAT.md` — the decode spec: framing, echo, error responses, the gotchas a library normally hides

- **`go-backend/`** — a **framework skeleton** for the Go backend. Shows the shape:
  serial read → ELM327 framing → from-scratch PID/DTC decode → WebSocket broadcast.
  Compiles the intent, not a finished product (stubs + TODOs where real wiring goes).

## Why parked, not deleted

The decoder is small and a genuinely good Go learning project, and Go has no
mature OBD library — so you'd write most of this yourself anyway. The transport
(Bluetooth/serial) is **not** worth hand-rolling: use `go.bug.st/serial`. The
skeleton reflects that split.
