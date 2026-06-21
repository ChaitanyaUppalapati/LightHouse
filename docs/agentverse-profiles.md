# Agentverse profiles — Lighthouse agents

Copy the **About** into each agent's short description and the **README** into the
agent's README/overview on Agentverse. Lighthouse is a multi-agent system that
protects an older adult's digital life from scams, with family oversight.

Addresses:
- `lighthouse` (coordinator): `agent1q2m2n78js6cs7rlemgullzt2gvlw250sh32stks84cxwm0u35sd77y3rsx7`
- `lighthouse-watcher`: `agent1q2pvrz4aw6fzsn24wyxf6jeeq967nn66u7fl9w643stzc3k9tph7unfp0ld`
- `lighthouse-guardian`: `agent1qf3j6f0lce4csuzwggj0d2apuvhcrpdmaa4hs9ja8g5syz2quz8pv9eqpuu`
- `lighthouse-executor`: `agent1qg64arczlxvq5yx2acg82d7ycn3avnh8t4deh89rfm8q43rg0l5yv44rw3e`

---

# 1. `lighthouse` — coordinator (the one you chat with)

**About:**
> 🔦 Lighthouse — an AI guardian that protects older adults from scams. Paste a suspicious email and it checks it, quietly handles safe threats on its own, and asks the family before anything risky (like moving money). Smart enough to act, safe enough to ask.

**README:**
```markdown
# 🔦 Lighthouse

An AI guardian for someone whose memory is declining — it watches their inbox for
scams, acts on the safe stuff automatically, and asks a family member before anything
risky. Chat with it on ASI:One: paste a suspicious email and see what it does.

## What it does
Lighthouse coordinates a small team of agents to turn an email into a safe outcome:

1. **Watcher** classifies the email — scam/phishing or benign, with severity,
   confidence, and the concrete cues it used.
2. **Guardian** chooses one protective action from a fixed, pre-approved list (it can
   never invent an action).
3. A **deterministic safety gate** decides who acts: reversible + low-stakes runs
   automatically; anything irreversible or high-stakes (like paying money) is routed
   to a human.
4. **Executor** carries out autonomous actions on the real interface (e.g. moving a
   scam email to Quarantine) and returns an undo token.

## How to use it
Just send a message. Examples:

- *"From: IT Helpdesk <support@mailbox-quota-alert.com> — Your mailbox is full,
  verify your account at http://mailbox-quota-alert.com/verify"*
  → flagged as phishing and **auto-quarantined** (reversible, low-stakes).
- *"Your account is locked — pay a $200 fee to unlock it."*
  → high-stakes, so it **will not pay on its own**. It asks you: reply **`approve`**
  or **`deny`**. Reply `deny` and nothing happens — the money is safe.
- A normal family note → *"This looks like an ordinary, safe message. No action needed."*

## Why it's safe
- **The default is to alert, not act.** Acting is the exception.
- **Reversibility gates autonomy** — a 99%-sure agent still cannot move money alone.
- Every consequential action is **logged to an append-only ledger** and is reversible
  where possible. Nothing here is medical, legal, or financial advice — a human
  approves anything that matters.

## Under the hood
Built with **Fetch.ai uAgents** (Agent Chat Protocol), reasoning by **Claude**,
real computer-use via **Browserbase**, and traced/evaluated in **Arize Phoenix**.
It collaborates with three sibling agents: `lighthouse-watcher`,
`lighthouse-guardian`, and `lighthouse-executor`.
```

---

# 2. `lighthouse-watcher` — detection

**About:**
> The detection brain of Lighthouse. It reads an incoming email and judges it — scam/phishing, financial anomaly, account risk, missed obligation, or benign — with a severity, a confidence score, a plain-English rationale, and the exact cues it spotted. It only raises concerns; it has no power to act.

**README:**
```markdown
# Lighthouse — Watcher

The detection agent in the Lighthouse system. Input: a `Signal` (an observed thing,
usually an email). Output: a `ThreatAssessment`.

## What it does
Using Claude at temperature 0, it classifies the item into:
- **category:** scam_phishing · financial_anomaly · missed_obligation · account_risk · benign
- **severity:** none · low · moderate · high
- **confidence:** 0–1
- **rationale:** one or two plain sentences a worried family member would understand
- **evidence:** the concrete cues (look-alike sender domain, urgency, credential/payment
  demand, suspicious link, …)

It deliberately does **not** over-flag legitimate security mail (real password resets,
bank fraud alerts) — those are benign.

## Role & safety
The Watcher has **no power to act** — separation of powers is the safety property. It
raises concerns and hands the assessment to `lighthouse-guardian`. Its rationale and
evidence are what the system's eval loop (Arize Phoenix LLM-as-judge) grades.

Part of the **Lighthouse** multi-agent system (coordinator: `lighthouse`). Built with
Fetch.ai uAgents + Claude.
```

---

# 3. `lighthouse-guardian` — decision

**About:**
> The decision-maker. Given a threat, it picks the single best protective action from a fixed, pre-approved registry (it can never invent one), then routes it through Lighthouse's deterministic safety gate. It only proposes — it never executes.

**README:**
```markdown
# Lighthouse — Guardian

The decision agent in the Lighthouse system. Input: a `ThreatAssessment`. Output: an
`ActionProposal`, routed through the safety gate.

## What it does
Using Claude, the Guardian chooses **one** action from a fixed registry — it may only
pick a pre-approved `action_type`, never invent one. The vocabulary is finite and each
action is pre-classified for reversibility and stakes:

| action | reversible | stakes |
|---|---|---|
| quarantine_email, flag_transaction, block_sender, label_and_notify | yes | low |
| freeze_card | yes | high |
| pay_bill, reset_credentials, reply_to_sender | no | high |

It then calls the **deterministic safety gate** (no AI, a pure lookup):
- reversible **and** low-stakes → **autonomous** (the executor acts)
- irreversible **or** high-stakes → **human_gate** (a family member decides)
- too-low confidence → **watch_only**

## Role & safety
The Guardian only **proposes** — it never executes and never decides the route. The
finite action registry plus the deterministic gate are core safety properties: a
catastrophic action is defined as irreversible/high-stakes and is mechanically routed
to a human.

Part of the **Lighthouse** multi-agent system (coordinator: `lighthouse`). Built with
Fetch.ai uAgents + Claude.
```

---

# 4. `lighthouse-executor` — action

**About:**
> The hands of Lighthouse. It carries out approved or autonomous actions on real web interfaces — e.g. opening the inbox and moving a scam email to Quarantine — using Browserbase + Stagehand, and returns evidence (a session replay) plus an undo token. High-stakes actions only ever run after a human approves.

**README:**
```markdown
# Lighthouse — Executor

The action agent in the Lighthouse system. Input: an approved/autonomous
`ActionProposal`. Output: an `ActionResult`.

## What it does
It operates the real interface a person would use — there's no "trusted third party"
API for these accounts — driving a cloud browser via **Browserbase + Stagehand**:
- **quarantine_email** — open the inbox, click the flagged email, click *Move to
  Quarantine*.
- **pay_bill** — open the banking page and make a payment (reached **only** after a
  human approves; in the demo the family denies, so it never runs).

It returns evidence (a Browserbase session **replay URL**) and an **undo token** for
reversible actions. Computer-use fails often, so failures are captured, not crashed,
and a `DEMO_MODE` returns a clean cached result instantly so a demo survives bad wifi.

## Role & safety
The Executor never decides *whether* to act — it only carries out what the gate (and,
for high-stakes, a human) already approved. Reversible actions return an undo token.

Part of the **Lighthouse** multi-agent system (coordinator: `lighthouse`). Built with
Fetch.ai uAgents + Browserbase + Stagehand.
```
