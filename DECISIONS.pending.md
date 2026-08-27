> Drafted by the midnight curator on 2026-08-24. Review, move keepers into DECISIONS.md, then delete this file.

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
