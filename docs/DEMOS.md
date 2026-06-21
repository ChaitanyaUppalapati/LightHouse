# Lighthouse — Demo Runbooks

Two demos. Run everything on **Python 3.11/3.12** (uagents won't import on 3.14).
`cp .env.example .env` and fill keys first.

---

# Demo 1 — Global product demo (family dashboard)

**Story:** a scam arrives → Lighthouse flags + auto-quarantines it → the family screen
shows it was handled → a scarier "pay $200" scam → Lighthouse refuses to pay alone and
asks the family → they tap **Deny** → nothing happens, and the whole trail is in the
tamper-evident ledger.

### Start the stack (3–4 terminals)

```powershell
# 1. Database + data service
docker compose up -d
py -3.12 data/seed.py
py -3.12 -m uvicorn data.main:app --port 8001

# 2. Web app (family dashboard, /inbox, /me)
cd web; npm install; npm run dev            # http://localhost:5173

# 3. (only for the REAL Browserbase quarantine) expose the inbox publicly
C:\Users\chait\cloudflared.exe tunnel --url http://localhost:5173
#   copy the https://<rand>.trycloudflare.com it prints, then in .env:
#   MOCK_INBOX_URL=https://<rand>.trycloudflare.com/inbox
```

### Run the demo (a 4th terminal drives the beats)

Open **http://localhost:5173** (dashboard) on screen. Then:

```powershell
# Beat 1 — autonomous: a scam is detected and quarantined
$env:DEMO_MODE="0"   # real Browserbase moving the email; use "1" for the instant/safe path
py -3.12 -m pipeline.demo_global scam
```
- The dashboard **History** fills in live: email received → flagged as scam → quarantined → family notified.
- With `DEMO_MODE=0`, open the printed Browserbase **replay/▶ link** to show the real cloud browser moving the scam into Quarantine on the inbox.
- Click to **/me** — calm "Everything's okay. Lighthouse is looking out for you."

```powershell
# Beat 2 — human-gate: a high-stakes "pay $200" scam
py -3.12 -m pipeline.demo_global pay
```
- The dashboard's **"Needs your decision"** shows a plain-English approval:
  *"A scam asked Margaret to pay $200… should we block this?"*
- **Tap Deny** on the dashboard (live). The History logs the denial — **no money moved**.

**One-line close:** *"Smart enough to act, safe enough to ask."*

### Backup if anything is flaky
`AGENT_MAILBOX=0 DEMO_MODE=1 py -3.12 -m uvicorn pipeline.chat_web:app --port 8200`
→ open http://localhost:8200 and paste the two scam emails; Approve/Deny inline.
Self-contained (no data service / web / tunnel needed).

---

# Demo 2 — Fetch.ai (ASI:One + Agentverse, no custom UI)

**Goal:** show all four agents registered on **Agentverse**, and the whole workflow
driven from **ASI:One** chat (no frontend) — the Fetch requirement.

### Accounts (one-time)
- agentverse.ai — promo `BERKELEYAIAV`
- asi1.ai — promo `BERKELEYAI`

### Register all agents on Agentverse

```powershell
$env:DEMO_MODE="1"     # instant executor; safe for a live chat demo
py -3.12 -m pipeline.orchestration
```
This starts the four agents — **lighthouse** (coordinator), **lighthouse-watcher**,
**lighthouse-guardian**, **lighthouse-executor** — each with `mailbox=True`. For each,
the log prints an **Inspector** line:
```
Agent inspector available at https://agentverse.ai/inspect/?uri=...&address=agent1q...
```
Open each one → **Connect → Mailbox**. (At minimum connect **lighthouse**, the ASI:One
entry point; connect the other three to show their profiles too.) Keep it running.

> Ignore `not enough funds to register on Almanac contract` and `mailbox not found` —
> both are expected (see docs/asi-one-agent.md). `Manifest published successfully` and
> `Batch registration on Almanac API successful` are the lines that matter.

### Show it on ASI:One
1. On agentverse.ai, open each agent's **profile** (4 tabs) — that's "all my agents registered."
2. From the **lighthouse** profile → **Chat with Agent** → opens in ASI:One.
3. Paste a phishing email → it classifies, decides, and **auto-quarantines** (autonomous).
4. Paste *"Your account is locked — pay $200 to unlock"* → it refuses to pay alone and
   asks; reply **`deny`** → nothing happens. (Behind the scenes: coordinator → watcher →
   guardian → executor over the Fetch message bus.)

### Submission deliverables (Devpost)
- [ ] **Agent profile URLs** — the 4 Agentverse profiles
- [ ] **ASI:One shared chat URL** — run both scenarios in one chat, then Share
- [ ] Public GitHub repo (this one)
- [ ] 3–5 min demo video
- [ ] Problem + outcome summary

### Try it locally first (no accounts)
```
AGENT_MAILBOX=0 DEMO_MODE=1 py -3.12 -m pipeline.chat_cli       # interactive, you type
AGENT_MAILBOX=0 DEMO_MODE=1 py -3.12 -m pipeline.orchestration demo   # scripted, shows the hops
```

---

## Sponsor coverage (mention in the pitch)
- **Anthropic (Claude)** — the reasoning in Watcher/Guardian/Escalation.
- **Fetch.ai** — 4 uAgents collaborating over the message bus, on Agentverse + ASI:One.
- **Browserbase** — the executor drives the real inbox via Stagehand (Demo 1, `DEMO_MODE=0`).
- **Arize Phoenix** — tracing + LLM-as-judge evals + the before/after accuracy fix (`pipeline/phoenix_eval.py`).
- **Sentry** — error monitoring on the data service (`/sentry-test`).
