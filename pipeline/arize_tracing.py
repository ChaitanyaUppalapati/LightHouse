"""Arize tracing for the Lighthouse pipeline (task C6, part 1).

init_tracing() registers an OpenTelemetry tracer provider that ships spans to Arize
and auto-instruments the Anthropic SDK, so every Claude call the Watcher, Guardian,
Escalation agent, and executor make becomes a span you can inspect in Arize. Agent
steps can be wrapped as spans via the `span()` helper.

Reads ARIZE_SPACE_ID and ARIZE_API_KEY from .env. If either is missing, tracing is
skipped and the pipeline runs normally — so a teammate without Arize keys is never
blocked (same posture as the Sentry setup). Safe to call many times; only the first
call registers.

Install (data/pipeline):  pip install arize-otel openinference-instrumentation-anthropic
"""

import os
from contextlib import contextmanager

from dotenv import load_dotenv

load_dotenv()

PROJECT_NAME = os.getenv("ARIZE_PROJECT_NAME", "lighthouse")

_initialized = False
_tracer = None


def init_tracing() -> bool:
    """Register the Arize tracer provider and instrument Anthropic. Returns True if
    tracing was set up, False if it was skipped (missing keys or SDK)."""
    global _initialized, _tracer
    if _initialized:
        return _tracer is not None

    _initialized = True  # only attempt once, even on failure

    space_id = os.getenv("ARIZE_SPACE_ID", "")
    api_key = os.getenv("ARIZE_API_KEY", "")
    if not space_id or not api_key:
        print("[arize] ARIZE_SPACE_ID / ARIZE_API_KEY not set — tracing disabled.")
        return False

    try:
        from arize.otel import register
        from openinference.instrumentation.anthropic import AnthropicInstrumentor
    except ImportError as e:
        print(f"[arize] tracing deps not installed ({e}) — tracing disabled.")
        return False

    try:
        tracer_provider = register(
            space_id=space_id,
            api_key=api_key,
            project_name=PROJECT_NAME,
        )
        # Instrument the Anthropic SDK so every Claude call is a span.
        AnthropicInstrumentor().instrument(tracer_provider=tracer_provider)
        from opentelemetry import trace
        _tracer = trace.get_tracer("lighthouse.pipeline", tracer_provider=tracer_provider)
        print(f"[arize] tracing on (project={PROJECT_NAME}).")
        return True
    except Exception as e:  # never let observability break the pipeline
        print(f"[arize] init failed ({e}) — tracing disabled.")
        return False


@contextmanager
def span(name: str, **attributes):
    """Wrap an agent step as a span. No-op if tracing isn't initialized.

    Usage:
        with span("guardian.propose_action", action_type=proposal.action_type):
            ...
    """
    if _tracer is None:
        yield None
        return
    with _tracer.start_as_current_span(name) as s:
        for k, v in attributes.items():
            try:
                s.set_attribute(k, v)
            except Exception:
                pass
        yield s
