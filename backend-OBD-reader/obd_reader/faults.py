"""Turn a raw DTC code (e.g. "P0217") into human meaning the UI and agent can use.

Pure lookup/logic with no I/O, so it is trivially testable and safe to call on any
string — including codes we have not mapped yet (it degrades to a generic entry
rather than raising).
"""

# Plain-language text for the codes our fixtures emit plus other common ones.
# Why: a raw DTC is meaningless to a driver; this is the minimum "what is it" the
# dashboard needs to show, and the baseline the agent can later enrich.
DTC_DESCRIPTIONS: dict[str, str] = {
    "P0101": "Mass Air Flow (MAF) sensor range/performance problem",
    "P0131": "O2 sensor low voltage (Bank 1, Sensor 1)",
    "P0135": "O2 sensor heater circuit malfunction (Bank 1, Sensor 1)",
    "P0171": "Fuel system too lean (Bank 1)",
    "P0174": "Fuel system too lean (Bank 2)",
    "P0217": "Engine over-temperature condition",
    "P0300": "Random/multiple cylinder misfire detected",
    "P0301": "Cylinder 1 misfire detected",
    "P0302": "Cylinder 2 misfire detected",
    "P0303": "Cylinder 3 misfire detected",
    "P0304": "Cylinder 4 misfire detected",
    "P0305": "Cylinder 5 misfire detected",
    "P0306": "Cylinder 6 misfire detected",
    "P0307": "Cylinder 7 misfire detected",
    "P0308": "Cylinder 8 misfire detected",
    "P0420": "Catalyst system efficiency below threshold (Bank 1)",
    "P0562": "System voltage low",
    "P0087": "Fuel rail/system pressure too low",
}

# Codes we treat as immediately serious. Why: these can strand the driver or cause
# engine damage if ignored, so the UI must flag them red and mark them non-deferrable.
_CRITICAL_CODES = {
    "P0217", "P0087", "P0562",
    "P0300", "P0301", "P0302", "P0303", "P0304", "P0305", "P0306", "P0307", "P0308",
}

# Codes that matter but usually aren't drive-stopping. Why: lets the UI distinguish
# "get this looked at soon" from "handle now", which is the enthusiast triage signal.
_WARNING_CODES = {"P0171", "P0174", "P0101", "P0131", "P0135", "P0420"}


def severity_for(code: str) -> str:
    """Classify a code as critical/warning/info.

    Why: a single place that drives UI color and the "what needs attention now vs.
    later" ranking, instead of scattering thresholds across the frontend.
    """
    if code in _CRITICAL_CODES:
        return "critical"
    if code in _WARNING_CODES:
        return "warning"
    return "info"


# DTC first letter selects the top-level vehicle system.
# Why: the non-powertrain families map cleanly by letter alone, so we avoid a
# per-code table for them.
_LETTER_ZONE = {"C": "chassis", "B": "body", "U": "network"}


def zone_for(code: str) -> str:
    """Map a code to a coarse body zone from its prefix.

    Why: powers fault grouping and the future 3D "highlight the affected area" view;
    kept prefix-based (not per-code) so it works on codes we haven't described, and
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
        return "exhaust"
    if family == "03":
        return "ignition"
    return "engine"


def describe(code: str) -> dict:
    """Return everything the UI/agent needs to render one fault, in a single call.

    Why: centralizes fault meaning so callers never parse codes themselves, and it
    degrades gracefully — an unmapped code yields a generic entry instead of an error,
    which keeps the live feed robust against codes we haven't catalogued.
    """
    severity = severity_for(code)
    return {
        "code": code,
        "description": DTC_DESCRIPTIONS.get(code, "Unrecognized code — needs diagnosis"),
        "severity": severity,
        "zone": zone_for(code),
        # deferrable answers "can this wait?" — Why: the enthusiast "what can I put
        # off" signal; anything critical is, by definition, not deferrable.
        "deferrable": severity != "critical",
    }
