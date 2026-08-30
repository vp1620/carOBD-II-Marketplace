# Golden fault cases

One file per scenario. Each file states, for a handful of DTCs (the 5-character fault
codes a car's computer stores, e.g. `P0217`), what `describe()` must return for the
**derived** fields — `zone`, `severity`, `deferrable`.

`backend-OBD-reader/tests/test_faults_golden.py` loads every `*.json` here and checks
each one. Adding a case is a new file; no new test function.

## The rule that matters

**Never generate these values by running `describe()`.** Write them from the OBD-II code
ranges and check the code agrees. If they disagree, one of the two is wrong — and it is
not automatically the file.

This is not theoretical. Before PR #6, `zone_for()` mapped the whole `P04xx` range to
`exhaust`, so a generated golden file would have contained `P0442 → exhaust` — an EVAP
fault (usually a loose fuel cap) filed as an exhaust problem. The fix would then have
*failed* the golden test and looked like a regression. Generating expected values from
the code under test launders bugs into "expected".

Same guardrail as the deferred `/new-pid` skill in `DECISIONS.md`.

## Why only the derived fields

`description` and `severity` are looked up verbatim from `obd_reader/data/dtc_generic.json`.
Restating a description here would just copy the catalog and mean editing two files per
code. `zone` is *computed* from the code prefix, so it is the field that can actually
drift. Severity is included only where the critical/deferrable distinction is the point
of the case.

Only the fields a case names are checked — omit anything the scenario is not about.

That selectivity is why `test_case_files_are_well_formed` exists. It catches two things
the golden test cannot report usefully on its own:

- **An entry that asserts nothing** — `{"code": "P0442"}` with no expected fields. The
  golden test checks zero things and passes, green, forever. This is the one that can
  hide, and the only reason it does not is that check.
- **A typo'd field name** — `"zoen"` instead of `"zone"`. The golden test *does* fail
  here, but with `expected: 'emissions' / actual: None`, which sends you looking at
  `describe()` rather than at the typo three feet away. The well-formed check says
  `unknown field(s) ['zoen']` instead.

So it is not generic validation, and the first case means it is genuinely load-bearing.
Don't remove it.

## Format

```json
{
  "_case": "short title",
  "_why": "why this scenario is worth pinning",
  "codes": [
    {"code": "P0442", "zone": "emissions", "_why": "EVAP small leak"}
  ]
}
```

Keys starting with `_` are commentary and are never compared.
