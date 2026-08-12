# ELM327 Stream Format — Decode Spec (for a from-scratch parser)

What the computer actually reads off the Bluetooth serial link, and how to turn it
into values. This is the stuff a library (`python-obd`) normally hides.

## Transport

- The Bluetooth adapter exposes a **serial-over-Bluetooth (SPP/RFCOMM)** link. To
  your code it's a byte stream — use a serial library (`go.bug.st/serial`), don't
  hand-roll Bluetooth.
- Full-duplex: you **write** commands, you **read** responses. The `.bin` capture
  here is the **read** side only (what to decode).

## Framing (the core of it)

- You write a command as ASCII + **CR**: `010C\r`  (CR = `\r` = 0x0D).
- The adapter replies, then prints the **prompt** `>` (0x3E) when ready for the
  next command. **Read until `>`** — that's one complete response.
- Inside a response, lines are separated by **CR (0x0D)**. There are **no line
  feeds (0x0A)** unless you enable them with `ATL1`. Don't split on `\n`.
- A full response with echo off looks like: `41 0C 1A F8\r\r>`.

## Echo

- Default is **echo ON**: the adapter echoes your command back first, so you'd
  read `010C\r41 0C 1A F8\r\r>`. Send **`ATE0`** to disable it (the init sequence
  does this), or strip the first line if it equals the command you sent.

## Init sequence

Send once on connect, waiting for the `>` prompt after each:
`ATZ` (reset) → `ATE0` (echo off) → `ATL0` (linefeeds off) → `ATSP0` (auto protocol).

## Decoding a Mode 01 PID response

`41 0C 1A F8`
- `0x41` = `0x40 + mode` → confirms a Mode 01 response.
- `0x0C` = the PID echoed back.
- remaining bytes are data `A, B, ...`; apply the PID's formula:
  - `010C` RPM = `(A*256 + B) / 4` → `(0x1A*256 + 0xF8)/4` = **1726**
  - `010D` speed = `A` km/h
  - `0105` coolant = `A - 40` °C
  - (full table: `../../testing/test_record_parsing.py` and `internal/obd/pids.go`)

## Decoding a Mode 03 DTC response

`43 02 17`
- `0x43` = Mode 03 response.
- then **pairs** of bytes, each pair one code:
  - top 2 bits of byte1 → letter: `00`=P, `01`=C, `10`=B, `11`=U
  - next 2 bits → first digit (0–3)
  - low nibble of byte1 → second digit
  - byte2 → third+fourth digits
  - → `02 17` = **P0217**
- `00 00` is padding — skip it. `43 00` means no codes.

## Non-hex responses your parser MUST handle

These arrive instead of hex and will crash a naive hex parser:
`NO DATA`, `?` (unknown command), `SEARCHING...`, `UNABLE TO CONNECT`,
`STOPPED`, `BUFFER FULL`, `CAN ERROR`. Branch on them before parsing hex.

## Multi-frame responses (later)

Long payloads (e.g. Mode 09 VIN) come back as **multiple lines**, each prefixed
with a frame counter (`0:`, `1:`, ...). Basic Mode 01 PIDs are single-frame, so
you can defer this until you need the bigger commands.

## Whitespace

Hex bytes are space-separated by default; strip/split on spaces. `ATS0` removes
the spaces entirely — handle both if you toggle it.

## A Go read-loop, in shape

```
write(cmd + "\r")
buf = readUntil('>')          // frame delimiter
lines = split(buf, '\r')      // NOT '\n'
drop empty / echo / status lines
parse the remaining hex line
```
