"""Transaction record emitted by the reader and pushed downstream."""

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Reading:
    timestamp: str
    vehicle_id: str
    type: str                       # "pid" | "dtc"
    name: str
    pid: Optional[str] = None
    value: Optional[float] = None
    unit: Optional[str] = None
    codes: Optional[list[str]] = None

    def to_dict(self) -> dict:
        """JSON-ready dict, dropping unset fields."""
        return {k: v for k, v in asdict(self).items() if v is not None}
