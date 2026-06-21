"""Global hero-demo driver (C7) — drives the family-dashboard story end to end.

Runs a scam email through the REAL pipeline (Watcher -> Guardian -> gate ->
executor/Escalation) and produces exactly what the family dashboard shows:
  - ledger events, so the dashboard History tells the story live, and
  - for a high-stakes scam, a pending approval the family DENIES live on the dashboard.
Autonomous scams are quarantined on the (tunnelled) mock inbox by the real Browserbase
executor when DEMO_MODE=0.

Prereqs: data service on :8001 (docker compose up -d; uvicorn data.main:app --port 8001),
the web app running, and for DEMO_MODE=0 a cloudflared tunnel with MOCK_INBOX_URL set to it.

    python -m pipeline.demo_global scam   # autonomous: classify -> quarantine -> History
    python -m pipeline.demo_global pay     # human-gate: classify -> approval on the dashboard (deny it live)
"""

import json
import os
import sys
import urllib.request
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
from pipeline.classifier import route_action  # noqa: E402
from pipeline.escalation import compose_message, request_approval  # noqa: E402
from pipeline.executor import execute  # noqa: E402
from pipeline.guardian import propose_action  # noqa: E402
from pipeline.watcher import classify_signal  # noqa: E402

load_dotenv()
DATA_URL = os.getenv("DATA_URL", os.getenv("VITE_DATA_URL", "http://localhost:8001")).rstrip("/")

SCAM_EMAIL = {
    "from_name": "IT Helpdesk",
    "from_address": "support@mailbox-quota-alert.com",
    "subject": "Your mailbox is almost full",
    "body": "Your mailbox is over quota and will stop receiving email. Verify your "
            "account now to keep it active: http://mailbox-quota-alert.com/verify",
}
PAY_EMAIL = {
    "from_name": "SecureBank Support",
    "from_address": "billing@secure-bank-help.com",
    "subject": "Your account is LOCKED",
    "body": "Pay a $200 verification fee within 24 hours to unlock your account or it "
            "will be permanently closed.",
}


def _ledger(event_type: str, detail: str) -> None:
    """Append an event so the dashboard History shows it."""
    body = json.dumps({
        "event_type": event_type,
        "person_id": MARGARET_PERSON_ID,
        "details": {"detail": detail},
    }).encode("utf-8")
    req = urllib.request.Request(f"{DATA_URL}/ledger", data=body,
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=5):
            print(f"   ledger << {event_type}: {detail}")
    except Exception as e:
        print(f"   [warn] ledger POST failed ({e}) — is the data service on {DATA_URL}?")


def _signal(email: dict) -> Signal:
    return Signal(signal_id="demo-" + uuid.uuid4().hex[:8], person_id=MARGARET_PERSON_ID,
                  source="email", payload=email, observed_at=datetime.now(timezone.utc))


def run(email: dict) -> None:
    subject = email.get("subject", "(no subject)")
    print(f"\n📨 A new email arrived: \"{subject}\"")
    _ledger("email_received", f"From {email['from_address']}: {subject}")

    print("🔎 Watcher is classifying it...")
    a = classify_signal(_signal(email))
    print(f"   -> {a.category} / {a.severity} (confidence {a.confidence:.0%})")
    if a.category == "benign":
        print("✅ Benign — nothing to do.")
        return
    _ledger("scam_detected", a.rationale)

    p = propose_action(a)
    d = route_action(p, a)
    print(f"🛡️  Guardian proposes {p.action_type}; the safety gate routes it -> {d.route} ({d.reason})")

    if d.route == "autonomous":
        print("⚙️  Executor is quarantining it on the inbox...")
        result = execute(p)
        print(f"   executor: {result.status}; evidence: {json.dumps(result.evidence)}")
        _ledger("email_quarantined", f"Moved the scam email to Quarantine ({p.action_type}).")
        _ledger("family_notified", "Notified the family that a scam was handled automatically.")
        replay = result.evidence.get("replay_url")
        if replay:
            print(f"   ▶ watch the browser do it: {replay}")
        print("✅ Handled automatically. Check the dashboard History + /inbox.")

    elif d.route == "human_gate":
        print("🧑‍⚖️  High-stakes — escalating to the family for approval...")
        msg = compose_message(p)
        apr_id = request_approval(p, msg)
        print(f"   posted approval {apr_id} to {DATA_URL}/approvals")
        print(f"   message: {msg}")
        print("\n👉 Now DENY it live on the family dashboard. Nothing happens until they decide.")

    else:  # watch_only
        _ledger("watch_only", "Logged a low-confidence concern; just watching.")
        print("🟡 Watch-only — logged, no action.")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "scam"
    if mode == "scam":
        run(SCAM_EMAIL)
    elif mode == "pay":
        run(PAY_EMAIL)
    else:
        print("usage: python -m pipeline.demo_global [scam|pay]")
        sys.exit(1)
