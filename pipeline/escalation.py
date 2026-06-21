"""The Escalation agent (task C4) — owns the family relationship.

The Escalation agent is a Fetch.ai uAgent. It receives an ActionProposal that the
deterministic gate routed to human_gate, uses Claude to write a short plain
6th-grade message explaining what was found and what it wants to do, POSTs it to
the approval bridge (Keya's K4: {DATA_URL}/approvals), then polls
{DATA_URL}/approvals/{id} every 2s until the family approves or denies.
  - approved -> send the proposal to the executor (placeholder until C5)
  - denied   -> log and stop; nothing happens

This is the human-in-the-loop that makes the system "safe enough to ask."

Demo against the live bridge:  python -m pipeline.escalation demo
"""

import json
import os
import sys
import time
import urllib.request

import anthropic
from dotenv import load_dotenv

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_HERE)
for _p in (_HERE, _REPO_ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from uagents import Agent, Context  # noqa: E402

from lighthouse_common.schemas import ActionProposal  # noqa: E402
from pipeline.arize_tracing import init_tracing  # noqa: E402

load_dotenv()
init_tracing()  # ship Claude calls to Arize as spans (no-op without keys)

MODEL = "claude-sonnet-4-6"
DATA_URL = os.getenv("DATA_URL", os.getenv("VITE_DATA_URL", "http://localhost:8001"))
EXECUTOR_ADDRESS = os.getenv("EXECUTOR_ADDRESS", "agent1q_executor_placeholder")

POLL_SECONDS = 2
DECISION_TIMEOUT = 120  # stop waiting after this long

_client = anthropic.Anthropic()

_SYSTEM_PROMPT = """You write a single short message to a busy family member (the \
guardian of an older adult Lighthouse protects). Lighthouse wants to do something that \
needs their OK. Explain, in warm plain English at about a 6th-grade reading level:
what was found, and what Lighthouse wants to do about it. Keep it to 2-3 short
sentences and end with one clear yes/no question. No jargon, no greeting, no sign-off."""


def compose_message(proposal: ActionProposal) -> str:
    """Use Claude to turn an ActionProposal into a plain message for the family."""
    response = _client.messages.create(
        model=MODEL,
        max_tokens=256,
        temperature=0,
        system=_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Proposed action: {proposal.action_type}\n"
                    f"Why: {proposal.rationale}\n"
                    f"What it would do: {proposal.expected_effect}\n\n"
                    "Write the message asking the family to approve or deny."
                ),
            }
        ],
    )
    return next(b.text for b in response.content if b.type == "text").strip()


def _post_json(url: str, body: dict) -> dict:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=5) as resp:
        return json.loads(resp.read().decode("utf-8"))


def request_approval(proposal: ActionProposal, message: str) -> str:
    """POST the proposal + message to the bridge; return the approval_id."""
    row = _post_json(
        f"{DATA_URL.rstrip('/')}/approvals",
        {
            "proposal": {
                "proposal_id": proposal.proposal_id,
                "assessment_id": proposal.assessment_id,
                "action_type": proposal.action_type,
                "target": proposal.target,
            },
            "message": message,
            "detail": proposal.rationale,
        },
    )
    return row["approval_id"]


def wait_for_decision(approval_id: str, timeout: int = DECISION_TIMEOUT) -> str:
    """Poll the bridge every POLL_SECONDS until approved/denied. Returns the status
    ('approved'/'denied'), or 'pending' if it times out."""
    deadline = time.monotonic() + timeout
    url = f"{DATA_URL.rstrip('/')}/approvals/{approval_id}"
    while time.monotonic() < deadline:
        status = _get_json(url)["status"]
        if status in ("approved", "denied"):
            return status
        time.sleep(POLL_SECONDS)
    return "pending"


def escalate_sync(proposal: ActionProposal, log=print) -> str:
    """Full human-gate loop: compose -> post -> wait. Returns the decision.

    Shared by the uAgent handler and the demo runner.
    """
    message = compose_message(proposal)
    log(f"message to family: {message}")
    approval_id = request_approval(proposal, message)
    log(f"posted approval {approval_id}; waiting for the family to decide...")
    decision = wait_for_decision(approval_id)
    log(f"decision: {decision}")
    return decision


# --- The uAgent ---------------------------------------------------------------

escalation = Agent(
    name="escalation",
    seed=os.getenv("ESCALATION_SEED", "lighthouse-escalation-seed"),
    port=8103,
    endpoint=["http://127.0.0.1:8103/submit"],
)


@escalation.on_message(model=ActionProposal)
async def handle_proposal(ctx: Context, sender: str, msg: ActionProposal) -> None:
    """Ask the family about a gated proposal; on approval, forward to the executor."""
    import asyncio

    decision = await asyncio.to_thread(escalate_sync, msg, ctx.logger.info)
    if decision == "approved":
        await ctx.send(EXECUTOR_ADDRESS, msg)
    else:
        ctx.logger.info(f"proposal {msg.proposal_id} {decision} — nothing happens")


# --- Demo runner --------------------------------------------------------------


def run_demo() -> None:
    """C4 done-when: a human_gate proposal produces a message and waits for a
    decision. Builds a sample high-stakes proposal and runs the real loop against
    Keya's live /approvals. (Approve/deny it from the dashboard, or via
    POST /approvals/{id}/decide, to see this return.)"""
    import uuid

    proposal = ActionProposal(
        proposal_id="prop_" + uuid.uuid4().hex[:12],
        assessment_id="asmt_demo",
        action_type="pay_bill",
        target={"signal_id": "sig_demo"},
        rationale=(
            "A scam claims Margaret's bank account is locked and demands a $200 "
            "payment to restore access."
        ),
        expected_effect="Pay $200 to the sender to 'unlock' the account.",
    )
    print(f"Escalating a human_gate proposal to {DATA_URL}/approvals ...")
    decision = escalate_sync(proposal)
    print(f"\nFinal: {decision}")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "demo"
    if mode == "demo":
        run_demo()
    elif mode == "agent":
        escalation.run()
    else:
        print("usage: python -m pipeline.escalation [demo|agent]")
        sys.exit(1)
