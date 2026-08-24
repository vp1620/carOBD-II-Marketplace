"""Turn a raw DTC code (e.g. "P0217") into human meaning the UI and agent can use.

A **DTC** (Diagnostic Trouble Code) is the 5-character fault code the car's computer
stores when something goes wrong. "P0217" on its own means nothing to a driver, so this
module answers three questions about it: what is it, how urgent is it, and where on the
car is it.

The code *meanings* live in `data/dtc_generic.json`, not in this file. This module holds
only the rules applied to them. Why the split: the catalog is reference data fixed by a
published standard and will grow to thousands of entries, while these rules are logic
that changes rarely — keeping them apart means a diff tells you which one actually
changed, and the same JSON can be read by the planned Go port (GO-1).

Everything here is pure lookup/logic with no I/O at call time, so it is trivially
testable and safe to call on any string — including codes we have not catalogued yet
(it degrades to a generic entry rather than raising).
"""

import json
from pathlib import Path

# Where the catalog lives, resolved relative to this file. Why: the reader must work
# from any working directory (cron job, test runner, web server), so we never rely on
# the process's cwd to find our own package data.
_CATALOG_PATH = Path(__file__).parent / "data" / "dtc_generic.json"


def _load_catalog() -> dict[str, dict]:
    """Read the DTC catalog from disk, once, at import time.

    Why a function rather than an inline read: this is the single place that knows
    *where* fault meanings come from. When manufacturer-specific codes arrive and need a
    database (DIAG-3), only this function changes — no caller has to.

    Why it is allowed to raise: a missing or malformed catalog is a broken install, not
    bad user input, and it should fail loudly at startup rather than silently reporting
    every code as unrecognized.
    """
    with _CATALOG_PATH.open(encoding="utf-8") as f:
        return json.load(f)["codes"]


# Loaded once and reused. Why: `describe()` is called per fault on a live feed, so we
# pay the file read at import instead of on every reading.
_CATALOG = _load_catalog()

# Shown when a code isn't in the catalog. Why: the live feed must stay useful when a car
# reports something we haven't catalogued — the driver still sees the raw code and knows
# it needs looking at, instead of hitting an error.
_UNKNOWN_DESCRIPTION = "Unrecognized code — needs diagnosis"


def description_for(code: str) -> str:
    """Look up the plain-language meaning of a code, or a generic fallback.

    Why it exists: gives callers (and future tiers of the catalog) one lookup point,
    so nothing outside this module reaches into the catalog dictionary directly.
    """
    entry = _CATALOG.get(code)
    return entry["description"] if entry else _UNKNOWN_DESCRIPTION


def severity_for(code: str) -> str:
    """Classify a code as critical/warning/info.

    Why: a single place that drives UI color and the "what needs attention now vs.
    later" ranking, instead of scattering thresholds across the frontend.

    Why 'info' is the default: an uncatalogued code has no *judged* urgency, and
    guessing "critical" would cry wolf on every unknown code.
    """
    entry = _CATALOG.get(code)
    return entry.get("severity", "info") if entry else "info"


# DTC first letter selects the top-level vehicle system.
# Why: the non-powertrain families map cleanly by letter alone, so we avoid a
# per-code table for them.
_LETTER_ZONE = {"C": "chassis", "B": "body", "U": "network"}

# The P04xx family is "auxiliary emission controls" — a grab-bag that is NOT all
# exhaust hardware. Why this table exists: we used to call the whole range "exhaust",
# which sent an EVAP fault (a leaking fuel-vapour hose, often just a loose fuel cap) to
# the exhaust zone. That matters beyond a label — zone routes the parts catalog (MKT-1)
# and the 3D "highlight the affected area" view, so a wrong zone recommends the wrong
# parts. The third digit picks the real system, so we key on it.
_P04_SUBZONE = {
    "0": "emissions",  # P040x — exhaust gas recirculation (EGR)
    "1": "emissions",  # P041x — secondary air injection
    "2": "exhaust",    # P042x — catalyst efficiency
    "3": "exhaust",    # P043x — heated catalyst
    "4": "emissions",  # P044x — evaporative emission (EVAP) system
    "5": "emissions",  # P045x — evaporative emission (EVAP) system
    "6": "engine",     # P046x — fuel level sensor
    "7": "exhaust",    # P047x — exhaust pressure / particulate filter
    "8": "engine",     # P048x — cooling fan
}


def zone_for(code: str) -> str:
    """Map a code to a coarse body zone from its prefix.

    Why: powers fault grouping and the future 3D "highlight the affected area" view;
    kept prefix-based (not per-code) so it works on codes we haven't catalogued, and
    it must never raise on odd input.
    """
    if not code:
        return "unknown"
    letter = code[0].upper()
    if letter in _LETTER_ZONE:
        return _LETTER_ZONE[letter]
    # Powertrain ("P") covers most codes, so split it further by the fault family
    # digits (chars 2-3). Why: a flat "engine" for every P-code would be too vague
    # to be useful on the dashboard.
    family = code[1:3]
    if family in ("07", "08"):
        return "transmission"
    if family == "04":
        # Slice rather than index the third digit: a truncated code like "P04" must
        # still return a zone instead of raising. "emissions" is the range's own name,
        # so it is the honest answer when we can't narrow it further.
        return _P04_SUBZONE.get(code[3:4], "emissions")
    if family == "03":
        return "ignition"
    return "engine"


def describe(code: str) -> dict:
    """Return everything the UI/agent needs to render one fault, in a single call.

    Why: centralizes fault meaning so callers never parse codes themselves, and it
    degrades gracefully — an uncatalogued code yields a generic entry instead of an
    error, which keeps the live feed robust against codes we haven't catalogued.
    """
    severity = severity_for(code)
    return {
        "code": code,
        "description": description_for(code),
        "severity": severity,
        "zone": zone_for(code),
        # deferrable answers "can this wait?" — Why: the enthusiast "what can I put
        # off" signal; anything critical is, by definition, not deferrable.
        "deferrable": severity != "critical",
    }
