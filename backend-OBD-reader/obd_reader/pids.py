"""OBD-2 PID definitions and decode formulas.

Formulas are verified by backend-OBD-reader/tests/test_decoder.py against the
shared golden fixture (testing/sample_obd_output.json).
"""

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class PID:
    command: str                          # e.g. "010C"
    name: str                             # e.g. "engine_rpm"
    unit: str                             # e.g. "rpm"
    decode: Callable[[list[int]], float]  # data bytes (A, B, ...) -> value


def _r1(x: float) -> float:
    return round(x, 1)


REGISTRY: dict[str, PID] = {
    "0104": PID("0104", "engine_load", "percent", lambda d: _r1(d[0] * 100 / 255)),
    "0105": PID("0105", "coolant_temp", "C", lambda d: d[0] - 40),
    "010C": PID("010C", "engine_rpm", "rpm", lambda d: (d[0] * 256 + d[1]) / 4),
    "010D": PID("010D", "vehicle_speed", "km/h", lambda d: float(d[0])),
    "010F": PID("010F", "intake_air_temp", "C", lambda d: d[0] - 40),
    "0110": PID("0110", "maf_air_flow", "g/s", lambda d: (d[0] * 256 + d[1]) / 100),
    "0111": PID("0111", "throttle_position", "percent", lambda d: _r1(d[0] * 100 / 255)),
    "0114": PID("0114", "o2_sensor_voltage", "V", lambda d: d[0] / 200),
    "012F": PID("012F", "fuel_level", "percent", lambda d: _r1(d[0] * 100 / 255)),
    "0142": PID("0142", "control_module_voltage", "V", lambda d: (d[0] * 256 + d[1]) / 1000),
}

# PIDs the reader polls each cycle by default.
DEFAULT_POLL = ["010C", "010D", "0105", "0111", "0110", "0114", "0142"]
