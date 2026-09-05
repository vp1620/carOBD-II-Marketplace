---
name: track-issue
description: Turn a problem discussed in conversation into tracked work. Searches existing GitHub issues and BACKLOG.md first so nothing is duplicated, then either comments on what already exists, opens an issue stating what it fixes and how, or files a BACKLOG story if the work is not near-term. Use when a discussion lands on something that needs doing later. Never opens a duplicate; never turns every idea into an issue.
allowed-tools: Bash, Read, Write, Edit, Grep
---

# track-issue — put a problem where it belongs, exactly once

A conversation surfaces a problem. This decides whether it becomes a GitHub issue, a
`BACKLOG.md` story, a comment on something that already exists, or nothing — and then
does that.

**The hard part is not writing the issue. It is not writing the fourth copy of it.**
Search before you create, every time.

## The two-surface split

Both exist on purpose. Do not merge them, and do not mirror one into the other.

| | `BACKLOG.md` | GitHub Issues |
|---|---|---|
| Holds | the whole roadmap — every epic and story, with rationale | only what is actually queued for work |
| Answers | "where is this project going?" | "what am I doing next?" |
| Lifetime | years | weeks |
| Ordering | by epic and phase | by milestone, then priority label |

52 stories live in `BACKLOG.md`. **Do not seed them all as issues** — most are later-phase
and would bury the handful that matter this month. An issue is created when work is
genuinely near-term. The story ID is the join key: an issue for a known story is titled
`DIAG-3: <short title>`.

## Step 1 — state the problem before touching anything

Write, in your own words, three things:
- **Problem** — what is broken, missing or risky. Concrete, not "improve X".
- **Fix** — what changes.
- **How** — the mechanism, enough that a reader can judge whether it would work.

If you cannot fill all three, the discussion is not finished. Say so and stop rather than
filing something vague — a vague issue is worse than no issue, because it looks tracked.

## Step 2 — find what already exists (both surfaces, always)

```bash
gh issue list --state all --search "<keywords>"     # open AND closed
grep -nE "<keywords>" BACKLOG.md
```

Search **closed** issues too. A closed one means this was decided before, and the reason
it closed usually matters more than the new idea.

Also check `DECISIONS.md` when the problem sounds like a design question — it may already
have been settled and deliberately deferred, in which case re-filing it loses the reason.

## Step 3 — route it

Pick exactly one:

- **An open issue already covers it** → add a comment with the *new* angle only. Do not
  restate the issue. Do not open a second one.
- **A closed issue covers it** → read why it closed. If the reason still holds, say so and
  stop. If genuinely new information changes it, open a new issue that links the old one
  and states what changed.
- **A `BACKLOG.md` story covers it, and the work is near-term** → open an issue titled
  `<STORY-ID>: <short title>`, linking back to the story. Do not duplicate the story text
  into the issue; summarise and reference.
- **A `BACKLOG.md` story covers it, and it is not near-term** → nothing to do. Sharpen the
  story in place if the discussion improved it.
- **Nothing covers it, and it is near-term** → add the `BACKLOG.md` story *and* open the
  issue. The story is the durable record; the issue is the queue entry.
- **Nothing covers it, and it is speculative or later-phase** → `BACKLOG.md` story only.

When unsure between issue and story, choose story. Backlog entries are cheap and quiet;
issues are a queue you have to look at.

## Step 4 — write it

Issue body, in this order and no longer than it needs to be:

```markdown
## Problem
What is wrong today, and what it costs. Reference real files/lines when they exist.

## What this fixes
The observable difference once done.

## How
The mechanism. Name the approach and the tradeoff taken.

## Done when
Checkable conditions, not a feeling.

---
Story: <ID> in BACKLOG.md · Depends on: <ID or #n> · Blocks: <ID or #n>
```

Rules:
- **Junior-readable.** Gloss jargon on first use (ELM327, PID, DTC, hex, fixture,
  golden-file, WebSocket, order analysis). Concrete examples over abstractions.
- **State the dependency.** Most stories here are gated on something (STORE-3 for vehicle
  records, PRED-3 for a baseline, a real write path). An issue that hides its blocker will
  get picked up and abandoned.
- Never invent acceptance criteria the discussion did not produce.

## Step 5 — place it in the order

Chronological layering is carried by the **milestone**; urgency within a milestone by the
**priority label**.

| Milestone | Meaning |
|---|---|
| `Phase 1 — Working demo` | reader → WebSocket → dashboard, deployed |
| `Phase 2 — Storage & agent` | persistence, RAG, marketplace groundwork |
| `Later phases` | everything gated on the two above |

| Label | Meaning |
|---|---|
| `p0` | blocking something already in progress |
| `p1` | next up once p0 clears |
| `p2` | real, not now |

```bash
gh issue create --title "..." --body-file <file> --milestone "Phase 1 — Working demo" --label p1
```

Every issue gets exactly one milestone and one priority label. An unlabelled issue is
invisible to the ordering, which defeats the point.

## Step 6 — report

Say which route was taken and why — especially when the route was "this already exists"
or "backlog only". Print the issue URL, or the story ID that was updated.

Never close an issue. Closing is the user's call, or a PR's (`Fixes #n`).
