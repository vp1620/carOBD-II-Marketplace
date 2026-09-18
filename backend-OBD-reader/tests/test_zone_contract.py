"""Assert the backend and the frontend agree about zone names.

This is a **contract test**: one side guarantees a set of values, the other side depends
on knowing all of them, and nothing in either codebase makes them agree. `faults.zone_for()`
can return nine zone names; `frontend-web/zone-icon.js` has to have a key for each. They
are in different languages, in different directories, and are only connected at runtime
by a WebSocket message — so nothing but a test can hold them together.

It is not hypothetical. PR #28 shipped `"emission"` where the backend emits `"emissions"`,
and it survived review, a manual browser check, and the whole existing suite. Two reasons
it went unnoticed:

  1. The fixture only ever produces `engine` and `ignition` zones, so the emissions icon
     never rendered.
  2. The miss is silent by design — an unknown zone falls back to the `unknown` icon
     rather than erroring, so the page looks fine and shows the wrong picture.

The fallback exists to make gaps *visible to a user*. This test makes them visible to CI,
which is the only place a typo gets caught before it ships.

Reading a JS file with a regex is crude, and it is the honest trade-off: the frontend has
no build step (a deliberate Phase 1 decision, app.js:2), so there is no module system to
import from. A brittle check that runs beats a clean one that does not exist.
"""

import json
import re
from pathlib import Path

import pytest

from obd_reader.faults import describe

REPO = Path(__file__).resolve().parents[2]
ZONES_JSON = REPO / "backend-OBD-reader" / "obd_reader" / "data" / "dtc_zones.json"
ZONE_ICONS_JS = REPO / "frontend-web" / "zone-icon.js"
SCENARIOS = REPO / "simulated_codes"


def backend_zones() -> set[str]:
    """Every zone name faults.zone_for() can return, read from the data it consults."""
    data = json.loads(ZONES_JSON.read_text())
    tables = ("by_letter", "powertrain_family", "p04_third_digit", "defaults")
    return {entry["zone"] for table in tables for entry in data[table].values()}


def frontend_zones() -> set[str]:
    """Keys of ZONE_PATHS in zone-icon.js.

    Regex rather than a parser: matches `"name":` at the start of an entry. Kept narrow
    so it cannot accidentally match path data, which is single-quoted.
    """
    return set(re.findall(r'^\s*"([a-z]+)"\s*:', ZONE_ICONS_JS.read_text(), re.MULTILINE))


def test_every_backend_zone_has_an_icon():
    """The contract: anything describe() can emit, the frontend can draw."""
    missing = backend_zones() - frontend_zones()
    assert not missing, (
        f"zone(s) the backend emits with no icon in zone-icon.js: {sorted(missing)}. "
        f"These render as the 'unknown' question-mark icon with no error — the page "
        f"looks fine and shows the wrong picture. Add a ZONE_PATHS entry, or fix the "
        f"spelling if this is a typo (this is how 'emission' vs 'emissions' happened)."
    )


def test_no_orphan_icons():
    """Icons for zones the backend cannot produce are dead weight.

    Not a correctness bug, but it means either a zone was removed from dtc_zones.json
    and the icon was left behind, or an icon was drawn for a zone that was never wired up.
    Both are worth knowing about.
    """
    orphans = frontend_zones() - backend_zones() - {"unknown"}
    assert not orphans, (
        f"icon(s) in zone-icon.js for zones the backend never emits: {sorted(orphans)}. "
        f"Either dtc_zones.json lost a mapping, or this icon was drawn speculatively."
    )


def test_unknown_icon_exists():
    """The fallback must exist, or a drifted zone renders an empty box instead.

    zoneIcon() falls back to ZONE_PATHS.unknown. If that key is missing the fallback is
    `undefined`, which produces an empty <svg> — the exact invisible failure the fallback
    was added to prevent.
    """
    assert "unknown" in frontend_zones(), "zone-icon.js has no 'unknown' key to fall back to"


# --- the simulated scenarios ---------------------------------------------------------

def scenario_files():
    if not SCENARIOS.is_dir():
        return []
    return sorted(p for p in SCENARIOS.glob("*.json") if p.name != "catalog-additions.json")


@pytest.mark.parametrize("path", scenario_files(), ids=lambda p: p.stem)
def test_scenario_resolves_to_drawable_zones(path):
    """Every code in every scenario maps to a zone the frontend can draw.

    Why bother, given the contract test above: a scenario can also go stale on its own —
    a code edited to a different prefix silently changes zone, and the README's claim
    about what it exercises quietly stops being true.
    """
    data = json.loads(path.read_text())
    codes = [c for r in data["records"] if r["type"] == "dtc" for c in r.get("codes", [])]
    undrawable = {describe(c)["zone"] for c in codes} - frontend_zones()
    assert not undrawable, f"{path.name}: zones with no icon: {sorted(undrawable)}"


def test_all_zones_scenario_actually_covers_all_zones():
    """all-zones.json is the scan-animation fixture; its whole value is total coverage.

    If a code in it is edited and coverage silently drops to seven, the scenario keeps
    passing every other check while no longer testing the thing it exists to test.
    """
    path = SCENARIOS / "all-zones.json"
    if not path.exists():
        pytest.skip("all-zones.json not present")
    data = json.loads(path.read_text())
    codes = [c for r in data["records"] if r["type"] == "dtc" for c in r.get("codes", [])]
    covered = {describe(c)["zone"] for c in codes}
    expected = backend_zones() - {"unknown"}
    assert covered == expected, (
        f"all-zones.json covers {sorted(covered)}; expected every drawable zone "
        f"{sorted(expected)}. Missing: {sorted(expected - covered)}"
    )
