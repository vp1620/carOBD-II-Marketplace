"""FastAPI app that streams live OBD readings to browsers over a WebSocket.

Reads from whatever make_reader() selects (fixture or real adapter), enriches DTC
readings with fault descriptions, and fans each reading out to every connected client.
"""

import asyncio
import contextlib
import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

from .faults import describe
from .models import Reading
from .reader import make_reader

# Connected browser sockets. Why: the broadcast loop needs a fan-out target, and a
# set gives cheap add/remove as clients connect and drop.
_clients: set[WebSocket] = set()

# Seconds between polling passes. Why: paces the fixture/adapter without hardcoding,
# so demos and real driving can tune it via env without code changes.
POLL_INTERVAL = float(os.environ.get("OBD_POLL_INTERVAL", "0.5"))

# Seconds between Mode 03 fault-code reads. Why it is not POLL_INTERVAL: a DTC read is a
# separate request to the ECU, and stored fault codes do not change between sensor ticks.
# Asking twice a second would spend a round-trip on an answer that is almost always
# identical, and on a real adapter every round-trip competes with the PID loop for the
# single serial port.
DTC_INTERVAL = float(os.environ.get("OBD_DTC_INTERVAL", "5.0"))

# What the browser is actually looking at. Three states, not two (#26):
#   live         — a real adapter answered
#   disconnected — a real adapter was configured but is not responding
#   replaying    — a recording, no vehicle involved
# The dashboard previously showed "live" for all three, because app.js set it inside
# ws.onopen — which reports that the WEBSOCKET connected and says nothing about the car.
_status = {"source": "replaying", "detail": None}


def _enrich(reading: Reading) -> dict:
    """Build the JSON payload a client receives for one reading.

    Why: attach human fault meaning here, at the edge, so the browser stays a dumb
    renderer that never has to understand DTC codes itself.
    """
    payload = reading.to_dict()
    if reading.type == "dtc" and reading.codes:
        payload["faults"] = [describe(code) for code in reading.codes]
    return payload


async def _broadcast(payload: dict) -> None:
    """Send one payload to every connected client, dropping any that error.

    Why: a single dead or slow socket must not break the live feed for everyone else.
    """
    stale = []
    for ws in _clients:
        try:
            await ws.send_json(payload)
        except Exception:
            stale.append(ws)
    for ws in stale:
        _clients.discard(ws)


async def _set_status(source: str, detail: str | None = None) -> None:
    """Record what the browser is looking at, and tell it when that changes.

    Why only on change: the status is not a reading. Re-sending it every tick would make
    a client unable to tell "still connected" from "reconnected", and would bury the
    readings it actually needs in noise.
    """
    if _status["source"] == source and _status["detail"] == detail:
        return
    _status.update(source=source, detail=detail)
    await _broadcast({"type": "status", **_status})


async def _broadcast_loop() -> None:
    """Poll the reader forever and broadcast each reading.

    Why asyncio.to_thread: reader.poll_once() blocks on serial I/O, so running it inline
    would stall the event loop that serves every connected WebSocket.

    Why DTCs are on their own timer: poll_once() reads Mode 01 sensors; fault codes are a
    Mode 03 request that has no reason to run at sensor cadence. Before this, poll_dtcs()
    had no production caller at all — faults reached the browser only because the fixture
    happened to contain dtc records, so a real adapter produced none (#30).
    """
    reader = make_reader()
    await _set_status("live" if reader.is_live else "replaying")

    next_dtc = 0.0
    while True:
        now = asyncio.get_event_loop().time()
        try:
            readings = await asyncio.to_thread(reader.poll_once)
            if now >= next_dtc:
                readings += await asyncio.to_thread(reader.poll_dtcs)
                next_dtc = now + DTC_INTERVAL
        except Exception as exc:
            # A live adapter that stops answering is a state the driver must see, not a
            # crash and not a frozen gauge showing the last good value as though it were
            # current. Fixture failures are genuine bugs, so they are not swallowed.
            if not reader.is_live:
                raise
            await _set_status("disconnected", f"{type(exc).__name__}: {exc}")
            await asyncio.sleep(POLL_INTERVAL)
            continue

        if reader.is_live:
            await _set_status("live")
        for reading in readings:
            await _broadcast(_enrich(reading))
        await asyncio.sleep(POLL_INTERVAL)


@contextlib.asynccontextmanager
async def _lifespan(app: FastAPI):
    """Start the polling loop with the app and cancel it on shutdown.

    Why: lifespan is FastAPI's current startup/shutdown hook (on_event is deprecated),
    and tying the task to app life keeps it from leaking after the server stops.
    """
    task = asyncio.create_task(_broadcast_loop())
    try:
        yield
    finally:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task


# The ASGI app uvicorn serves. Why: one app hosts the WS feed now and (PR 4) the
# static dashboard, so there's a single server and no CORS to configure.
app = FastAPI(title="carOBD reader", lifespan=_lifespan)


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket) -> None:
    """Register a browser for the live feed and hold the socket open.

    Why: we only push data, so the receive loop exists solely to detect disconnects
    and keep _clients accurate.
    """
    await ws.accept()
    _clients.add(ws)
    # Send the current state immediately. Without this a client that connects mid-session
    # shows its default until something changes, which for a healthy connection is never.
    await ws.send_json({"type": "status", **_status})
    try:
        while True:
            await ws.receive_text()  # ignored; used only to notice a disconnect
    except WebSocketDisconnect:
        pass
    finally:
        _clients.discard(ws)


# Serve the vanilla dashboard from the same origin as the WS feed. Why: one server for
# both the page and the data means no CORS and a single command to run. Mounted last,
# after /ws, so the catch-all "/" mount can't shadow the WebSocket route.
_FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend-web"))
app.mount("/", StaticFiles(directory=_FRONTEND_DIR, html=True), name="frontend")
