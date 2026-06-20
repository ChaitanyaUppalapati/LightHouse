#!/usr/bin/env bash
# PreToolUse hook: blocks Edit/Write unless a fresh preflight marker exists.
# Fast (<500ms): no network here — just checks the marker the /preflight command wrote.
# Reads the tool-call JSON from stdin; exit 2 blocks the action and shows the message to Claude.

MARKER=".claude/state/preflight-ok"
MAX_AGE=5400   # 90 minutes — re-run /preflight if your last check is older

# Only gate edits to actual project source; never block docs, the marker, or state files.
input=$(cat)
path=$(printf '%s' "$input" | grep -o '"file_path"[^,}]*' | head -1)
case "$path" in
  *".claude/"*|*"docs/"*|*".md"*) exit 0 ;;   # don't gate docs/config edits
esac

if [ ! -f "$MARKER" ]; then
  echo "BLOCKED: run /preflight <TASK ID> before editing. No preflight marker found." >&2
  exit 2
fi

age=$(( $(date +%s) - $(cut -d' ' -f2 "$MARKER" 2>/dev/null || echo 0) ))
if [ "$age" -gt "$MAX_AGE" ]; then
  echo "BLOCKED: your last preflight is stale (${age}s old). Re-run /preflight <TASK ID>." >&2
  exit 2
fi

exit 0
