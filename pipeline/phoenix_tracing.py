"""Phoenix tracing for the Lighthouse pipeline (task C6, part 1).

Sends OpenTelemetry traces to Arize **Phoenix** (Phoenix Cloud) and auto-instruments
the Anthropic SDK, so every Claude call the Watcher, Guardian, Escalation agent, and
executor make becomes a span you can inspect in Phoenix. Agent steps can be wrapped
as spans via the `span()` helper. Phoenix is the observability/eval target for this
project (the prize is Phoenix, not Arize AX).

Reads PHOENIX_API_KEY and PHOENIX_COLLECTOR_ENDPOINT from .env. If the API key is
missing, tracing is skipped and the pipeline runs normally — so a teammate without
Phoenix access is never blocked (same posture as the Sentry setup). Safe to call
many times; only the first call registers.

Install:  pip install arize-phoenix-otel openinference-instrumentation-anthropic
Phoenix Cloud: grab the API key + collector endpoint from app.phoenix.arize.com.
"""

import os
from contextlib import contextmanager

from dotenv import load_dotenv

load_dotenv()

PROJECT_NAME = os.getenv("PHOENIX_PROJECT_NAME", "lighthouse")
# Phoenix Cloud default collector; override per-space via PHOENIX_COLLECTOR_ENDPOINT.
DEFAULT_ENDPOINT = "https://app.phoenix.arize.com"

_initialized = False
_tracer = None


def init_tracing() -> bool:
    """Register the Phoenix tracer provider and instrument Anthropic. Returns True if
    tracing was set up, False if it was skipped (missing key or SDK)."""
    global _initialized, _tracer
    if _initialized:
        return _tracer is not None

    _initialized = True  # only attempt once, even on failure

    api_key = os.getenv("PHOENIX_API_KEY", "")
    if not api_key:
        print("[phoenix] PHOENIX_API_KEY not set — tracing disabled.")
        return False

    # phoenix.otel.register reads these from the environment.
    os.environ.setdefault("PHOENIX_COLLECTOR_ENDPOINT", DEFAULT_ENDPOINT)

    try:
        from phoenix.otel import register
    except ImportError as e:
        print(f"[phoenix] tracing deps not installed ({e}) — tracing disabled.")
        return False

    try:
        # auto_instrument=True picks up installed openinference instrumentors,
        # including openinference-instrumentation-anthropic.
        tracer_provider = register(
            project_name=PROJECT_NAME,
            auto_instrument=True,
        )
        from opentelemetry import trace
        _tracer = trace.get_tracer("lighthouse.pipeline", tracer_provider=tracer_provider)
        endpoint = os.environ.get("PHOENIX_COLLECTOR_ENDPOINT", DEFAULT_ENDPOINT)
        print(f"[phoenix] tracing on (project={PROJECT_NAME}, endpoint={endpoint}).")
        return True
    except Exception as e:  # never let observability break the pipeline
        print(f"[phoenix] init failed ({e}) — tracing disabled.")
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
