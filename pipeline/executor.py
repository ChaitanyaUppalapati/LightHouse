"""The computer-use executor (task C5) — acts on real web interfaces.

Takes an APPROVED or autonomous ActionProposal and performs it on a real browser
using Browserbase + Stagehand (architecture §7). Two actions:
  - quarantine_email: open MOCK_INBOX_URL, click the flagged email, click
    "Move to Quarantine" (reversible -> returns an undo_token).
  - pay_bill: open MOCK_BANK_URL and make a payment. HIGH-STAKES and irreversible —
    only ever reached AFTER human approval (the gate + Escalation guarantee this).

Returns an ActionResult with a screenshot reference as evidence and an undo_token
where the action is reversible.

DEMO_MODE: if DEMO_MODE=1, skip the live Browserbase call and return a realistic
fake ActionResult instantly. The live computer-use path is the highest-risk part of
the system, so the demo runs on DEMO_MODE and the real path is validated separately
(Browserbase booth). Both paths return the same ActionResult shape.

Run the demo path:   DEMO_MODE=1 python -m pipeline.executor
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

from lighthouse_common.schemas import ActionProposal, ActionResult  # noqa: E402
from pipeline.phoenix_tracing import init_tracing, span  # noqa: E402

load_dotenv()
init_tracing()

DEMO_MODE = os.getenv("DEMO_MODE", "0") == "1"
MOCK_INBOX_URL = os.getenv("MOCK_INBOX_URL", "https://example.com/inbox")
MOCK_BANK_URL = os.getenv("MOCK_BANK_URL", "https://example.com/bank")
BROWSERBASE_API_KEY = os.getenv("BROWSERBASE_API_KEY", "")
BROWSERBASE_PROJECT_ID = os.getenv("BROWSERBASE_PROJECT_ID", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
EXECUTOR_MODEL = "anthropic/claude-sonnet-4-6"

# Which registry actions the executor can physically carry out today.
_SUPPORTED = {"quarantine_email", "pay_bill"}


def _now():
    return datetime.now(timezone.utc)


def _demo_result(proposal: ActionProposal) -> ActionResult:
    """A realistic fake result so the demo survives bad wifi (DEMO_MODE=1)."""
    reversible = proposal.action_type in {"quarantine_email"}
    return ActionResult(
        proposal_id=proposal.proposal_id,
        status="executed",
        evidence={
            "mode": "demo",
            "action_type": proposal.action_type,
            "screenshot": f"demo://screenshots/{proposal.action_type}-{proposal.proposal_id}.png",
            "note": f"DEMO_MODE: simulated {proposal.action_type} on the mock interface.",
            "session_replay_url": "demo://browserbase/session/replay",
        },
        undo_token=("undo_" + uuid.uuid4().hex[:12]) if reversible else None,
        completed_at=_now(),
    )


def _run_browserbase(url: str, instructions: list[str]) -> dict:
    """Drive a real Browserbase cloud browser with Stagehand: open `url`, then perform
    each natural-language instruction. Returns an evidence dict with the Browserbase
    session id + a replay URL (the recording is the evidence — there is no screenshot
    op in the Stagehand SDK).

    Verified against the live Stagehand 3.x API (sync client). NOTE: Browserbase runs
    the browser in the cloud, so `url` must be PUBLICLY reachable — point MOCK_INBOX_URL
    / MOCK_BANK_URL at a deployed/tunnelled page, not localhost. DEMO_MODE=1 is the demo
    path and skips this entirely.
    """
    from stagehand import Stagehand  # imported lazily so DEMO_MODE has no dependency

    client = Stagehand(
        browserbase_api_key=BROWSERBASE_API_KEY,
        browserbase_project_id=BROWSERBASE_PROJECT_ID,
        model_api_key=ANTHROPIC_API_KEY,
    )
    session = client.sessions.start(model_name=EXECUTOR_MODEL)
    sid = session.data.session_id
    try:
        client.sessions.navigate(sid, url=url)
        for instruction in instructions:
            client.sessions.act(sid, input=instruction)  # input accepts a plain string
        return {
            "mode": "browserbase",
            "session_id": sid,
            "replay_url": f"https://www.browserbase.com/sessions/{sid}",
        }
    finally:
        client.sessions.end(sid)


def _quarantine_email(proposal: ActionProposal) -> ActionResult:
    evidence = _run_browserbase(
        MOCK_INBOX_URL,
        [
            "click the email flagged as suspicious",
            "click the 'Move to Quarantine' button",
        ],
    )
    return ActionResult(
        proposal_id=proposal.proposal_id,
        status="executed",
        evidence=evidence,
        undo_token="undo_" + uuid.uuid4().hex[:12],  # quarantine is reversible
        completed_at=_now(),
    )


def _pay_bill(proposal: ActionProposal) -> ActionResult:
    # Reached only after human approval. Irreversible -> no undo_token.
    evidence = _run_browserbase(
        MOCK_BANK_URL,
        [
            "click the 'Make a payment' button",
            "fill in the payment form with the approved amount and recipient",
            "click 'Send payment'",
        ],
    )
    return ActionResult(
        proposal_id=proposal.proposal_id,
        status="approved_executed",
        evidence=evidence,
        undo_token=None,
        completed_at=_now(),
    )


def execute(proposal: ActionProposal) -> ActionResult:
    """Perform an approved/autonomous action and return an ActionResult."""
    with span("executor.execute", action_type=proposal.action_type, demo_mode=DEMO_MODE):
        if proposal.action_type not in _SUPPORTED:
            return ActionResult(
                proposal_id=proposal.proposal_id,
                status="failed",
                evidence={"error": f"executor cannot perform '{proposal.action_type}' yet"},
                undo_token=None,
                completed_at=_now(),
            )

        if DEMO_MODE:
            return _demo_result(proposal)

        try:
            if proposal.action_type == "quarantine_email":
                return _quarantine_email(proposal)
            return _pay_bill(proposal)
        except Exception as e:  # computer-use fails often — capture, don't crash
            return ActionResult(
                proposal_id=proposal.proposal_id,
                status="failed",
                evidence={"error": str(e), "action_type": proposal.action_type},
                undo_token=None,
                completed_at=_now(),
            )


if __name__ == "__main__":
    demo_proposal = ActionProposal(
        proposal_id="prop_" + uuid.uuid4().hex[:12],
        assessment_id="asmt_demo",
        action_type="quarantine_email",
        target={"signal_id": "sig_demo"},
        rationale="Phishing email impersonating a bank.",
        expected_effect="Move the scam email to the Quarantine folder.",
    )
    result = execute(demo_proposal)
    print(f"status:     {result.status}")
    print(f"undo_token: {result.undo_token}")
    print(f"evidence:   {result.evidence}")
