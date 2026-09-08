"""Readers that produce Reading records.

- SerialReader: talks to a real ELM327 adapter over serial (pyserial, imported
  lazily so this module loads without hardware deps).
- FixtureReader: replays test_files/sample_obd_output.json for offline development
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
_FIXTURE = os.path.join(_REPO_ROOT, "test_files", "sample_obd_output.json")

# Fixed label the reader stamps on every Mode 03 (fault-code) record. The ECU
# frame carries no name, so it's pinned here — one place — rather than inline, so
# the fixture and the live path agree on what a DTC record is called.
_DTC_RECORD_NAME = "active_fault_codes"


class FixtureReader:
    """Replays the JSON fixture, one record per poll_once(), cycling forever."""

    # Why the readers advertise this rather than the server inspecting their type: the UI
    # must be able to say "replaying a recording" instead of "live" (#26), and asking
    # isinstance() at the call site would need updating every time a reader is added.
    is_live = False

    def __init__(self, vehicle_id: str = "veh_fixture", path: str = _FIXTURE):
        with open(path) as fh:
            self._records = json.load(fh)["records"]
        self._vehicle_id = vehicle_id
        self._i = 0

    def poll_dtcs(self) -> list[Reading]:
        """Return the fault codes this recording carries, as one Mode 03 read.

        Why FixtureReader needs this at all: SerialReader has it, and until now the two
        readers did not satisfy the same interface — anything calling poll_dtcs()
        generically raised AttributeError in fixture mode, which is the default and
        therefore the path most likely to be developed against (#30).

        Why it scans the whole recording rather than stepping: poll_once() walks records
        one per call to simulate a stream, but a Mode 03 read is a *question asked now*
        and the answer does not depend on how far through the file we are. Returning the
        codes the scenario declares is the honest fixture equivalent.

        Always returns exactly one record — with codes=[] when the recording has no
        faults — so "no faults" stays an explicit, storable fact rather than a silent gap,
        matching SerialReader.poll_dtcs().
        """
        codes = [c for rec in self._records
                 if rec["type"] == "dtc" for c in rec.get("codes", [])]
        return [Reading(
            timestamp=utc_now_iso(), vehicle_id=self._vehicle_id,
            type="dtc", name=_DTC_RECORD_NAME, codes=codes,
        )]

    def poll_once(self) -> list[Reading]:
        """Return the next Mode 01 sensor reading, cycling forever.

        **DTC records are skipped here.** poll_once() is the Mode 01 sensor loop —
        SerialReader's never returns a fault, and until FixtureReader had poll_dtcs()
        this one did, because there was nowhere else for faults to come from.

        Leaving both in place made the two paths fight: stepping onto the recording's dtc
        records emitted a *changing* set of codes (and an empty one, which cleared the
        banner) while poll_dtcs() emitted the stable full set every few seconds. The
        browser saw both and flickered between them.
        """
        rec = self._records[self._i % len(self._records)]
        self._i += 1
        if rec["type"] == "dtc":
            return []
        return [Reading(
            timestamp=utc_now_iso(), vehicle_id=self._vehicle_id,
            type="pid", pid=rec["pid"], name=rec["name"],
            value=rec["value"], unit=rec["unit"],
        )]


class SerialReader:
    """Polls a real ELM327 adapter. Requires pyserial and a connected adapter."""

    is_live = True

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
    """Pick a reader from the environment: OBD_PORT set -> real adapter, else fixture.

    OBD_FIXTURE selects which recording to replay — a path, or "rotate" for a
    different scenario each day. That selection is **development scaffolding** and lives
    in scenario.py, not here: this module is about readers, not about which recording is
    interesting on a Tuesday. See that file for how and when to delete it.
    """
    port = os.environ.get("OBD_PORT")
    vehicle_id = os.environ.get("OBD_VEHICLE_ID", "veh_local")
    if port:
        return SerialReader(port, vehicle_id=vehicle_id)
    # Default to the day rotation rather than the one hardcoded recording. Why: that
    # recording produces only two of the eight zones, which is how six icons went
    # unrendered and how an emission/emissions typo survived review. A default that only
    # ever exercises a quarter of the UI is the wrong default for a dev tool.
    fixture = os.environ.get("OBD_FIXTURE", "rotate")
    if fixture:
        # Development scaffolding — see scenario.py for what this is and how to remove it.
        # Imported lazily so production paths never load it.
        from .scenario import resolve
        return FixtureReader(vehicle_id=vehicle_id, path=resolve(fixture, _REPO_ROOT))
    return FixtureReader(vehicle_id=vehicle_id)
