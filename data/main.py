"""Lighthouse data service — FastAPI app (data/ track).

K2: the mock email feed — GET /signals/next gives Chaitanya's Watcher (C1) a
real HTTP source of email Signals.
K3: the append-only ledger — POST /ledger writes an event, GET /ledger reads a
person's events newest-first. ledger_events is locked append-only at startup
(our tamper-evidence feature, arch §9).
Later tasks (K4 approval bridge, K5 Sentry) extend this app.

Run it:
    uvicorn data.main:app --port 8001      # from the repo root
    python data/main.py                    # equivalent, runs on :8001
"""

import json
import os
import sys
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from itertools import cycle
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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
from init_db import apply_schema                      # noqa: E402
import ledger                                         # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure the tables exist and the ledger is locked append-only before serving.
    apply_schema()
    ledger.apply_append_only()
    yield


app = FastAPI(title="Lighthouse data service", version="0.3.0", lifespan=lifespan)

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


# --- Ledger (K3) --------------------------------------------------------------
# The immutable audit trail (arch §9). Every meaningful thing Lighthouse does is
# appended here; the table is locked append-only at startup so history cannot be
# rewritten. This is a local request model (pydantic v2) — unrelated to the
# frozen uagents schemas.

class LedgerEventIn(BaseModel):
    event_type: str
    details: dict = {}
    person_id: Optional[str] = None


@app.post("/ledger")
def post_ledger(event: LedgerEventIn) -> dict:
    """Append an event to the immutable ledger and return the stored row."""
    return ledger.add_event(
        event_type=event.event_type,
        details=event.details,
        person_id=event.person_id,
    )


@app.get("/ledger")
def get_ledger(person_id: Optional[str] = None) -> list[dict]:
    """Return ledger events newest-first, optionally filtered by person_id."""
    return ledger.get_events(person_id=person_id)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
