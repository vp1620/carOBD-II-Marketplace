"""Readers that produce Reading records.

- SerialReader: talks to a real ELM327 adapter over serial (pyserial, imported
  lazily so this module loads without hardware deps).
- FixtureReader: replays testing/sample_obd_output.json for offline development
  and demos — no car required.

Both expose poll_once() -> list[Reading]; the server calls it on an interval.
"""

import json
import os
import time
from typing import Optional

from .decoder import NoData, decode_dtcs, decode_pid
from .models import Reading, utc_now_iso
from .pids import DEFAULT_POLL, REGISTRY

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_FIXTURE = os.path.join(_REPO_ROOT, "testing", "sample_obd_output.json")

# Fixed label the reader stamps on every Mode 03 (fault-code) record. The ECU
# frame carries no name, so it's pinned here — one place — rather than inline, so
# the fixture and the live path agree on what a DTC record is called.
_DTC_RECORD_NAME = "active_fault_codes"


class FixtureReader:
    """Replays the JSON fixture, one record per poll_once(), cycling forever."""

    def __init__(self, vehicle_id: str = "veh_fixture", path: str = _FIXTURE):
        with open(path) as fh:
            self._records = json.load(fh)["records"]
        self._vehicle_id = vehicle_id
        self._i = 0

    def poll_once(self) -> list[Reading]:
        rec = self._records[self._i % len(self._records)]
        self._i += 1
        if rec["type"] == "dtc":
            return [Reading(
                timestamp=utc_now_iso(), vehicle_id=self._vehicle_id,
                type="dtc", name=rec["name"], codes=list(rec["codes"]),
            )]
        return [Reading(
            timestamp=utc_now_iso(), vehicle_id=self._vehicle_id,
            type="pid", pid=rec["pid"], name=rec["name"],
            value=rec["value"], unit=rec["unit"],
        )]


class SerialReader:
    """Polls a real ELM327 adapter. Requires pyserial and a connected adapter."""

    def __init__(self, port: str, baud: int = 38400,
                 vehicle_id: str = "veh_local", pids: Optional[list[str]] = None,
                 transport=None):
        self._port_name = port
        self._baud = baud
        self._vehicle_id = vehicle_id
        self._pids = pids or DEFAULT_POLL
        # transport: an injected serial-like object exposing write()/read_until().
        # It lets a test drive the REAL command/decode/Reading path with a byte
        # replay (FakeSerial) instead of opening hardware; None -> open a real
        # pyserial port in connect(). This is what makes the offline golden test
        # exercise the live path rather than a parallel parser.
        self._transport = transport
        self._port = None

    def connect(self):
        if self._transport is not None:
            self._port = self._transport  # injected (tests): skip real serial
        else:
            import serial  # lazy: only needed with real hardware
            self._port = serial.Serial(self._port_name, self._baud, timeout=2)
        for cmd in ("ATZ", "ATE0", "ATL0", "ATSP0"):
            self._command(cmd)
            if self._transport is None:
                time.sleep(0.1)  # adapter settle time; only meaningful on real hardware

    def _command(self, cmd: str) -> str:
        self._port.write((cmd + "\r").encode())
        raw = self._port.read_until(b">").decode(errors="replace")
        # strip prompt + echo, keep the data line
        for line in raw.replace(">", "").split("\r"):
            line = line.strip()
            if line and line != cmd:
                return line
        return ""

    def poll_once(self) -> list[Reading]:
        if self._port is None:
            self.connect()
        out: list[Reading] = []
        for pid in self._pids:
            raw = self._command(pid)
            try:
                value = decode_pid(pid, raw)
            except (NoData, ValueError):
                continue
            meta = REGISTRY[pid]
            out.append(Reading(
                timestamp=utc_now_iso(), vehicle_id=self._vehicle_id,
                type="pid", pid=pid, name=meta.name, value=value, unit=meta.unit,
            ))
        return out

    def poll_dtcs(self) -> list[Reading]:
        """Read the ECU's active fault codes once (Mode 03 request "03").

        This is the live-path counterpart to poll_once(): poll_once() handles the
        fast Mode 01 sensor loop, this handles Mode 03 diagnostic trouble codes.
        Kept as a separate call because DTCs are a different request and are read
        on demand / on a slower cadence than every sensor tick. Always returns one
        record — with codes=[] when the ECU reports no active faults — so "no
        faults" is an explicit, storable fact rather than a silent gap.
        """
        if self._port is None:
            self.connect()
        raw = self._command("03")
        return [Reading(
            timestamp=utc_now_iso(), vehicle_id=self._vehicle_id,
            type="dtc", name=_DTC_RECORD_NAME, codes=decode_dtcs(raw),
        )]


def make_reader() -> "FixtureReader | SerialReader":
    """Pick a reader from the environment: OBD_PORT set -> real adapter, else fixture."""
    port = os.environ.get("OBD_PORT")
    vehicle_id = os.environ.get("OBD_VEHICLE_ID", "veh_local")
    if port:
        return SerialReader(port, vehicle_id=vehicle_id)
    return FixtureReader(vehicle_id=vehicle_id)
