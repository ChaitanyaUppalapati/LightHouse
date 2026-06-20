# FROZEN — do not edit, ask the team first.
#
# Lighthouse shared state model. These five objects flow through the whole system
# (architecture reference §2). Every component is built against them, so any change
# here breaks all three tracks at once.
#
# Each class subclasses uagents.Model so the objects can be sent between Fetch.ai
# uAgents. uagents.Model is itself a Pydantic BaseModel, so these are also ordinary
# Pydantic models for FastAPI / validation use.

from datetime import datetime
from typing import Literal, Optional

from uagents import Model


class Signal(Model):
    """A raw thing observed in the world. Read-only. Never trusted."""

    signal_id: str
    person_id: str
    source: Literal["email", "transaction", "account_event", "voice"]
    payload: dict  # the email, the charge, the lockout notice, the utterance
    observed_at: datetime


class ThreatAssessment(Model):
    """The Watcher's judgment about a Signal. LLM-produced."""

    assessment_id: str
    signal_id: str
    category: Literal[
        "scam_phishing",
        "financial_anomaly",
        "missed_obligation",
        "account_risk",
        "benign",
    ]
    severity: Literal["none", "low", "moderate", "high"]
    confidence: float  # 0..1, the Watcher's certainty
    rationale: str  # why — human-readable, feeds the ledger and the eval
    evidence: list[str]  # the specific cues (sender mismatch, urgency language, etc.)


class ActionProposal(Model):
    """The Guardian's chosen response. action_type MUST exist in the action registry."""

    proposal_id: str
    assessment_id: str
    action_type: str  # must be a key in lighthouse_common/action_registry.yaml
    target: dict  # what it acts on (email id, card id, etc.)
    rationale: str
    expected_effect: str  # plain-language, shown to the guardian if gated


class RoutingDecision(Model):
    """The deterministic router's verdict. NOT agent-produced."""

    proposal_id: str
    route: Literal["autonomous", "human_gate", "watch_only"]
    reason: str  # which rule fired: "reversible+low_stakes" / "irreversible" / "low_confidence"


class ActionResult(Model):
    """What actually happened."""

    proposal_id: str
    status: Literal["executed", "approved_executed", "denied", "failed", "watching"]
    evidence: dict  # screenshot ref, confirmation, error
    undo_token: Optional[str] = None  # how to reverse it, if reversible
    completed_at: datetime
