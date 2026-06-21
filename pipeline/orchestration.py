"""Genuine agent-to-agent orchestration of the Lighthouse pipeline (Fetch.ai).

Four uAgents collaborate over the Fetch message bus to handle one request — this is
the real multi-agent / separation-of-powers story (the thing that detects danger is
not the thing that acts, which is not the thing that talks to the family):

    coordinator (ASI:One chat front door)
        --AnalyzeRequest-->  watcher    (classify a Signal -> ThreatAssessment)
        <--AssessmentMsg--   ...
    watcher  --AssessmentMsg-->  guardian   (propose an action + deterministic gate)
    guardian --ProposalMsg---->  executor   (autonomous: act, return result)
             \--ProposalMsg--->  coordinator (human_gate: ask the family in chat)
    executor --ResultMsg------>  coordinator (-> reply in chat)

Every envelope carries `chat_sender`, so the final ResultMsg returns to the right
ASI:One conversation with no shared coordinator state. Each agent reuses the
verified pipeline functions (classify_signal, propose_action, route_action, execute).

Run the whole thing locally and watch the hops:
    AGENT_MAILBOX=0 DEMO_MODE=1 python -m pipeline.orchestration demo

Run for real (coordinator on Agentverse for ASI:One; sub-agents local in-process):
    python -m pipeline.orchestration
"""

import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_HERE)
for _p in (_HERE, _REPO_ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from uagents import Agent, Bureau, Context, Model, Protocol  # noqa: E402
from uagents_core.contrib.protocols.chat import (  # noqa: E402
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    StartSessionContent,
    TextContent,
    chat_protocol_spec,
)

from lighthouse_common.demo_ids import MARGARET_PERSON_ID  # noqa: E402
from lighthouse_common.schemas import (  # noqa: E402
    ActionProposal,
    Signal,
    ThreatAssessment,
)
from pipeline.classifier import route_action  # noqa: E402
from pipeline.executor import execute  # noqa: E402
from pipeline.guardian import propose_action  # noqa: E402
from pipeline.phoenix_tracing import init_tracing  # noqa: E402
from pipeline.watcher import classify_signal  # noqa: E402

load_dotenv()
init_tracing()

_MAILBOX = os.getenv("AGENT_MAILBOX", "1") == "1"


# --- Inter-agent envelopes (carry chat_sender for correlation) ----------------

class AnalyzeRequest(Model):
    job_id: str
    chat_sender: str
    signal: Signal


class AssessmentMsg(Model):
    job_id: str
    chat_sender: str
    assessment: ThreatAssessment


class ProposalMsg(Model):
    job_id: str
    chat_sender: str
    assessment: ThreatAssessment
    proposal: ActionProposal
    route: str
    reason: str


class ResultMsg(Model):
    job_id: str
    chat_sender: str
    summary: str


# --- The agents (separation of powers) ----------------------------------------
# All four register on Agentverse when run live (AGENT_MAILBOX=1) so each has its own
# profile — the multi-agent story. AGENT_MAILBOX=0 runs them all locally in a Bureau.

watcher_agent = Agent(name="lighthouse-watcher", seed="lh-orch-watcher-seed", port=8111,
                      mailbox=_MAILBOX, publish_agent_details=_MAILBOX)
guardian_agent = Agent(name="lighthouse-guardian", seed="lh-orch-guardian-seed", port=8112,
                       mailbox=_MAILBOX, publish_agent_details=_MAILBOX)
executor_agent = Agent(name="lighthouse-executor", seed="lh-orch-executor-seed", port=8113,
                       mailbox=_MAILBOX, publish_agent_details=_MAILBOX)
coordinator = Agent(
    name="lighthouse",
    seed=os.getenv("LIGHTHOUSE_AGENT_SEED", "lighthouse-asi-one-coordinator-seed"),
    port=int(os.getenv("AGENT_PORT", "8104")),
    mailbox=_MAILBOX,
    publish_agent_details=_MAILBOX,
)

WATCHER = watcher_agent.address
GUARDIAN = guardian_agent.address
EXECUTOR = executor_agent.address
COORDINATOR = coordinator.address


# --- Summary text (what the family sees in chat) ------------------------------

def _head(a: ThreatAssessment) -> str:
    return (
        f"🔦 Lighthouse looked at this.\n\n"
        f"• What I see: **{a.category}** (severity {a.severity}, "
        f"confidence {a.confidence:.0%})\n"
        f"• Why: {a.rationale}\n"
    )


def _benign_summary(a: ThreatAssessment) -> str:
    return _head(a) + "\n✅ This looks like an ordinary, safe message. No action needed."


def _watch_summary(a: ThreatAssessment, reason: str) -> str:
    return _head(a) + f"\n🟡 I'm not sure enough to act, so I'm just keeping watch ({reason})."


def _acted_summary(a: ThreatAssessment, p: ActionProposal, result) -> str:
    line = (
        f"\n✅ Safe + reversible, so I handled it automatically: **{p.action_type}** — "
        f"{p.expected_effect}"
    )
    if result is not None:
        undo = f" You can undo it (token {result.undo_token})." if result.undo_token else ""
        line += f"\nResult: {result.status}.{undo}"
    return _head(a) + line


def _ask_summary(a: ThreatAssessment, p: ActionProposal, reason: str) -> str:
    return (
        _head(a)
        + f"\n🛑 This is high-stakes ({reason}), so I will NOT do it on my own. I want "
        f"to **{p.action_type}** — {p.expected_effect}\n\n**Reply `approve` or `deny`.**"
    )


# --- Watcher agent: classify ---------------------------------------------------

@watcher_agent.on_message(AnalyzeRequest)
async def watcher_handle(ctx: Context, sender: str, msg: AnalyzeRequest) -> None:
    ctx.logger.info(f"[watcher] classifying job {msg.job_id}")
    assessment = await asyncio.to_thread(classify_signal, msg.signal)
    ctx.logger.info(f"[watcher] -> {assessment.category} -> guardian")
    await ctx.send(GUARDIAN, AssessmentMsg(
        job_id=msg.job_id, chat_sender=msg.chat_sender, assessment=assessment))


# --- Guardian agent: propose + deterministic gate ------------------------------

@guardian_agent.on_message(AssessmentMsg)
async def guardian_handle(ctx: Context, sender: str, msg: AssessmentMsg) -> None:
    a = msg.assessment
    if a.category == "benign":
        ctx.logger.info(f"[guardian] benign -> coordinator (no action)")
        await ctx.send(COORDINATOR, ResultMsg(
            job_id=msg.job_id, chat_sender=msg.chat_sender, summary=_benign_summary(a)))
        return

    proposal = await asyncio.to_thread(propose_action, a)
    decision = route_action(proposal, a)
    ctx.logger.info(f"[guardian] {proposal.action_type} -> {decision.route}")
    pm = ProposalMsg(
        job_id=msg.job_id, chat_sender=msg.chat_sender, assessment=a,
        proposal=proposal, route=decision.route, reason=decision.reason)
    if decision.route == "autonomous":
        await ctx.send(EXECUTOR, pm)          # act now
    else:
        await ctx.send(COORDINATOR, pm)       # human_gate (ask) or watch_only


# --- Executor agent: act on the proposal --------------------------------------

@executor_agent.on_message(ProposalMsg)
async def executor_handle(ctx: Context, sender: str, msg: ProposalMsg) -> None:
    p = msg.proposal
    ctx.logger.info(f"[executor] executing {p.action_type}")
    if p.action_type == "quarantine_email":
        result = await asyncio.to_thread(execute, p)         # real computer-use action
        summary = _acted_summary(msg.assessment, p, result)
    else:
        summary = _acted_summary(msg.assessment, p, None)    # soft action, no browser
    await ctx.send(COORDINATOR, ResultMsg(
        job_id=msg.job_id, chat_sender=msg.chat_sender, summary=summary))


# --- Coordinator: the ASI:One chat front door ---------------------------------

chat = Protocol(spec=chat_protocol_spec)
_pending: dict[str, ProposalMsg] = {}  # chat_sender -> the gated proposal envelope


def _signal_from_text(text: str) -> Signal:
    lines = [ln for ln in text.splitlines() if ln.strip()]
    subject = lines[0][:120] if lines else "(no subject)"
    return Signal(
        signal_id="asi-" + uuid.uuid4().hex[:10],
        person_id=MARGARET_PERSON_ID,
        source="email",
        payload={"subject": subject, "body": text},
        observed_at=datetime.now(timezone.utc),
    )


def _chat(text: str) -> ChatMessage:
    return ChatMessage(
        timestamp=datetime.now(timezone.utc),
        msg_id=uuid.uuid4(),
        content=[TextContent(type="text", text=text), EndSessionContent(type="end-session")],
    )


@chat.on_message(ChatMessage)
async def coordinator_chat(ctx: Context, sender: str, msg: ChatMessage) -> None:
    await ctx.send(sender, ChatAcknowledgement(
        timestamp=datetime.now(timezone.utc), acknowledged_msg_id=msg.msg_id))

    if any(isinstance(c, StartSessionContent) for c in msg.content):
        await ctx.send(sender, _chat(
            "Hi — I'm Lighthouse. Paste a suspicious email and I'll have my agents "
            "check it, decide, and either handle it safely or ask you first."))
        return

    text = "".join(c.text for c in msg.content if isinstance(c, TextContent)).strip()
    if not text:
        return

    # Is this a decision on a pending high-stakes proposal?
    pending = _pending.get(sender)
    if pending is not None:
        word = text.lower()
        if word in ("approve", "approved", "yes"):
            _pending.pop(sender, None)
            ctx.logger.info("[coordinator] approved -> executor")
            await ctx.send(EXECUTOR, pending)   # now act
            return
        if word in ("deny", "denied", "no"):
            _pending.pop(sender, None)
            await ctx.send(sender, _chat(
                f"🚫 Denied. I did **not** do {pending.proposal.action_type}. "
                f"Nothing happened — the money/account is safe."))
            return
        await ctx.send(sender, _chat("You have a pending decision — reply `approve` or `deny`."))
        return

    # New email: kick off the agent chain at the Watcher.
    job_id = uuid.uuid4().hex[:8]
    ctx.logger.info(f"[coordinator] job {job_id} -> watcher")
    await ctx.send(WATCHER, AnalyzeRequest(
        job_id=job_id, chat_sender=sender, signal=_signal_from_text(text)))


@coordinator.on_message(ResultMsg)
async def coordinator_result(ctx: Context, sender: str, msg: ResultMsg) -> None:
    await ctx.send(msg.chat_sender, _chat(msg.summary))


@coordinator.on_message(ProposalMsg)
async def coordinator_proposal(ctx: Context, sender: str, msg: ProposalMsg) -> None:
    if msg.route == "watch_only":
        await ctx.send(msg.chat_sender, _chat(_watch_summary(msg.assessment, msg.reason)))
        return
    # human_gate: ask the family in chat; remember the proposal for the decision.
    _pending[msg.chat_sender] = msg
    await ctx.send(msg.chat_sender,
                   _chat(_ask_summary(msg.assessment, msg.proposal, msg.reason)))


@chat.on_message(ChatAcknowledgement)
async def coordinator_ack(ctx: Context, sender: str, msg: ChatAcknowledgement) -> None:
    pass


coordinator.include(chat, publish_manifest=True)


def build_bureau() -> Bureau:
    bureau = Bureau()
    for a in (coordinator, watcher_agent, guardian_agent, executor_agent):
        bureau.add(a)
    return bureau


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "run"
    if mode == "demo":
        from pipeline._orch_demo_driver import add_driver
        bureau = build_bureau()
        add_driver(bureau, COORDINATOR)
        bureau.run()
    else:
        print(f"coordinator (ASI:One) address: {COORDINATOR}")
        print(f"  watcher={WATCHER}\n  guardian={GUARDIAN}\n  executor={EXECUTOR}")
        build_bureau().run()
