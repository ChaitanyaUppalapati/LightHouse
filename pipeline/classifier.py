"""The deterministic safety gate (task C2) — the keystone of the whole design.

route_action() decides whether a proposed action runs on its own, needs a human,
or is just watched. There is **NO AI here** — it is a pure lookup against the
frozen action registry (architecture reference §5). The route must be:

  - reproducible: same proposal + assessment -> same route, every time
  - auditable:    every route traces to exactly one rule (the `reason` field)
  - fail-safe:    an unknown action always goes to a human

The agent's confidence can only DOWNGRADE to watch_only — it can never upgrade an
irreversible / high-stakes action to autonomous. Reversibility picks act-alone vs
ask-a-human; confidence picks act vs just-watch.
"""

import os

import yaml

from lighthouse_common.schemas import ActionProposal, RoutingDecision, ThreatAssessment

# Below this confidence the system is too unsure to act OR to ask — it only watches.
CONFIDENCE_FLOOR = 0.5

# lighthouse_common/action_registry.yaml lives at the repo root (one level up from pipeline/).
_REGISTRY_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "lighthouse_common",
    "action_registry.yaml",
)


def _load_registry() -> dict:
    """Load the frozen action registry. Returns the `actions` mapping."""
    with open(_REGISTRY_PATH, "r") as f:
        return yaml.safe_load(f)["actions"]


def route_action(
    proposal: ActionProposal, assessment: ThreatAssessment
) -> RoutingDecision:
    """Route a proposed action to autonomous / human_gate / watch_only.

    Rule order (from the C2 spec) — the first match wins, and `reason` records
    which rule fired so every decision is auditable:

      1. action_type not in the registry        -> human_gate   (fail-safe)
      2. confidence < CONFIDENCE_FLOOR           -> watch_only   (too unsure)
      3. reversible AND stakes == "low"          -> autonomous   (safe to act)
      4. otherwise (irreversible or high-stakes) -> human_gate   (a human decides)
    """
    registry = _load_registry()
    entry = registry.get(proposal.action_type)

    if entry is None:
        route, reason = "human_gate", "unknown_action"
    elif assessment.confidence < CONFIDENCE_FLOOR:
        route, reason = "watch_only", "low_confidence"
    elif entry["reversible"] and entry["stakes"] == "low":
        route, reason = "autonomous", "reversible+low_stakes"
    else:
        route, reason = "human_gate", "irreversible_or_high_stakes"

    return RoutingDecision(proposal_id=proposal.proposal_id, route=route, reason=reason)
