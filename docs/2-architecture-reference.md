# Lighthouse — Architecture Specification

**A protective multi-agent system that quietly holds together the digital life of a person whose cognition is declining — acting with family oversight, never overstepping.**

UC Berkeley AI Hackathon 2026. Target prizes: Anthropic, Fetch.ai, Browserbase, Sentry, Arize.

---

## 1. Design philosophy

Lighthouse acts inside a vulnerable person's real digital life. The user *cannot reliably judge the agent's mistakes* — that's the premise. So safety cannot lean on the user; it must be structural. Three principles, and they are the pitch:

1. **The default is to alert, not to act.** Acting is the exception; escalating is the norm. The interesting engineering is deciding what is safe enough to do without asking.
2. **Reversibility gates autonomy.** The system acts alone only on reversible, low-stakes things. Anything irreversible or high-stakes requires a human. This is a property of the *action*, not the agent's confidence — a 99%-sure agent still cannot move money alone.
3. **Protected person and guardian are different users with asymmetric powers.** The person is observed and protected; the family member authorizes and oversees. The person cannot, alone, remove their own protection — because a scam (or a confused moment) must never be able to talk them out of it.

One-line architecture: **signals in → agents reason → a deterministic gate decides act-alone vs ask-a-human → real actions on real interfaces → an immutable ledger watches all of it.** Intelligence at the edges, determinism at the gate.

---

## 2. The state model (the objects everything else references)

Five objects flow through the system. Freezing these is your hour-0 task — every component is built against them.

```python
# A raw thing observed in the world. Read-only. Never trusted.
class Signal(BaseModel):
    signal_id: str
    person_id: str
    source: Literal["email", "transaction", "account_event", "voice"]
    payload: dict           # the email, the charge, the lockout notice, the utterance
    observed_at: datetime

# The Watcher's judgment about a Signal. LLM-produced.
class ThreatAssessment(BaseModel):
    assessment_id: str
    signal_id: str
    category: Literal["scam_phishing", "financial_anomaly",
                      "missed_obligation", "account_risk", "benign"]
    severity: Literal["none", "low", "moderate", "high"]
    confidence: float       # 0..1, the Watcher's certainty
    rationale: str          # why — human-readable, feeds the ledger and the eval
    evidence: list[str]     # the specific cues (sender mismatch, urgency language, etc.)

# The Guardian's chosen response. Action is from a fixed registry, never freeform.
class ActionProposal(BaseModel):
    proposal_id: str
    assessment_id: str
    action_type: str        # MUST exist in the action registry (§4)
    target: dict            # what it acts on (email id, card id, etc.)
    rationale: str
    expected_effect: str    # plain-language, shown to the guardian if gated

# The deterministic router's verdict. NOT agent-produced.
class RoutingDecision(BaseModel):
    proposal_id: str
    route: Literal["autonomous", "human_gate", "watch_only"]
    reason: str             # "reversible+low_stakes" / "irreversible" / "low_confidence"

# What actually happened.
class ActionResult(BaseModel):
    proposal_id: str
    status: Literal["executed", "approved_executed", "denied", "failed", "watching"]
    evidence: dict          # screenshot ref, confirmation, error
    undo_token: str | None  # how to reverse it, if reversible
    completed_at: datetime
```

Persistence: **Postgres** for everything durable (people, guardians, trust grants, and the full chain of objects above). **Redis** (optional, see §11) for agent working memory and the per-person "normal" baseline used in anomaly detection.

---

## 3. Signal layer — watched, never trusted

**Purpose.** Sense the person's digital life without ever acting on it. Everything here is read-only, which is why it's the safe outer ring.

**Sources, in build-priority order:**
- **Email** (build first). The richest scam/phishing surface and the easiest to demo. Polls a controlled test inbox, emits one `Signal` per new message.
- **Transactions.** A feed of charges (real bank API is out of scope; use a mock feed you control). Emits a `Signal` per charge for anomaly assessment.
- **Account events.** Lockouts, password-reset emails, unpaid-bill notices — often arrive *as* emails, so this can piggyback on the email source initially.
- **Voice** (cheap to add, see Deepgram in §10). The person speaks ("did I pay the electric bill?"); transcript becomes a `Signal` with `source="voice"`. For this population, voice is often the only working interface.

**Contract.** Each source's only job: produce well-formed `Signal` objects onto a queue. No judgment here — judgment is the Watcher's.

**Failure posture.** A source that can't read a field still emits the `Signal` with what it has; missing data becomes the Watcher's problem to flag, never silently dropped.

---

## 4. Multi-agent core

Three agents, separated **on purpose**: the thing that *detects* danger is not the thing that *acts*, and neither is the thing that *talks to family*. Separation of powers is the safety property, and it is exactly the multi-agent collaboration Fetch.ai rewards. Implement each as a **Fetch.ai uAgent** so they communicate over the Fetch agent layer — that is the load-bearing Fetch integration and clears the BAND "≥2 agents collaborating" bar honestly.

### 4.1 Watcher — detects and classifies (LLM)

Input: a `Signal`. Output: a `ThreatAssessment`. Powered by Claude.

It answers: is this a threat, what kind, how severe, how sure am I, and *why*. The `rationale` and `evidence` fields are not decoration — they are what the Arize evaluator grades (§9) and what the ledger records. Use a structured-output prompt at temperature 0. The Watcher has **no power to act**; it raises concerns.

For anomaly detection (transactions), the Watcher compares against the person's baseline (usual payees, usual amounts) — pulled from Redis/Postgres. "A $4,000 charge to a new payee" is anomalous *relative to this person*.

**This is the most build-priority-critical agent**, because its classifications are what the Arize eval loop measures. Get it traced and gradeable early.

### 4.2 Guardian — proposes a response (LLM, but constrained)

Input: a `ThreatAssessment`. Output: an `ActionProposal`. Powered by Claude.

It decides *what to do* about a threat — but it selects from a **fixed action registry**, it cannot invent actions. This is a core safety design: the vocabulary of things the system can ever do is finite, and each entry is pre-classified for reversibility and stakes. The Guardian's LLM judgment is "which registry action fits this threat," not "what arbitrary thing should I do."

The Guardian also *proposes* only. It never executes — the routing decision and execution happen downstream.

### 4.3 The action registry (the finite vocabulary)

Every action the system can ever take, each tagged with reversibility and stakes. This is data (a YAML/table), versioned, and the Guardian may only emit `action_type` values from it.

| action_type | reversible? | stakes | what it does |
|---|---|---|---|
| `quarantine_email` | yes | low | move suspected scam to a holding folder |
| `flag_transaction` | yes | low | annotate a charge as suspicious for review |
| `block_sender` | yes | low | block a sender address |
| `label_and_notify` | yes | low | tag an item and tell the guardian |
| `unsubscribe` | partly | medium | stop a recurring subscription |
| `pay_bill` | no | high | pay an outstanding bill (money out) |
| `freeze_card` | yes | high | freeze a card (reversible but disruptive) |
| `reset_credentials` | no | high | change a password / recover an account |
| `reply_to_sender` | no | high | send a message (cannot unsend) |
| `(unknown)` | — | — | anything not in the registry → human gate |

### 4.4 Escalation — owns the family relationship (LLM + deterministic loop)

Input: a `ThreatAssessment`, and for gated actions, an `ActionProposal`. It decides what to surface to the guardian, with what urgency, composes the plain-language message (LLM), and runs the **approval/acknowledgment loop** (deterministic state machine — this is the OpenPill alert loop, reused almost wholesale). An unacknowledged approval request is not "sent" — it retries and escalates, because for this to be safe the human must actually respond.

---

## 5. Action classifier — deterministic, the keystone

Input: an `ActionProposal`. Output: a `RoutingDecision`. **No LLM. No agent. A lookup.**

Logic, in full:
```
entry = action_registry[proposal.action_type]   # unknown → fail-safe to human_gate
if assessment.confidence < CONFIDENCE_FLOOR:
    route = "watch_only"           # too unsure to act OR ask — just observe + soft-inform
elif entry.reversible and entry.stakes == "low":
    route = "autonomous"           # safe to do alone
else:
    route = "human_gate"           # irreversible OR high-stakes → a human decides
```

Why deterministic: the route an action takes must be **reproducible** (same action, same route, every time), **auditable** (every route traces to a rule), and **fail-safe** (unknown action → human). The agent's confidence never overrides reversibility — it can only *downgrade* to watch-only, never upgrade to autonomous. This box is your answer to "what stops it doing something catastrophic?": catastrophe is defined as irreversibility/high-stakes, and that is mechanically routed to a human.

---

## 6. The confidence × reversibility decision model

The two axes are independent and together define behavior. Worth a slide.

|                          | **Reversible + low-stakes** | **Irreversible or high-stakes** |
|--------------------------|------------------------------|----------------------------------|
| **High confidence**      | Act autonomously, log, inform | Propose → human approves → execute |
| **Low confidence**       | Watch only, soft-inform       | Watch only, surface as "we noticed, you decide" |

Reversibility picks the column (act-alone vs ask). Confidence picks the row (act/propose vs just-watch). The bottom-right is the most important cell: when unsure *and* the stakes are high, the system does the humble thing — it points the human at it without acting.

---

## 7. Execution paths + the computer-use executor (Browserbase + Stagehand)

Both routes, once cleared, run through one **computer-use executor** built on **Browserbase + Stagehand** (Stagehand is Browserbase's open-source browser-agent framework: `act()`/`observe()` primitives driving a cloud browser session). This is where the system acts on real interfaces — because these services have no clean "trusted third party acts on this account" API; you operate the UI the way a person would. Browserbase is a hackathon sponsor, so this layer also carries a prize. (Fallbacks if access stalls: the open-source Browser Use library, or a plain Playwright script over our own mock pages.)

- **Autonomous path:** reversible+low-stakes proposals execute immediately, then notify. Each returns an `undo_token` so a wrong call is recoverable.
- **Human-gate path:** the Escalation agent sends the guardian an approval request; only on approval does the executor run. Denial is logged and the action never happens.

**The executor is the highest technical risk in the system.** Mitigations are non-negotiable (see §12): it operates **controlled stand-in interfaces** (a mock inbox / mock bank you build), never real Gmail/Chase, and every demo path is cached behind `DEMO_MODE`.

---

## 8. Two-role interface + permission model

Two users, asymmetric powers — the design insight most teams miss.

**Protected person (PP):** sees gentle, reassuring status ("Lighthouse is looking out for you"); can talk to it (voice); sees what was done for them in plain terms. **Cannot:** disable protection, change the guardian, or approve high-stakes actions.

**Guardian (G):** authorized family member. **Can:** approve/deny gated actions, see the full ledger and traces, configure protection, serve as the recovery path.

**The load-bearing rule:** removing or weakening protection requires the Guardian, never the PP alone. A scam that tries to get the PP to "turn off the security thing" structurally cannot succeed — the control isn't theirs to give away.

**Trust establishment:** at setup, the PP grants the Guardian authority (modeled on how families already arrange power-of-attorney / account delegation). The demo can assume this is done, but the architecture names it so the legitimacy question has an answer (§13).

---

## 9. Ledger + observability (Arize) — and the $1,000 eval loop

**Immutable ledger.** Every `Signal`, `ThreatAssessment`, `ActionProposal`, `RoutingDecision`, and `ActionResult` is written append-only (DB-level `REVOKE UPDATE, DELETE`). This is simultaneously the ethical necessity (an agent in someone's financial life must be fully accountable), the "not terrifying" answer (every action is traced and reviewable), and the substrate Arize traces.

**Arize, done to win the prize (their explicit 5 steps):**
1. **Tracing on** — instrument every agent call (Watcher classify, Guardian propose, classifier route, executor run) as spans. Works with Claude/Fetch out of the box.
2. **Look at traces** — keep the dashboard open; be ready to walk one at the booth.
3. **Build an evaluator** — an LLM-as-judge prompt scoring the Watcher's classifications: given an email + the Watcher's verdict, was it correct? Run it over a labeled set of ~30 signals (scams, legit, borderline). This set doubles as demo content *and* `DEMO_MODE` cache — one artifact, three uses.
4. **Close the loop** — the eval surfaces failures (a legit pharmacy email flagged as phishing; worse, a scam let through). Change the Watcher prompt/threshold, re-run, show the score move. **The before/after number is the winning artifact:** "we were flagging 30% of legit mail as scam; the eval caught it; we fixed the prompt; now 8%."
5. **Tell them at the booth** — show the trace, the evaluator, the before/after.

This is the highest-ROI prize on the list: light integration, half a day of focused work, and almost no team will construct the explicit before/after narrative. It's $1,000 cash.

---

## 10. Prize integration map (your 5 targets)

Every integration is load-bearing, not bolted on:

- **Anthropic** — built with Claude Code; Claude is the reasoning in Watcher/Guardian/Escalation; "protecting people losing cognitive capacity" is dead-center in their health / biggest-swing brief.
- **Fetch.ai** — the three agents are real uAgents collaborating over the Fetch layer; satisfies BAND's ≥2-agents bar by design.
- **Browserbase** — the executor operates real interfaces via Stagehand on a Browserbase browser session; acting on accounts the person can no longer safely operate is a strong, justified use case.
- **Arize** — the eval loop in §9; the agent graph is the observability subject.
- **Sentry** — instrument the pipeline with the Sentry SDK for error/performance monitoring. Computer-use *fails constantly*, so Sentry catching and surfacing those failures is a genuine integration, not theater. Their judging also rewards team execution and communication under pressure — so you win this by using the SDK for real *and* demoing with poise.

**One-step-away stretch prizes:** voice is already in the signal layer → **Deepgram** is nearly free to add (STT for the voice `Signal`, TTS for the reassurance UI). Agent memory/baseline is already in the design → **Redis** (Redis Iris for agent memory + vector recall of past assessments) is nearly free. Pursue only after the core 5 are solid.

---

## 11. Tech stack

| Concern | Choice |
|---|---|
| Build tool | Claude Code |
| Reasoning LLM | Claude |
| Agent runtime | Fetch.ai uAgents (Watcher / Guardian / Escalation) |
| Browser-agent executor | Browserbase + Stagehand (fallback: Browser Use, or Playwright) |
| Tracing + eval | Arize |
| Error monitoring | Sentry SDK |
| Backend | FastAPI + Pydantic |
| Datastore | Postgres (durable) + Redis (optional: memory/baseline) |
| Frontend | React (two-role dashboard) + the stand-in mock interfaces |
| Voice (stretch) | Deepgram STT/TTS |

---

## 12. Demo architecture + DEMO_MODE

**Never operate real accounts on stage.** Build **controlled stand-in interfaces** — a mock email inbox and a mock banking page that look real — and point the browser agent at those. The computer-use is genuinely real (Stagehand drives a real browser); only the *accounts* are stand-ins. This keeps the demo live and honest while removing the ethical and reliability landmine.

**Hero demo, two scenarios to show both paths:**
1. *Autonomous path:* a phishing email arrives on stage → Watcher flags it (high confidence, scam) → Guardian proposes `quarantine_email` (reversible, low) → classifier routes autonomous → the browser agent quarantines it in the stand-in inbox → ledger logs → guardian dashboard updates. Visceral, fast, proves the agents act.
2. *Human-gate path:* a "your account is locked — pay $200 to restore" scam → Watcher flags → Guardian proposes a high-stakes action → classifier routes to human gate → guardian's phone gets an approval request → guardian **denies** → logged, nothing happens. Proves the safety thesis live.

**DEMO_MODE:** cached browser-agent runs and scripted interface states so a flaky live computer-use call degrades to an identical-looking cached path instead of a dead demo.

---

## 13. The two questions judges will ask, and the answers

**"How is this not terrifying?"** Three structural answers: nothing irreversible or high-stakes happens without human approval (the deterministic gate); every action is traced in an immutable ledger and is reversible where possible (undo tokens); the system's default is to alert, not act. The fail-safe-toward-caution instinct is the whole spine.

**"Is this even legal / who consented?"** The guardian is an authorized family member acting on prior consent — the way families already arrange power-of-attorney and account delegation for declining relatives. Lighthouse operationalizes a relationship that already exists legally; it doesn't invent a new authority. (Not a hackathon deliverable to solve fully, but having the answer preempts the objection.)

Nothing Lighthouse outputs is medical, legal, or financial advice; the human-in-the-loop approval on every consequential action is what keeps it on the right side of that line — which is also what makes it trustworthy to judges.

---

## 14. MVP cut line — it is the night of the 20th, ~20 hours to submit

**Must exist (the thesis + all 5 prizes):**
- Watcher classifying **email scams** (one signal type), as a Fetch uAgent, traced in Arize.
- Guardian proposing from a **3-action registry** (`quarantine_email`, `flag_transaction`, `pay_bill`), as a Fetch uAgent.
- Deterministic action classifier + the routing matrix.
- Browser-agent executor (Browserbase + Stagehand) on a **mock inbox** (autonomous quarantine) + a **mock bank** approval (human-gate deny).
- Escalation approval/ack loop (reuse OpenPill's).
- Append-only ledger + Sentry instrumentation.
- Two-role dashboard: guardian approval UI + live ledger view; PP reassurance view (can be simple).
- Arize evaluator over the Watcher + one before/after improvement.

**Stretch, only if ahead:** transaction anomaly signal; voice + Deepgram; Redis memory/baseline; a richer PP interface; a third demo scenario.

**Cut without mercy if behind:** real anything (always stand-ins); multiple signal types beyond email; the trust-establishment UI (assume it done); anything that doesn't either prove the thesis or land a prize.

---

## 15. Three-person build split (hard technical → Chaitanya)

**Chaitanya — the agent spine + the brain (and 3 prizes):** the three Fetch uAgents (Watcher/Guardian/Escalation orchestration), the deterministic action classifier + registry, the Browserbase + Stagehand executor integration, and the Arize tracing + evaluator loop. This is the technical heart and carries Fetch, Browserbase, and Arize.

**Teammate 2 — data, ledger, workflow, Sentry:** Postgres schema for the §2 objects, the append-only ledger, the escalation approval/ack loop (port from OpenPill), the two-role permission model, and Sentry instrumentation across the pipeline.

**Teammate 3 — interfaces + demo + pitch:** the two-role React dashboard (guardian approval + live ledger/trace view + PP reassurance), the **stand-in mock inbox and mock bank** that the browser agent drives (demo-critical infrastructure), the deck, and the demo script for both scenarios.

Shared hour-0 task, all three: freeze the §2 state model into `schemas.py`, agree the action registry, pin demo identities. Then build against mocks in parallel; integrate around the executor last.