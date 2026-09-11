#!/usr/bin/env python3
"""Render every zone icon at the size the fault banner actually uses, and open it.

WHY THIS IS A SCRIPT AND NOT A PAGE IN frontend-web/
    It is a development tool. `frontend-web/` is what ships to a user, and a legend for
    judging whether our own artwork reads is not part of the product. Same reasoning as
    `obd_reader/scenario.py`: scaffolding lives where scaffolding lives.

WHY IT STILL PRODUCES HTML
    The question this answers is *"does an 18px gear read as a gear in a browser?"*, and
    only a browser can answer it. Terminal rendering cannot: character cells are roughly
    1:2 rather than square, there is no antialiasing, and the stroke weight that makes an
    icon legible at 18px is exactly what a text grid destroys. An ASCII gear would tell you
    the gear has spokes — which you already know — and nothing about whether it reads.

WHAT IT IS FOR
    PR #28 shipped nine icons and said the one thing it could not verify was whether each
    one reads at 1.15em. Three do not: the transmission gear reads as a sun, the emissions
    cloud reads as weather, the ignition bolt reads as a generic warning triangle.

    That went unnoticed for a structural reason — the dashboard only ever shows icons for
    *currently active* faults, so two or three at a time. Nine can never be compared, and
    the daily fixture rotation shows a different subset each day, which hides it further.

USAGE
    python backend-OBD-reader/tools/show_icons.py          # write to a temp file and open
    python backend-OBD-reader/tools/show_icons.py --print  # write the path, open nothing
"""

import json
import os
import re
import subprocess
import sys
import tempfile
import webbrowser

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
FRONTEND = os.path.join(REPO, "frontend-web")
ZONES_JSON = os.path.join(REPO, "backend-OBD-reader", "obd_reader", "data", "dtc_zones.json")

# What each icon is *trying* to depict. Documentation for a human judging the drawing, so
# it lives here rather than in zone-icon.js, which the dashboard loads at runtime.
INTENT = {
    "engine": "cylinder block",
    "transmission": "gear",
    "exhaust": "tailpipe with gas",
    "emissions": "vapour cloud (EVAP / EGR)",
    "ignition": "spark / lightning bolt",
    "chassis": "wheel and suspension",
    "body": "car outline",
    "network": "connected modules (CAN bus)",
    "unknown": "question mark — the fallback",
}


def code_prefixes() -> dict[str, list[str]]:
    """Which DTC prefixes route to each zone, read from the mapping the backend uses.

    Derived rather than hardcoded: a hand-written list here would be a third copy of the
    zone table and would drift the way the `emission`/`emissions` typo did.
    """
    data = json.load(open(ZONES_JSON, encoding="utf-8"))
    out: dict[str, list[str]] = {}
    for prefix, e in data["by_letter"].items():
        out.setdefault(e["zone"], []).append(f"{prefix}xxxx")
    for fam, e in data["powertrain_family"].items():
        out.setdefault(e["zone"], []).append(f"P{fam}xx")
    for d, e in data["p04_third_digit"].items():
        out.setdefault(e["zone"], []).append(f"P04{d}x")
    for key, e in data["defaults"].items():
        out.setdefault(e["zone"], []).append(f"fallback ({key})")
    return out


def read_frontend_source() -> tuple[str, str]:
    """Pull ZONE_PATHS and zoneIcon() out of the real frontend files.

    Why read them rather than reimplement: this page must show what the dashboard shows.
    A second copy of the SVG wrapper here could differ in stroke-width or viewBox and the
    legend would be quietly lying about the thing it exists to check.
    """
    zone_icons = open(os.path.join(FRONTEND, "zone-icon.js"), encoding="utf-8").read()
    app = open(os.path.join(FRONTEND, "app.js"), encoding="utf-8").read()
    fn = re.search(r"function zoneIcon\(zone\)\s*\{.*?\n\}", app, re.S)
    if not fn:
        sys.exit("could not find zoneIcon() in frontend-web/app.js — did it get renamed?")
    return zone_icons, fn.group()


def build_html() -> str:
    zone_icons, zone_icon_fn = read_frontend_source()
    prefixes = code_prefixes()
    rows = json.dumps({z: {"intent": INTENT.get(z, "—"),
                           "codes": ", ".join(prefixes.get(z, [])) or "—"}
                       for z in INTENT})
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<title>carOBD — zone icon legend</title>
<style>
  body {{ margin:0; background:#0f1115; color:#e6e6e6;
         font-family: system-ui, sans-serif; }}
  .wrap {{ padding:28px; max-width:880px; }}
  h1 {{ font-size:20px; margin:0 0 4px; }}
  .sub {{ color:#8a8f98; font-size:14px; margin:0 0 26px; max-width:64ch; line-height:1.55; }}
  table {{ border-collapse:collapse; width:100%; }}
  th,td {{ text-align:left; padding:12px 10px; border-bottom:1px solid #262a33; vertical-align:middle; }}
  th {{ font-size:12px; text-transform:uppercase; letter-spacing:.05em; color:#8a8f98; font-weight:500; }}
  .name {{ font-weight:600; }}
  .codes {{ color:#8a8f98; font-size:13px; font-family:ui-monospace,Menlo,monospace; }}
  /* The point of the page: 1.15em on a 16px base, exactly what .zone-icon resolves to
     in the fault banner. A legend at 48px would report that everything looks fine. */
  .at-size {{ font-size:16px; }}
  .at-size svg {{ width:1.15em; height:1.15em; }}
  .big svg {{ width:64px; height:64px; }}
  .note {{ margin-top:26px; padding:14px 18px; border-radius:10px; font-size:14px;
           line-height:1.55; background:#12293d; color:#7fc4ff; border:1px solid #204f7a; }}
  .bad {{ background:#3d1212; color:#ff9a9a; border-color:#7a2020; }}
</style></head><body><div class="wrap">
<h1>Zone icon legend</h1>
<p class="sub">Every icon <code>faults.zone_for()</code> can produce, at the size the fault
banner renders it (<strong>1.15em &asymp; 18px</strong>) and blown up so the intended shape
is visible. <strong>If the small one does not read as the big one, that icon needs
redrawing.</strong> Generated from <code>frontend-web/zone-icon.js</code> and
<code>dtc_zones.json</code>, so it cannot drift from what the dashboard shows.</p>
<table><thead><tr><th>At size</th><th>Blown up</th><th>Zone</th><th>Meant to be</th>
<th>Codes that route here</th></tr></thead><tbody id="rows"></tbody></table>
<div class="note" id="drift"></div></div>
<script>{zone_icons}</script>
<script>
{zone_icon_fn}
const META = {rows};
const rows = document.getElementById("rows");
Object.keys(ZONE_PATHS).forEach((z) => {{
  const m = META[z] || {{ intent: "—", codes: "—" }};
  const tr = document.createElement("tr");
  tr.innerHTML = `<td class="at-size">${{zoneIcon(z)}}</td>`
               + `<td class="big">${{zoneIcon(z)}}</td>`
               + `<td class="name">${{z}}</td><td>${{m.intent}}</td>`
               + `<td class="codes">${{m.codes}}</td>`;
  rows.appendChild(tr);
}});
const undocumented = Object.keys(ZONE_PATHS).filter((z) => !META[z]);
const stale = Object.keys(META).filter((z) => !ZONE_PATHS[z]);
const d = document.getElementById("drift");
if (undocumented.length || stale.length) {{
  d.className = "note bad";
  d.textContent = (undocumented.length ? `Drawn but not described here: ${{undocumented.join(", ")}}. ` : "")
                + (stale.length ? `Described but no longer drawn: ${{stale.join(", ")}}.` : "");
}} else {{
  d.textContent = `All ${{Object.keys(ZONE_PATHS).length}} icons drawn and described. `
    + `Backend/frontend agreement is checked by tests/test_zone_contract.py; this page only `
    + `checks the legend against the artwork.`;
}}
</script></body></html>"""


def main() -> None:
    path = os.path.join(tempfile.mkdtemp(prefix="carobd-icons-"), "icons.html")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(build_html())

    if "--print" in sys.argv:
        print(path)
        return

    print(f"  wrote {path}")
    # webbrowser is stdlib and handles the platform differences; `open` as a fallback for
    # the case where no browser is registered, which happens on bare Linux boxes.
    if not webbrowser.open(f"file://{path}"):
        try:
            subprocess.run(["open" if sys.platform == "darwin" else "xdg-open", path],
                           check=False)
        except FileNotFoundError:
            print("  no browser found — open the path above manually")


if __name__ == "__main__":
    main()
