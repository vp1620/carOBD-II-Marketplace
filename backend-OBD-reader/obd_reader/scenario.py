"""Pick which recorded scenario the fixture reader replays. **Development scaffolding.**

WHY THIS IS A SEPARATE MODULE
    `reader.py` is production code: it talks to a real adapter and turns bytes from a car
    into Readings. Deciding *which recording to replay on a Tuesday* is a convenience for
    building the dashboard offline, and it has no business sitting next to that.

    Keeping it here means the whole feature is one file plus one call site, so removing it
    is a two-line diff rather than an archaeology exercise.

HOW TO DECOMMISSION IT
    Delete this file, delete the `simulated_codes/` directory, and drop the three lines in
    `reader.make_reader()` that call `resolve()`. Nothing else imports it.

WHEN
    When reading from a real adapter is reliable enough that offline scenarios are no
    longer how the UI gets built — realistically once a working adapter is in hand and
    OBD-5 has captured enough real-car traces to replay instead. Those traces are strictly
    better test material than these hand-written scenarios, because they contain the
    things a car actually sends (`SEARCHING...`, `BUS INIT: ERROR`, partial frames) that
    nobody thinks to invent.

    Same rule as GO-5's fallback switch: scaffolding gets an expiry when it is added, or
    it becomes permanent by default.
"""

import datetime
import os

# Scenarios `OBD_FIXTURE=rotate` cycles through, one per calendar day.
#
# Why a rotation at all: building against a single recording is how six of the eight zone
# icons went unrendered for weeks, and how an `emission`/`emissions` typo survived review
# — the default fixture produces only two zones, so the other six were never on screen.
# Switching by hand requires remembering to switch, which is the part that fails.
#
# Why the DAY and not random: a random pick makes "it worked yesterday" meaningless, and a
# glitch cannot be reproduced by restarting. Keying on the date gives the variety without
# giving up reproducibility — it changes overnight, holds still all day, and can always be
# worked out after the fact.
#
# `healthy.json` is deliberately excluded: a day landing on it shows no faults at all,
# which reads as the app being broken rather than as a car that is fine. Still available
# by name.
ROTATION = [
    "simulated_codes/gas-cap.json",
    "simulated_codes/severity-mix.json",
    "simulated_codes/all-zones.json",
    "simulated_codes/uncatalogued.json",
    "simulated_codes/limp-mode.json",
]


def resolve(value: str, repo_root: str) -> str:
    """Turn an OBD_FIXTURE value into an absolute path, and say which was chosen.

    `value` is either "rotate" or a path. Relative paths resolve against the repo root
    rather than the cwd, so the same value works whether you launch from the repo or
    from anywhere else.

    The choice is always printed. Silent selection is what makes a rotation miserable to
    debug — you have to be able to see which recording you are looking at without guessing.
    """
    if value == "rotate":
        value = ROTATION[datetime.date.today().toordinal() % len(ROTATION)]
        source = "day rotation"
    else:
        source = "OBD_FIXTURE"

    path = value if os.path.isabs(value) else os.path.join(repo_root, value)
    print(f"using fixture: {os.path.relpath(path, repo_root)} ({source})")
    return path
