# Go Backend — Framework Skeleton (parked)

The shape of the Go backend for when the project migrates off Python. Not built,
not wired to a real adapter — a skeleton that shows the layering and implements
the interesting part (the from-scratch decoder).

## Layout

```
go-backend/
├── main.go                      # wires serial poll loop → WebSocket hub
├── go.mod
└── internal/
    ├── obd/
    │   └── pids.go              # PID table + decode formulas (matches Python)
    ├── elm327/
    │   ├── decode.go            # from-scratch Mode 01 / Mode 03 decoding  ← the real work
    │   └── client.go            # serial connect + read-until-'>' framing
    └── server/
        └── hub.go               # WebSocket broadcast of readings
```

## The split that matters

- **Write yourself:** `decode.go` (hex → values, DTC decoding). Small, no good Go
  library exists, great learning. It's fully implemented here as a starting point.
- **Use a library:** `client.go` leans on `go.bug.st/serial` for the transport.
  Don't hand-roll Bluetooth/serial.

## Getting it to run (later)

```bash
cd archive/go-backend
go mod tidy          # fetch gorilla/websocket + go.bug.st/serial
go run .             # serves :8080, /ws — poll loop idles with no adapter
```

## Suggested first steps when you pick this up

1. Port the Python tests: `internal/elm327/decode_test.go` asserting against the
   same values as `testing/test_record_parsing.py` (P0217 etc.).
2. Feed `archive/parser-fixtures/sample_obd_raw_stream.bin` through a fake reader
   so you can develop `client.go` framing offline (read-until-'>', split on '\r').
3. Only then connect a real adapter and handle the messy responses documented in
   `../parser-fixtures/RAW_STREAM_FORMAT.md` (NO DATA, SEARCHING..., multi-frame).

## Decode reference

`decode.go` implements exactly the formulas in `pids.go`. Example: `010C` RPM =
`(A*256+B)/4`, so `41 0C 1A F8` → 1726 rpm. DTCs: `43 02 17` → `P0217`.
