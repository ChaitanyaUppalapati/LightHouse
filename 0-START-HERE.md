# Lighthouse team kit — start here

Files in this kit:
- `1-MASTER-PLAN.md` — THE plan. Shared timeline, all three tracks side by side, copy-paste prompts.
  Everyone reads this fully.
- `2-architecture-reference.md` — the design and the reasoning. Skim once.
- `CLAUDE.md` — rules Claude Code reads automatically. Goes in the repo root.
- `.claude/` — the preflight system (commands + the enforcement hook + settings). Goes in the repo root.

## The preflight system (so nobody builds on a broken dependency)

Two safety nets, both automatic once the `.claude/` folder is in the repo:

1. Soft: `CLAUDE.md` tells Claude Code to run `/preflight <TASK ID>` itself before starting any task,
   and `/handoff <TASK ID>` when it finishes something a teammate depends on.
2. Hard: a hook blocks code edits until `/preflight` has passed for your task. If you see
   "BLOCKED: run /preflight", that's the system working — run the check first.

You can also run them by hand anytime: `/preflight C5` before you build C5, `/handoff K4` before you
tell a teammate K4 is ready.

## Setup order
1. Chaitanya runs task C0 (creates the repo + foundation), then copies this kit's `CLAUDE.md` and
   `.claude/` folder into the repo root, and the two docs into `docs/`. Commit and push.
2. Keya and Sonakshi clone, and the preflight system is active for everyone automatically.
