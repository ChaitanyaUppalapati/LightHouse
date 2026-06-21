"""Real Gmail email source (task K6, STRETCH).

Reads UNREAD emails from a test Gmail account via the Gmail API with read-only
OAuth and turns them into email Signals — the real-data version of the K2 mock
feed. The mock list stays as the fallback (see main.py), so the demo never breaks
if Gmail/OAuth is unavailable.

Two phases, on purpose:
  - authorize()  : one-time, interactive. Opens a browser so you click "Allow";
                   saves token.json. Run it once:  python data/gmail_feed.py
  - the server   : silent. Uses the saved token.json only; never opens a browser
                   mid-request. If no/expired token, it simply yields nothing and
                   the caller falls back to the mock feed.

Secrets (credentials.json, token.json) live at the repo root and are gitignored.
"""

import base64
import os
import sys
from datetime import datetime, timezone
from email.utils import parseaddr, parsedate_to_datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Make the repo root importable so lighthouse_common resolves when run directly.
_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_HERE)
for _p in (_HERE, _REPO_ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from lighthouse_common.schemas import Signal              # noqa: E402
from lighthouse_common.demo_ids import MARGARET_PERSON_ID  # noqa: E402

# Read-only: this app can READ mail, never send, modify, or delete it.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
CREDENTIALS_PATH = os.path.join(_REPO_ROOT, "credentials.json")
TOKEN_PATH = os.path.join(_REPO_ROOT, "token.json")


def has_token() -> bool:
    """True if a saved token exists (server should attempt Gmail)."""
    return os.path.exists(TOKEN_PATH)


def authorize():
    """One-time interactive consent. Opens a browser, then saves token.json."""
    if not os.path.exists(CREDENTIALS_PATH):
        raise FileNotFoundError(
            f"credentials.json not found at {CREDENTIALS_PATH} — download it from "
            "Google Cloud (OAuth client, Desktop app) and place it there."
        )
    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
    creds = flow.run_local_server(port=0)
    with open(TOKEN_PATH, "w") as f:
        f.write(creds.to_json())
    return creds


def _load_saved_credentials():
    """Load token.json silently (refresh if expired). None if unusable — never
    launches a browser, so the server stays non-interactive."""
    if not os.path.exists(TOKEN_PATH):
        return None
    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if creds and creds.valid:
        return creds
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())
        return creds
    return None


def _service(creds):
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def _decode_part(part) -> str:
    data = part.get("body", {}).get("data")
    if not data:
        return ""
    return base64.urlsafe_b64decode(data.encode("utf-8")).decode("utf-8", "replace")


def _extract_body(payload) -> str:
    """Pull plain-text body, walking multipart messages."""
    if payload.get("mimeType") == "text/plain":
        return _decode_part(payload)
    for part in payload.get("parts", []) or []:
        text = _extract_body(part)
        if text:
            return text
    return ""


def _message_to_signal(service, msg_id: str) -> Signal:
    msg = service.users().messages().get(userId="me", id=msg_id, format="full").execute()
    payload = msg.get("payload", {})
    headers = {h["name"].lower(): h["value"] for h in payload.get("headers", [])}
    from_name, from_address = parseaddr(headers.get("from", ""))
    body = _extract_body(payload) or msg.get("snippet", "")

    observed_at = datetime.now(timezone.utc)
    if headers.get("date"):
        try:
            observed_at = parsedate_to_datetime(headers["date"])
        except (TypeError, ValueError):
            pass

    return Signal(
        signal_id="gmail-" + msg_id,          # stable id -> save_signal dedupes
        person_id=MARGARET_PERSON_ID,
        source="email",
        payload={
            "from_name": from_name or from_address,
            "from_address": from_address,
            "subject": headers.get("subject", ""),
            "body": body,
        },
        observed_at=observed_at,
    )


def next_unread_signal(served_ids: set) -> Signal | None:
    """Return the next not-yet-served UNREAD email as a Signal, or None.

    None means "no Gmail available or nothing new" — the caller then falls back
    to the mock feed. served_ids tracks what we've already handed out (read-only
    scope can't mark mail as read, so we de-dupe in memory).
    """
    creds = _load_saved_credentials()
    if creds is None:
        return None
    service = _service(creds)
    resp = service.users().messages().list(
        userId="me", labelIds=["UNREAD", "INBOX"], maxResults=10
    ).execute()
    for m in resp.get("messages", []):
        if m["id"] in served_ids:
            continue
        served_ids.add(m["id"])
        return _message_to_signal(service, m["id"])
    return None


if __name__ == "__main__":
    # One-time setup: opens a browser for consent, then shows a sample unread email.
    print("Opening a browser for Google sign-in — pick your TEST account and click Allow...")
    authorize()
    print("token.json saved.\n")
    sig = next_unread_signal(set())
    if sig is None:
        print("Authorized, but no unread emails found. Send the test inbox an email and re-run.")
    else:
        print("Got a real unread email as a Signal:")
        print("  from:   ", sig.payload["from_address"])
        print("  subject:", sig.payload["subject"])
