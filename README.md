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

## Multi-agent system on Fetch.ai & ASI:One

Lighthouse runs as a team of cooperating Fetch.ai uAgents, published on Agentverse and reachable
through the ASI:One Chat Protocol. You can talk to the coordinator in plain language and watch the
pipeline (classify, propose, gate, act) play out.

**Live ASI:One chat session:** https://asi1.ai/shared-chat/6f328aeb-7e9c-4f34-9f62-f7ecc7e117b3

**Agent profiles on Agentverse:**

- [lighthouse-ai (coordinator)](https://agentverse.ai/agents/details/agent1q2m2n78js6cs7rlemgullzt2gvlw250sh32stks84cxwm0u35sd77y3rsx7/profile)
- [lighthouse-watcher](https://agentverse.ai/agents/details/agent1q2pvrz4aw6fzsn24wyxf6jeeq967nn66u7fl9w643stzc3k9tph7unfp0ld/profile)
- [lighthouse-guardian](https://agentverse.ai/agents/details/agent1qf3j6f0lce4csuzwggj0d2apuvhcrpdmaa4hs9ja8g5syz2quz8pv9eqpuu/profile)
- [lighthouse-executor](https://agentverse.ai/agents/details/agent1qg64arczlxvq5yx2acg82d7ycn3avnh8t4deh89rfm8q43rg0l5yv44rw3e/profile)

## Sponsors & integrations

- **Claude (Anthropic)** — reasoning behind the Watcher (threat classification) and Guardian (action choice).
- **Fetch.ai / ASI:One** — multi-agent orchestration over the Chat Protocol; agents published on Agentverse (links above).
- **Arize Phoenix** — tracing + an LLM-as-judge evaluator. The Watcher improved from **86.7% to 93.3%** on our hard adversarial email set after acting on the eval's explanations.
- **Browserbase + Stagehand** — the Executor operates the mock inbox and bank in a real browser.
- **Deepgram** — voice helper on the protected-person screen (speech to text + text to speech).
- **Sentry** — error capture on the data service (verified via `/sentry-test`).
