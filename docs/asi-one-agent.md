# Lighthouse on ASI:One / Agentverse (Fetch.ai challenge)

The Fetch.ai track ("ASI:One Agent — From Intent to Action") requires an agent that
is **registered on Agentverse**, implements the **Agent Chat Protocol**, is **usable
through ASI:One**, and **completes the workflow with no custom frontend**.

`pipeline/asi_agent.py` is that agent: one Chat-Protocol coordinator (`lighthouse`)
that drives the whole pipeline from chat — Watcher → Guardian → deterministic safety
gate → executor — and runs the human-gate approval **in chat** (it asks, you reply
`approve`/`deny`). Brain is Claude; the Chat Protocol is just how ASI:One talks to it.

## Run + register on Agentverse

1. (Recommended) `DEMO_MODE=1` in `.env` so the executor returns instant results — no
   live Browserbase needed for the chat demo.
2. Start the agent (Python 3.11/3.12):
   ```
   python -m pipeline.asi_agent
   ```
   It prints the agent address and an **Inspector** link.
3. Open the Inspector link → **Connect → Mailbox**. The agent registers on the
   Almanac and becomes reachable from Agentverse / ASI:One.
4. Apply the hackathon promo codes:
   - Agentverse: `BERKELEYAIAV`
   - ASI:One (asi1.ai): `BERKELEYAI`
5. From the agent's **Agentverse profile**, click **Chat with Agent** → it opens in
   ASI:One. Paste a suspicious email and watch it classify → decide → act / ask.

## Two entry points

- **`pipeline/orchestration.py`** — the full **multi-agent** version: the coordinator
  delegates to separate **Watcher → Guardian → Executor** agents over the Fetch
  message bus (real agent-to-agent orchestration / separation of powers). **Use this
  for the Fetch demo.** Run it for real with `python -m pipeline.orchestration`
  (coordinator registers on Agentverse for ASI:One; the sub-agents run in-process).
- **`pipeline/asi_agent.py`** — a simpler single coordinator agent that runs the same
  pipeline as in-process tool calls. Lighter, same chat behaviour.

## See it run end-to-end without an Agentverse account

```
# Multi-agent (recommended) — watch the coordinator -> watcher -> guardian -> executor hops:
AGENT_MAILBOX=0 DEMO_MODE=1 python -m pipeline.orchestration demo

# Single-agent equivalent:
AGENT_MAILBOX=0 DEMO_MODE=1 python -m pipeline.demo_e2e
```

Both drive the coordinator with the **real Chat Protocol** messages ASI:One sends and
play both scenarios automatically: a phishing email (auto-quarantined) and a "pay
$200" scam (asks the family in chat → reply `deny` → nothing happens).

## Two demo scenarios (both run entirely in ASI:One chat)

- **Autonomous:** paste a phishing email → "scam_phishing, high" → it auto-quarantines
  (reversible, low-stakes) and reports the result + an undo token.
- **Human-gate:** paste a "pay $200 to unlock your account" scam → "high-stakes, I will
  NOT do it on my own" → it asks **approve or deny** → reply `deny` → nothing happens.

## Submission deliverables (devpost / README)

- [ ] **ASI:One shared chat session URL** — run both scenarios in one chat, then share.
- [ ] **Agentverse agent profile URL** — from the agent's profile page.
- [ ] Public GitHub repo (this one) with these instructions.
- [ ] 3–5 min demo video.
- [ ] Problem + outcome summary.

## Going live on Agentverse — the one interactive step

Use the **single** coordinator for the mailbox connect (it prints a clean Inspector
URL; the Bureau does not):

```
python -m pipeline.asi_agent
```

It logs a line like:
```
Agent inspector available at https://agentverse.ai/inspect/?uri=http%3A//127.0.0.1%3A8104&address=agent1q2m2n78...
```
Open that URL (logged in to agentverse.ai, promo `BERKELEYAIAV`) → **Connect → Mailbox**.
The agent's profile then gets a **Chat with Agent** button that opens it in ASI:One
(promo `BERKELEYAI`). Grab the agent profile URL + a shared chat URL for the submission.

### Warnings you can safely ignore

- `WARNING: I do not have enough funds to register on Almanac contract` — this is the
  optional **on-chain** registration. The lines `Manifest published successfully` and
  `Batch registration on Almanac API successful` are the ones that matter (Chat Protocol
  + off-chain registry). No funds needed.
- `WARNING: Agent mailbox not found: create one using the agent inspector` — expected
  **until** you do the Inspector → Connect → Mailbox step above; it clears once connected.

## Running with REAL computer-use (DEMO_MODE=0)

By default the executor returns an instant fake result (`DEMO_MODE=1`). To have it
actually drive a browser via Browserbase + Stagehand, you need three things:

1. **Install Stagehand:** `py -3.12 -m pip install stagehand` (already in requirements.txt).
2. **Make the mock pages public.** Browserbase runs the browser in the *cloud*, so it
   cannot reach `localhost:5173`. Run the web app and expose it:
   ```
   cd web && npm run dev                       # terminal 1 -> http://localhost:5173
   cloudflared tunnel --url http://localhost:5173   # terminal 2 -> prints https://<rand>.trycloudflare.com
   ```
   (Install cloudflared once: `winget install cloudflare.cloudflared`, or use ngrok.)
   Then point the URLs at the public tunnel in `.env`:
   ```
   MOCK_INBOX_URL=https://<rand>.trycloudflare.com/inbox
   MOCK_BANK_URL=https://<rand>.trycloudflare.com/bank
   ```
3. **Run with `DEMO_MODE=0`.** The executor opens the public inbox, clicks the flagged
   email, and clicks "Move to Quarantine" (the page's `data-testid`s make it findable).
   Evidence comes back as a Browserbase **session id + replay URL** (the recording is
   the proof — there's no screenshot op in the SDK).

The live Stagehand API (sync `Stagehand` client, `sessions.start/navigate/act/end`,
`model_name="anthropic/claude-sonnet-4-6"`) is verified working with the project keys.
Keep `DEMO_MODE=1` for the ASI:One chat demo; use `DEMO_MODE=0` at the Browserbase booth.

## Notes

- Run on Python 3.11/3.12 (uagents does not import on 3.14).
- The agent reuses the exact pipeline code (`classify_signal`, `propose_action`,
  `route_action`, `execute`) — same brain as the web-dashboard path, just exposed
  through the Chat Protocol instead of a frontend.
- Every Claude call + agent step is traced to Phoenix when `PHOENIX_API_KEY` is set.
