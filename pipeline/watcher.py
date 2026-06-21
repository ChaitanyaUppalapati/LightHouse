"""The Watcher agent (task C1) — detects and classifies threats.

The Watcher is a Fetch.ai uAgent. It receives a `Signal` (a raw observed thing,
e.g. an email) and produces a `ThreatAssessment` using Claude. It has NO power to
act — it only raises concerns. Its rationale + evidence are what the Arize
evaluator (C6) grades and what the ledger records, so they matter.

Run it over the built-in samples:      python -m pipeline.watcher samples
Run it over Keya's live feed (K2):     python -m pipeline.watcher feed

The shared classify_signal() does the Claude call; the uAgent message handler and
both runners all go through it, so the feed and the samples classify identically.
"""

import json
import os
import sys
import uuid
import urllib.request
from datetime import datetime, timezone

import anthropic
from dotenv import load_dotenv

# Make the repo root importable so `lighthouse_common` resolves regardless of how
# this is launched (python -m pipeline.watcher, or python pipeline/watcher.py).
_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_HERE)
for _p in (_HERE, _REPO_ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from uagents import Agent, Context  # noqa: E402

from lighthouse_common.schemas import Signal, ThreatAssessment  # noqa: E402
from pipeline.phoenix_tracing import init_tracing, span  # noqa: E402

load_dotenv()
init_tracing()  # ship Claude calls to Arize as spans (no-op without keys)

# Deterministic classifier: Sonnet 4.6 at temperature 0 so the same email always
# gets the same verdict — important for the Arize eval loop and reproducibility.
MODEL = "claude-sonnet-4-6"

# Where to send the ThreatAssessment. Wired to the real Guardian (C3) later; until
# then this is a placeholder and the send simply doesn't deliver.
GUARDIAN_ADDRESS = os.getenv("GUARDIAN_ADDRESS", "agent1q_guardian_placeholder")

# Keya's mock email feed (K2). Used by the `feed` runner at Checkpoint 1.
DATA_URL = os.getenv("DATA_URL", os.getenv("VITE_DATA_URL", "http://localhost:8001"))

_client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment

_SYSTEM_PROMPT = """You are Lighthouse's Watcher: a security analyst protecting an \
older adult whose memory is declining from scams and digital harm. You are given one \
item the person received (usually an email). Judge ONLY this item — do not assume \
anything not present in it.

Classify it into:
- category: scam_phishing (fraud, phishing, fake alerts, prize/refund bait),
  financial_anomaly (unusual charge or money movement), missed_obligation (an unpaid
  bill or deadline), account_risk (lockout, password reset, security event), or
  benign (legitimate, ordinary message).
- severity: none, low, moderate, or high (how much potential harm).
- confidence: 0.0 to 1.0 — how sure you are of the category.
- rationale: one or two plain sentences a worried family member would understand.
- evidence: the specific concrete cues you used (e.g. "sender domain does not match
  the real bank", "urgent payment demand", "asks for password and card details").

Scam cues include: mismatched/look-alike sender domains, urgency and threats, demands
for payment or credentials, too-good-to-be-true prizes or refunds. Ordinary mail
(family notes, pharmacy pickups, appointment reminders) is benign with severity none.

IMPORTANT — do not over-flag legitimate security and transactional notices. Banks,
Apple/Google/Microsoft, and other real services routinely send sign-in alerts,
"card temporarily locked", password-reset codes, and fraud-confirmation notices.
Treat such a message as benign (NOT account_risk, NOT scam_phishing) when ALL of
these hold: the sender domain is the provider's real domain (e.g. chase.com,
accounts.google.com, okta.com — not a look-alike like secure-bank-help.com), it does
NOT demand a password/PIN/card number or a payment, it has no suspicious or
look-alike link, and it tells the person they can verify through the app or a number
on their card (or simply ignore it). Only use account_risk when there is a genuine,
actionable compromise — and use scam_phishing the moment a look-alike domain,
credential/payment demand, or suspicious link is present, however polished the
wording is."""

# Structured-output schema mirroring the ThreatAssessment classification fields.
_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "category": {
            "type": "string",
            "enum": [
                "scam_phishing",
                "financial_anomaly",
                "missed_obligation",
                "account_risk",
                "benign",
            ],
        },
        "severity": {"type": "string", "enum": ["none", "low", "moderate", "high"]},
        "confidence": {"type": "number"},
        "rationale": {"type": "string"},
        "evidence": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["category", "severity", "confidence", "rationale", "evidence"],
    "additionalProperties": False,
}


def classify_signal(signal: Signal) -> ThreatAssessment:
    """Run Claude over a Signal and return a ThreatAssessment (the C1 core)."""
    with span(
        "watcher.classify_signal",
        **{
            "openinference.span.kind": "CHAIN",
            "input.value": json.dumps(signal.payload),
            "signal.source": signal.source,
        },
    ) as s:
        response = _client.messages.create(
            model=MODEL,
            max_tokens=1024,
            temperature=0,
            system=_SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Classify this item the person received:\n\n"
                        + json.dumps(signal.payload, indent=2)
                    ),
                }
            ],
            output_config={"format": {"type": "json_schema", "schema": _OUTPUT_SCHEMA}},
        )

        # output_config.format guarantees the first text block is schema-valid JSON.
        text = next(b.text for b in response.content if b.type == "text")
        verdict = json.loads(text)

        assessment = ThreatAssessment(
            assessment_id=str(uuid.uuid4()),
            signal_id=signal.signal_id,
            category=verdict["category"],
            severity=verdict["severity"],
            confidence=float(verdict["confidence"]),
            rationale=verdict["rationale"],
            evidence=verdict["evidence"],
        )
        if s is not None:
            s.set_attribute(
                "output.value",
                f"{assessment.category}/{assessment.severity} "
                f"(confidence {assessment.confidence})",
            )
        return assessment


def _print_assessment(label: str, signal: Signal, assessment: ThreatAssessment) -> None:
    subject = signal.payload.get("subject", "(no subject)")
    print(f"\n[{label}] {subject}")
    print(f"  -> {assessment.category} / {assessment.severity} "
          f"(confidence {assessment.confidence:.2f})")
    print(f"  rationale: {assessment.rationale}")
    print(f"  evidence:  {assessment.evidence}")


# --- The uAgent ---------------------------------------------------------------

watcher = Agent(
    name="watcher",
    seed=os.getenv("WATCHER_SEED", "lighthouse-watcher-seed"),
    port=8101,
    endpoint=["http://127.0.0.1:8101/submit"],
)


@watcher.on_message(model=Signal)
async def handle_signal(ctx: Context, sender: str, msg: Signal) -> None:
    """Classify an incoming Signal and forward the ThreatAssessment to the Guardian."""
    assessment = classify_signal(msg)
    ctx.logger.info(
        f"{assessment.category}/{assessment.severity} "
        f"(conf {assessment.confidence:.2f}) for signal {msg.signal_id}"
    )
    await ctx.send(GUARDIAN_ADDRESS, assessment)


# --- Runners (no agent messaging loop needed) ---------------------------------


def run_over_samples() -> None:
    """C1 done-when: classify the 5 built-in samples and print the verdicts."""
    from pipeline.tests.sample_signals import sample_signals

    print("Watcher over built-in samples (3 scam, 2 normal):")
    for label, signal in sample_signals():
        _print_assessment(label, signal, classify_signal(signal))


def _fetch_signal_from_feed() -> Signal:
    """Checkpoint 1: pull one Signal from Keya's K2 feed at /signals/next."""
    url = f"{DATA_URL.rstrip('/')}/signals/next"
    with urllib.request.urlopen(url, timeout=5) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return Signal(**data)


def run_over_feed(count: int = 6) -> None:
    """Checkpoint 1: classify `count` signals pulled live from Keya's feed."""
    print(f"Watcher over Keya's feed at {DATA_URL}/signals/next:")
    for _ in range(count):
        signal = _fetch_signal_from_feed()
        _print_assessment("feed", signal, classify_signal(signal))


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "samples"
    if mode == "feed":
        run_over_feed()
    elif mode == "samples":
        run_over_samples()
    elif mode == "agent":
        watcher.run()  # start the uAgent and listen for Signals
    else:
        print("usage: python -m pipeline.watcher [samples|feed|agent]")
        sys.exit(1)
