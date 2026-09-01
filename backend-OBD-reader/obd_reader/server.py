"""FastAPI app that streams live OBD readings to browsers over a WebSocket.

Reads from whatever make_reader() selects (fixture or real adapter), enriches DTC
readings with fault descriptions, and fans each reading out to every connected client.
"""

import asyncio
import contextlib
import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from .faults import describe
from .models import Reading
from .reader import make_reader

# Connected browser sockets. Why: the broadcast loop needs a fan-out target, and a
# set gives cheap add/remove as clients connect and drop.
_clients: set[WebSocket] = set()

# Seconds between polling passes. Why: paces the fixture/adapter without hardcoding,
# so demos and real driving can tune it via env without code changes.
POLL_INTERVAL = float(os.environ.get("OBD_POLL_INTERVAL", "0.5"))


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


async def _broadcast_loop() -> None:
    """Poll the reader forever and broadcast each reading.

    Why: reader.poll_once() blocks on serial I/O, so we run it via asyncio.to_thread
    to keep the event loop that serves the WebSockets responsive.
    """
    reader = make_reader()
    while True:
        readings = await asyncio.to_thread(reader.poll_once)
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
    try:
        while True:
            await ws.receive_text()  # ignored; used only to notice a disconnect
    except WebSocketDisconnect:
        pass
    finally:
        _clients.discard(ws)
