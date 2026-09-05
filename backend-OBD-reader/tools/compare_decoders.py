#!/usr/bin/env python3
"""Cross-check our decoder against python-obd on identical bytes.

WHY THIS EXISTS
    Our golden test proves the reader still does what it used to do. The J1979 test
    (tests/test_spec_conformance.py) proves it matches formulas we transcribed from the
    standard. Both are ours. If we misread the standard the same way twice, both agree
    and both are wrong.

    python-obd is a third opinion written by people who never saw our code. It is not
    authoritative — it is independent, which is the useful property. When it disagrees,
    one of us has misread SAE J1979 and it is worth finding out which.

WHY WE STILL DON'T DEPEND ON IT
    python-obd owns its own serial connection (OBD(portstr=...)) with no way to inject a
    transport, so adopting it would break the FakeSerial golden test and close the door on
    a BLE transport. It also has no BLE support at all. It is a good oracle and a bad
    dependency for this project. Used here, imported nowhere in obd_reader/.

USAGE
    python tools/compare_decoders.py                  # offline, synthetic frames
    python tools/compare_decoders.py --port /dev/cu.usbserial-XXXX

    The --port mode reads real frames off the adapter, then decodes those SAME bytes both
    ways. It deliberately does NOT open two connections and compare readings: a running
    engine changes between reads, so RPM would differ by timing rather than by logic and
    every run would look like a failure. Same bytes in, or the comparison means nothing.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from obd_reader.decoder import decode_pid                      # noqa: E402
from obd_reader.pids import REGISTRY                           # noqa: E402

try:
    import obd                                                 # noqa: E402
    from obd.protocols import ECU                              # noqa: E402
    from obd.protocols.protocol import Message                 # noqa: E402
except ImportError:
    sys.exit("python-obd not installed:  pip install obd")


# Our PID command -> python-obd command name. Hand-mapped because the two projects
# name things differently; a mismatch here is a mapping bug, not a decoder bug.
LIB_NAME = {
    "0104": "ENGINE_LOAD",
    "0105": "COOLANT_TEMP",
    "010C": "RPM",
    "010D": "SPEED",
    "010F": "INTAKE_TEMP",
    "0110": "MAF",
    "0111": "THROTTLE_POS",
    "0114": "O2_B1S1",
    "012F": "FUEL_LEVEL",
    "0142": "CONTROL_MODULE_VOLTAGE",
}

# Byte patterns to compare on. Boundaries first: 0x00 and 0xFF are where an off-by-one,
# a sign error or a scaling mistake actually shows up. A mid-range value alone can agree
# by accident.
SAMPLES = {1: [(0x00,), (0x7F,), (0xFF,)],
           2: [(0x00, 0x00), (0x1A, 0xF8), (0xFF, 0xFF)]}


def _arity(pid: str) -> int:
    return 2 if pid in ("010C", "0110", "0142") else 1


def frame(pid: str, data) -> str:
    """The Mode 01 response an adapter sends for these data bytes."""
    return " ".join(f"{b:02X}" for b in (0x41, int(pid[2:], 16), *data))


def lib_decode(pid: str, raw: str):
    """Decode one frame with python-obd.

    The ECU assignment is load-bearing: OBDCommand.__call__ filters messages with
    `(self.ecu & m.ecu) > 0`, so a Message with no ECU is silently dropped and you get
    None back with no error. That is a very easy hour to lose.
    """
    name = LIB_NAME.get(pid)
    if name is None or not hasattr(obd.commands, name):
        return None, f"no python-obd command mapped for {pid}"
    msg = Message([])
    msg.ecu = ECU.ENGINE
    msg.data = bytearray(int(t, 16) for t in raw.split())
    value = getattr(obd.commands, name)([msg]).value
    if value is None:
        return None, "python-obd returned no value"
    return value.magnitude, str(value.units)


def compare(pid: str, raw: str):
    """Return (ours, theirs, agree, note) for one frame."""
    try:
        ours = decode_pid(pid, raw)
    except Exception as exc:
        return None, None, False, f"our decoder raised {type(exc).__name__}: {exc}"

    theirs, units = lib_decode(pid, raw)
    if theirs is None:
        return ours, None, False, units

    ours_f, theirs_f = float(ours), float(theirs)

    if abs(ours_f - theirs_f) < 1e-9:
        return ours, theirs, "ok", units

    # Same formula, our rounding. pids.py:19 puts _r1() on the percentage PIDs, so
    # A*100/255 becomes 49.8 where python-obd keeps 49.80392156862745. Reporting that
    # as a disagreement would make this tool cry wolf on every run and it would stop
    # being read. Called out separately instead, because it IS a real difference —
    # just a deliberate one.
    if abs(round(theirs_f, 1) - ours_f) < 1e-9:
        return ours, theirs, "round", units

    return ours, theirs, "differ", units


def run_offline():
    print("Comparing our decoder against python-obd on synthetic frames.\n")
    rows, disagreements, unmapped, rounded = 0, [], [], []

    for pid in sorted(REGISTRY):
        meta = REGISTRY[pid]
        for data in SAMPLES[_arity(pid)]:
            raw = frame(pid, data)
            ours, theirs, verdict, note = compare(pid, raw)
            rows += 1
            if theirs is None:
                unmapped.append((pid, meta.name, note)); mark = "SKIP"
            elif verdict == "ok":
                mark = "ok"
            elif verdict == "round":
                rounded.append((pid, meta.name, ours, theirs)); mark = "round"
            else:
                disagreements.append((pid, meta.name, raw, ours, theirs)); mark = "DIFFER"
            shown = "-" if theirs is None else f"{theirs:.6g}"
            print(f"  {mark:<7}{pid}  {raw:<17}ours={ours!s:<10}lib={shown:<12}{meta.name}")

    print(f"\n  {rows} frames compared")
    _report(disagreements, unmapped, rounded)


def run_live(port: str, baud: int):
    """Read real frames off an adapter, then decode those same bytes both ways."""
    from obd_reader.reader import SerialReader

    print(f"Reading live frames from {port} at {baud}.\n")
    reader = SerialReader(port=port, baud=baud)
    reader.connect()

    disagreements, unmapped, rounded, rows = [], [], [], 0
    for pid in sorted(REGISTRY):
        raw = reader._command(pid)
        if not raw or "NO DATA" in raw.upper():
            print(f"  SKIP   {pid}  {raw!r:<20}(unsupported on this vehicle)")
            continue
        ours, theirs, verdict, note = compare(pid, raw)
        rows += 1
        if theirs is None:
            unmapped.append((pid, REGISTRY[pid].name, note)); mark = "SKIP"
        elif verdict == "ok":
            mark = "ok"
        elif verdict == "round":
            rounded.append((pid, REGISTRY[pid].name, ours, theirs)); mark = "round"
        else:
            disagreements.append((pid, REGISTRY[pid].name, raw, ours, theirs)); mark = "DIFFER"
        shown = "-" if theirs is None else f"{theirs:.6g}"
        print(f"  {mark:<7}{pid}  {raw:<17}ours={ours!s:<10}lib={shown!s:<10}{REGISTRY[pid].name}")

    print(f"\n  {rows} live frames compared")
    print("  Frames captured here are worth keeping — a real-car capture is OBD-5/OBD-6")
    print("  material you cannot manufacture from a fixture.")
    _report(disagreements, unmapped, rounded)


def _report(disagreements, unmapped, rounded):
    if unmapped:
        print(f"\n  {len(unmapped)} not compared:")
        for pid, name, note in unmapped:
            print(f"    {pid} ({name}): {note}")

    if rounded:
        print(f"\n  {len(rounded)} value(s) differ only by our rounding (_r1, pids.py:19):")
        for pid, name, ours, theirs in rounded[:4]:
            print(f"    {pid} ({name}): ours {ours}  lib {theirs}")
        print("    Same formula, different precision. Deliberate — but note it is LOSSY:")
        print("    49.80392 cannot be recovered from 49.8. Fine for a dashboard, worth")
        print("    revisiting before STORE-4 and the PRED-3 baselines, which need the")
        print("    spread of a signal and will be reading whatever we chose to persist.")

    if not disagreements:
        print("\n  AGREE — two independent implementations produce the same values.")
        print("  Not proof of correctness (both could misread the standard), but a")
        print("  disagreement would have been proof that something is wrong.")
        return 0

    print(f"\n  {len(disagreements)} DISAGREEMENT(S) — go read SAE J1979 for these:\n")
    for pid, name, raw, ours, theirs in disagreements:
        print(f"    {pid} ({name}) on {raw!r}")
        print(f"      ours: {ours}")
        print(f"      lib:  {theirs}")
    print("\n  Do NOT just copy python-obd's answer. Look up the formula in the standard")
    print("  and decide which is right — the library is a second opinion, not an authority.")
    return 1


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--port", help="serial port of a real adapter, e.g. /dev/cu.usbserial-1420")
    ap.add_argument("--baud", type=int, default=38400)
    args = ap.parse_args()
    sys.exit(run_live(args.port, args.baud) if args.port else run_offline())


if __name__ == "__main__":
    main()
