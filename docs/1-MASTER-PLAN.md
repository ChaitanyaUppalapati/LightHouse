# Lighthouse — Master Build Plan (one plan, three people, shared timeline)

**This is the single plan for the whole team. Read it top to bottom. You'll see what all three of you are doing at the same time, who is waiting on whom, and the exact prompts to paste into Claude Code.**

Building: a multi-agent system that protects the digital life of someone whose memory is declining, with family oversight. Full design is in `architecture.md` (skim once). Target prizes: Anthropic, Fetch.ai, Browserbase, Sentry, Arize.

Team and tracks:
- **Chaitanya** -> `pipeline/` folder: the AI agents, the safety gate, the computer-use executor, Arize. (Carries Fetch, Browserbase, Arize.)
- **Keya** -> `data/` folder: the database, the event log, the email feed, the approval bridge, Sentry.
- **Sonakshi** -> `web/` folder: the family dashboard, the person's screen, the fake inbox and bank, the pitch.

You only ever edit your own folder. You build against fake data first, so nobody is ever blocked. The plan tells you exactly when the fake gets swapped for the real thing.

---

## How to read this plan

The plan runs in time blocks. In each block there is a section for each person with the prompt to run, plus joint **CHECKPOINTS** where you all stop and connect your pieces. Two markers tell you about dependencies:

- **NEEDS:** something from a teammate must exist first. If it doesn't yet, use the fake version noted and keep going.
- **UNBLOCKS:** finishing this lets a teammate move. Tell them when it's done.

Back-calculate the clock from the **11:00 AM submission**. The hour numbers below are relative to when you start building.

---

## Vibe coding ground rules (read even if you've never coded)

You won't hand-write code. You tell Claude Code what to build, one task at a time, by pasting the prompts below.

- Launch Claude Code from YOUR folder so it loads your rules. Unsure? Ask it "what folder am I in?"
- Say "use plan mode first" on every task. Read what it plans. If it wants to touch a file you don't own or edit `lighthouse_common/schemas.py` or `action_registry.yaml`, say "no, don't touch that."
- One task at a time. Finish and check before the next.
- After each task: "commit this with a clear message."
- When it breaks: copy the exact red error, paste it, say "this broke, explain simply and fix it." Don't fix it yourself.
- Stuck more than 15 minutes? Message the team. Chaitanya is lead.

Never edit the two frozen files (`schemas.py`, `action_registry.yaml`). They are the shared contract; one change breaks everyone.

---

## The whole weekend at a glance

| Time | Chaitanya (pipeline) | Keya (data) | Sonakshi (web) |
|---|---|---|---|
| **Setup 0-2h** | C0 build + push the foundation | clone, then K1 database | clone, then start S1 |
| **Block A 2-8h** | C1 Watcher, C2 safety gate | K2 mock email feed, K3 ledger | S1 dashboard, S2 history |
| *Checkpoint 1 (~6h)* | Watcher reads Keya's feed | — | — |
| **Block B 8-12h** | C3 Guardian, C4 Escalation | K4 approval bridge, K5 Sentry | S3 person screen, S4 fake inbox |
| *Checkpoint 2 (~12h)* | **Autonomous path end-to-end (all three)** | | |
| **Block C 12-16h** | C5 browser-agent executor, C6 Arize | K6 real Gmail (stretch) | S5 fake bank, S6 connect backend |
| *Checkpoint 3 (~15h)* | **Human-gate path + Arize before/after (all three)** | | |
| **Block D 16-19h** | C7 integration + harden | support + DEMO_MODE | S7 deck + rehearse, S8 voice (stretch) |
| **Submit 19-20h** | **Devpost submission + booth visits (all three)** | | |

The critical chain that must not stall: **C0 -> K2 -> C1**. That is the path to your first real signal flowing through an agent. Get C0 pushed, point Keya at K2 immediately, then Chaitanya can test the Watcher.

---

## SETUP (hours 0-2) — all three together

1. All three install Claude Code (`npm install -g @anthropic-ai/claude-code`) and log in.
2. All three split up and collect sponsor credits: Claude credits first (you burn these), then Browserbase access (for the browser-agent executor), then the Fetch code, then sign up for Arize and Sentry (free). Don't all sit in one workshop.
3. Chaitanya creates a private GitHub repo `lighthouse`, adds Keya and Sonakshi, then runs **C0** below and pushes.
4. Keya and Sonakshi: once C0 is pushed, `git clone` the repo, `cp .env.example .env`, paste your credit codes into `.env`. Then start your first task.

### C0 — Chaitanya: build the shared foundation (everyone is blocked until this is pushed)

Run Claude Code from the repo root, paste:

```
I'm building Lighthouse, a multi-agent eldercare safety app, for a hackathon. Set up the project
foundation. Use plan mode first, then create:
1. Folders: pipeline/, data/, web/, lighthouse_common/, docs/.
2. lighthouse_common/schemas.py — Pydantic + Fetch uAgent Model classes (subclass uagents.Model so
   they can be sent between agents) for: Signal(signal_id, person_id, source[email/transaction/
   account_event/voice], payload dict, observed_at); ThreatAssessment(assessment_id, signal_id,
   category[scam_phishing/financial_anomaly/missed_obligation/account_risk/benign], severity[none/
   low/moderate/high], confidence float, rationale, evidence list); ActionProposal(proposal_id,
   assessment_id, action_type, target dict, rationale, expected_effect); RoutingDecision(proposal_id,
   route[autonomous/human_gate/watch_only], reason); ActionResult(proposal_id, status, evidence dict,
   undo_token optional, completed_at).
3. lighthouse_common/action_registry.yaml — allowed actions with reversible(true/false) and
   stakes(low/high): quarantine_email(yes,low), flag_transaction(yes,low), block_sender(yes,low),
   label_and_notify(yes,low), pay_bill(no,high), freeze_card(yes,high), reset_credentials(no,high),
   reply_to_sender(no,high).
4. lighthouse_common/demo_ids.py — fixed UUIDs for demo person "Margaret" and guardian "Priya".
5. README, .env.example with empty keys (ANTHROPIC_API_KEY, ARIZE_API_KEY, SENTRY_DSN, Fetch and
   BROWSERBASE_API_KEY, BROWSERBASE_PROJECT_ID, DEEPGRAM_KEY), plus DATABASE_URL, VITE_DATA_URL, MOCK_INBOX_URL, MOCK_BANK_URL,
   DEMO_MODE=0.
6. docker-compose.yml running Postgres image pgvector/pgvector:pg16.
Add a top comment to schemas.py and action_registry.yaml: "FROZEN — do not edit, ask the team first."
```

Done when: folders exist, the two frozen files are there. Then "commit everything and give me the push command." Push. Copy `architecture.md` into `docs/`, commit, push. **Tell Keya and Sonakshi: clone now.**

---

## BLOCK A (hours 2-8) — first real pieces, built against fakes

### Chaitanya

**C1 — the Watcher agent** (your most important agent; Arize grades it). NEEDS: Keya's K2 feed to test against, but you can start now with the built-in samples and switch to her feed at Checkpoint 1.

```
Use plan mode first. Build the Watcher as a Fetch.ai uAgent in pipeline/watcher.py. It receives a
Signal (from lighthouse_common.schemas) and produces a ThreatAssessment. To decide, call the Claude
API (anthropic library, model claude-sonnet-4-6, temperature 0) with a structured-output prompt that
classifies into category + severity + confidence and fills a plain-English rationale and an evidence
list (e.g. "sender address doesn't match display name", "urgent payment demand"). For now print the
ThreatAssessment and send it to a placeholder Guardian address. Read ANTHROPIC_API_KEY from .env. Add
3 scam and 2 normal sample emails in pipeline/tests/sample_signals.py and a way to run the Watcher
over them.
```
Done when: the 5 samples classify sensibly (scams high, normal benign). Commit.

**C2 — the safety gate** (deterministic, NOT an agent — this is your "not terrifying" answer).

```
Use plan mode first. In pipeline/classifier.py write route_action(proposal, assessment) ->
RoutingDecision. NO AI — pure rules: look up proposal.action_type in
lighthouse_common/action_registry.yaml (not found -> "human_gate"); if assessment.confidence < 0.5 ->
"watch_only"; elif reversible AND stakes==low -> "autonomous"; else -> "human_gate". Set reason to
which rule fired. Add pytest tests for: reversible+low+high-confidence (autonomous), pay_bill
(human_gate), low confidence (watch_only), unknown action (human_gate).
```
Done when: `pytest` passes all four. Commit.

### Keya

**K1 — the database** (do first; others need it).

```
Use plan mode first. Start Postgres with `docker compose up -d` (compose file in repo root, image
pgvector/pgvector:pg16). In data/ create tables using lighthouse_common/schemas.py objects: people,
guardians, trust_grants; plus tables for Signals, ThreatAssessments, ActionProposals,
RoutingDecisions, ActionResults; plus ledger_events (auto-increment id, timestamp, person_id,
event_type text, details JSON). Write data/seed.py inserting demo "Margaret" and guardian "Priya"
using the fixed IDs from lighthouse_common/demo_ids.py. Make seed.py safe to run many times.
```
Done when: `python data/seed.py` runs and Margaret + Priya exist. Commit.

**K2 — the mock email feed** (UNBLOCKS: Chaitanya's C1 — do this right after K1).

```
Use plan mode first. In data/ build a FastAPI app (data/main.py) on port 8001. Add GET /signals/next
returning one fake email Signal at a time (matching the Signal class, source="email"), from a
built-in list of ~6 emails: some scams ("account locked, pay $200", fake bank link), some normal
(pharmacy refill, note from family). Add CORS for http://localhost:5173.
```
Done when: `http://localhost:8001/signals/next` returns a fake email JSON. **Tell Chaitanya it's ready.** Commit.

**K3 — the ledger** (the trust story).

```
Use plan mode first. Add to the FastAPI app: POST /ledger (saves an event: event_type + details JSON
+ person_id to ledger_events) and GET /ledger?person_id=... (returns events newest first). Make
ledger_events append-only: the DB user can INSERT and SELECT but NOT UPDATE or DELETE (run a REVOKE
so the database enforces it). Comment that this is our tamper-evidence feature.
```
Done when: you can POST an event and GET it back; deleting a ledger row is refused. Commit.

### Sonakshi

**S1 — app skeleton + family dashboard** (the most important screen; uses fake data, no backend yet).

```
Use plan mode first. Create a React app (Vite) in web/ with Tailwind. Build the family guardian
dashboard with FAKE hard-coded data (no backend yet): a header "Lighthouse — watching out for
Margaret"; a "Needs your decision" section listing pending approvals, each with a plain message
("A scam email asked Margaret to pay $200. Should I pay it?") and two big buttons Approve (green) and
Deny (red) with icon + word; a "What I've handled" section of recent automatic actions. Design for an
older person's family: text at least 18px, high contrast, big buttons, calm and trustworthy, not
techy.
```
Done when: dashboard loads (`npm run dev`, http://localhost:5173) showing the fake approval and actions. Commit.

**S2 — the history timeline** (trust + Arize story).

```
Use plan mode first. Add a "History" panel to the dashboard showing a timeline of everything
Lighthouse did for Margaret, newest first (email received -> flagged as scam -> quarantined -> family
notified). Use fake timeline data. Each entry shows time and a clear icon for the event type. Clean
and complete-looking.
```
Done when: the timeline renders with fake events. Commit.

### CHECKPOINT 1 (~hour 6) — Chaitanya + Keya

Connect the feed to the Watcher: change Chaitanya's Watcher to pull a Signal from Keya's
`http://localhost:8001/signals/next` instead of the built-in samples, and confirm it classifies a
real-from-the-feed scam email. If it works, the data->pipeline seam is proven. If it breaks, paste
the error into Claude Code: "this is the call from my Watcher to Keya's /signals/next, here's the
error, find which side is wrong." Fix before moving on.

---

## BLOCK B (hours 8-12) — the decision flow

### Chaitanya

**C3 — the Guardian agent** (decides what to do, then routes through your gate).

```
Use plan mode first. Build the Guardian as a Fetch.ai uAgent in pipeline/guardian.py. It receives a
ThreatAssessment. Using Claude, it picks ONE action_type from lighthouse_common/action_registry.yaml
(it may ONLY pick from that file — never invent an action) and builds an ActionProposal. Then it calls
route_action() from classifier.py. If route is "autonomous", send to the executor (placeholder). If
"human_gate", send to the Escalation agent (placeholder). If "watch_only", just log. Print each step.
```
Done when: a scam assessment -> quarantine_email routed autonomous; a "pay to unlock" assessment -> high-stakes proposal routed human_gate. Commit.

**C4 — the Escalation agent** (asks the family). NEEDS: Keya's K4 approval bridge; until it exists, point at a fake endpoint that auto-denies after 5s.

```
Use plan mode first. Build the Escalation agent as a Fetch.ai uAgent in pipeline/escalation.py. It
receives an ActionProposal needing approval, uses Claude to write a short plain 6th-grade message
explaining what was found and what it wants to do, POSTs it to {DATA_URL}/approvals (read DATA_URL
from .env, default http://localhost:8001), then polls {DATA_URL}/approvals/{id} every 2s until
"approved" or "denied". Approved -> send to executor; denied -> log and stop. Until Keya's endpoint
exists, use a fake local endpoint that auto-denies after 5s.
```
Done when: a human_gate proposal produces a message and waits for a decision. Commit.

### Keya

**K4 — the approval bridge** (the link between Chaitanya's Escalation agent and Sonakshi's dashboard; take your time). UNBLOCKS: Chaitanya's C4 and Sonakshi's S6.

```
Use plan mode first. Add approval endpoints to the FastAPI app: POST /approvals (Escalation calls
this with a proposal + message; saves status="pending", returns approval_id); GET
/approvals?status=pending (dashboard lists what needs deciding); POST /approvals/{id}/decide (dashboard
sends "approved"/"denied", updates status); GET /approvals/{id} (the agent polls for the decision).
Also write every approval and decision to the ledger (POST /ledger).
```
Done when: you can create a pending approval, list it, decide it, and read the decision back. Test it yourself. **Tell Chaitanya and Sonakshi the endpoints are live.** Commit.

**K5 — Sentry** (your prize, and genuinely useful).

```
Use plan mode first. Add the Sentry SDK to the data/ FastAPI app (read SENTRY_DSN from .env) to
auto-capture errors and slow requests. Add GET /sentry-test that throws an error so I can confirm it
shows in the Sentry dashboard.
```
Done when: hitting `/sentry-test` makes an error appear in Sentry. Commit. Tell Chaitanya how to add the same setup to the agents (the executor crashes a lot — Sentry catching it is a real demo point). Visit the Sentry booth.

### Sonakshi

**S3 — the protected-person screen** (gentle, simple).

```
Use plan mode first. Make a simple page for Margaret herself at route /me. Calm and reassuring — NOT
scary scam details or controls. Just a friendly message ("Everything's okay. Lighthouse is looking
out for you."), the date, maybe one gentle reminder. Huge text, lots of space. She must have NO
button that turns off protection — only family can. No settings or off switches at all.
```
Done when: /me loads and feels calm and safe. Commit.

**S4 — the fake inbox the robot acts on** (demo-critical: Chaitanya's browser agent drives this). UNBLOCKS: Chaitanya's C5.

```
Use plan mode first. Build a standalone page at route /inbox that looks like a real email inbox (list
with sender, subject, time) and a "Quarantine" folder in a sidebar. Pre-load a few emails including
an obvious scam. A computer-use robot will operate THIS page to move a scam email into Quarantine, so
make clicking an email and a "Move to Quarantine" button actually move it. Clear, clearly labeled
buttons so an automated agent can find them.
```
Done when: you can manually move a scam email to Quarantine and see it move. **Tell Chaitanya the inbox URL; set MOCK_INBOX_URL in .env.** Commit.

### CHECKPOINT 2 (~hour 12) — all three: the autonomous path end-to-end

Wire the full happy path with real pieces: Keya's feed -> Chaitanya's Watcher flags a scam ->
Guardian proposes quarantine -> gate says autonomous -> (for now, before the executor) the action is
recorded -> the event shows on Sonakshi's dashboard history. This is demo scenario 1. Get it working
before Block C. Whoever's seam breaks, pair on it with the error pasted into Claude Code.

---

## BLOCK C (hours 12-16) — real actions and the prize loop

### Chaitanya

**C5 — the browser-agent executor** (your Browserbase prize). NEEDS: Sonakshi's S4 inbox and S5 bank; use example.com until they exist.

This is the part that lets the AI actually operate a web page like a human (click the email, move it to Quarantine). We use **Browserbase + Stagehand** — Browserbase is a hackathon sponsor with its own prize, and Stagehand is its open-source framework with simple commands (`act()` to click/type, `observe()` to find elements). **Go to the Browserbase booth first** and confirm you can get an API key for the event; this is the riskiest task, so settle access before building.

```
Use plan mode first. In pipeline/executor.py build an executor that takes an approved ActionProposal
and performs it on a real web page using Browserbase + Stagehand (the Stagehand SDK driving a
Browserbase browser session; read BROWSERBASE_API_KEY and BROWSERBASE_PROJECT_ID from .env). Two
actions: quarantine_email (open MOCK_INBOX_URL, use Stagehand act() to click the flagged email and
click "Move to Quarantine") and the pay action (open MOCK_BANK_URL — only ever after approval).
Return an ActionResult with a screenshot as evidence and an undo_token where possible. Add a
DEMO_MODE path: if DEMO_MODE=1, skip the real browser call and return a realistic fake ActionResult
instantly (so the demo survives bad wifi).
```
Done when: with DEMO_MODE=1 it returns a clean fake result instantly; with real Browserbase it drives the mock inbox. Commit.

**Fallback if Browserbase keys are ALSO unavailable** — paste this instead (free, local, no booth needed):
```
Use plan mode first. Rebuild pipeline/executor.py to use the open-source Browser Use library
(Python, runs locally, no account needed) instead of Browserbase. Same two actions on MOCK_INBOX_URL
and MOCK_BANK_URL, same ActionResult output, same DEMO_MODE fallback. Keep the executor's function
signature identical so nothing else in the pipeline changes.
```
If even that fights you with under ~4 hours left, tell Claude Code: "replace the browser agent with a
simple Playwright script that clicks the known buttons on my mock pages" — for pages we built and
control, a fixed script demos identically. (If you drop to Playwright you lose the Browserbase prize
but keep the working demo.)

**C6 — Arize tracing + the evaluator** (the $1,000 cash; your highest-value half-day).

```
Use plan mode first. Part 1: add Arize tracing to all three agents and the executor — every Claude
call and agent step as a span (Arize tracing SDK, ARIZE_API_KEY from .env). Part 2: in
pipeline/evaluator.py build an LLM-as-judge. Make pipeline/tests/eval_emails.py with ~25 emails each
tagged true_label (scam/legit). Run the Watcher on all, then for each ask Claude "given this email
and the Watcher's verdict, was it correct? correct/incorrect + reason." Compute accuracy and print
the mistakes.
```
Done when: you have an accuracy number and a list of mistakes. **Then improve:** tell Claude Code "the Watcher wrongly flagged these as scam; improve its prompt to fix this without breaking the others," re-run, and screenshot before/after accuracy. That screenshot is your Arize booth artifact. Commit.

### Keya

**K6 — real Gmail feed** (STRETCH, only if ahead; otherwise the mock feed demos identically).

```
Use plan mode first. Add a real email source reading a test Gmail account via the Gmail API with
read-only OAuth, replacing /signals/next with real unread emails. Keep the fake list as a fallback.
Walk me through getting the Google OAuth credentials step by step like I'm new to this.
```
Done when: real emails come through. If OAuth fights you for 45+ minutes, stop and keep the mock feed. Commit. Otherwise, help Chaitanya add Sentry to the agents and support integration.

### Sonakshi

**S5 — the fake bank** (for the "ask first" scenario). UNBLOCKS: Chaitanya's C5 pay action.

```
Use plan mode first. Build a standalone page at route /bank that looks like a simple online banking
page — a balance and a "Make a payment" button leading to a payment form. In our demo the family
DENIES, so the payment never happens, but the page must exist and look real. Clean and realistic.
```
Done when: /bank loads and looks believable. **Set MOCK_BANK_URL in .env.** Commit.

**S6 — connect the dashboard to the real backend.** NEEDS: Keya's K4 bridge and K3 ledger.

```
Use plan mode first. Replace the fake data in my dashboard with real calls: pending approvals from
GET {VITE_DATA_URL}/approvals?status=pending (VITE_DATA_URL from .env, default
http://localhost:8001), poll every 2s; Approve/Deny buttons POST to
{VITE_DATA_URL}/approvals/{id}/decide; history from GET {VITE_DATA_URL}/ledger?person_id=<Margaret's
id from lighthouse_common/demo_ids.py>, poll every 2s. Keep fake data as a fallback if the backend is
unreachable so the screen never looks broken.
```
Done when: with Keya's backend running, a real pending approval appears and tapping Deny records it. Test with Keya. Commit.

### CHECKPOINT 3 (~hour 15) — all three: the human-gate path + the Arize number

Wire scenario 2 end-to-end: a "pay $200 to unlock" scam -> Watcher flags -> Guardian proposes a
high-stakes action -> gate routes human_gate -> Escalation posts to Keya's /approvals -> it appears on
Sonakshi's dashboard -> someone taps Deny live -> logged, nothing happens. Then confirm Chaitanya has
the Arize before/after screenshot. These two scenarios are the entire demo.

---

## BLOCK D (hours 16-19) — harden and rehearse

- **Chaitanya (C7):** lead final integration; confirm both scenarios run clean; make sure DEMO_MODE=1 produces an identical-looking run for when wifi dies.
- **Keya:** help test both paths; confirm the ledger shows the full trail for each scenario; make sure Sentry is catching executor errors.
- **Sonakshi (S7):** build the ~6-slide deck and run the full demo start-to-finish 3 times, timed to 2:40, including once in DEMO_MODE so everyone has felt the fallback. You hold the timer and direct who says what.

Deck (Sonakshi owns this; no AI writes your pitch): 1) the problem — someone you love is losing track of their digital life and scammers know it; 2) what Lighthouse is — watches, acts on safe things, asks family about risky things (say: not medical/financial advice, family stays in control); 3) live demo; 4) how it's safe — safe+reversible = it acts, risky+irreversible = it asks, always; 5) the person can't disable their own protection, only family can; 6) what's real + sponsors used (Claude, Fetch agents, Browserbase, Arize, Sentry).

Demo script (rehearse to 2:40): dashboard -> scam email arrives -> flagged and auto-quarantined on the inbox -> family screen shows "I handled this" -> scarier scam -> approval request appears -> tap Deny live -> logged. End line: "smart enough to act, safe enough to ask."

**S8 — voice (STRETCH, only if everything above is done):**
```
Use plan mode first. On the /me page add a mic button so Margaret can speak a question. Use Deepgram
(DEEPGRAM_KEY from .env) for speech-to-text, send it to the backend as a voice Signal, and read the
answer back with Deepgram text-to-speech. Walk me through getting a Deepgram key.
```

---

## SUBMIT (hours 19-20) — all three

- [ ] Public GitHub repo with all code
- [ ] A screenshot of the project (the dashboard mid-scenario looks great)
- [ ] A demo video, 3 minutes max (screen-record both scenarios + the one-line pitch)
- [ ] ~200-word writeup (what it does, the safety design, which sponsors you used)
- [ ] Table number on the submission so judges can find you
- [ ] All 3 teammates listed
- [ ] Booth visits done — especially Arize (their prize requires telling them at the booth)

Rule: all code must be written during the hackathon. This plan and the architecture are planning (allowed); you start from empty folders, so you're clean.

---

## If you fall behind — cut in this order, without guilt

1. Voice (S8) — cut first.
2. Real Gmail (K6) — use the mock feed; nobody can tell.
3. Transaction scenarios — email-only is enough.
4. The fancy /me page — a simple reassurance screen is fine.

Never cut: the two demo scenarios, the deterministic safety gate (C2), the Arize before/after (C6), and the ledger (K3). Those are the thesis and the prizes.