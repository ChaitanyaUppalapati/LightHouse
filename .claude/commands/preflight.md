---
description: Check a task's NEEDS dependencies are live before building. Read-only. Writes a pass-marker if clear.
argument-hint: [TASK ID, e.g. C5]
allowed-tools: Read, Grep, Glob, Bash
---
PREFLIGHT CHECK for task $ARGUMENTS — read-only. Do NOT edit, create, or fix any project file
(creating the marker file in step 5 is the only allowed write). Only inspect and report.

1. Find task $ARGUMENTS in docs/1-MASTER-PLAN.md and read its "NEEDS:" line. If the task has no
   NEEDS line, report "no dependencies — safe to proceed" and still write the marker in step 5.
   If you can't find the plan, ask me to paste the dependency list.

2. For each dependency, verify it WITHOUT changing anything:
   - HTTP endpoint (e.g. http://localhost:8001/signals/next): curl it, report the status code and a
     short snippet. Passes ONLY if it returns valid data shaped like the task expects — a 200 with
     the right fields, not an error page or empty body.
   - Env var (e.g. MOCK_INBOX_URL): check it's set and non-empty in .env; if it's a URL, check the
     page loads.
   - File (e.g. lighthouse_common/schemas.py): check it exists and contains the expected classes.
   - Running service / port: check the port is open and responding.

3. Print a table: dependency | CLEARED or BLOCKED | evidence (status code, value, or exact error).

4. Verdict:
   - All CLEARED: say "SAFE TO PROCEED with $ARGUMENTS".
   - Any BLOCKED: say "DO NOT PROCEED YET" and for each blocker give exactly one of:
     (a) the fallback this task allows, quoted from the plan (e.g. "use the built-in samples"), or
     (b) which teammate to message and what to ask.

5. ONLY if the verdict is SAFE TO PROCEED, write a marker file so the enforcement hook will allow
   edits: run `mkdir -p .claude/state && echo "$ARGUMENTS $(date +%s)" > .claude/state/preflight-ok`.
   If BLOCKED, do NOT write the marker.

Make zero other changes. This is a check, not a fix.
