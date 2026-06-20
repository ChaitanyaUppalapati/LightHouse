# Lighthouse — Claude Code rules (read automatically every session)

You are building Lighthouse. The full plan is in `docs/1-MASTER-PLAN.md`; the design is in
`docs/2-architecture-reference.md`. You work in ONE folder (pipeline/, data/, or web/) — only edit
that folder plus your own tests. Never edit `lighthouse_common/schemas.py` or
`lighthouse_common/action_registry.yaml` — they are frozen; adapt the calling code instead.

## Automatic preflight — do this without being asked

Before starting ANY task from the plan, FIRST run the preflight check for that task:
`/preflight <TASK ID>`. Do not begin editing or creating code until preflight reports
"SAFE TO PROCEED". If preflight reports "DO NOT PROCEED YET", stop and tell me the fallback or which
teammate to message — do not work around a missing dependency.

When you finish a task that has an "UNBLOCKS:" line, run `/handoff <TASK ID>` and give me the exact
message to send the teammate. Don't tell anyone a piece is ready until handoff confirms it.

## Why edits may be blocked

A safety hook blocks Edit/Write until a fresh preflight marker exists. If you see
"BLOCKED: run /preflight", that is expected — run `/preflight <TASK ID>` first, then continue. The
hook does not gate docs or config, only source edits. If preflight passed over 90 minutes ago it goes
stale on purpose; just re-run it.

## Working rules
- Use plan mode first on every task. Show the plan before editing.
- One task at a time. Commit after each with a clear message.
- When something breaks, report the exact error and propose a fix — don't silently change unrelated files.
