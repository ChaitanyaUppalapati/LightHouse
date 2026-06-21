"""The Guardian agent (task C3) — proposes a response, then routes it through the gate.

The Guardian is a Fetch.ai uAgent. It receives a `ThreatAssessment` and decides
*what to do* about it — but it may ONLY pick an action_type from the frozen action
registry (lighthouse_common/action_registry.yaml); it can never invent an action.
That finite vocabulary is a core safety property (architecture §4.2).

The Guardian only *proposes*. It does not execute and it does not decide the route
— it hands the ActionProposal to the deterministic gate (route_action, C2):
  - autonomous -> send to the executor (placeholder until C5)
  - human_gate -> send to the Escalation agent (placeholder until C4 is wired)
  - watch_only -> just log

Run it over the built-in sample assessments:  python -m pipeline.guardian samples
"""

import json
import os
import sys
import uuid

import anthropic
from dotenv import load_dotenv

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_HERE)
for _p in (_HERE, _REPO_ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from uagents import Agent, Context  # noqa: E402

from lighthouse_common.schemas import (  # noqa: E402
    ActionProposal,
    ThreatAssessment,
)
from pipeline.classifier import _load_registry, route_action  # noqa: E402
from pipeline.arize_tracing import init_tracing  # noqa: E402

load_dotenv()
init_tracing()  # ship Claude calls to Arize as spans (no-op without keys)

MODEL = "claude-sonnet-4-6"

# Downstream agents/executor. Wired to the real addresses later; until then these
# are placeholders and the sends simply don't deliver.
EXECUTOR_ADDRESS = os.getenv("EXECUTOR_ADDRESS", "agent1q_executor_placeholder")
ESCALATION_ADDRESS = os.getenv("ESCALATION_ADDRESS", "agent1q_escalation_placeholder")

_client = anthropic.Anthropic()

# The Guardian may only choose from these — the registry's keys, nothing else.
_REGISTRY = _load_registry()
_ACTION_TYPES = list(_REGISTRY.keys())


def _registry_menu() -> str:
    """A readable menu of the allowed actions for the prompt."""
    lines = []
    for name, meta in _REGISTRY.items():
        rev = "reversible" if meta["reversible"] else "irreversible"
        lines.append(f"- {name}: {meta.get('description', '')} ({rev}, {meta['stakes']} stakes)")
    return "\n".join(lines)


_SYSTEM_PROMPT = f"""You are Lighthouse's Guardian. You receive a threat assessment about \
something that happened to an older adult you protect, and you choose the single best \
PROTECTIVE action to take in response.

You may ONLY choose an action from this fixed list — never invent one:
{_registry_menu()}

PRIORITY RULE — money first: if the threat involves any demand or pressure to PAY
MONEY (a fee to unlock/restore an account, a redelivery or verification fee, paying
to claim a prize, an invoice), propose pay_bill. That is the decision the situation
is pushing the person toward, and it is the one that must reach a human. Proposing
pay_bill does NOT mean money moves — the safety gate requires explicit family
approval for it, which is exactly the protection we want. Do NOT pick quarantine_email
when money is being demanded; the payment decision is what has to be gated to family.

Otherwise, pick the one action that best protects the person:
- For a scam/phishing email with no payment demand, quarantine_email moves it out of
  harm's way (safe, reversible).
- For a repeat bad sender, block_sender.
- For a suspicious charge that already happened, flag_transaction; to stop further
  loss on a compromised card, freeze_card.
- To secure a compromised account, reset_credentials.
- For something merely worth noting, label_and_notify.

Fill in a short rationale and a plain-language expected_effect describing what the
person/family would see."""

_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "action_type": {"type": "string", "enum": _ACTION_TYPES},
        "rationale": {"type": "string"},
        "expected_effect": {"type": "string"},
    },
    "required": ["action_type", "rationale", "expected_effect"],
    "additionalProperties": False,
}


def propose_action(assessment: ThreatAssessment) -> ActionProposal:
    """Use Claude to pick ONE registry action and build an ActionProposal (C3 core)."""
    response = _client.messages.create(
        model=MODEL,
        max_tokens=1024,
        temperature=0,
        system=_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    "Threat assessment:\n"
                    f"  category:   {assessment.category}\n"
                    f"  severity:   {assessment.severity}\n"
                    f"  confidence: {assessment.confidence}\n"
                    f"  rationale:  {assessment.rationale}\n"
                    f"  evidence:   {assessment.evidence}\n\n"
                    "Choose the single best protective action."
                ),
            }
        ],
        output_config={"format": {"type": "json_schema", "schema": _OUTPUT_SCHEMA}},
    )

    text = next(b.text for b in response.content if b.type == "text")
    choice = json.loads(text)

    # Defense in depth: the enum already constrains this, but never trust a model
    # to stay inside the registry — the gate would fail-safe to human_gate anyway.
    if choice["action_type"] not in _REGISTRY:
        choice["action_type"] = "label_and_notify"

    return ActionProposal(
        proposal_id="prop_" + uuid.uuid4().hex[:12],
        assessment_id=assessment.assessment_id,
        action_type=choice["action_type"],
        target={"signal_id": assessment.signal_id},
        rationale=choice["rationale"],
        expected_effect=choice["expected_effect"],
    )


def handle_assessment_sync(assessment: ThreatAssessment, log=print):
    """Propose an action, route it through the gate, and return (proposal, decision).

    Pure logic shared by the uAgent handler and the sample runner. Dispatch (who
    the proposal is sent to) is decided here; the actual send happens in the agent
    handler. `log` lets the runner print and the agent use ctx.logger.
    """
    proposal = propose_action(assessment)
    decision = route_action(proposal, assessment)
    log(
        f"proposed {proposal.action_type} -> route={decision.route} "
        f"({decision.reason})"
    )
    return proposal, decision


# --- The uAgent ---------------------------------------------------------------

guardian = Agent(
    name="guardian",
    seed=os.getenv("GUARDIAN_SEED", "lighthouse-guardian-seed"),
    port=8102,
    endpoint=["http://127.0.0.1:8102/submit"],
)


@guardian.on_message(model=ThreatAssessment)
async def handle_assessment(ctx: Context, sender: str, msg: ThreatAssessment) -> None:
    """Propose an action for an assessment and route it to the right place."""
    proposal, decision = handle_assessment_sync(msg, log=ctx.logger.info)
    if decision.route == "autonomous":
        await ctx.send(EXECUTOR_ADDRESS, proposal)
    elif decision.route == "human_gate":
        await ctx.send(ESCALATION_ADDRESS, proposal)
    else:  # watch_only
        ctx.logger.info(f"watch_only: logging {proposal.action_type}, taking no action")


# --- Runner -------------------------------------------------------------------


def run_over_samples() -> None:
    """C3 done-when: a scam -> quarantine_email (autonomous); a 'pay to unlock'
    -> a high-stakes proposal (human_gate)."""
    from pipeline.tests.sample_assessments import sample_assessments

    print("Guardian over sample assessments:")
    for label, assessment in sample_assessments():
        print(f"\n[{label}] {assessment.category}/{assessment.severity} "
              f"(conf {assessment.confidence:.2f})")
        proposal, decision = handle_assessment_sync(assessment)
        print(f"  action:   {proposal.action_type}")
        print(f"  route:    {decision.route}  ({decision.reason})")
        print(f"  effect:   {proposal.expected_effect}")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "samples"
    if mode == "samples":
        run_over_samples()
    elif mode == "agent":
        guardian.run()
    else:
        print("usage: python -m pipeline.guardian [samples|agent]")
        sys.exit(1)
