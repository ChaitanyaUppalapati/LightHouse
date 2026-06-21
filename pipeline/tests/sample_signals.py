"""Built-in sample email Signals for testing the Watcher (C1).

Three obvious scams and two normal messages, as frozen `Signal` objects. The
Watcher must classify these sensibly with no feed running (scams -> high severity
scam_phishing; normal -> benign). These mirror the shape of the emails Keya's
K2 feed serves at /signals/next, so the same classify_signal() works on both.

`label` is for our own readability only — it is NOT part of the payload the
Watcher sees, because the Watcher must judge the email itself, never read a
pre-baked verdict.
"""

import uuid
from datetime import datetime, timezone

from lighthouse_common.demo_ids import MARGARET_PERSON_ID
from lighthouse_common.schemas import Signal

# (label, payload) pairs — label kept separate so it never leaks into the Signal.
_SAMPLES = [
    # --- scams -------------------------------------------------------------
    (
        "scam",
        {
            "from_name": "Wells Fargo Security",
            "from_address": "alerts@wellsfargo-secure-login.com",
            "subject": "Your account is LOCKED — pay $200 to restore access",
            "body": (
                "Dear Customer, we detected unusual activity and locked your "
                "account. To restore access you must pay a $200 verification fee "
                "within 24 hours or your account will be permanently closed. "
                "Click here to pay now: http://wellsfargo-secure-login.com/restore"
            ),
        },
    ),
    (
        "scam",
        {
            "from_name": "Apple Support",
            "from_address": "no-reply@apple-id-verify.net",
            "subject": "Your Apple ID has been suspended",
            "body": (
                "We have locked your Apple ID due to a security concern. Verify "
                "your identity immediately by confirming your password and card "
                "details at http://apple-id-verify.net/unlock or your account "
                "will be deleted."
            ),
        },
    ),
    (
        "scam",
        {
            "from_name": "IRS Tax Refund",
            "from_address": "refunds@irs-gov-payments.com",
            "subject": "You are owed a $1,438.00 tax refund — claim now",
            "body": (
                "Our records show you are eligible for a tax refund of $1,438.00. "
                "To receive your refund, confirm your Social Security number and "
                "bank account details at http://irs-gov-payments.com/claim. This "
                "offer expires in 24 hours."
            ),
        },
    ),
    # --- normal ------------------------------------------------------------
    (
        "normal",
        {
            "from_name": "Walgreens Pharmacy",
            "from_address": "no-reply@walgreens.com",
            "subject": "Your prescription is ready for pickup",
            "body": (
                "Hello Margaret, your prescription refill is ready for pickup at "
                "your Walgreens on Main Street. Store hours are 9am-9pm. No action "
                "needed — just stop by when convenient."
            ),
        },
    ),
    (
        "normal",
        {
            "from_name": "David Chen",
            "from_address": "david.chen@gmail.com",
            "subject": "Sunday dinner this weekend?",
            "body": (
                "Hi Mom, hope you're doing well! Are you free for dinner on "
                "Sunday? I can pick you up around 5. Let me know. Love, David."
            ),
        },
    ),
]


def sample_signals() -> list[tuple[str, Signal]]:
    """Return (label, Signal) pairs. Each Signal gets a fresh id at call time."""
    out = []
    for label, payload in _SAMPLES:
        signal = Signal(
            signal_id=str(uuid.uuid4()),
            person_id=MARGARET_PERSON_ID,
            source="email",
            payload=payload,
            observed_at=datetime.now(timezone.utc),
        )
        out.append((label, signal))
    return out
