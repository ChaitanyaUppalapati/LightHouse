"""Demo driver for pipeline/orchestration.py — a `user` agent that drives the
coordinator with real Chat Protocol messages and prints the conversation, so the
agent-to-agent flow can be watched end-to-end locally.
"""

import os
from datetime import datetime, timezone
from uuid import uuid4

from uagents import Agent, Bureau, Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
    chat_protocol_spec,
)

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


def add_driver(bureau: Bureau, coordinator_address: str) -> None:
    user = Agent(name="user", seed="lighthouse-demo-user-seed", port=8114)
    user_chat = Protocol(spec=chat_protocol_spec)
    step = {"n": 0}

    async def say(ctx: Context, text: str) -> None:
        shown = text.splitlines()[1] if "\n" in text else text
        print(f"\n\033[1mUSER →\033[0m {shown}", flush=True)
        await ctx.send(coordinator_address, ChatMessage(
            timestamp=datetime.now(timezone.utc), msg_id=uuid4(),
            content=[TextContent(type="text", text=text)]))

    @user.on_event("startup")
    async def kick_off(ctx: Context) -> None:
        print("=" * 70, flush=True)
        print("AGENT-TO-AGENT end-to-end (coordinator -> watcher -> guardian -> executor)",
              flush=True)
        print("=" * 70, flush=True)
        print("\n--- Scenario 1: phishing email (expect autonomous quarantine) ---", flush=True)
        await say(ctx, PHISHING)

    @user_chat.on_message(ChatMessage)
    async def on_reply(ctx: Context, sender: str, msg: ChatMessage) -> None:
        await ctx.send(sender, ChatAcknowledgement(
            timestamp=datetime.now(timezone.utc), acknowledged_msg_id=msg.msg_id))
        reply = "".join(c.text for c in msg.content if isinstance(c, TextContent)).strip()
        print(f"\n\033[1mLIGHTHOUSE →\033[0m\n{reply}", flush=True)

        step["n"] += 1
        if step["n"] == 1:
            print("\n--- Scenario 2: 'pay $200 to unlock' scam (expect human gate) ---",
                  flush=True)
            await say(ctx, PAY_SCAM)
        elif step["n"] == 2:
            print("\n--- The family decides, in chat ---", flush=True)
            await say(ctx, "deny")
        else:
            print("\n" + "=" * 70, flush=True)
            print("END-TO-END COMPLETE — 4 agents collaborated over the Fetch message bus.",
                  flush=True)
            print("=" * 70, flush=True)
            os._exit(0)

    @user_chat.on_message(ChatAcknowledgement)
    async def on_ack(ctx: Context, sender: str, msg: ChatAcknowledgement) -> None:
        pass

    user.include(user_chat)
    bureau.add(user)
