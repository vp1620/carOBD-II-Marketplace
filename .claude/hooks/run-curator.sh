#!/usr/bin/env bash
# The decision curator: turn the day's prompts + real git changes into drafted
# DECISIONS.md entries, and open a PR for review.
#
# Runs from TWO triggers, whichever fires first (see .claude/settings.json and the
# crontab entry):
#   1. SessionEnd  — the conversation ended (/clear, terminal exit, logout)
#   2. 00:30 local — nightly safety net, in case a hard kill skipped the hook
# Whichever runs first rotates the cache, so the second one finds nothing to do and
# exits quietly. That is the dedup mechanism — no extra bookkeeping needed.
#
# Why the shell does the git work and the model does not: every git/PR operation here
# is deterministic and reviewable, so it belongs in testable shell. The model is given
# NO tools and only ever produces text (the entries), which removes any chance of an
# unattended run touching the repo in a way nobody reviewed.
#
# Safety: never touches the user's working tree. All work happens in a throwaway
# git worktree cut from origin/main, so a background run can never disturb an
# in-progress branch or uncommitted edits.
set -uo pipefail

# Repo root from this script's location (.claude/hooks/run-curator.sh -> repo).
# Why not CLAUDE_PROJECT_DIR: cron has no Claude env, so we cannot rely on it.
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
CACHE="$REPO/.claude/decision-cache.jsonl"
ARCHIVE="$REPO/.claude/decision-cache.archive.jsonl"
LOG="$REPO/.claude/curator.log"
# mkdir is atomic, which makes it a valid lock. Why we need one: closing two terminals
# at once would otherwise start two curators racing on the same branch. macOS has no
# flock, so this is the portable option.
LOCK="$REPO/.claude/.curator.lock"

TRANSCRIPT="${1:-}"   # SessionEnd passes the conversation transcript; cron passes nothing
TRIGGER="${2:-cron}"  # for the log + PR body, so you can tell which trigger produced a PR

log() { printf '%s [%s] %s\n' "$(date -Iseconds)" "$TRIGGER" "$*" >> "$LOG"; }

if ! mkdir "$LOCK" 2>/dev/null; then
    log "another curator is running; exiting"
    exit 0
fi
# Clean up the lock and the worktree no matter how we exit, so a crash cannot wedge
# every future run.
cleanup() {
    rmdir "$LOCK" 2>/dev/null
    [ -n "${WORKTREE:-}" ] && git -C "$REPO" worktree remove --force "$WORKTREE" 2>/dev/null
}
trap cleanup EXIT

cd "$REPO" || exit 0

# --- Step 1: was there a conversation at all? --------------------------------------
# HARD GATE. This log records decisions, and a decision comes out of a conversation.
# Commits alone are NOT a trigger: work pushed from elsewhere, or plain git tidying
# with no session, must not wake the curator. Without conversation evidence we exit
# before spending a model call, so a quiet day produces no PR and costs nothing.
CACHE_LINES=0
[ -f "$CACHE" ] && CACHE_LINES=$(wc -l < "$CACHE" | tr -d ' ')

HAVE_CONVO=0
[ "$CACHE_LINES" -gt 0 ] && HAVE_CONVO=1
[ -n "$TRANSCRIPT" ] && [ -f "$TRANSCRIPT" ] && HAVE_CONVO=1

if [ "$HAVE_CONVO" -eq 0 ]; then
    log "no conversation in window (cache empty, no transcript) — exiting without a PR"
    exit 0
fi

# Commits are context for the entries, not a reason to run.
COMMITS=$(git log --since="24 hours ago" --oneline 2>/dev/null | wc -l | tr -d ' ')

# Date the work happened, which is NOT necessarily today: the nightly run fires at
# 00:30, so a session that ended at 11pm belongs to the previous calendar day. Take it
# from the newest cached prompt and fall back to today only if the cache is empty.
SESSION_DATE="$(/usr/bin/python3 -c '
import json, sys, datetime
try:
    lines = [l for l in open(sys.argv[1]) if l.strip()]
    print(json.loads(lines[-1])["ts"][:10])
except Exception:
    print(datetime.date.today().isoformat())
' "$CACHE" 2>/dev/null)"
[ -z "$SESSION_DATE" ] && SESSION_DATE="$(date +%Y-%m-%d)"

# --- Step 2: build the context blob ------------------------------------------------
# Everything the model needs, gathered by us. Why pre-gather instead of letting the
# model read files: it can then run with no tools and no permissions at all, which is
# what makes an unattended run safe.
CTX="$(mktemp)"
{
    # Stated first because every entry heading must carry it. The model must never
    # infer the date — it has no reliable clock, and the run often happens after
    # midnight, on the day AFTER the conversation it is describing.
    echo "=== SESSION DATE: $SESSION_DATE ==="
    echo "(Use exactly this date on every entry heading.)"
    echo
    echo "=== PROMPTS THE USER SENT (the day's questions) ==="
    [ "$CACHE_LINES" -gt 0 ] && /usr/bin/python3 -c '
import json, sys
for line in open(sys.argv[1]):
    try:
        d = json.loads(line)
        print(f"- [{d[\"ts\"]}] {d[\"prompt\"]}")
    except Exception:
        pass
' "$CACHE" || echo "(cache empty)"

    echo
    echo "=== WHAT ACTUALLY CHANGED (last 24h of git) ==="
    git log --since="24 hours ago" --oneline 2>/dev/null || true
    echo
    git log --since="24 hours ago" --stat 2>/dev/null | head -100 || true
    echo
    echo "--- uncommitted ---"
    git diff --stat 2>/dev/null || true

    # The transcript is the richest input, but only SessionEnd has one. Extract just the
    # message text and cap it: a long session's raw JSONL would swamp the context and
    # cost far more than the decisions are worth.
    if [ -n "$TRANSCRIPT" ] && [ -f "$TRANSCRIPT" ]; then
        echo
        echo "=== CONVERSATION TRANSCRIPT (trimmed) ==="
        /usr/bin/python3 -c '
import json, sys
LIMIT = 60000   # characters; enough for the arc of a session, not the whole thing
out = []
for line in open(sys.argv[1], errors="replace"):
    try:
        d = json.loads(line)
    except Exception:
        continue
    msg = d.get("message") or {}
    role = msg.get("role") or d.get("type") or ""
    content = msg.get("content")
    text = ""
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        text = " ".join(c.get("text", "") for c in content if isinstance(c, dict))
    text = text.strip()
    if role in ("user", "assistant") and text:
        out.append(f"[{role}] {text}")
blob = "\n\n".join(out)
# Keep the END of the session: decisions usually settle late in a conversation.
print(blob[-LIMIT:] if len(blob) > LIMIT else blob)
' "$TRANSCRIPT" 2>/dev/null || echo "(transcript unreadable)"
    fi
} > "$CTX"

# --- Step 3: ask the model to judge significance and draft entries -----------------
read -r -d '' INSTRUCTION <<'PROMPT'
You are the decision curator for a solo developer's project (carOBD-II-Marketplace).
Below is the day's material: the prompts the user sent, the real git changes, and
possibly the conversation transcript.

Draft entries for the project's DECISIONS.md — a journal of design decisions where the
developer read generated code, questioned it, and changed direction.

BE STRICT. Most prompts are noise. Draft an entry ONLY for a decision that:
  - changed an interface, data model, or architecture, OR
  - reversed/redirected a generated approach after the user pushed back, OR
  - set a convention or policy, OR
  - deferred something with a stated reason worth remembering.
Drop mechanical edits, "commit it"/"yes"/"run it", typo fixes, routine progress.
Collapse related prompts across the day into ONE entry. When unsure, DROP.

HONESTY RULES (non-negotiable):
  - Attribute accurately. If the user raised a point, say so. If a tool/refactor
    surfaced it, phrase it neutrally. NEVER credit the user with a catch that was not
    theirs — they must be able to defend every entry in a job interview.
  - Base "what changed" on the real git diff shown, never on what a prompt hoped for.
  - Plain, junior-readable language.

DATE: use the SESSION DATE given at the top of the material as the heading date on
EVERY entry. That is when the conversation happened. Do NOT use today's date and do
NOT infer a date from anything else — this log is a record of when decisions were
actually made, and the curator often runs after midnight.

Use EXACTLY this format per entry, separated by a line containing only ---

## <SESSION DATE> — <short title>

**Status:** done | deferred | planned

- **Question I raised —** …
- **Initially generated —** …
- **My concern —** …
- **Decision —** …
- **Files / follow-up —** …

Output ONLY the entries. No preamble, no commentary, no code fences.
If nothing meets the bar, output exactly: NOTHING_TO_CURATE
PROMPT

log "invoking model (cache=$CACHE_LINES commits=$COMMITS transcript=${TRANSCRIPT:-none})"
ENTRIES="$(claude -p "$INSTRUCTION" < "$CTX" 2>>"$LOG")"
rm -f "$CTX"

if [ -z "$ENTRIES" ] || printf '%s' "$ENTRIES" | grep -q "NOTHING_TO_CURATE"; then
    log "model judged nothing significant; rotating cache and exiting"
    [ "$CACHE_LINES" -gt 0 ] && cat "$CACHE" >> "$ARCHIVE" && : > "$CACHE"
    exit 0
fi

# --- Step 4: land it on a throwaway worktree, then open OR update the day's PR ------
git fetch -q origin 2>>"$LOG"
SLUG="$(git -C "$REPO" remote get-url origin | sed -E 's#(git@github.com:|https://github.com/)##; s#\.git$##')"

# Everything below is labelled with SESSION_DATE (when the work happened), never with
# today's date. The nightly run fires at 00:30, so those differ whenever you work late.
BRANCH="decisions/$SESSION_DATE"

# ONE decision PR PER DAY. A second session on the same day appends to the PR that is
# already open rather than opening a rival. Why: if unreviewed decision PRs are meant
# to hold up other work, a queue of them makes that rule unworkable — you would be
# merging paperwork several times a day. One PR per day grows through the day and gets
# merged once.
EXISTING_PR=""
if git ls-remote --exit-code --heads origin "$BRANCH" >/dev/null 2>&1; then
    # TODO (API exercise — read): set EXISTING_PR to the URL of the open PR whose head
    # is "$BRANCH". Empty if there isn't one. $SLUG holds owner/repo.
    # Until this is implemented the curator opens a new branch each run instead of
    # appending to the day's PR.

    if [ -z "$EXISTING_PR" ]; then
        # Branch exists but its PR is already closed or merged. Reusing it would mean
        # force-pushing over merged history, so start a clean one instead.
        BRANCH="decisions/$SESSION_DATE-$(date +%H%M)"
    fi
fi

WORKTREE="$(mktemp -d)/curator"
# -B (not -b) so the local branch is created or reset without failing if it lingers
# from an earlier run. Base: the existing remote branch when we are appending to an
# open PR, otherwise origin/main for a fresh one.
if [ -n "$EXISTING_PR" ]; then
    BASE_REF="origin/$BRANCH"
    log "appending to existing PR $EXISTING_PR"
else
    BASE_REF="origin/main"
fi
git worktree add -q -B "$BRANCH" "$WORKTREE" "$BASE_REF" 2>>"$LOG" || {
    log "worktree creation failed"; exit 0;
}

# Entries append chronologically — DECISIONS.md runs oldest-first, so new ones go last.
{ echo; echo "---"; echo; printf '%s\n' "$ENTRIES"; } >> "$WORKTREE/DECISIONS.md"

git -C "$WORKTREE" add DECISIONS.md
git -C "$WORKTREE" commit -q -m "docs(decisions): decision log update — $SESSION_DATE

Drafted by the decision curator (trigger: $TRIGGER).
Dated $SESSION_DATE — when the conversation happened, not when this PR was raised.
Entries are machine-drafted from the day's prompts and the real git diff --
review and edit them before merging, then delete anything that does not
reflect a decision you actually made.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>" 2>>"$LOG"

git -C "$WORKTREE" push -q -u origin "$BRANCH" 2>>"$LOG" || { log "push failed"; exit 0; }

# Summarise the actual decisions for the PR body. Why: the point of opening a PR is
# that you can see WHAT was decided from the notification alone, without opening the
# diff. Run counts and trigger names tell you nothing about the content, so the summary
# leads and the mechanics shrink to a footer.
#
# Summarise from the branch's FULL diff against main, not from this run's entries.
# Why: on the second session of a day we are updating a PR that already contains
# earlier entries, and a body describing only the latest batch would misrepresent
# what merging it would actually land.
ALL_ADDED="$(git -C "$WORKTREE" diff origin/main -- DECISIONS.md \
             | grep '^+' | grep -v '^+++' | sed 's/^+//')"
[ -z "$ALL_ADDED" ] && ALL_ADDED="$ENTRIES"

SUMMARY="$(printf '%s' "$ALL_ADDED" | /usr/bin/python3 -c '
import sys, re
text = sys.stdin.read()
rows = []
for block in re.split(r"^## ", text, flags=re.M):
    if not block.strip():
        continue
    lines = block.splitlines()
    heading = lines[0].strip()
    # Headings look like "2026-08-24 — short title"; keep just the title.
    title = heading.split("—", 1)[1].strip() if "—" in heading else heading
    status, decision = "", ""
    for raw in lines:
        s = raw.strip()
        if s.startswith("**Status:**"):
            status = s.replace("**Status:**", "").strip()
        if "**Decision —**" in s:
            decision = s.split("**Decision —**", 1)[1].strip()
    # First sentence only — enough to know what was decided, short enough to scan.
    m = re.match(r"(.+?[.!?])(\s|$)", decision)
    if m:
        decision = m.group(1)
    rows.append((title, status, decision))

if not rows:
    print("_(no entries parsed — read the diff)_")
for title, status, decision in rows:
    tag = f" _({status})_" if status else ""
    print(f"- **{title}**{tag}" + (f"\n  {decision}" if decision else ""))
' 2>/dev/null)"
[ -z "$SUMMARY" ] && SUMMARY="_(summary unavailable — read the diff)_"

BODY="Decisions from **$SESSION_DATE**, appended to \`DECISIONS.md\`.

$SUMMARY

### Before merging
These entries are machine-drafted. Edit them so they read as *your* reasoning, and delete any that do not reflect a decision you actually made. The point of this log is that you can defend every entry — an unedited draft defeats that.

<sub>Not a numbered roadmap PR — docs only. Last trigger: \`$TRIGGER\` · $CACHE_LINES prompts · $COMMITS commits in window.</sub>

🤖 Generated with [Claude Code](https://claude.com/claude-code)"

TITLE="docs(decisions): decision log update — $SESSION_DATE"

# TODO (API exercise — write): open a PR for "$BRANCH" into main using $TITLE and
# $BODY. If EXISTING_PR is set, update that PR's body instead of opening a new one.
# Set PR_URL to whichever URL applies.
# Note the two cases are different HTTP verbs — worth knowing which and why.
PR_URL=""

if [ -z "$PR_URL" ]; then
    log "TODO not implemented — branch $BRANCH is pushed, open its PR by hand"
fi

log "opened $PR_URL"

# --- Step 5: rotate the cache ------------------------------------------------------
# Archive for provenance, then reset the working set so the other trigger finds
# nothing and exits. This is what makes "whichever fires first" work.
if [ "$CACHE_LINES" -gt 0 ]; then
    cat "$CACHE" >> "$ARCHIVE"
    : > "$CACHE"
fi

log "done"
exit 0
