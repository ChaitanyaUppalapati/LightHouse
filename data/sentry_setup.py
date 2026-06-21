"""Sentry instrumentation for the Lighthouse data service (task K5).

Initializes the Sentry SDK so unhandled errors and slow requests on the FastAPI
app are auto-captured. Sentry is genuinely useful here: computer-use and the
agent pipeline fail often, so surfacing those failures (and the data service's
own errors) is a real integration, not theater.

Reads SENTRY_DSN from the environment (.env). If it's empty, init is skipped and
the app runs normally — so a teammate without a DSN is never blocked. The dsn /
before_send overrides exist so tests can prove capture without a real account.
"""

import os

import sentry_sdk
from dotenv import load_dotenv

load_dotenv()


def init_sentry(dsn: str | None = None, before_send=None) -> bool:
    """Initialize Sentry. Returns True if initialized, False if skipped (no DSN).

    sentry-sdk auto-enables its FastAPI/Starlette integration when fastapi is
    installed, so simply calling this before the app is created instruments every
    route. traces_sample_rate turns on performance monitoring (slow requests).
    """
    dsn = dsn if dsn is not None else os.getenv("SENTRY_DSN", "")
    if not dsn:
        print("[sentry] SENTRY_DSN not set — Sentry disabled (app runs normally).")
        return False

    sentry_sdk.init(
        dsn=dsn,
        traces_sample_rate=1.0,        # capture performance / slow requests
        send_default_pii=False,        # don't ship personal data to Sentry
        environment=os.getenv("SENTRY_ENV", "dev"),
        before_send=before_send,       # tests hook this to capture events locally
    )
    print("[sentry] initialized.")
    return True
