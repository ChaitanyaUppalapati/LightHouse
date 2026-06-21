"""Interactive Lighthouse chat (local, multi-agent) — like ASI:One, from your keyboard.

Paste a suspicious email (or type a question); the Lighthouse agents collaborate
(coordinator -> watcher -> guardian -> executor) and reply. For a high-stakes action
it asks YOU to approve or deny — you type the decision. Same Chat Protocol ASI:One
uses, just driven interactively instead of by a scripted driver.

    AGENT_MAILBOX=0 DEMO_MODE=1 python -m pipeline.chat_cli      # instant executor
    AGENT_MAILBOX=0 DEMO_MODE=0 python -m pipeline.chat_cli      # real Browserbase (needs the tunnel)

Type your message, then a blank line to send. Type 'quit' to exit.
"""

import asyncio
import os
import sys
from datetime import datetime, timezone
from uuid import uuid4

os.environ.setdefault("AGENT_MAILBOX", "0")  # run the coordinator locally in a Bureau

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_HERE)
for _p in (_HERE, _REPO_ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from uagents import Agent, Context, Protocol  # noqa: E402
from uagents_core.contrib.protocols.chat import (  # noqa: E402
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
    chat_protocol_spec,
)

import pipeline.orchestration as orch  # noqa: E402  (builds the coordinator + sub-agents)

COORDINATOR = orch.COORDINATOR

_CYAN = "\033[1m\033[36m"
_YELLOW = "\033[1m\033[33m"
_RESET = "\033[0m"

user = Agent(name="you", seed="lighthouse-cli-user-seed", port=8115)
user_chat = Protocol(spec=chat_protocol_spec)


def _read_block() -> str | None:
    """Read a multi-line message from stdin, submitted by a blank line. None = quit."""
    print(f"\n{_CYAN}You{_RESET} (paste an email or type a reply, then a blank line to send):")
    lines: list[str] = []
    while True:
        try:
            line = input()
        except (EOFError, KeyboardInterrupt):
            return None
        stripped = line.strip()
        if stripped.lower() in ("quit", "exit", "q") and not lines:
            return None
        if stripped == "":
            if lines:
                break          # blank line after content -> send
            continue           # ignore leading blank lines
        lines.append(line)
    return "\n".join(lines)


async def _prompt_and_send(ctx: Context) -> None:
    text = await asyncio.to_thread(_read_block)
    if text is None:
        print("\nGoodbye.")
        os._exit(0)
    await ctx.send(COORDINATOR, ChatMessage(
        timestamp=datetime.now(timezone.utc), msg_id=uuid4(),
        content=[TextContent(type="text", text=text)]))


@user.on_event("startup")
async def _start(ctx: Context) -> None:
    print("=" * 66)
    print("  Lighthouse — interactive chat (multi-agent). Type 'quit' to exit.")
    print("  Try: a scam email, a 'pay $200 to unlock' email, or a normal note.")
    print("=" * 66)
    await _prompt_and_send(ctx)


@user_chat.on_message(ChatMessage)
async def _on_reply(ctx: Context, sender: str, msg: ChatMessage) -> None:
    await ctx.send(sender, ChatAcknowledgement(
        timestamp=datetime.now(timezone.utc), acknowledged_msg_id=msg.msg_id))
    reply = "".join(c.text for c in msg.content if isinstance(c, TextContent)).strip()
    print(f"\n{_YELLOW}Lighthouse{_RESET}:\n{reply}")
    await _prompt_and_send(ctx)


@user_chat.on_message(ChatAcknowledgement)
async def _on_ack(ctx: Context, sender: str, msg: ChatAcknowledgement) -> None:
    pass


user.include(user_chat)


if __name__ == "__main__":
    bureau = orch.build_bureau()
    bureau.add(user)
    bureau.run()
