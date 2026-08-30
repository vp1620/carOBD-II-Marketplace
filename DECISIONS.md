# Decision Log

A running journal of design decisions — lightweight [ADRs](https://adr.github.io/)
(Architecture Decision Records). This project is built with AI assistance (Claude Code);
this log records where I **read the generated code, questioned it, and changed direction**,
so the reasoning behind the codebase is visible and reviewable — not just the final diff.

**Entry template**

```
## YYYY-MM-DD — <short title>

**Status:** done | deferred | planned

- **Question I raised —** …
- **Initially generated —** …
- **My concern —** …
- **Decision —** …
- **Files / follow-up —** …
```

---

## 2026-08-14 — Tests should be file-driven (golden-file), not hard-coded

**Status:** done

- **Question I raised —** Don't hard-code decode inputs in the test; read inputs from a file and diff the output against an expected file.
- **Initially generated —** A test with decode inputs and expected values written inline as assertions.
- **My concern —** Inline cases are hard to grow and can't be reused. I want to reuse the "raw capture → records" transformation to write Gherkin/BDD tests later.
- **Decision —** Adopt a golden-file test: read `sample_obd_raw_stream.txt`, produce output, diff against `sample_obd_output.json`.
- **Files / follow-up —** `backend-OBD-reader/tests/test_decoder.py`, `test_files/`.

---

## 2026-08-16 — The test must exercise the REAL code path, not a parallel copy

**Status:** done

- **Question I raised —** "stream.py is not the right way of testing since it's not using the functions the live path would use."
- **Initially generated —** The golden test decoded the capture through a separate `stream.py` module (`decode_stream`) — a second implementation of the parse/extract logic that only the test used. The code a real adapter drives was never exercised.
- **My concern —** A test that runs a parallel parser can pass while the real path is broken; the two silently drift. There were actually *three* copies of the decode logic.
- **Decision —** Inject a `FakeSerial` transport into the **real** `SerialReader` so the test drives the live path (framing → decode → `Reading`). Delete the duplicates (`stream.py`, `testing/test_record_parsing.py`, `obd-2-parsing.py`).
- **Files / follow-up —** `obd_reader/reader.py` (injectable `transport`), `tests/test_decoder.py`. The refactor also surfaced that `poll_once()` only read Mode 01 PIDs, so `decode_dtcs` had no live caller — added `poll_dtcs()` to fix that.

---

## 2026-08-16 — A `/new-pid` helper skill: deferred, with a correctness guardrail

**Status:** deferred

- **Question I raised —** Would a skill that adds a PID make the test suite more robust over time?
- **Initially generated —** A skill that scaffolds a new PID across the registry, fixture, and golden file, then runs the tests.
- **My concern —** It only helps if it doesn't cheat. If the skill fills the expected golden value by running the decoder, it enshrines a wrong formula as "golden" (bigger coverage, zero correctness).
- **Decision —** Not building it yet. When we do, the expected value must be supplied by me / the OBD-II spec and asserted against the decoder — never scraped from the decoder's own output.
- **Files / follow-up —** None yet (idea parked).

---

## 2026-08-16 — Domain modeling: Vehicle vs. Reading (is-a vs. has-a)

**Status:** planned

- **Question I raised —** Should there be a `Vehicle` superclass with `Sensor` and `ErrorRead` subclasses to keep things organized?
- **Initially generated —** (my proposal) inheritance — `Sensor` / `ErrorRead` extend `Vehicle`.
- **My concern —** A sensor reading is not a *kind of* vehicle, so inheritance is wrong here. A Vehicle **has** readings (composition). If anything subclasses, it's the readings themselves.
- **Decision —** `Vehicle` is a thin entity (identity + metadata) that *has* readings via a repository — not a fat aggregate holding every reading in memory. Split `Reading` into `SensorReading` / `FaultReading` (removes the `type ==` branching).
- **Files / follow-up —** Lands with persistence; the `Reading` split is the cheap first step.

---

## 2026-08-16 — `Problem` as a first-class derived entity (the marketplace's contract)

**Status:** planned

- **Question I raised —** I want a per-car list of *problems* that the marketplace reads to recommend parts + fixes, derived from a summary of all the readings.
- **Initially generated —** Readings (and fault codes) stored in a DB; consumers query them directly.
- **My concern —** A raw fault-code list isn't what the marketplace needs, and it shouldn't understand PIDs/hex. Problems are derived, deduplicated, and stateful (open → fixed), and can come from sensor trends with no DTC at all.
- **Decision —** Introduce `Problem` — distinct from `FaultReading` — as the derived, stateful entity the marketplace/agent/resale report consume. It's the decoupling boundary between the telemetry and commerce sides.
- **Files / follow-up —** Spine for the DIAG / MKT / AGENT / PRED / MAINT epics.

---

## 2026-08-24 — DTC catalog: data file now, DB only for the tier that actually grows

**Status:** done (file split) / planned (DIAG-3 manufacturer tier)

- **Question I raised —** For PR 2, is it better to keep the fault codes in a separate constants file, or even a DB that grows as new codes are found for specific types of vehicles?
- **Initially generated —** PR 2 shipped the code meanings as dictionary literals inside `faults.py` — `DTC_DESCRIPTIONS` plus two hard-coded sets (`_CRITICAL_CODES`, `_WARNING_CODES`) — mixed in with the lookup logic.
- **My concern —** The list is going to grow, and some codes are specific to a make of car, so hard-coded dictionaries in a logic module won't hold up. If it grows continuously, a database may be the right home rather than a file.
- **Decision —** Split the catalog out of `faults.py` into `data/dtc_generic.json`, but do **not** introduce a DB yet. Reviewing the codes showed they are really two datasets with different change rates: **generic** codes (`P0xxx`, `P2xxx`, `C0`, `B0`, `U0`) are fixed by a published standard and identical on every car, while **manufacturer-specific** codes (`P1xxx`, `C1/C2`, `B1/B2`, `U1/U2`) differ per make and are the only tier that grows. Everything currently in the repo is the generic tier. A DB for it would buy nothing and cost something real: `describe()` is a pure function today, and putting the catalog behind Postgres would mean the decoder needs a running database to decode — breaking the "test suite runs with no hardware or services" property (OBD-4) and the hermetic golden-file test. Reference data also belongs in the repo where a wrong description surfaces as a reviewable diff rather than a silent row edit. JSON rather than a `constants.py` specifically so the planned Go port (GO-1) can read the same catalog, which a Python dict could not provide. The DB becomes correct at the manufacturer tier, which needs two things that don't exist yet: vehicle records (STORE-3) to know the make, and a genuine runtime write path (AGENT-2/4, EVAL-3).
- **Files / follow-up —** `backend-OBD-reader/obd_reader/data/dtc_generic.json` (new), `backend-OBD-reader/obd_reader/faults.py` (rules only; catalog now read through a single `_load_catalog()` so the source can change in one place), tests unchanged and passing (11/11). Manufacturer tier tracked as **DIAG-3** in BACKLOG.md, with the guardrail that community/scraped sources may supply `description` only — `severity` stays a human judgement.

---

## 2026-08-24 — P04xx is not all exhaust: split emissions from exhaust zones

**Status:** done

- **Question I raised —** (not mine) Raised during review of the fault-detection code, not by me.
- **Initially generated —** `zone_for()` mapped the whole `P04xx` family to the `exhaust` zone.
- **My concern —** Confirmed the problem once it was pointed out: `P04xx` is "auxiliary emission controls", which also covers EGR (`P040x`), secondary air (`P041x`) and EVAP (`P044x`/`P045x`). An EVAP fault — often just a loose fuel cap — was being reported as an exhaust problem.
- **Decision —** Split the range on its third digit and add an `emissions` zone; catalyst (`P042x`/`P043x`) and exhaust pressure (`P047x`) stay `exhaust`. This matters beyond a label because zone routes the parts catalog (MKT-1) and the 3D affected-area view, so a wrong zone recommends the wrong parts. Lookup uses a slice, not an index, so a truncated code like `"P04"` still resolves rather than raising.
- **Files / follow-up —** `obd_reader/faults.py`, `tests/test_faults.py`, README zone mapping. Shipped as PR #6, stacked on PR #2 because `faults.py` does not exist on `main`.

---

## 2026-08-24 — Per-make control is capability data + release gates, not per-make toggles

**Status:** planned

- **Question I raised —** When onboarding each make, should there be toggles so we control which features are available and contain bugs that disrupt certain features?
- **Initially generated —** (my proposal) a per-make toggle per feature, one file per make.
- **My concern —** A bug affecting one make shouldn't disrupt the whole app, and new makes shouldn't silently enable half-working features.
- **Decision —** Separate the two things the proposal conflated. **Capability** ("what can this car do?") is permanent per-vehicle data, discovered from the ECU itself via the supported-PID bitmasks (`0100`/`0120`/`0140`) and stored on the vehicle record — not a hand-maintained per-make table, which would be wrong for trims and model years anyway. **Release gating** ("do we trust this yet?") is a real feature flag, but keyed feature-major with make as an *optional* narrowing, since most features fail make-independently; per-make-per-feature flags would be an N×M matrix that cannot be tested. Catalog trust becomes a `status: experimental | verified` field reusing the PRED-6 "general guidance — not yet personalized" hedge, rather than a separate mechanism.
- **Files / follow-up —** Not built. `features.yaml` schema + env-override precedence + a flag-expiry test to be storied in BACKLOG.md.

---

## 2026-08-24 — Rejected a graph/GraphQL context layer for token optimization

**Status:** deferred

- **Question I raised —** Should I implement a graph-based context layer (seen described as "GraphQL Claude context for less token usage") as a skill that runs at all times?
- **Initially generated —** Two conflated ideas: GraphQL as an MCP tool interface, and knowledge-graph memory servers.
- **My concern —** Token burn across long sessions.
- **Decision —** Don't build it. A skill that "runs at all times" is self-defeating — skills load on demand, so an always-on one *adds* tokens every turn. Claude Code already ships Tool Search, which defers tool definitions natively. And the repo already has the useful 80%: stable story IDs, terse index docs pointing at detail, load-on-demand. Automated traversal is the expensive, low-payoff remainder. Revisit if `DECISIONS.md` reaches ~50 entries and needs semantic retrieval; until then, build retrieval where it's the actual product feature (AGENT-1/2, Qdrant).
- **Files / follow-up —** None. Measure with `/context` before optimizing anything here.

---

## 2026-08-24 — Decision curator: two triggers, and the PR becomes the ratify step

**Status:** done (scripts) / planned (wiring)

- **Question I raised —** The curator should run on whichever comes first — 00:30 CT or the conversation closing (`/clear` or terminal exit) — and should open a PR for review, not a numbered roadmap PR.
- **Initially generated —** `/log-decisions` as originally written: drafts to `DECISIONS.pending.md`, and **never** commits, pushes, or writes `DECISIONS.md`.
- **My concern —** The draft file relies on me noticing it. Investigation confirmed the risk was real: the prompt cache sat empty from 2026-08-16 to 2026-08-24 and the skill had never once run, because project hooks only load when Claude Code is launched from the repo directory.
- **Decision —** Amend the skill's contract: the curator writes entries to `DECISIONS.md` on a throwaway branch and opens a PR, and **the PR review is the ratification step**. This keeps the "human ratifies" principle — arguably strengthens it, since a PR is versioned and can't be silently forgotten — while removing the reliance on spotting a local file. Supporting choices: the shell does all git/PR mechanics and the model runs with no tools and returns only text, so an unattended run can't touch the repo unreviewed; work happens in a detached git worktree so a background run never disturbs an in-progress branch; entries are dated by *session* date, not run date, because the 00:30 run is already the next calendar day; a hard gate on conversation evidence means commits alone never produce a PR; and one PR per day, appended to, so unreviewed decision PRs can't pile into a queue.
- **Files / follow-up —** `.claude/hooks/run-curator.sh`, `curator-trigger.sh`, `.claude/hooks/README.md`. Still to wire: `SessionEnd` in `settings.json`, the `SKILL.md` rewrite, the cron entry. The GitHub API calls were deliberately removed and left as TODOs to implement by hand.

---

## 2026-08-24 — Guardrails: branch protection and a written policy, not hard blocks

**Status:** done (protection deleted for a learning exercise — reapply)

- **Question I raised —** Should there be hard guardrails preventing conversations or edits while a decision PR is unmerged, and requiring the decision PR to merge before any other PR is touched — breakable only for emergencies?
- **Initially generated —** (my proposal) enforce both as hard blocks.
- **My concern —** The decision log rots if nothing forces it to be kept current.
- **Decision —** Don't hard-block. Review surfaced three problems: no hook can distinguish a bug fix from a feature, so the emergency exception collapses to self-declaration and trains me to bypass it; as a solo dev I am both author and approver, so a gate I can always open is a ritual; and it inverts the dependency, gating work on the documentation of that work. Landed instead on **GitHub branch protection** on `main` (PR required, 0 approvals — GitHub forbids self-approval, so requiring 1 would be a permanent lockout) with `enforce_admins: false` as an *auditable* emergency override, plus a **written working agreement in `CLAUDE.md`** that Claude honours and I can waive by saying so. Also noted: the log's decay traced to the hooks never firing, not to a lack of discipline — a plumbing bug, not a process one.
- **Files / follow-up —** `CLAUDE.md`. Protection was applied, then deliberately deleted so I can reapply it myself as a GitHub API exercise; `CLAUDE.md` currently claims `main` is protected and will be accurate again once I do.

---

## 2026-08-24 — Defer the DTC catalog to first use instead of import

**Status:** planned

- **Question I raised —** Isn't it bad to keep reloading all the codes? Shouldn't it only load info for codes that match what's being read?
- **Initially generated —** `_CATALOG = _load_catalog()` at module level, so the file is read as a side effect of importing `faults`.
- **My concern —** Loading the whole catalog when only a few codes are ever read looks wasteful.
- **Decision —** Keep loading the whole catalog; don't go per-code. It already loads once (module-level, and Python caches modules), and per-code loading would put disk I/O on a hot path called per fault — ~900KB for the full generic set is negligible against a ~50–80MB server baseline. The real defect is different: reading a file as an *import side effect* makes the module untestable, since the first import pins the real catalog for the whole run. Fix is `@cache` on the loader — same single read, but deferred to first use and resettable via `cache_clear()`. Only the loader gets cached, never `describe()`, which returns a mutable dict that callers could corrupt for everyone. The one regression — a broken catalog would surface at first lookup instead of at startup — is cancelled by calling the loader once explicitly in the server's `lifespan`, which is better than the current implicit behaviour. Per-make catalogs (DIAG-3) *do* load on demand, keyed by make.
- **Files / follow-up —** Deferred as a follow-up after PR #2 merges — `obd_reader/faults.py` (2 call sites), plus a warmup line in `server.py`. Add a BACKLOG story on `feat/fault-detection` after merge, not now, since BACKLOG.md differs across branches.

---

## 2026-08-29 — Android Auto ships as its own repo, but it is a client, not a microservice

**Status:** planned

- **Question I raised —** Android Auto should be a separate repo so the project ends up as a microservices setup; adding it to the backend would complicate the code too much.
- **Initially generated —** Nothing built; it sits under Future Concepts.
- **My concern —** Bolting a Kotlin surface onto the Python backend would tangle two ecosystems in one codebase.
- **Decision —** Separate repo, yes — but the reasoning is ecosystem, not architecture. An Android Auto app runs *on the phone* ("render 3D on the phone, push a flat image to the head unit"); it consumes the API like the React dashboard does and serves nothing. Calling it a microservice would invite service infrastructure it has no use for. The real reason to split is different language, toolchain and release cadence (Kotlin/Gradle/Play Store vs Python/uv). What actually makes a later split cheap is the **API contract**, not the repo boundary — and that pressure is live now, since `/ws` already has to serve the web dashboard and eventually React Native. If a genuine microservice is wanted, the agent layer is the better candidate: its heavy deps are already isolated behind a `pyproject` extra. Not creating the repo yet — nothing to put in it, and an empty repo is a second thing to keep in sync.
- **Files / follow-up —** None. Revisit when Phase 1 is done.

---

## 2026-08-30 — Golden fault cases: selective assertions, hand-written, never generated

**Status:** done

- **Question I raised —** Why not use the golden-file test method again for fault detection?
- **Initially generated —** Seven inline assertions spread across two test functions in `test_faults.py`.
- **My concern —** The decoder's golden-file approach worked well and should be reused where it fits.
- **Decision —** Adopt it, but **only for the derived fields** (`zone`, `severity`, `deferrable`). `description` and `severity` are read verbatim from the catalog, so restating them would copy `dtc_generic.json` into a second file and mean editing two files per code. Unlike the decoder's full-replica comparison, each case asserts **only the fields it names** — so a case stays about one claim. Structured as **one file per scenario** (my call; better than a single table because the story lives next to the codes that prove it, and adding a case is a new file rather than a merge-conflict-prone table edit). The non-negotiable rule: cases are **hand-written from the OBD-II ranges and never generated by running `describe()`** — generated before the P04xx fix, a file would have contained `P0442 → exhaust`, freezing the EVAP-as-exhaust bug as "expected" and making the correct fix look like a regression. Same guardrail as the deferred `/new-pid` skill.
- **Files / follow-up —** `tests/faults/test_golden.py`, `tests/faults/cases/` (PR #9, #15). `test_case_files_are_well_formed` is load-bearing, not boilerplate: it catches an entry that names no expected fields, which the golden test would otherwise pass green.

---

## 2026-08-30 — Tests split by what a failure tells you, and grouped per feature

**Status:** done

- **Question I raised —** Should `test_faults.py` be separate from `test_faults_golden.py`? And should there be a folder per feature holding a golden test, an assertion test, and that feature's JSON?
- **Initially generated —** Flat `tests/` directory, fixtures three levels away under `test_files/`, and the same mappings asserted in two places with partial overlap — nine codes in both files, four only inline.
- **My concern —** Neither file was authoritative, so adding a case meant guessing where it belonged.
- **Decision —** One folder per feature, cases co-located, and the two test kinds split by **what a red run tells you**: `test_golden.py` means "a mapping is wrong", `test_contract.py` means "a guarantee broke". Not everything becomes golden — a guarantee like "must not raise" cannot be expressed as a value comparison, and written as a case it would silently pass the moment the function returned a constant. One carve-out: `test_files/sample_obd_output.json` **cannot move**, because `reader.py`'s `FixtureReader` loads it at runtime, making it production input as well as test data.
- **Files / follow-up —** PR #15. Coverage rose despite the test count falling 15 → 13: 20 codes and 36 assertions, up from 23. Added two guarantees no golden case could catch — that `describe()` returns all five keys, and that the catalog is actually being read at all.

---

## 2026-08-30 — Zone mappings become data; both catalogs load lazily

**Status:** done

- **Question I raised —** We agreed not to keep JSON data inside `faults.py` but to load it in — the zone tables should be a bank somewhere reasonable too.
- **Initially generated —** The catalog was extracted in PR #2, but `_LETTER_ZONE` and `_P04_SUBZONE` stayed as dict literals and the family mapping stayed an if-chain.
- **My concern —** Same argument as the catalog: these are data sitting inside a logic module.
- **Decision —** Move them to `data/dtc_zones.json` — not `pids.py`, which is the Mode 01 *sensor* registry and a different domain. **Mappings become data, rules stay code**: `zone_for()` keeps the lookup order, the `code[3:4]` slice that survives a truncated code, and the fallbacks. The deciding argument was that I am about to research these against the OBD-II ranges, and as data a revision is a reviewable diff against a source. Took the deferred `@cache` change at the same time, so importing `faults` no longer touches the filesystem — verified as 0 cache misses at import and 1 across 51 lookups. Only the loaders are cached, never `describe()`, which returns a mutable dict that shared callers could corrupt.
- **Files / follow-up —** PR #14. Trade-off recorded in the docstring: a broken catalog now fails at first lookup rather than at import, so whatever starts the reader should call it once at startup. Nothing does yet.

---

## 2026-08-30 — Two tracking surfaces, and what an issue is actually for

**Status:** done

- **Question I raised —** I want active layering of priority segmented chronologically, and the skill should understand the problem, check what already exists on GitHub, and file a story or comment saying what the issue fixes and how.
- **Initially generated —** `BACKLOG.md` as a flat file of 52 stories with no notion of what is next, and nothing linking a PR to the work it does.
- **My concern —** I proposed container issues per feature, then noticed the flaw myself — such an issue never closes.
- **Decision —** Two surfaces, deliberately not mirrored: `BACKLOG.md` is the **roadmap** (everything, with rationale), GitHub Issues are **only what is queued now**, joined by story ID. The 52 stories are explicitly **not** 52 issues — most are later-phase and would bury the few that matter. No container issues: the epic already exists as a `BACKLOG.md` heading and the story-ID prefix already carries attribution, so a container would restate it and then drift. Chronological layering is the milestone; urgency is a `p0/p1/p2` label. Routing for work with no story: **fixing it now → just the PR** (an issue created and closed within the hour is ceremony); **noting it for later → an issue**, because otherwise there is nowhere for it to live.
- **Files / follow-up —** `/track-issue` skill (PR #10). First use surfaced a gap in my own routing table — it had no branch for bugs and chores, which is what issue #13 turned out to be.

---

## 2026-08-30 — Correcting a claim means grepping for it everywhere

**Status:** done

- **Question I raised —** Is this change consistent with the other changes in main and the different PRs?
- **Initially generated —** A docstring and a README that said the opposite of each other about what `test_case_files_are_well_formed` protects against.
- **My concern —** A correction had been applied in one place only, so the code and the docs disagreed.
- **Decision —** Adopt it as a repo convention: when correcting a claim about behaviour, **verify it by running it**, then `git grep` the phrase before pushing — a claim worth writing is usually written in two or three places. Verification leads because both wrong claims came from reasoning about the code instead of executing it. Placed in `CLAUDE.md` under Docs & code style, with comment-the-why and junior-readable, since all three are about keeping documentation honest. Note this is *not* covered by `/new-pr`'s "alter in place, don't duplicate", which is about avoiding a second copy while writing — the opposite failure.
- **Files / follow-up —** `CLAUDE.md` (PR #12, merged). It caught its first real case immediately: a docstring in PR #14 referencing a `server.py` warm-up that does not exist on `main`.

---

## 2026-08-30 — Calendar integrates for deadlines, not for merge events

**Status:** planned

- **Question I raised —** Connect a calendar that updates when a PR is merged — then, on reflection, build it for accurate deadlines instead.
- **Initially generated —** (my first framing) one calendar event per merged PR.
- **My concern —** Reframed it myself: a merged PR is a past event and a calendar is for scheduling future time, so the merge-event version fights the tool. GitHub's own history already records what shipped when.
- **Decision —** Build it for **deadlines**, which are genuine future commitments. GitHub milestones own the due date; the calendar is read for *capacity context* before a date is picked, then written one-way. That is not two-way sync — nothing contests ownership of the date. A new conflicting event prompts a conversation rather than silently moving the deadline, sized by **new commitment ÷ remaining unallocated time before the deadline**, because a one-hour meeting three weeks out and two interview days before a Friday deadline are the same hours and completely different facts. Learning time is scheduled the same way and comes out of the same budget — tied to queued stories (GO-1, DASH-1) rather than abstract skills, so it has a completion criterion and cannot rot.
- **Files / follow-up —** Not built. Calendar connection verified (`p.vishveshkumar@gmail.com`, America/Chicago). Needs: due dates on the milestones, and my real weekly hours plus the shipping/learning split. Note the throughput data cannot distinguish a queue stall from a deliberate pause — PR #2's 13.7 days was interview prep — which is itself an argument for the calendar supplying that context.
