---
name: log-decisions
description: Curate the decision cache into DECISIONS.md entries and open a PR for review. Reads .claude/decision-cache.jsonl plus the last 24h of git history, judges which changes were significant enough to record, appends entries to DECISIONS.md on a throwaway branch, and opens a decision-log PR. The PR review is the ratification step. Runs non-interactively. Never merges its own PR.
allowed-tools: Bash, Read, Write, Edit
---

# log-decisions — draft the day's decision-log entries and open a PR

Curates the raw prompt cache into `DECISIONS.md` entries. It **drafts**; the user
**ratifies**. That split is the point: automation does the tedious gather-and-filter,
and the human keeps final say so the log stays authentic (see DECISIONS.md — this
workflow exists so the log reflects real engagement, not machine output).

**Ratification happens in the PR.** Entries are written to `DECISIONS.md` on a
throwaway branch and opened as a pull request, which the user edits and merges. This
replaces the earlier `DECISIONS.pending.md` draft file: a local file relies on the user
noticing it, whereas a PR is versioned, reviewable, and cannot be silently forgotten.
An unedited draft still defeats the purpose — the PR body says so explicitly.

This skill NEVER merges its own PR, and never touches a branch the user is working on.

## Automated vs. manual

Most runs are automated by `.claude/hooks/run-curator.sh`, which fires from two
triggers (`SessionEnd`, and a nightly cron) and implements the steps below in shell —
deliberately, so no unattended model run performs git operations. See
`.claude/hooks/README.md`.

Invoking `/log-decisions` by hand does the same job for the current cache. Follow the
same rules; the honesty rules below are the part that matters most.

## Step 1 — gather inputs (both are required)
- **Prompt cache:** read `.claude/decision-cache.jsonl` (one `{ts, prompt}` per line).
  These are the day's *questions* — the seeds of decisions.
- **What actually changed:** run
  `git log --since="24 hours ago" --oneline` and
  `git log --since="24 hours ago" --stat` (and `git diff --stat` if there are
  uncommitted changes). The cache holds questions; git holds outcomes. You need
  both to reconstruct "question → change".

- **Transcript (when available):** the `SessionEnd` trigger supplies a
  `transcript_path` — the actual conversation, which is richer than prompts alone.
  Trim it; a long session's raw JSONL will swamp the context for no benefit.

**Hard gate — conversation evidence is required.** If there is no cached prompt and no
transcript, stop and write nothing, *even if there are commits*. A decision comes out
of a conversation; commits pushed from elsewhere or plain git tidying must never
produce a PR. A quiet day is supposed to produce nothing. Do not invent entries.

## Step 2 — judge significance (be strict; most prompts are noise)
Draft an entry ONLY for a decision that meaningfully shaped the project. Include if it:
- changed an **interface, data model, or architecture** (e.g. a new class/entity, a module boundary),
- **reversed or redirected** a generated approach (the user pushed back and the design changed),
- set a **convention or policy** (testing approach, doc rule, workflow), or
- **deferred** something with a stated reason/guardrail worth remembering.

Drop: mechanical edits, "commit it" / "yes" / "run it", typo/format fixes, and
routine progress. Collapse several related prompts across the day into ONE entry.
When unsure, lean toward dropping — a short honest log beats a padded one.

## Step 3 — append to DECISIONS.md on a branch, then open a PR
Match the entry template in `DECISIONS.md` exactly (dated `##` heading, a
**Status** line, and the five bulleted fields). Entries append at the end — the log
runs oldest-first.

- **Date entries with the SESSION date, not today's date.** The nightly run fires after
  midnight, so it is usually curating the *previous* calendar day. Take the date from
  the newest cached prompt.
- Work on a `decisions/<session-date>` branch cut from `origin/main`, in a **separate
  git worktree** — never check out over the user's working tree.
- **One decision PR per day.** If that day's PR is already open, append to it and
  rewrite its body; do not open a second.
- The PR body leads with a **summary of what was decided**, not run statistics, and
  states that entries are machine-drafted and need editing before merge.
- Title it `DEC-<n>: decision log update — <session-date>`, where `<n>` is the next
  number in the **decision series** — count every PR whose head branch starts with
  `decisions/`, in all states, and add one. All states, so a closed PR's number is
  never reused.

  This series is deliberately separate from the roadmap's `PR 1` / `PR 2` titles, so
  decision PRs never consume roadmap numbers. Note it is also separate from GitHub's
  own PR number, which is assigned server-side from a counter shared with issues and
  cannot be chosen — both numbers will appear, and that is expected.

**Honesty rules (non-negotiable):**
- Attribute accurately. If the user raised the question, say so; if a change was
  surfaced by the tool/refactor rather than the user, phrase it neutrally — never
  credit the user with a catch that wasn't theirs. The user must be able to defend
  every entry in an interview.
- Base "what changed" on the real git diff, not on what the prompt hoped for.
- Plain language, junior-readable, consistent with the repo's doc conventions.

## Step 4 — rotate the cache
After drafting, preserve provenance and reset the working set:
- Append the processed lines of `.claude/decision-cache.jsonl` to
  `.claude/decision-cache.archive.jsonl`.
- Truncate `.claude/decision-cache.jsonl` to empty.
(Both files are gitignored local scratch. Storage is trivial — prompt text is tiny —
so there is no compression step; the archive is for provenance only.)

## Step 5 — report (never merge)
Print: how many prompts were processed, how many entries were drafted (and how many
candidates were dropped as insignificant), and the PR URL awaiting review.

**Never merge the PR.** Merging is the ratification, and ratification is the user's.
Never touch a branch other than the `decisions/*` one, and never leave the user's
working tree modified.
