---
name: pr-doc
description: Generate or update the PR documentation file (docs/prs/PRn.md) for the current branch in the project house style — review-order table, a Data flow section when review order differs from runtime flow, and a junior-level Key terms glossary. Use when finishing a PR, preparing a branch for review, or when asked to write/update a PR doc. This is the ONLY way PR docs should be created — never hand-write docs/prs/*.md ad hoc.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# pr-doc — generate the PR documentation file

Produce (or update) `docs/prs/PRn.md` for the current branch. These docs are the
single artifact a reviewer reads to understand a PR, so they follow a fixed house
style. This skill IS the process for making them — do not hand-write PR docs
outside of it, and do not skip any required section.

## Step 1 — gather the facts (don't guess)

Run these and read the results before writing anything:

1. Current branch and default branch:
   `git branch --show-current` ; default branch is `main`.
2. Files changed vs. main, with stats:
   `git diff main...HEAD --stat` and `git diff main...HEAD --name-status`.
3. The actual changes, so descriptions are concrete not vague:
   `git diff main...HEAD` (read it; base every "what it does" on real code).
4. Next PR number: list `docs/prs/` — if `PR1.md`..`PRn.md` exist, this is `PR(n+1).md`
   unless the user names a specific number or you're updating an existing one.
5. Skim `BACKLOG.md` for the roadmap, to fill the "Not in this PR (coming next)" list.

If the branch has no diff vs main, stop and tell the user — there's nothing to document.

## Step 2 — write docs/prs/PRn.md using this exact section order

```
# PR N — <short title>

**Branch:** `<branch>` → `main`
**Goal:** <2–3 sentences: what this PR turns into what, and what's explicitly out of scope>

## Why this PR exists
<Why this work is needed now, in plain terms.>

## Key terms (read this first if you're new to <domain>)
<Plain-language glossary. REQUIRED whenever the PR uses any domain jargon or
acronym. One bullet per term: the term in bold, then a junior-friendly definition
with a concrete example. Define every acronym on first use.>

## Review guide — click through the changes
Suggested reading order (each link opens the file):

| # | File | What it adds & why |
|---|------|--------------------|
| 1 | [`path`](../../path) | <what it adds AND why it exists — concrete, tied to the real change> |
| ... |

<Order the table DEPENDENCY-FIRST (foundations before the code that uses them),
which is a *reading* order for review, not the runtime order.>

## Data flow (≠ the reading order above)
<REQUIRED whenever the review/reading order differs from the path data actually
takes at runtime. Show the runtime path as an arrow diagram in a code block, e.g.
live path and fixture/test path. Add short notes for any stage that is a lookup
called by another stage, or any file that is off the live path. OMIT this whole
section only when reading order and runtime order genuinely coincide.>

## Testing approach
<How the change is tested and why that approach. Name the test files and fixtures.>

## How to verify
```bash
<real, copy-pasteable commands that a reviewer can run, with expected output>
```

## Not in this PR (coming next)
<Bulleted list of the next PRs / deferred work, pulled from BACKLOG.md.>
```

## Step 3 — apply the house rules (non-negotiable)

- **Never vague.** Every description must be understandable by someone at a
  **Junior Engineer** level. Spell out domain jargon on first use (e.g. for this
  project: ELM327, PID, DTC, Mode 01/02/03, freeze-frame, hex, fixture,
  golden-file test, Gherkin/BDD, WebSocket) with a short plain-language gloss.
  Assume the reader is competent but new to the domain and this codebase.
- **Concrete over abstract.** Prefer "turns raw hex like `41 0C 1A F8` into
  `1726.0` rpm" over "decodes data". Show real examples from the diff.
- **Data flow ≠ reading order.** Keep the review table dependency-first, and add
  the Data flow section whenever runtime order differs. Don't let a reader assume
  the table is the data path.
- **Base everything on the real diff.** Do not invent files, behaviors, or test
  counts — read the code and the test output first.
- **Link every file** in the table with a working relative path
  (`../../` from `docs/prs/` reaches the repo root).

## Step 4 — confirm

After writing, show the reviewer: the path written, and a one-line summary of each
section. Do not commit unless the user asks; if they do, commit ONLY the PR doc
with a `docs(prN): ...` message and the standard Co-Authored-By trailer.
