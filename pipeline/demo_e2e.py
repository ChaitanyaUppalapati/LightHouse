"""End-to-end ASI:One-native demo (no Agentverse account needed).

Runs the Lighthouse coordinator agent and a `user` agent together in a uAgents
Bureau, and has the user agent drive it with REAL Chat Protocol messages — the exact
ChatMessage / ChatAcknowledgement traffic ASI:One sends. So this exercises the full
chat-in -> pipeline -> chat-out loop over the agent transport, just like ASI:One
would, but entirely locally.

It plays both demo scenarios:
  1. a phishing email   -> the agent auto-quarantines (autonomous)
  2. a "pay $200" scam  -> the agent asks; the user replies "deny" -> nothing happens

Run:  AGENT_MAILBOX=0 DEMO_MODE=1 python -m pipeline.demo_e2e
(AGENT_MAILBOX=0 keeps the coordinator local; DEMO_MODE=1 makes the executor instant.)
"""

import os
import sys
from datetime import datetime, timezone
from uuid import uuid4

os.environ.setdefault("AGENT_MAILBOX", "0")  # local Bureau, no Agentverse
os.environ.setdefault("DEMO_MODE", "1")      # instant executor

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_HERE)
for _p in (_HERE, _REPO_ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from uagents import Agent, Bureau, Context, Protocol  # noqa: E402
from uagents_core.contrib.protocols.chat import (  # noqa: E402
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
    chat_protocol_spec,
)

import pipeline.asi_agent as lighthouse  # noqa: E402  (builds the coordinator agent)

COORDINATOR = lighthouse.agent.address

PHISHING = (
    "From: IT Helpdesk <support@mailbox-quota-alert.com>\n"
    "Subject: Your mailbox is almost full\n"
    "Your mailbox is over quota and will stop receiving email. Verify your account "
    "now to keep it active: http://mailbox-quota-alert.com/verify"
)
PAY_SCAM = (
    "From: SecureBank Support <billing@secure-bank-help.com>\n"
    "Subject: Your account is LOCKED\n"
    "Pay a $200 verification fee within 24 hours to unlock your account or it will be closed."
)

user = Agent(name="user", seed="lighthouse-demo-user-seed", port=8107)
user_chat = Protocol(spec=chat_protocol_spec)
_step = {"n": 0}


async def _say(ctx: Context, text: str) -> None:
    print(f"\n\033[1mUSER →\033[0m {text.splitlines()[1] if chr(10) in text else text}")
    await ctx.send(
        COORDINATOR,
        ChatMessage(timestamp=datetime.now(timezone.utc), msg_id=uuid4(),
                    content=[TextContent(type="text", text=text)]),
    )


@user.on_event("startup")
async def kick_off(ctx: Context) -> None:
    print("=" * 70)
    print("END-TO-END over the ASI:One Chat Protocol (local Bureau)")
    print(f"coordinator: {COORDINATOR}")
    print("=" * 70)
    print("\n--- Scenario 1: a phishing email (expect autonomous quarantine) ---")
    await _say(ctx, PHISHING)


@user_chat.on_message(ChatMessage)
async def on_reply(ctx: Context, sender: str, msg: ChatMessage) -> None:
    await ctx.send(sender, ChatAcknowledgement(
        timestamp=datetime.now(timezone.utc), acknowledged_msg_id=msg.msg_id))
    reply = "".join(c.text for c in msg.content if isinstance(c, TextContent)).strip()
    print(f"\n\033[1mLIGHTHOUSE →\033[0m\n{reply}")

    _step["n"] += 1
    if _step["n"] == 1:
        print("\n--- Scenario 2: a 'pay $200 to unlock' scam (expect human gate) ---")
        await _say(ctx, PAY_SCAM)
    elif _step["n"] == 2:
        print("\n--- The family decides, in chat ---")
        await _say(ctx, "deny")
    else:
        print("\n" + "=" * 70)
        print("END-TO-END COMPLETE — both scenarios ran over the Chat Protocol.")
        print("=" * 70)
        os._exit(0)


@user_chat.on_message(ChatAcknowledgement)
async def on_ack(ctx: Context, sender: str, msg: ChatAcknowledgement) -> None:
    pass


user.include(user_chat)


if __name__ == "__main__":
    bureau = Bureau()
    bureau.add(lighthouse.agent)
    bureau.add(user)
    bureau.run()
