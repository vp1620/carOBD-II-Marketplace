# carOBD-II-Marketplace — Working Agreements

Terse index of how we work in this repo. Detail lives in the skills (loaded on
demand when invoked) and the docs linked at the bottom — don't duplicate it here.

## PR discipline
- One concern per branch/PR. If work drifts out of scope: say so, suggest a
  separate PR, and add the idea to BACKLOG.md. Don't silently bundle.
- Open PRs with the `/new-pr` skill (folds durable info into README, opens the
  PR). No per-PR doc files.

## Docs & code style
- Docs junior-readable: gloss jargon on first use (ELM327, PID, DTC, hex,
  fixture, golden-file, WebSocket). Prefer concrete examples over abstractions.
- Comment the *why* (intent) on every new function/class/variable — not the mechanics.
- When data flow changes, update the README data-flow section; note that a
  module's reading order ≠ the runtime path.
- Correcting a claim about how something behaves? **Verify it by running it**, then
  `git grep` the phrase before pushing — a claim worth writing is usually written in
  two or three places (README, docstring, PR body), and fixing one leaves the code and
  the docs contradicting each other.

## Tracking work
- Two surfaces, on purpose: `BACKLOG.md` is the **roadmap** (every story + rationale);
  GitHub Issues are only what's **queued now**. Don't mirror one into the other — the
  52 backlog stories are not 52 issues.
- File work with the `/track-issue` skill. It searches issues (open *and* closed) and
  BACKLOG.md before writing anything, so the same problem isn't tracked twice.
- Issue titles carry the story ID when one exists: `DIAG-3: <title>`.
- Every issue gets one milestone (chronological phase) + one priority label
  (`p0` blocking / `p1` next / `p2` real, not now). Unlabelled = invisible to the order.

## Decisions
- Record substantive design decisions in DECISIONS.md (question → initial
  approach → concern → decision). Draft them with `/log-decisions`.

## Pointers
- Market/demand: docs/market/ (go-to-market + validation questions; findings/ is empty until customers are talked to)
- Roadmap: BACKLOG.md · Plan: DEVELOPMENT_PLAN.md · Skills: .claude/skills/
