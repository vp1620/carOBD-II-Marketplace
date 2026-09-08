# `.claude/hooks/` — what each script does

**Hooks** are shell commands Claude Code runs automatically at defined moments (a
prompt is submitted, a tool finishes, a session ends). They are configured in
[`.claude/settings.json`](../settings.json), and they run *outside* the model — Claude
does not decide whether to run them, the harness does. That is the point: a hook can
enforce a workflow that a model might forget.

All four scripts live here. Nothing else in the repo is a shell script.

| Script | Fires on | What it does |
|---|---|---|
| [`decision-capture.sh`](decision-capture.sh) | `UserPromptSubmit` — every prompt you send | Appends the prompt to the decision cache. Dumb capture, no judgement. |
| [`curator-trigger.sh`](curator-trigger.sh) | `SessionEnd` — `/clear`, terminal exit, logout | Launches the curator in the background, then exits immediately. |
| [`run-curator.sh`](run-curator.sh) | *Not a hook* — called by `curator-trigger.sh` **and** by cron | Does the real work: drafts decision entries and opens a PR. |
| [`new-pr-reminder.sh`](new-pr-reminder.sh) | `PostToolUse` — new branch created, or a plan approved | Injects a reminder to open PRs via the `/new-pr` skill. |

> **Capture vs. curator.** *Capture* runs constantly and records raw prompts with no
> judgement. The *curator* runs once at the end and decides which of those prompts
> represented a real decision. Two different jobs, deliberately kept apart: judging
> significance needs the whole day's hindsight, which you do not have mid-conversation.
>
> The trigger and the worker are named as a pair — `curator-trigger.sh` starts it,
> `run-curator.sh` does it.

---

## The decision-log pipeline

Three of the four scripts are one system. Data flows like this:

```
  every prompt you send
        │
        ▼
  decision-capture.sh ──────► .claude/decision-cache.jsonl   (raw prompts, gitignored)
                                        │
        ┌───────────────────────────────┴───────────────────────────┐
        │                                                            │
  session ends (/clear, terminal close)                     00:30 local (cron)
        │                                                            │
        ▼                                                            │
  curator-trigger.sh ── nohup ──┐                                    │
                                ▼                                    ▼
                          run-curator.sh ◄───────────────────────────┘
                                │
                                ├─ gathers: cached prompts + 24h of git + transcript
                                ├─ asks the model which decisions were significant
                                ├─ appends entries to DECISIONS.md on a throwaway branch
                                ├─ opens a PR for you to review
                                └─ rotates the cache → archive
```

**Whichever trigger fires first wins.** There is no coordination between them: the
first run rotates the cache, so the second finds nothing and exits quietly. That is
the entire dedup mechanism.

**A quiet day produces nothing.** `run-curator.sh` hard-gates on conversation
evidence — cached prompts or a transcript. Commits alone never wake it, so git tidying
with no session cannot produce a PR.

---

## Why `run-curator.sh` is not itself a hook

Two reasons:

1. **`SessionEnd` hooks share a ~1.5 second budget** and cannot block session teardown.
   A curator run calls a model and opens a PR, taking minutes — it would be killed
   partway. So `curator-trigger.sh` detaches it with `nohup` (which also lets it
   survive the SIGHUP you get from closing a terminal) and returns instantly.
2. **Cron needs to call the same worker.** A hook script is only ever invoked by
   Claude Code; keeping the work in a plain script lets both triggers share it.

## Why the shell does the git work, not the model

Every git and PR operation in `run-curator.sh` is deterministic, so it belongs in
testable shell. The model is invoked with **no tools** and only ever returns text (the
drafted entries). An unattended run therefore cannot touch the repo in a way nobody
reviewed — the worst it can do is write prose into a PR you then read.

---

## Local scratch files (all gitignored)

| File | Purpose |
|---|---|
| `.claude/decision-cache.jsonl` | Prompts awaiting curation. Emptied after each run. |
| `.claude/decision-cache.archive.jsonl` | Every prompt ever curated, kept for provenance. |
| `.claude/curator.log` | What the curator did and why it exited. **Check here first when a PR you expected did not appear.** |
| `.claude/.curator.lock` | A directory, not a file — `mkdir` is atomic, and macOS has no `flock`. Prevents two curators racing when you close several terminals at once. |

---

## Gotchas

**Hooks only load when Claude Code is launched from the repo.** Project settings are
read from the working directory, so starting a session in `~` means *none* of these
run and `$CLAUDE_PROJECT_DIR` is never set. This is not hypothetical — the cache sat
empty from 2026-08-16 to 2026-08-24 for exactly this reason.

```bash
cd ~/VishveshFolder/carOBD-II-Marketplace   # then start Claude Code
```

**Scripts must be executable.** `chmod +x` after creating one. A non-executable script
fails silently — `curator-trigger.sh` guards with `[ -x "$RUNNER" ]` and simply exits.

**`jq` is deliberately not used.** All JSON parsing shells out to `/usr/bin/python3`
so the hooks work on a clean macOS with no extra installs.

---

## Testing a hook by hand

Hooks read their payload as JSON on stdin, so you can run them directly. Point them at
a sandbox first — a real run appends to your actual cache.

```bash
# capture: does it record a prompt?
mkdir -p /tmp/hooktest/.claude
echo '{"prompt":"test prompt"}' | CLAUDE_PROJECT_DIR=/tmp/hooktest .claude/hooks/decision-capture.sh
cat /tmp/hooktest/.claude/decision-cache.jsonl

# curator: what would it decide to do? (tail the log, it is the only output)
.claude/hooks/run-curator.sh "" manual-test ; tail -5 .claude/curator.log
```
