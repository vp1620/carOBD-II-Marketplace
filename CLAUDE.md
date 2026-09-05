# carOBD-II-Marketplace — Working Agreements

Terse index of how we work in this repo. Detail lives in the skills (loaded on
demand when invoked) and the docs linked at the bottom — don't duplicate it here.

## PR discipline
- One concern per branch/PR. If work drifts out of scope: say so, suggest a
  separate PR, and add the idea to BACKLOG.md. Don't silently bundle.
- Open PRs with the `/new-pr` skill (folds durable info into README, opens the
  PR). No per-PR doc files.
- Every change lands via PR — no direct pushes to `main`. (GitHub branch protection
  to enforce this is pending; note self-approval is impossible, so it must require 0
  reviews or it would lock the repo.)

## Decision log first
While a `decisions/*` PR is open, don't start new features and don't change code
structure or flow — merge the decision PR first. Bug fixes and genuine emergencies
are exempt.

Why: the log is only worth keeping if it stays ahead of the code it explains. A
backlog of unreviewed decision PRs means the reasoning is being written after the
fact, which is exactly what this log exists to prevent.

At the start of a session, check for an open `decisions/*` PR and say so before
starting feature work. This is a working agreement, not a hard block — Vishvesh can
waive it by saying so, and the emergency escape hatch on `main` is admin override
(which GitHub logs).

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

## Decisions
- Record substantive design decisions in DECISIONS.md (question → initial
  approach → concern → decision). Draft them with `/log-decisions`.

## Pointers
- Market/demand: docs/market/ (go-to-market + validation questions; findings/ is empty until customers are talked to)
- Roadmap: BACKLOG.md · Plan: DEVELOPMENT_PLAN.md · Skills: .claude/skills/
