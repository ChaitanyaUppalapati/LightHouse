"""Lighthouse data service — FastAPI app (data/ track).

Task K2: the mock email feed. Serves fake email Signals one at a time from
GET /signals/next so Chaitanya's Watcher (C1) has a real HTTP source to classify
against. Later tasks (K3 ledger, K4 approval bridge, K5 Sentry) extend this app.

Run it:
    uvicorn data.main:app --port 8001      # from the repo root
    python data/main.py                    # equivalent, runs on :8001
"""

import json
import os
import sys
import uuid
from datetime import datetime, timezone
from itertools import cycle

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Make the repo root importable so lighthouse_common resolves regardless of how
# the app is launched (uvicorn data.main:app, or python data/main.py).
_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_HERE)
for _p in (_HERE, _REPO_ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from lighthouse_common.schemas import Signal          # noqa: E402
from lighthouse_common.demo_ids import MARGARET_PERSON_ID  # noqa: E402
from sample_emails import SAMPLE_EMAILS               # noqa: E402

app = FastAPI(title="Lighthouse data service", version="0.2.0")

# Sonakshi's dashboard (Vite) runs on :5173 and calls this API from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endless rotation over the built-in emails so /signals/next always returns the
# "next" one and wraps around forever.
_email_cycle = cycle(SAMPLE_EMAILS)


def _email_to_signal(email: dict) -> Signal:
    """Wrap a raw email dict as a well-formed email Signal."""
    # Drop our internal-only 'label' so the payload is just the raw email; the
    # Watcher must judge it itself, never read a pre-baked verdict.
    payload = {k: v for k, v in email.items() if k != "label"}
    return Signal(
        signal_id=str(uuid.uuid4()),
        person_id=MARGARET_PERSON_ID,
        source="email",
        payload=payload,
        observed_at=datetime.now(timezone.utc),
    )


@app.get("/")
def health():
    return {"service": "lighthouse-data", "status": "ok", "emails": len(SAMPLE_EMAILS)}


@app.get("/signals/next")
def next_signal() -> dict:
    """Return the next fake email as a Signal (cycles through the built-in list).

    Note: the shared schemas subclass uagents.Model, which is built on pydantic
    v1; current FastAPI no longer accepts a v1 model as response_model. So we
    construct a Signal (validating against the frozen schema), then serialize it
    via pydantic's own .json() — which renders observed_at as an ISO string —
    and return a plain JSON-ready dict.
    """
    signal = _email_to_signal(next(_email_cycle))
    return json.loads(signal.json())


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
