---
id: —
name: Decision curator
status: in progress
stories: []
prs: [7]
key_files:
  - .claude/hooks/run-curator.sh
  - .claude/hooks/curator-trigger.sh
  - .claude/hooks/README.md
  - .claude/skills/log-decisions/SKILL.md
---

# Decision curator

> **Status: not yet merged (PR #7), and it has never run.**

## What it does

Drafts entries for `DECISIONS.md` from a session's conversation and the real git diff,
then opens a PR. Reviewing that PR is how an entry gets ratified.

## How it works

Two triggers, whichever fires first — the session ending, or a nightly cron. No
coordination is needed between them: the first run rotates the prompt cache, so the
second finds nothing and exits. That *is* the deduplication.

**The one non-obvious choice:** the shell does every git and PR operation; the model is
invoked with **no tools** and returns only text. An unattended run therefore cannot touch
the repo in a way nobody reviewed — the worst it can do is write prose into a PR you
then read.

Work happens in a detached git worktree, so a run started by closing a terminal can never
disturb an in-progress branch.

## History

| PR | What it did |
|---|---|
| [#7](https://github.com/vp1620/carOBD-II-Marketplace/pull/7) | The curator, both triggers, the hooks README, and the amended skill contract. Not merged. |

## Gotchas

**It has never run.** The prompt cache has captured nothing since 2026-08-16, because
project hooks only load when Claude Code is launched **from the repo directory**. Started
from `~`, none of this fires. That is the actual blocker; everything else is plumbing.

**Entries are dated by session date, not run date.** The nightly run fires at 00:30,
already the next calendar day, so dating by the clock would claim a decision happened a
day after it did.

**A quiet day produces nothing, deliberately.** Commits alone never wake it — only
conversation evidence does. Git tidying with no session must not generate a PR.

**Merging #7 turns on `SessionEnd`.** With the write TODO unimplemented, every session
end would push a `decisions/*` branch with no PR attached. Finish that TODO first.

## Related

- `.claude/hooks/README.md` — the pipeline in detail. Not linked because it lands with #7; it does not exist on `main` yet.
- `DECISIONS.md` — "Decision curator: two triggers, and the PR becomes the ratify step".
