#!/usr/bin/env bash
# UserPromptSubmit hook: append each user prompt to the decision cache so the
# end-of-day /log-decisions skill (run by a midnight cron) can curate the day's
# genuinely-significant decisions into DECISIONS.md. This is DUMB capture only —
# no filtering here; significance is judged later in batch, with the day's
# hindsight and git diff. Must never block or slow a prompt, so it fails silent.
set -uo pipefail

# Repo root: prefer the hook-provided env var, fall back to this script's location
# (so the script also works when pipe-tested by hand).
ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
CACHE="$ROOT/.claude/decision-cache.jsonl"

input="$(cat)"

# python3 (not jq) to match the repo's other hook and avoid a jq dependency.
printf '%s' "$input" | /usr/bin/python3 -c '
import sys, json, datetime
cache = sys.argv[1]
try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)  # never fail the prompt over a cache hiccup
# Field name for the submitted text can vary; try the likely keys.
prompt = (data.get("prompt") or data.get("user_prompt") or "").strip()
if prompt:
    entry = {"ts": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
             "prompt": prompt}
    with open(cache, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
' "$CACHE" 2>/dev/null || true

exit 0
