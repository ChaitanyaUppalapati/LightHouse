# Lighthouse — data/ track

The durable layer: Postgres schema for the shared state model, the demo seed, the
mock email feed, the append-only ledger, the approval bridge, and Sentry.

## Run it

```bash
# 0. Install deps
pip install -r data/requirements.txt

# 1. Start Postgres (compose file is in the repo root)
docker compose up -d

# 2. From the repo root, with the .env in place (cp .env.example .env)
python data/seed.py

# 3. Start the data service (port 8001)
python data/main.py
```

## HTTP endpoints (data service, :8001)

| method | path | purpose |
|---|---|---|
| GET | `/signals/next` | next mock email Signal (feeds the Watcher, C1) |
| POST/GET | `/ledger` | append / read the immutable ledger |
| POST | `/approvals` | Escalation (C4) creates a pending approval |
| GET | `/approvals?status=pending` | dashboard (S6) lists what needs deciding |
| GET | `/approvals/{id}` | the agent polls for the decision |
| POST | `/approvals/{id}/decide` | dashboard records approved/denied |
| GET | `/sentry-test` | deliberately errors to verify Sentry capture |

## Real Gmail feed (K6, stretch)

`/signals/next` prefers a real **unread** email from a test Gmail account (read-only
OAuth) and **falls back to the mock list** if Gmail isn't set up, the token is
missing/expired, or the inbox is empty — so the demo never breaks.

One-time setup:
1. In Google Cloud, create an OAuth client (Desktop app), download it as
   `credentials.json` at the repo root, and add your test account under
   **Audience → Test users**.
2. Authorize once (opens a browser to click *Allow*): `python data/gmail_feed.py`
   — this saves `token.json`. After that the server uses the token silently.

`credentials.json` and `token.json` are secrets — both are gitignored, never commit them.

## Sentry (K5)

Sentry auto-captures errors and slow requests. Set `SENTRY_DSN` in `.env` (free
account at sentry.io → new project → copy DSN). With no DSN it's disabled and the
app runs normally. To confirm it works: set the DSN, restart, hit
`http://localhost:8001/sentry-test`, and watch the error appear in your Sentry
dashboard. `data/tests/test_sentry.py` proves capture locally without an account.

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
| `main.py` | the FastAPI data service (feed, ledger, approvals, sentry-test) |
| `ledger.py` | ledger + signal persistence helpers |
| `approvals.py` | approval-bridge data layer |
| `sentry_setup.py` | Sentry init (no-ops without `SENTRY_DSN`) |

## Tables

- `people`, `guardians`, `trust_grants` — the two-role permission model (§8)
- `signals`, `threat_assessments`, `action_proposals`, `routing_decisions`,
  `action_results` — the five shared objects (§2)
- `ledger_events` — the audit trail (§9). Locked append-only in task **K3**.
- `approvals` — the human-gate approval bridge (**K4**).
