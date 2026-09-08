# Simulated fault scenarios

Recorded-shaped data for building the dashboard without a car. Each file is a drop-in
replacement for `test_files/sample_obd_output.json` — same format, same reader, same
code path. Nothing here is a mock: `FixtureReader` replays these through the real
`Reading` → `_enrich` → WebSocket → `renderFaults` pipeline, so what you see in the
browser is what a car producing those codes would look like.

**A DTC** (Diagnostic Trouble Code) is the five-character code an engine computer stores
when something goes wrong, e.g. `P0217`. **A zone** is the coarse area of the car it
points at — `faults.py` derives it from the code's prefix, and it drives which icon shows.

---

## Running one

There is a blocker first. `make_reader()` (`reader.py:128`) never passes a path:

```python
return FixtureReader(vehicle_id=vehicle_id)
```

`FixtureReader.__init__` already accepts `path`, so it is a one-line change to read an
env var — then:

```bash
OBD_FIXTURE=simulated_codes/all-zones.json ./obdvenv/bin/python backend-OBD-reader/main.py
```

Until that exists, swap the file by hand or point `_FIXTURE` at a scenario temporarily.
Worth doing properly: you will switch scenarios constantly while building the UI, and
editing a constant each time gets old within an hour.

---

## Why these exist — two gaps in the current fixture

**The existing fixture exercises 2 of 8 zones.** Its only codes are `P0217`, `P0171`
(both `engine`) and `P0302` (`ignition`). Six zone icons — transmission, exhaust,
emissions, chassis, body, network — never render from it. That is why the
`emission`/`emissions` key typo in `zone-icon.js` survived: nothing in the fixture
produces an emissions zone, so the wrong-icon fallback never fired.

**There are no `info`-severity codes anywhere.** The catalog is 12 critical and 6
warning. So `rank()`'s `info: 0` (`app.js:20`) and `.fault-banner.info` (`style.css:24`)
are code paths you have never seen run. `gas-cap.json` is the first thing that will
exercise them — and only after `catalog-additions.json` is merged.

---

## The scenarios

| File | Codes | Zones | What the UI should do |
|---|---|---|---|
| `healthy.json` | none | — | Gauges populate, no banner. After a scan, every zone icon stays **grey**. |
| `gas-cap.json` | 1 | emissions | One icon, **blue** `info` styling. First render of `.fault-banner.info`. |
| `severity-mix.json` | 3 | engine, emissions | Engine icon takes **critical**, not warning. Watch the info code get wrongly reddened. |
| `all-zones.json` | 8 | all 8 | Eight distinct icons. **No `unknown` icon should appear.** |
| `uncatalogued.json` | 4 | engine, emissions, transmission, chassis | Correct icons, generic text, all `info`. |
| `limp-mode.json` | 12 | 6 zones | Collapsed banner must summarise; expanded panel must scroll. |

### What each one is really for

**`healthy.json`** — the state you will look at most and design for least. Note the
distinction your scan UI needs to make: *checked and clean* is not the same as *not yet
checked*, and both are "no faults". Grey-for-both loses that.

**`gas-cap.json`** — `P0442` is a small EVAP leak, famously a loose fuel cap. It lights
the check-engine lamp and nothing is wrong. It is the honest test of `deferrable` in
`describe()`, and the only `info` code proposed.

**`severity-mix.json`** — the one that shows you the bug. `app.js:47` puts a single
severity class on the whole banner, so the `info`-level `P0442` renders in critical red
purely because `P0217` shares the bar. Row-per-fault fixes it; this is how you see it.

**`all-zones.json`** — the scan animation's real test. All eight icons at once. If an
`unknown` icon appears, a zone name in `dtc_zones.json` has no matching key in
`zone-icon.js` — the exact drift the fallback exists to catch.

**`uncatalogued.json`** — what a real car actually hands you. The catalog knows 18 codes;
the standard has thousands, and `P1xxx` codes are per-manufacturer (`DIAG-3`). Zone comes
from the prefix so it still works; description and severity fall back. The UI has to stay
useful knowing only *where* a fault is.

**`limp-mode.json`** — twelve faults that tell one coherent story: misfires wreck fuel
trim, raw fuel kills catalyst efficiency, the ECU drops the transmission into limp mode,
and failing bus voltage takes modules offline. Cars do fail all at once, and that is
exactly when the list most needs to be readable.

---

## Notes on the scan UI

- **The `unknown` icon is a drift detector, not a state.** All eight zone names have keys
  in `zone-icon.js`, so no valid data can produce it. To see it deliberately, add a zone
  to `dtc_zones.json` without adding an icon.
- **Zone-by-zone reveal is animation, not measurement.** Mode 03 returns every stored code
  in one response — there is no per-zone query to wait on. Sequencing is a presentation
  choice over data you already have in full. Legitimate, but decide it deliberately: it is
  the same class of claim as issue #26.
- **Severity is per fault, zone colour is per zone.** A zone with a warning and a critical
  shows critical. That is `rank()` applied per group rather than globally.

---

## `catalog-additions.json`

Fourteen proposed entries covering the five zones with no catalogued code. **Not loaded by
anything** — it is a review queue.

Descriptions are the generic SAE J2012 meanings and are facts. **Severities are not.**
Per the `DIAG-3` guardrail, only `description` may come from an outside source; `severity`
stays a human judgement so the UI never marks something critical on the say-so of a
scrape. The proposed values are Claude's, with reasoning in `_severity_notes_for_review`.

Fold them into `dtc_generic.json` as a **separate commit** — that is catalog data, not
simulation, and mixing them makes the diff unreviewable.
