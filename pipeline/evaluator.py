"""LLM-as-judge evaluator for the Watcher (task C6, part 2) — the Arize eval loop.

Runs the Watcher over the labeled eval set (pipeline/tests/eval_emails.py), then
uses Claude as an independent judge: given the email, the Watcher's verdict, and
the ground-truth label, was the Watcher right? Computes accuracy and prints the
mistakes. The before/after accuracy number — after improving the Watcher prompt —
is the Arize booth artifact.

Run:  python -m pipeline.evaluator
"""

import json
import os
import sys
import uuid
from datetime import datetime, timezone

import anthropic
from dotenv import load_dotenv

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_HERE)
for _p in (_HERE, _REPO_ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from lighthouse_common.demo_ids import MARGARET_PERSON_ID  # noqa: E402
from lighthouse_common.schemas import Signal, ThreatAssessment  # noqa: E402
from pipeline.watcher import classify_signal  # noqa: E402

load_dotenv()

JUDGE_MODEL = "claude-sonnet-4-6"
_client = anthropic.Anthropic()

_JUDGE_SYSTEM = """You are an impartial evaluator grading a security classifier (the \
"Watcher") that flags scams for an older adult. You are given an email, the Watcher's \
verdict, and the GROUND-TRUTH label for that email.

The Watcher's category maps to the binary label like this:
  scam_phishing  -> "scam"
  benign         -> "legit"
  financial_anomaly / account_risk / missed_obligation -> judge by intent: if the
    Watcher is treating a genuinely dangerous item as a threat, that aligns with
    "scam"; if it is flagging an ordinary legitimate message, that is a miss.

Decide whether the Watcher's verdict is CORRECT relative to the ground-truth label.
Return correct=true/false and one short sentence explaining why (especially what cue
the Watcher missed or over-weighted if it was wrong)."""

_JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "correct": {"type": "boolean"},
        "reason": {"type": "string"},
    },
    "required": ["correct", "reason"],
    "additionalProperties": False,
}


def _email_to_signal(email: dict) -> Signal:
    return Signal(
        signal_id="eval_" + uuid.uuid4().hex[:10],
        person_id=MARGARET_PERSON_ID,
        source="email",
        payload=email,
        observed_at=datetime.now(timezone.utc),
    )


def judge_verdict(email: dict, assessment: ThreatAssessment, true_label: str):
    """Ask Claude whether the Watcher's verdict is correct. Returns (bool, reason)."""
    response = _client.messages.create(
        model=JUDGE_MODEL,
        max_tokens=512,
        temperature=0,
        system=_JUDGE_SYSTEM,
        messages=[
            {
                "role": "user",
                "content": (
                    f"EMAIL:\n{json.dumps(email, indent=2)}\n\n"
                    f"WATCHER VERDICT:\n"
                    f"  category:   {assessment.category}\n"
                    f"  severity:   {assessment.severity}\n"
                    f"  confidence: {assessment.confidence}\n"
                    f"  rationale:  {assessment.rationale}\n\n"
                    f"GROUND-TRUTH LABEL: {true_label}\n\n"
                    "Was the Watcher correct?"
                ),
            }
        ],
        output_config={"format": {"type": "json_schema", "schema": _JUDGE_SCHEMA}},
    )
    text = next(b.text for b in response.content if b.type == "text")
    verdict = json.loads(text)
    return bool(verdict["correct"]), verdict["reason"]


def run_eval(emails=None) -> dict:
    """Run the full eval loop. Prints per-item progress, accuracy, and mistakes.
    Returns a summary dict (accuracy, counts, mistakes)."""
    if emails is None:
        from pipeline.tests.eval_emails import EVAL_EMAILS as emails

    results = []
    print(f"Evaluating the Watcher over {len(emails)} labeled emails...\n")
    for item in emails:
        assessment = classify_signal(_email_to_signal(item["email"]))
        correct, reason = judge_verdict(item["email"], assessment, item["true_label"])
        results.append({
            "id": item["id"],
            "true_label": item["true_label"],
            "category": assessment.category,
            "severity": assessment.severity,
            "confidence": assessment.confidence,
            "correct": correct,
            "reason": reason,
        })
        mark = "OK " if correct else "XX "
        print(f"  {mark}{item['id']:4} truth={item['true_label']:5} "
              f"watcher={assessment.category:16} conf={assessment.confidence:.2f}")

    n = len(results)
    n_correct = sum(1 for r in results if r["correct"])
    accuracy = n_correct / n if n else 0.0

    # Confusion against the binary truth (scam_phishing => scam, else legit).
    def predicted(r):
        return "scam" if r["category"] == "scam_phishing" else "legit"

    false_pos = [r for r in results if r["true_label"] == "legit" and predicted(r) == "scam"]
    false_neg = [r for r in results if r["true_label"] == "scam" and predicted(r) == "legit"]
    mistakes = [r for r in results if not r["correct"]]

    print(f"\n=== Accuracy: {accuracy:.1%} ({n_correct}/{n}) ===")
    print(f"  false positives (legit flagged as scam): {len(false_pos)}")
    print(f"  false negatives (scam let through):       {len(false_neg)}")

    if mistakes:
        print("\nMistakes:")
        for r in mistakes:
            print(f"  - {r['id']} (truth {r['true_label']}, watcher {r['category']}): {r['reason']}")
    else:
        print("\nNo mistakes — the Watcher matched the labels on every email.")

    return {
        "accuracy": accuracy,
        "n": n,
        "correct": n_correct,
        "false_positives": [r["id"] for r in false_pos],
        "false_negatives": [r["id"] for r in false_neg],
        "mistakes": mistakes,
        "results": results,
    }


if __name__ == "__main__":
    run_eval()
