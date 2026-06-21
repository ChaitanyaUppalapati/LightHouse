# Lighthouse — data/ track

The durable layer: Postgres schema for the shared state model, the demo seed, and
(coming next) the mock email feed, the append-only ledger, and the approval bridge.

## Run it

```bash
# 1. Start Postgres (compose file is in the repo root)
docker compose up -d

# 2. From the repo root, with the .env in place (cp .env.example .env)
python data/seed.py
```

`seed.py` creates the tables (via `schema.sql`) and inserts the demo person
**Margaret** and guardian **Priya** using the frozen UUIDs in
`lighthouse_common/demo_ids.py`. It is idempotent — run it as often as you like.

## Files

| file | what it is |
|---|---|
| `db.py` | connection helper — reads `DATABASE_URL` from `.env`, one place that knows how to reach Postgres |
| `schema.sql` | idempotent DDL for all tables (mirrors `lighthouse_common/schemas.py`) |
| `init_db.py` | applies `schema.sql` (`apply_schema()`, importable + runnable) |
| `seed.py` | inserts Margaret + Priya + their trust grant; verifies and prints |

## Tables

- `people`, `guardians`, `trust_grants` — the two-role permission model (§8)
- `signals`, `threat_assessments`, `action_proposals`, `routing_decisions`,
  `action_results` — the five shared objects (§2)
- `ledger_events` — the audit trail (§9). Locked append-only in task **K3**.
