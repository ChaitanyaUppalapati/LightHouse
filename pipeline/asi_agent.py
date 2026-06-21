"""Lighthouse ASI:One coordinator agent (Fetch.ai "Intent to Action" challenge).

ONE Chat-Protocol agent that exposes the whole Lighthouse pipeline through ASI:One,
so the entire workflow runs from chat with no custom frontend (a Fetch requirement).

Paste an email (or describe a situation) in ASI:One chat and this agent orchestrates
the real multi-agent pipeline:
    Watcher (classify) -> Guardian (propose an action) -> deterministic safety gate
    -> executor (act, or ask a human)
then replies in plain English: what it found, what it decided, how the gate routed
it, and what it did. The HIGH-STAKES / human-gate path is handled in chat — it asks
"approve or deny?" and you reply — so both demo scenarios run end-to-end from ASI:One.

The agent's brain is Claude (the same pipeline code as the rest of Lighthouse); the
Chat Protocol is just how ASI:One discovers and talks to it.

Run + register on Agentverse:
    python -m pipeline.asi_agent
Then open the Inspector link it prints -> Connect -> Mailbox. The agent's Agentverse
profile gets a "Chat with Agent" button that opens it in ASI:One.
"""

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

from uagents import Agent, Context, Protocol  # noqa: E402
from uagents_core.contrib.protocols.chat import (  # noqa: E402
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    StartSessionContent,
    TextContent,
    chat_protocol_spec,
)

from lighthouse_common.demo_ids import MARGARET_PERSON_ID  # noqa: E402
from lighthouse_common.schemas import Signal  # noqa: E402
from pipeline.classifier import route_action  # noqa: E402
from pipeline.executor import execute  # noqa: E402
from pipeline.guardian import propose_action  # noqa: E402
from pipeline.phoenix_tracing import init_tracing, span  # noqa: E402
from pipeline.watcher import classify_signal  # noqa: E402

load_dotenv()
init_tracing()

# mailbox=True registers on Agentverse for ASI:One. Set AGENT_MAILBOX=0 to run the
# agent purely locally (e.g. the end-to-end Bureau demo, pipeline/demo_e2e.py).
_MAILBOX = os.getenv("AGENT_MAILBOX", "1") == "1"
# Three ways to run, in priority order:
#   AGENT_ENDPOINT set -> register by a PUBLIC endpoint (the Agentverse "Add your agent
#       details" wizard: tunnel port 8104 and pass https://<tunnel>/submit).
#   AGENT_MAILBOX=1     -> mailbox (Inspector -> Connect), no public endpoint needed.
#   AGENT_MAILBOX=0     -> fully local (Bureau demos).
_ENDPOINT = os.getenv("AGENT_ENDPOINT")
if _ENDPOINT:
    _conn = {"endpoint": [_ENDPOINT], "publish_agent_details": True}
elif _MAILBOX:
    _conn = {"mailbox": True, "publish_agent_details": True}
else:
    _conn = {}
agent = Agent(
    name="lighthouse",
    seed=os.getenv("LIGHTHOUSE_AGENT_SEED", "lighthouse-asi-one-coordinator-seed"),
    port=int(os.getenv("AGENT_PORT", "8104")),
    **_conn,
)

chat = Protocol(spec=chat_protocol_spec)

# Per-sender pending high-stakes approval, so the human-gate path runs in chat:
# we ask "approve or deny?" and resolve it on the sender's next message.
_pending: dict[str, dict] = {}


def _signal_from_text(text: str) -> Signal:
    """Treat the pasted chat text as the email to judge."""
    lines = [ln for ln in text.splitlines() if ln.strip()]
    subject = lines[0][:120] if lines else "(no subject)"
    return Signal(
        signal_id="asi-" + uuid.uuid4().hex[:10],
        person_id=MARGARET_PERSON_ID,
        source="email",
        payload={"subject": subject, "body": text},
        observed_at=datetime.now(timezone.utc),
    )


def _run_pipeline(text: str, sender: str) -> str:
    """Run Watcher -> Guardian -> gate -> executor and return a chat-ready report."""
    with span("asi_agent.handle", **{"openinference.span.kind": "AGENT"}):
        assessment = classify_signal(_signal_from_text(text))

        head = (
            f"🔦 Lighthouse looked at this.\n\n"
            f"• What I see: **{assessment.category}** (severity {assessment.severity}, "
            f"confidence {assessment.confidence:.0%})\n"
            f"• Why: {assessment.rationale}\n"
        )

        # An ordinary, safe message needs no action — the default is to alert, not act.
        if assessment.category == "benign":
            return head + "\n✅ This looks like an ordinary, safe message. No action needed."

        proposal = propose_action(assessment)
        decision = route_action(proposal, assessment)

        if decision.route == "watch_only":
            return (
                head
                + f"\n🟡 I'm not sure enough to act, so I'm just keeping watch "
                f"(rule: {decision.reason}). Nothing was changed."
            )

        if decision.route == "autonomous":
            # quarantine_email is a real computer-use action (the executor drives the
            # inbox); the other low-stakes actions are bookkeeping, no browser needed.
            if proposal.action_type == "quarantine_email":
                result = execute(proposal)
                undo = (
                    f" You can undo it (token {result.undo_token})."
                    if result.undo_token else ""
                )
                return (
                    head
                    + f"\n✅ Safe + reversible, so I handled it automatically: "
                    f"**{proposal.action_type}** — {proposal.expected_effect}\n"
                    f"Result: {result.status}.{undo}"
                )
            return (
                head
                + f"\n✅ Safe + reversible, so I handled it automatically: "
                f"**{proposal.action_type}** — {proposal.expected_effect}"
            )

        # human_gate — ask the family/guardian, in chat.
        _pending[sender] = {"proposal": proposal, "assessment": assessment}
        return (
            head
            + f"\n🛑 This is high-stakes ({decision.reason}), so I will NOT do it on my "
            f"own. I want to **{proposal.action_type}** — {proposal.expected_effect}\n\n"
            f"**Reply `approve` or `deny`.**"
        )


def _resolve_pending(text: str, sender: str) -> str | None:
    """If this sender has a pending approval and said approve/deny, resolve it."""
    pending = _pending.get(sender)
    if not pending:
        return None
    word = text.strip().lower()
    if word not in ("approve", "approved", "yes", "deny", "denied", "no"):
        return (
            "You have a pending decision. Please reply `approve` or `deny`."
        )
    _pending.pop(sender, None)
    proposal = pending["proposal"]
    if word in ("approve", "approved", "yes"):
        result = execute(proposal)
        return (
            f"✅ Approved. I carried out **{proposal.action_type}**. "
            f"Result: {result.status}."
        )
    return (
        f"🚫 Denied. I did **not** do {proposal.action_type}. Nothing happened — "
        f"the money/account is safe."
    )


def _reply(text: str) -> ChatMessage:
    return ChatMessage(
        timestamp=datetime.now(timezone.utc),
        msg_id=uuid.uuid4(),
        content=[TextContent(type="text", text=text), EndSessionContent(type="end-session")],
    )


@chat.on_message(ChatMessage)
async def handle_chat(ctx: Context, sender: str, msg: ChatMessage) -> None:
    # Acknowledge receipt (Chat Protocol contract).
    await ctx.send(
        sender,
        ChatAcknowledgement(timestamp=datetime.now(timezone.utc), acknowledged_msg_id=msg.msg_id),
    )

    # Greet on session start.
    if any(isinstance(c, StartSessionContent) for c in msg.content):
        await ctx.send(
            sender,
            _reply(
                "Hi — I'm Lighthouse. Paste a suspicious email (or describe what "
                "happened) and I'll check it, decide what to do, and either handle it "
                "safely or ask you before anything risky."
            ),
        )
        return

    text = "".join(c.text for c in msg.content if isinstance(c, TextContent)).strip()
    if not text:
        return

    import asyncio

    resolved = await asyncio.to_thread(_resolve_pending, text, sender)
    reply_text = resolved if resolved is not None else await asyncio.to_thread(
        _run_pipeline, text, sender
    )
    await ctx.send(sender, _reply(reply_text))


@chat.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement) -> None:
    pass


agent.include(chat, publish_manifest=True)


if __name__ == "__main__":
    print(f"Lighthouse agent address: {agent.address}")
    agent.run()
