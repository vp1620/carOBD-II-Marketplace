---
name: log-decisions
description: End-of-day curation of the decision cache into DECISIONS.md drafts. Reads .claude/decision-cache.jsonl plus the last 24h of git history, judges which changes were significant enough to record, and writes proposed entries to DECISIONS.pending.md for the user to review and ratify. Runs non-interactively (safe for a midnight cron). Does NOT edit DECISIONS.md, commit, or push.
allowed-tools: Bash, Read, Write, Edit
---

# log-decisions — draft the day's decision-log entries for morning review

Curates the raw prompt cache into candidate `DECISIONS.md` entries. It **drafts**;
the user **ratifies**. This split is deliberate: a midnight cron does the tedious
gather-and-filter while asleep, and the human keeps final say so the log stays
authentic (see DECISIONS.md — this workflow exists so the log reflects real
engagement, not machine output). Therefore this skill NEVER writes to
`DECISIONS.md`, and NEVER commits or pushes.

## Step 1 — gather inputs (both are required)
- **Prompt cache:** read `.claude/decision-cache.jsonl` (one `{ts, prompt}` per line).
  These are the day's *questions* — the seeds of decisions.
- **What actually changed:** run
  `git log --since="24 hours ago" --oneline` and
  `git log --since="24 hours ago" --stat` (and `git diff --stat` if there are
  uncommitted changes). The cache holds questions; git holds outcomes. You need
  both to reconstruct "question → change".

If the cache is empty **and** there were no commits in the window, write nothing
and stop (report "nothing to curate"). Do not invent entries.

## Step 2 — judge significance (be strict; most prompts are noise)
Draft an entry ONLY for a decision that meaningfully shaped the project. Include if it:
- changed an **interface, data model, or architecture** (e.g. a new class/entity, a module boundary),
- **reversed or redirected** a generated approach (the user pushed back and the design changed),
- set a **convention or policy** (testing approach, doc rule, workflow), or
- **deferred** something with a stated reason/guardrail worth remembering.

Drop: mechanical edits, "commit it" / "yes" / "run it", typo/format fixes, and
routine progress. Collapse several related prompts across the day into ONE entry.
When unsure, lean toward dropping — a short honest log beats a padded one.

## Step 3 — write drafts to DECISIONS.pending.md (never DECISIONS.md)
Match the entry template in `DECISIONS.md` exactly (dated `##` heading, a
**Status** line, and the five bulleted fields). Prepend a one-line banner:
`> Drafted by the midnight curator on <date>. Review, move keepers into DECISIONS.md, then delete this file.`
Append to `DECISIONS.pending.md` if it already exists (don't clobber unreviewed drafts).

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

## Step 5 — report (do not commit)
Print: how many prompts were processed, how many entries were drafted (and how many
candidates were dropped as insignificant), and the reminder that
`DECISIONS.pending.md` awaits the user's morning review. Leave all files uncommitted.
