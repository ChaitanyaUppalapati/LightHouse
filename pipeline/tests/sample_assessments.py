"""Built-in sample ThreatAssessments for testing the Guardian (C3).

These stand in for what the Watcher (C1) produces, so the Guardian can be exercised
without running the full agent chain. They cover the two demo scenarios plus a
low-confidence case:
  - a clear phishing email   -> expect quarantine_email -> autonomous
  - a "pay to unlock" demand -> expect a high-stakes action -> human_gate
  - a low-confidence hunch    -> expect watch_only (gate downgrades on confidence)
"""

import uuid

from lighthouse_common.schemas import ThreatAssessment


def _a(category, severity, confidence, rationale, evidence) -> ThreatAssessment:
    return ThreatAssessment(
        assessment_id="asmt_" + uuid.uuid4().hex[:12],
        signal_id="sig_" + uuid.uuid4().hex[:12],
        category=category,
        severity=severity,
        confidence=confidence,
        rationale=rationale,
        evidence=evidence,
    )


def sample_assessments():
    """Return (label, ThreatAssessment) pairs."""
    return [
        (
            "clear phishing email",
            _a(
                "scam_phishing",
                "high",
                0.98,
                "A phishing email impersonating a delivery service with a fake "
                "tracking link, trying to harvest the person's details.",
                [
                    "sender domain does not match the real courier",
                    "fake tracking link to a lookalike site",
                    "urgent 'package held' pressure",
                ],
            ),
        ),
        (
            "pay-to-unlock demand",
            _a(
                "scam_phishing",
                "high",
                0.97,
                "A scam claims the person's bank account is locked and demands a "
                "$200 payment to restore access — a direct demand to move money.",
                [
                    "demands a $200 payment to 'unlock' the account",
                    "lookalike bank domain",
                    "threat of permanent closure to force quick payment",
                ],
            ),
        ),
        (
            "low-confidence hunch",
            _a(
                "account_risk",
                "low",
                0.35,
                "A password-reset notice that might be routine or might be an "
                "account-takeover attempt — not enough signal to be sure.",
                ["password reset from an unrecognized device"],
            ),
        ),
    ]
