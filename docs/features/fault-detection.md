---
id: DIAG
name: Fault detection
status: shipped
stories: [DIAG-1, DIAG-2]
prs: [2, 9]
key_files:
  - backend-OBD-reader/obd_reader/faults.py
  - backend-OBD-reader/obd_reader/data/dtc_generic.json
  - backend-OBD-reader/tests/test_faults_golden.py
  - test_files/faults/
---

# Fault detection

## What it does

A car's computer stores a **DTC** — a five-character fault code like `P0217` — when
something goes wrong. On its own that means nothing to a driver. This turns it into four
things the dashboard and the agent can use:

```python
describe("P0217")
# {"code": "P0217",
#  "description": "Engine over-temperature condition",
#  "severity": "critical",
#  "zone": "engine",
#  "deferrable": False}
```

`severity` drives the colour on screen. `zone` says roughly where on the car the problem
is. `deferrable` answers "can this wait?" — the question a budget-conscious owner
actually asks.

## How it works

Two of those four fields are **looked up**, two are **derived**, and the difference
explains most of the design.

| Field | Source |
|---|---|
| `description` | verbatim from `data/dtc_generic.json` |
| `severity` | verbatim from the same file |
| `zone` | computed from the code's prefix |
| `deferrable` | `severity != "critical"` |

The catalog is data because it will grow to thousands of entries fixed by a published
standard (SAE J2012). It lives in JSON rather than a Python dict so the planned Go port
can read the same file.

`zone_for()` is prefix logic, not a table lookup, so it works on codes nobody has
catalogued yet. Letters `C`/`B`/`U` map straight to chassis / body / network. `P` codes
split by their family digits — `P03` ignition, `P07`/`P08` transmission, and `P04`
resolves on its *third* digit.

**The one non-obvious choice:** nothing raises. Ever. `describe()` on garbage returns a
generic record and `zone_for()` on a truncated code returns a zone, because these run
inside the poll loop and one malformed frame must not take down the live feed for every
other reading.

## History

| PR | What it did |
|---|---|
| [#2](https://github.com/vp1620/carOBD-II-Marketplace/pull/2) | Built it — `describe()`, severity classification, prefix-based zones. Catalog started as dict literals inside `faults.py`. |
| [#2](https://github.com/vp1620/carOBD-II-Marketplace/pull/2) | Moved the catalog out to `data/dtc_generic.json`. It is reference data, not code, and a wrong description should show up as a reviewable diff. |
| [#9](https://github.com/vp1620/carOBD-II-Marketplace/pull/9) | Fixed `P04xx`, which mapped wholesale to `exhaust`. That range is *auxiliary emission controls* — an EVAP leak (often a loose fuel cap) was filing as an exhaust fault. Added the `emissions` zone. |
| [#9](https://github.com/vp1620/carOBD-II-Marketplace/pull/9) | Added golden case files so the mappings are pinned as data rather than inline asserts. |

## Gotchas

**Never generate the golden cases by running `describe()`.** Generated before #9, the
files would have contained `P0442 → exhaust`, freezing the bug as "expected" — and the
correct fix would then have *failed* the test and looked like a regression. The cases are
hand-written from the OBD-II ranges. Same rule as the deferred `/new-pid` skill in
`DECISIONS.md`.

**`test_case_files_are_well_formed` is load-bearing, not boilerplate.** Cases only assert
the fields they name, so an entry naming *no* fields would be checked against nothing and
pass green forever. That check is the only thing standing in front of it.

**Zone is not cosmetic.** It routes the parts catalog (MKT-1) and the planned 3D
affected-area view, so a wrong zone recommends the wrong parts to a driver.

**The zone mappings are unverified editorial judgement.** Particularly: every `P` family
without its own rule falls back to `engine`, which lumps fuel/air metering (`P01xx`,
`P02xx`), auxiliary inputs (`P05xx`) and computer output (`P06xx`) into one bucket.

## Related

- **DIAG-3** in `BACKLOG.md` — manufacturer-specific codes (`P1xxx`), the tier that
  actually grows per make. Blocked on STORE-3 and a real write path.
- [`decisions`](../../DECISIONS.md) — "DTC catalog: data file now, DB only for the tier
  that actually grows", and "P04xx is not all exhaust".
- [OBD reader](obd-reader.md) — produces the codes this consumes.
