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
from functools import cache
from pathlib import Path

# Where the catalog lives, resolved relative to this file. Why: the reader must work
# from any working directory (cron job, test runner, web server), so we never rely on
# the process's cwd to find our own package data.
_DATA_DIR = Path(__file__).parent / "data"
_CATALOG_PATH = _DATA_DIR / "dtc_generic.json"
_ZONES_PATH = _DATA_DIR / "dtc_zones.json"


@cache
def _catalog() -> dict[str, dict]:
    """Read the DTC catalog from disk, once, on first use.

    Why a function rather than an inline read: this is the single place that knows
    *where* fault meanings come from. When manufacturer-specific codes arrive and need a
    database (DIAG-3), only this function changes — no caller has to.

    Why @cache rather than a module-level read: importing this module should not touch
    the filesystem. A read at import means the catalog is pinned before any test can
    swap it, and a process that never looks up a fault pays for a file read it never
    uses. Cached, so the live feed still reads the file exactly once per process;
    `_catalog.cache_clear()` resets it for a test.

    Why it is allowed to raise: a missing or malformed catalog is a broken install, not
    bad user input. Note the trade-off deferring introduces: a broken catalog now fails
    at the first lookup rather than at import. For a long-running service that means
    mid-drive instead of at boot, so whatever starts the reader should call this once
    on startup to fail fast. Nothing does yet — the WebSocket server is not on main.
    """
    with _CATALOG_PATH.open(encoding="utf-8") as f:
        return json.load(f)["codes"]


@cache
def _zones() -> dict:
    """Read the prefix → zone tables, once, on first use.

    Why they are data at all: these mappings are editorial judgements due for revision
    against the OBD-II ranges. As data a revision is a reviewable diff; as code it is an
    edit to the same file that holds the slice/fallback logic, which is easier to break
    by accident. The Go port (GO-1) can also read this file rather than reimplementing
    the table.
    """
    with _ZONES_PATH.open(encoding="utf-8") as f:
        return json.load(f)


_UNKNOWN_DESCRIPTION = "Unrecognized code — needs diagnosis"


def description_for(code: str) -> str:
    """Look up the plain-language meaning of a code, or a generic fallback.

    Why it exists: gives callers (and future tiers of the catalog) one lookup point,
    so nothing outside this module reaches into the catalog dictionary directly.
    """
    entry = _catalog().get(code)
    return entry["description"] if entry else _UNKNOWN_DESCRIPTION


def severity_for(code: str) -> str:
    """Classify a code as critical/warning/info.

    Why: a single place that drives UI color and the "what needs attention now vs.
    later" ranking, instead of scattering thresholds across the frontend.

    Why 'info' is the default: an uncatalogued code has no *judged* urgency, and
    guessing "critical" would cry wolf on every unknown code.
    """
    entry = _catalog().get(code)
    return entry.get("severity", "info") if entry else "info"


def zone_for(code: str) -> str:
    """Map a code to a coarse body zone from its prefix.

    Why: powers fault grouping and the future 3D "highlight the affected area" view;
    kept prefix-based (not per-code) so it works on codes we haven't catalogued, and
    it must never raise on odd input.

    The mappings live in data/dtc_zones.json. What stays here is the *order* they are
    consulted in and the fallbacks — which is logic, not data.
    """
    zones = _zones()
    if not code:
        return zones["defaults"]["empty_code"]["zone"]

    # Non-powertrain families are decided by the first letter alone, so they never
    # reach the P-code logic below.
    letter = code[0].upper()
    if letter in zones["by_letter"]:
        return zones["by_letter"][letter]["zone"]

    # Powertrain ("P") covers most codes, so split it further by the fault family
    # digits (chars 2-3). Why: a flat "engine" for every P-code would be too vague
    # to be useful on the dashboard.
    family = code[1:3]

    # P04xx resolves on its THIRD digit, so it is handled before the flat family
    # table. Why: the range is "auxiliary emission controls", a grab-bag that is not
    # all exhaust hardware — EVAP (P044x/P045x) is a fuel-vapour fault, often just a
    # loose fuel cap, and routing it to exhaust would recommend exhaust parts.
    if family == "04":
        # Slice rather than index: a truncated code like "P04" must still return a
        # zone instead of raising.
        sub = zones["p04_third_digit"].get(code[3:4])
        return sub["zone"] if sub else zones["defaults"]["p04"]["zone"]

    entry = zones["powertrain_family"].get(family)
    return entry["zone"] if entry else zones["defaults"]["powertrain"]["zone"]


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
