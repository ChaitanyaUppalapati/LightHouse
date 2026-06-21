# Lighthouse

A multi-agent system that quietly protects the digital life of someone whose memory is declining —
acting on safe, reversible things on its own, and asking the family before anything risky or
irreversible. Built for the UC Berkeley AI Hackathon 2026.

**One-line architecture:** signals in → agents reason → a deterministic gate decides act-alone vs
ask-a-human → real actions on real interfaces → an immutable ledger watches all of it.

See `docs/1-MASTER-PLAN.md` for the build plan and `docs/2-architecture-reference.md` for the design.

## Repo layout — one owner per folder

| Folder | Owner | What's in it |
|---|---|---|
| `pipeline/` | Chaitanya | the AI agents (Watcher / Guardian / Escalation), the deterministic safety gate, the Browserbase + Stagehand executor, Arize |
| `data/` | Keya | Postgres schema, the append-only ledger, the mock email feed, the approval bridge, Sentry |
| `web/` | Sonakshi | the family dashboard, the protected-person screen, the mock inbox & bank, the pitch |
| `lighthouse_common/` | shared | the frozen contract: `schemas.py`, `action_registry.yaml`, `demo_ids.py` |

**Only edit your own folder.** `lighthouse_common/schemas.py` and `lighthouse_common/action_registry.yaml`
are **FROZEN** — they're the shared contract; changing one breaks everyone. Ask the team first.

## Quick start

```bash
cp .env.example .env          # then paste your sponsor credit codes into .env
docker compose up -d          # start Postgres (pgvector/pgvector:pg16)
pip install -r requirements.txt
```

The `web/` track uses its own Node toolchain (`cd web && npm install && npm run dev`).
