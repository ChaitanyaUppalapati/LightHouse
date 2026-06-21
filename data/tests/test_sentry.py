"""Prove Sentry auto-captures errors on the data service — without a real account.

We init Sentry with a syntactically-valid DUMMY dsn and a before_send hook that
records the event and returns None (so nothing is sent over the network). Then we
hit /sentry-test and assert the RuntimeError was captured. This verifies the K5
wiring locally; the only thing a real SENTRY_DSN adds is the event showing up in
the Sentry dashboard.

Run:  pip install -r data/requirements.txt pytest
      python -m pytest data/tests/test_sentry.py -q     # from the repo root
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import sentry_sdk  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402  (import-time init_sentry() no-ops: no DSN in env)
from sentry_setup import init_sentry  # noqa: E402

# A well-formed but fake DSN so init succeeds without talking to Sentry.
DUMMY_DSN = "https://examplePublicKey@o0.ingest.sentry.io/0"


def test_sentry_test_route_is_captured():
    captured = []

    def capture(event, hint):
        captured.append((event, hint))
        return None  # drop — never send over the network

    assert init_sentry(dsn=DUMMY_DSN, before_send=capture) is True
    try:
        # raise_server_exceptions=False so the 500 is returned, like a real server.
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/sentry-test")
        assert resp.status_code == 500

        # The RuntimeError we raised must have reached Sentry.
        assert captured, "Sentry captured no event for /sentry-test"
        exc_values = [
            v.get("type")
            for event, _ in captured
            for v in event.get("exception", {}).get("values", [])
        ]
        assert "RuntimeError" in exc_values, f"expected RuntimeError, got {exc_values}"
    finally:
        # Close the dummy client so its at-exit flush doesn't hang on the fake DSN.
        sentry_sdk.get_client().close(timeout=0.0)


def test_init_skips_without_dsn():
    # No DSN -> init returns False and the app is unaffected.
    assert init_sentry(dsn="") is False
