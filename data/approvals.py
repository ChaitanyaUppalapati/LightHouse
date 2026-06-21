"""Approval bridge data layer (task K4, architecture §4.4).

The link between Chaitanya's Escalation agent (C4) and Sonakshi's dashboard (S6):
the agent creates a pending approval with a plain-language message; the dashboard
lists what's pending and records the family's decision; the agent polls for it.

Every approval AND every decision is also written to the append-only ledger, so
the whole human-gate trail shows up in the family's history timeline.
"""

import json
import uuid
from contextlib import closing

from db import get_connection
import ledger
from lighthouse_common.demo_ids import MARGARET_PERSON_ID

# Columns we read back, in order — kept in one place so every query stays in sync.
_COLUMNS = "approval_id, person_id, proposal, message, detail, status, created_at, decided_at"


def create_approval(proposal: dict, message: str,
                    person_id: str | None = None, detail: str | None = None) -> dict:
    """Create a pending approval and log it to the ledger. Returns the stored row.

    person_id defaults to the demo person (Margaret) when the caller omits it, so
    the approval still lands in her history timeline.
    """
    approval_id = "apr_" + uuid.uuid4().hex[:12]
    person_id = person_id or MARGARET_PERSON_ID

    with closing(get_connection()) as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO approvals (approval_id, person_id, proposal, message, detail)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING {_COLUMNS}
                """,
                (approval_id, person_id, json.dumps(proposal), message, detail),
            )
            row = cur.fetchone()
        conn.commit()

    ledger.add_event(
        event_type="approval_requested",
        details={
            "approval_id": approval_id,
            "message": message,
            "action_type": proposal.get("action_type"),
        },
        person_id=person_id,
    )
    return _row_to_dict(row)


def list_approvals(status: str | None = None) -> list[dict]:
    """List approvals (optionally filtered by status), newest first."""
    with closing(get_connection()) as conn:
        with conn.cursor() as cur:
            if status is None:
                cur.execute(
                    f"SELECT {_COLUMNS} FROM approvals ORDER BY created_at DESC"
                )
            else:
                cur.execute(
                    f"SELECT {_COLUMNS} FROM approvals WHERE status = %s "
                    f"ORDER BY created_at DESC",
                    (status,),
                )
            rows = cur.fetchall()
    return [_row_to_dict(r) for r in rows]


def get_approval(approval_id: str) -> dict | None:
    """Fetch one approval (what the agent polls). None if it doesn't exist."""
    with closing(get_connection()) as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT {_COLUMNS} FROM approvals WHERE approval_id = %s",
                (approval_id,),
            )
            row = cur.fetchone()
    return _row_to_dict(row) if row else None


def decide_approval(approval_id: str, decision: str) -> dict | None:
    """Record the family's decision (approved/denied) and log it to the ledger.

    Only acts on a still-pending approval (idempotent: a second decide is a no-op
    that returns the current state). Returns None if the approval doesn't exist.
    """
    if decision not in ("approved", "denied"):
        raise ValueError("decision must be 'approved' or 'denied'")

    with closing(get_connection()) as conn:
        with conn.cursor() as cur:
            # Only the first decision sticks (WHERE status='pending').
            cur.execute(
                f"""
                UPDATE approvals
                SET status = %s, decided_at = now()
                WHERE approval_id = %s AND status = 'pending'
                RETURNING {_COLUMNS}
                """,
                (decision, approval_id),
            )
            updated = cur.fetchone()
            if updated is None:
                # Either it doesn't exist or it was already decided — read current.
                cur.execute(
                    f"SELECT {_COLUMNS} FROM approvals WHERE approval_id = %s",
                    (approval_id,),
                )
                existing = cur.fetchone()
        conn.commit()

    if updated is None:
        return _row_to_dict(existing) if existing else None

    row = _row_to_dict(updated)
    ledger.add_event(
        event_type="approval_decided",
        details={"approval_id": approval_id, "decision": decision},
        person_id=row["person_id"],
    )
    return row


def _row_to_dict(row) -> dict:
    """(approval_id, person_id, proposal, message, detail, status, created_at,
    decided_at) -> JSON-ready dict. Includes an `id` alias to match the dashboard."""
    (approval_id, person_id, proposal, message, detail,
     status, created_at, decided_at) = row
    return {
        "approval_id": approval_id,
        "id": approval_id,  # alias: Sonakshi's ApprovalCard keys on `id`
        "person_id": str(person_id) if person_id is not None else None,
        "proposal": proposal,            # already a dict (jsonb)
        "message": message,
        "detail": detail,
        "status": status,
        "created_at": created_at.isoformat(),
        "decided_at": decided_at.isoformat() if decided_at is not None else None,
    }
