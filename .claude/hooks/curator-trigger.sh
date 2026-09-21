#!/usr/bin/env bash
# SessionEnd hook: the conversation just ended (/clear, terminal exit, logout), so
# kick off the decision curator for what was just discussed.
#
# Why this script does almost nothing: SessionEnd hooks share a ~1.5s budget and
# CANNOT block session teardown. A curator run takes minutes (it calls a model and
# opens a PR), so doing the work here would simply be killed halfway. Instead we hand
# the job to a detached background process and return immediately.
#
# nohup matters specifically for the terminal-close case: closing the window SIGHUPs
# the process group, which would kill the curator mid-run. nohup makes it survive.
set -uo pipefail

ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
RUNNER="$ROOT/.claude/hooks/run-curator.sh"

input="$(cat)"

# Pull the transcript path and the reason the session ended. The transcript is the
# richest input the curator gets — the full conversation rather than prompts alone —
# so it is worth passing through.
eval "$(printf '%s' "$input" | /usr/bin/python3 -c '
import sys, json, shlex
try:
    d = json.load(sys.stdin)
except Exception:
    d = {}
t = d.get("transcript_path") or ""
r = d.get("reason") or d.get("matcher") or "other"
print(f"TRANSCRIPT={shlex.quote(t)}")
print(f"REASON={shlex.quote(r)}")
' 2>/dev/null)"

TRANSCRIPT="${TRANSCRIPT:-}"
REASON="${REASON:-other}"

# "resume" is reported through SessionEnd but the conversation is continuing, not
# finishing. Curating there would draft entries mid-thought and rotate the cache out
# from under the rest of the session.
if [ "$REASON" = "resume" ]; then
    exit 0
fi

[ -x "$RUNNER" ] || exit 0

nohup "$RUNNER" "$TRANSCRIPT" "session-end:$REASON" >/dev/null 2>&1 &
disown 2>/dev/null || true

exit 0
