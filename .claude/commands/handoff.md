---
description: Before telling a teammate your piece is ready, prove it actually works end to end.
argument-hint: [TASK ID you finished, e.g. K4]
allowed-tools: Read, Grep, Glob, Bash
---
HANDOFF CHECK for task $ARGUMENTS — verify MY finished work is genuinely usable by a teammate before
I tell them it's ready. Read-only except for nothing — just inspect and report.

1. Find task $ARGUMENTS in docs/1-MASTER-PLAN.md and read its "UNBLOCKS:" line and its "Done when:"
   line. If there's no UNBLOCKS, report "this task doesn't unblock anyone — no handoff needed".

2. Re-verify the "Done when:" condition actually holds right now (run the check, don't assume it
   still passes from earlier).

3. For the thing it UNBLOCKS, test it the way the TEAMMATE will call it, not the way I built it:
   - If it's an endpoint, curl it exactly as their task's prompt says they'll call it, with a
     realistic input, and confirm the response matches the shape in lighthouse_common/schemas.py.
   - If it's a URL/page for the computer-use agent, confirm it loads and the target buttons exist.
   - If it's a shared file, confirm it has what the consumer imports.

4. Report: is this REALLY ready for the teammate? Print exactly what to send them — either
   "Ready: <endpoint/url/file> returns <evidence>, go ahead with <their task>" or
   "Not ready yet: <what's still broken>".

Do not claim ready unless you tested it as the consumer would. A teammate building on a half-working
handoff loses an hour — be strict.
