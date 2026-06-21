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

## See it run end-to-end without an Agentverse account

`pipeline/demo_e2e.py` runs the coordinator + a `user` agent together in a uAgents
Bureau and drives the coordinator with the **real Chat Protocol** messages ASI:One
sends — so you can watch the full chat-in → pipeline → chat-out loop locally:

```
AGENT_MAILBOX=0 DEMO_MODE=1 python -m pipeline.demo_e2e
```

It plays both scenarios automatically: a phishing email (auto-quarantined) and a
"pay $200" scam (asks the family in chat → replies `deny` → nothing happens).

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

## Notes

- Run on Python 3.11/3.12 (uagents does not import on 3.14).
- The agent reuses the exact pipeline code (`classify_signal`, `propose_action`,
  `route_action`, `execute`) — same brain as the web-dashboard path, just exposed
  through the Chat Protocol instead of a frontend.
- Every Claude call + agent step is traced to Phoenix when `PHOENIX_API_KEY` is set.
