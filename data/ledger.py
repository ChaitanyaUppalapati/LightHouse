"""Append-only ledger access (task K3).

Thin data layer over the ledger_events table: apply the append-only lockdown,
write an event, and read a person's events newest-first. The HTTP surface lives
in main.py; keeping the SQL here makes it reusable (K4 writes approvals and
decisions to the ledger through add_event()).
"""

import json
import os
from contextlib import closing

from db import get_connection

_LOCKDOWN_SQL = os.path.join(os.path.dirname(__file__), "ledger_append_only.sql")


def apply_append_only():
    """Make ledger_events append-only (REVOKE + trigger). Idempotent."""
    with open(_LOCKDOWN_SQL, "r") as f:
        sql = f.read()
    with closing(get_connection()) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()


def add_event(event_type: str, details: dict | None = None,
              person_id: str | None = None) -> dict:
    """Append one event to the ledger and return the stored row."""
    with closing(get_connection()) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO ledger_events (person_id, event_type, details)
                VALUES (%s, %s, %s)
                RETURNING id, ts, person_id, event_type, details
                """,
                (person_id, event_type, json.dumps(details or {})),
            )
            row = cur.fetchone()
        conn.commit()
    return _row_to_dict(row)


def get_events(person_id: str | None = None) -> list[dict]:
    """Return ledger events newest-first, optionally filtered by person."""
    with closing(get_connection()) as conn:
        with conn.cursor() as cur:
            if person_id is None:
                cur.execute(
                    """
                    SELECT id, ts, person_id, event_type, details
                    FROM ledger_events
                    ORDER BY ts DESC, id DESC
                    """
                )
            else:
                cur.execute(
                    """
                    SELECT id, ts, person_id, event_type, details
                    FROM ledger_events
                    WHERE person_id = %s
                    ORDER BY ts DESC, id DESC
                    """,
                    (person_id,),
                )
            rows = cur.fetchall()
    return [_row_to_dict(r) for r in rows]


def _row_to_dict(row) -> dict:
    """(id, ts, person_id, event_type, details) -> JSON-ready dict."""
    _id, ts, person_id, event_type, details = row
    return {
        "id": _id,
        "ts": ts.isoformat(),
        "person_id": str(person_id) if person_id is not None else None,
        "event_type": event_type,
        "details": details,  # already a dict (jsonb column)
    }
