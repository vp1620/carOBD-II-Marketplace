#!/usr/bin/env bash
# Reminds Claude to run the /new-pr skill when a PR branch is started or a plan is
# approved — so README updates + PR creation always go through the standard workflow
# instead of drifting. Reads the PostToolUse hook payload (JSON) on stdin and, when
# relevant, injects a one-line reminder back into Claude's context.
set -euo pipefail

input="$(cat)"

# tool_name / command are pulled with python3 so we don't depend on jq being installed.
tool="$(printf '%s' "$input" | /usr/bin/python3 -c 'import sys,json; print(json.load(sys.stdin).get("tool_name",""))' 2>/dev/null || true)"

remind() {
  # additionalContext is surfaced to Claude after the tool runs.
  printf '{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"%s"}}' "$1"
}

MSG_READY="Repo convention: when this branch is ready to become a pull request, run the /new-pr skill — it folds high-level info + important commands into README.md and opens the PR. Do NOT create docs/prs/*.md files (that pattern is retired)."

case "$tool" in
  ExitPlanMode)
    remind "A plan was just approved. $MSG_READY"
    ;;
  Bash)
    cmd="$(printf '%s' "$input" | /usr/bin/python3 -c 'import sys,json; print(json.load(sys.stdin).get("tool_input",{}).get("command",""))' 2>/dev/null || true)"
    if printf '%s' "$cmd" | grep -Eq 'git +(checkout +-b|switch +-c|branch +[^-])'; then
      remind "A new branch was just created. $MSG_READY"
    fi
    ;;
esac
exit 0
