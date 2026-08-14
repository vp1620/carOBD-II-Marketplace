---
name: new-pr
description: Create a new pull request for the current branch. Reads the branch diff, folds durable high-level information and important commands into the master README.md (adding new info OR altering existing info), then opens the PR with gh — the file-by-file review guide goes in the PR description, not a checked-in file. Use whenever a branch is ready to become a PR. This REPLACES the retired per-PR docs/prs/*.md files; do not create those.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# new-pr — open a PR and keep the README current

This is the single workflow for turning the current branch into a pull request.
It does two jobs so documentation never drifts:

1. **Updates the master `README.md`** with the *durable* high-level information and
   important commands the change introduces — the living documentation everyone reads.
2. **Opens the PR** with `gh`, putting the *ephemeral* review guide (file-by-file
   table, how-to-verify) in the PR description, where point-in-time review notes belong.

There are NO per-PR markdown files (`docs/prs/*.md` is retired). Durable info lives in
the README; ephemeral review info lives in the GitHub PR description.

## Step 1 — gather the facts (don't guess)
- `git branch --show-current` (head) ; base is `main`.
- `git diff main...HEAD --name-status` and `--stat` — the changed files.
- `git diff main...HEAD` — read it, so every description is concrete, not vague.
- `git log main..HEAD --oneline` — the commits going into the PR.
If there is no diff vs `main`, stop and say so — there's nothing to PR.

## Step 2 — update README.md (add OR alter — never blind-append)
Decide, per piece of information, whether it is **durable** (belongs in the README) or
**ephemeral** (belongs only in the PR description).

Durable → merge into the README:
- **High-level: what the change adds/alters at a system level** — update the relevant
  existing section if one exists (e.g. Repository Structure, a data-flow section, Tech
  Stack); create a new section only if none fits.
- **Important commands** the change introduces (how to run/test/use it) — fold into the
  existing commands/quick-start areas.

Editing rules:
- **Alter in place, don't duplicate.** If a section already covers the topic, update it;
  don't append a second copy.
- **Never vague. Junior-Engineer readable.** Gloss domain jargon on first use (ELM327,
  PID, DTC, Mode 01/02/03, freeze-frame, hex, fixture, golden-file, Gherkin/BDD,
  WebSocket). Prefer concrete examples ("`41 0C 1A F8` → `1726.0` rpm") over abstractions.
- **Keep a data-flow explanation** when the change affects how data moves through the
  system, and make clear that a module's *reading order* is not necessarily the *runtime*
  path the data takes.
- Base everything on the real diff — do not invent files, behaviors, or command output.

Commit the README change on the branch with a `docs(readme): ...` message and the
standard `Co-Authored-By` trailer, then push the branch.

## Step 3 — open the PR
Compose a title and a body. The body is the *ephemeral* review guide:
- one-paragraph summary of the change,
- a **Review guide** table (dependency-first reading order): file → what it adds & why,
- a **How to verify** block with real, copy-pasteable commands,
- a short **Not in this PR** list from `BACKLOG.md`.

Then:
```bash
gh pr create --base main --head "$(git branch --show-current)" --title "<title>" --body "<body>"
```
If `gh` is missing or not authenticated, print the title + body for the user to paste,
and tell them how to authenticate (`gh auth login`).

## Step 4 — confirm
Report: which README sections were added vs. altered, the commit that carried them, and
the PR URL (or the body to paste). Do not touch files unrelated to this change.
