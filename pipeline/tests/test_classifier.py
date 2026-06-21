"""Tests for the deterministic safety gate (C2).

The four cases from the C2 spec, one per routing rule:
  reversible+low+high-confidence -> autonomous
  pay_bill (irreversible, high)  -> human_gate
  low confidence                 -> watch_only
  unknown action                 -> human_gate
"""

import os
import sys

import pytest

# Make the repo root importable so `lighthouse_common` and `pipeline` resolve
# no matter where pytest is launched from.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from lighthouse_common.schemas import ActionProposal, ThreatAssessment  # noqa: E402
from pipeline.classifier import route_action  # noqa: E402


def _assessment(confidence: float) -> ThreatAssessment:
    return ThreatAssessment(
        assessment_id="a1",
        signal_id="s1",
        category="scam_phishing",
        severity="high",
        confidence=confidence,
        rationale="test",
        evidence=["test cue"],
    )


def _proposal(action_type: str) -> ActionProposal:
    return ActionProposal(
        proposal_id="p1",
        assessment_id="a1",
        action_type=action_type,
        target={"email_id": "e1"},
        rationale="test",
        expected_effect="test",
    )


def test_reversible_low_high_confidence_is_autonomous():
    decision = route_action(_proposal("quarantine_email"), _assessment(0.95))
    assert decision.route == "autonomous"
    assert decision.reason == "reversible+low_stakes"


def test_pay_bill_is_human_gate():
    # pay_bill is irreversible + high stakes -> a human must decide.
    decision = route_action(_proposal("pay_bill"), _assessment(0.95))
    assert decision.route == "human_gate"
    assert decision.reason == "irreversible_or_high_stakes"


def test_low_confidence_is_watch_only():
    # Even a reversible+low action is only watched when we're not sure enough.
    decision = route_action(_proposal("quarantine_email"), _assessment(0.30))
    assert decision.route == "watch_only"
    assert decision.reason == "low_confidence"


def test_unknown_action_is_human_gate():
    # Fail-safe: anything not in the registry goes to a human.
    decision = route_action(_proposal("launch_missiles"), _assessment(0.95))
    assert decision.route == "human_gate"
    assert decision.reason == "unknown_action"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
