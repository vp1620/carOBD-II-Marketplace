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

## Decisions
- Record substantive design decisions in DECISIONS.md (question → initial
  approach → concern → decision). Draft them with `/log-decisions`.

## Pointers
- Roadmap: BACKLOG.md · Plan: DEVELOPMENT_PLAN.md · Skills: .claude/skills/
