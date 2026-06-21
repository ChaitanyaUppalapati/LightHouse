"""Phoenix evals for the Watcher (task C6) — traces + LLM-judge annotations in Phoenix.

This is the Phoenix "build an eval + close the loop" move. It:
  1. runs the Watcher over the labeled eval set with tracing on, so each item
     becomes a CHAIN span in your Phoenix project (input = the email, output = the
     Watcher's verdict);
  2. pulls those spans back from Phoenix;
  3. scores each with a Phoenix ClassificationEvaluator (Claude as judge) — correct
     vs incorrect, WITH explanations;
  4. logs the results back to Phoenix as span annotations, so every trace carries a
     pass/fail label and a written reason you can read in the UI.

The explanations on the failing spans are what you feed back to the coding agent to
fix the Watcher prompt (the before/after loop; see pipeline/tests/eval_emails_hard.py).

Run:  python -m pipeline.phoenix_eval         # uses the base + hard sets
Needs PHOENIX_API_KEY + PHOENIX_COLLECTOR_ENDPOINT in .env.
"""

import asyncio
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_HERE)
for _p in (_HERE, _REPO_ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from lighthouse_common.demo_ids import MARGARET_PERSON_ID  # noqa: E402
from lighthouse_common.schemas import Signal  # noqa: E402
import pipeline.phoenix_tracing as tracing  # noqa: E402
from pipeline.watcher import classify_signal  # noqa: E402

load_dotenv()

PROJECT_NAME = os.getenv("PHOENIX_PROJECT_NAME", "lighthouse")
JUDGE_MODEL = "claude-sonnet-4-6"

# openinference semantic-convention attribute keys.
_SPAN_KIND = "openinference.span.kind"
_INPUT_VALUE = "input.value"
_OUTPUT_VALUE = "output.value"
_EVAL_ID = "metadata.eval_id"

_SPAN_NAME = "watcher.evaluate"


def _signal(email: dict) -> Signal:
    return Signal(
        signal_id="pxeval_" + uuid.uuid4().hex[:10],
        person_id=MARGARET_PERSON_ID,
        source="email",
        payload=email,
        observed_at=datetime.now(timezone.utc),
    )


def generate_eval_traces(emails):
    """Run the Watcher over each email inside a CHAIN span. Returns
    (truth_by_input, run_start): a {email_json: true_label} map and the UTC time the
    run began (used to scope the span query to just this run)."""
    if not tracing.init_tracing():
        raise RuntimeError("Phoenix tracing is off — set PHOENIX_API_KEY in .env.")
    tracer = tracing._tracer
    run_start = datetime.now(timezone.utc)
    truth_by_input = {}
    print(f"Generating {len(emails)} Watcher traces in Phoenix project '{PROJECT_NAME}'...")
    for item in emails:
        email_json = json.dumps(item["email"])
        with tracer.start_as_current_span(_SPAN_NAME) as span:
            assessment = classify_signal(_signal(item["email"]))  # child LLM span
            span.set_attribute(_SPAN_KIND, "CHAIN")
            span.set_attribute(_INPUT_VALUE, email_json)
            span.set_attribute(
                _OUTPUT_VALUE,
                f"category={assessment.category}; severity={assessment.severity}; "
                f"confidence={assessment.confidence}; rationale={assessment.rationale}",
            )
        truth_by_input[email_json] = item["true_label"]
    return truth_by_input, run_start


_JUDGE_TEMPLATE = """You are grading the "Watcher", a classifier that flags scams for an \
older adult. Its category maps to a binary label: scam_phishing -> "scam"; benign -> \
"legit"; financial_anomaly / account_risk / missed_obligation -> a non-benign threat \
call (correct only if the email is genuinely dangerous, a miss if the email is an \
ordinary legitimate message).

EMAIL:
{attributes.input.value}

WATCHER VERDICT:
{attributes.output.value}

GROUND-TRUTH LABEL: {true_label}

Was the Watcher's verdict correct relative to the ground truth? Answer "correct" or \
"incorrect", then explain in one sentence what cue it missed or over-weighted if wrong."""


def evaluate_and_log(truth_by_input: dict, run_start, project_name: str = PROJECT_NAME,
                     timeout: int = 120) -> dict:
    """Pull this run's eval spans from Phoenix, judge them, and log annotations back."""
    from datetime import timedelta

    from phoenix.client import Client
    from phoenix.evals import LLM, ClassificationEvaluator, async_evaluate_dataframe
    from phoenix.evals.utils import to_annotation_dataframe
    from phoenix.trace import suppress_tracing

    # Point the client at Phoenix Cloud (same base as the collector) — without these
    # the client silently defaults to a local Phoenix and finds no spans.
    px = Client(
        base_url=os.getenv("PHOENIX_COLLECTOR_ENDPOINT"),
        api_key=os.getenv("PHOENIX_API_KEY"),
    )

    want = len(truth_by_input)
    in_col = "attributes." + _INPUT_VALUE
    since = run_start - timedelta(seconds=5)  # small buffer for clock skew
    deadline = time.monotonic() + timeout
    spans = None
    while time.monotonic() < deadline:
        df = px.spans.get_spans_dataframe(project_name=project_name, start_time=since)
        if df is not None and not df.empty and "name" in df.columns and in_col in df.columns:
            ours = df[df["name"] == _SPAN_NAME].copy()
            ours["true_label"] = ours[in_col].map(truth_by_input)
            ours = ours[ours["true_label"].notna()]  # only THIS run's eval spans
            if len(ours) >= want:
                spans = ours
                break
        time.sleep(3)
    if spans is None:
        raise RuntimeError(f"only found {0 if spans is None else len(spans)}/{want} "
                           "eval spans in Phoenix before timeout.")

    judge = ClassificationEvaluator(
        name="watcher_correctness",
        llm=LLM(provider="anthropic", model=JUDGE_MODEL),
        prompt_template=_JUDGE_TEMPLATE,
        choices={"correct": 1.0, "incorrect": 0.0},
        include_explanation=True,
    )

    print(f"Judging {len(spans)} spans with Claude (Phoenix ClassificationEvaluator)...")
    with suppress_tracing():  # don't trace the judge's own LLM calls
        results = asyncio.run(
            async_evaluate_dataframe(dataframe=spans, evaluators=[judge], concurrency=8)
        )

    annotations = to_annotation_dataframe(results)
    px.spans.log_span_annotations_dataframe(
        dataframe=annotations, annotator_kind="LLM"
    )

    # Each evaluator writes a "<name>_score" column whose value is a dict
    # {name, score, label, explanation}. Pull the label out of it.
    score_col = next((c for c in results.columns if c.endswith("_score")), None)

    def _label(v):
        return v.get("label") if isinstance(v, dict) else None

    labels = results[score_col].apply(_label) if score_col else []
    n = len(results)
    n_correct = int((labels == "correct").sum()) if score_col else 0
    mistakes = []
    if score_col:
        for v in results[score_col]:
            if isinstance(v, dict) and v.get("label") == "incorrect":
                mistakes.append(v.get("explanation", ""))
    accuracy = n_correct / n if n else 0.0
    print(f"\n=== Logged {n} annotations to Phoenix. Accuracy: {accuracy:.1%} "
          f"({n_correct}/{n}) ===")
    if mistakes:
        print("Mistakes (explanations the eval attached to the failing spans):")
        for m in mistakes:
            print(f"  - {m}")
    print("Open Phoenix -> project '%s' -> Traces to see the pass/fail + explanations."
          % project_name)
    return {"accuracy": accuracy, "n": n, "correct": n_correct}


def run_phoenix_eval(emails=None) -> dict:
    if emails is None:
        from pipeline.tests.eval_emails import EVAL_EMAILS
        from pipeline.tests.eval_emails_hard import EVAL_EMAILS_HARD
        emails = EVAL_EMAILS + EVAL_EMAILS_HARD
    truth_by_input, run_start = generate_eval_traces(emails)
    return evaluate_and_log(truth_by_input, run_start)


if __name__ == "__main__":
    run_phoenix_eval()
