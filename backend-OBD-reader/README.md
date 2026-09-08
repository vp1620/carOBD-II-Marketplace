# OBD Reader Backend

Reads OBD-2 data (a real ELM327 adapter, or a built-in fixture) and streams it to
browsers over a WebSocket at `/ws`.

## Install
```bash
# from the repo root
pip install -r requirements.txt
```

## Run
```bash
python3 backend-OBD-reader/main.py        # fixture mode — no car needed, serves on :8000
```
With a real adapter:
```bash
OBD_PORT=/dev/tty.OBDII python3 backend-OBD-reader/main.py
```

## Environment variables
- `OBD_PORT` — serial port of the ELM327 adapter. Unset → replays the sample fixture.
- `OBD_VEHICLE_ID` — id stamped on each reading (default `veh_local`).
- `OBD_POLL_INTERVAL` — seconds between polls (default `0.5`).

## See the stream (quick client)
```python
# pip install websockets
import asyncio, websockets

async def main():
    async with websockets.connect("ws://localhost:8000/ws") as ws:
        for _ in range(20):
            print(await ws.recv())

asyncio.run(main())
```
Each message is a JSON reading, e.g.
`{"type":"pid","pid":"010C","name":"engine_rpm","value":1726.0,"unit":"rpm",...}`,
and DTC messages include an enriched `"faults"` list.
