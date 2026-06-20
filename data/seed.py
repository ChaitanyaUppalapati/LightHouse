"""Seed the Lighthouse database with the fixed demo identities.

Inserts the demo protected person "Margaret" and guardian "Priya" using the
frozen UUIDs from lighthouse_common/demo_ids.py, plus the trust grant that gives
Priya authority over Margaret (§8). Ensures the schema exists first.

Idempotent by design (INSERT ... ON CONFLICT): safe to run as many times as you
like. Run it with:  python data/seed.py
"""

import os
import sys

# Make both this folder (for db/init_db) and the repo root (for lighthouse_common)
# importable, regardless of where python is invoked from.
_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_HERE)
for _p in (_HERE, _REPO_ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from db import get_connection           # noqa: E402  (after sys.path setup)
from init_db import apply_schema        # noqa: E402
from lighthouse_common.demo_ids import MARGARET_PERSON_ID, PRIYA_GUARDIAN_ID  # noqa: E402

MARGARET_NAME = "Margaret"
PRIYA_NAME = "Priya"


def seed():
    apply_schema()  # tables must exist before we insert

    with get_connection() as conn:
        with conn.cursor() as cur:
            # Demo person. ON CONFLICT keeps re-runs safe and refreshes the name.
            cur.execute(
                """
                INSERT INTO people (person_id, name)
                VALUES (%s, %s)
                ON CONFLICT (person_id) DO UPDATE SET name = EXCLUDED.name
                """,
                (MARGARET_PERSON_ID, MARGARET_NAME),
            )

            # Demo guardian.
            cur.execute(
                """
                INSERT INTO guardians (guardian_id, name)
                VALUES (%s, %s)
                ON CONFLICT (guardian_id) DO UPDATE SET name = EXCLUDED.name
                """,
                (PRIYA_GUARDIAN_ID, PRIYA_NAME),
            )

            # Priya's authority over Margaret (the consent relationship).
            cur.execute(
                """
                INSERT INTO trust_grants (person_id, guardian_id)
                VALUES (%s, %s)
                ON CONFLICT (person_id, guardian_id) DO NOTHING
                """,
                (MARGARET_PERSON_ID, PRIYA_GUARDIAN_ID),
            )
        conn.commit()


def verify():
    """Read back what we seeded and print a clear confirmation."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT name, person_id FROM people WHERE person_id = %s",
                        (MARGARET_PERSON_ID,))
            person = cur.fetchone()
            cur.execute("SELECT name, guardian_id FROM guardians WHERE guardian_id = %s",
                        (PRIYA_GUARDIAN_ID,))
            guardian = cur.fetchone()
            cur.execute(
                "SELECT count(*) FROM trust_grants WHERE person_id = %s AND guardian_id = %s",
                (MARGARET_PERSON_ID, PRIYA_GUARDIAN_ID),
            )
            grant_count = cur.fetchone()[0]

    print("Seed complete:")
    print(f"  person   : {person[0]}  ({person[1]})")
    print(f"  guardian : {guardian[0]}  ({guardian[1]})")
    print(f"  trust_grant Priya -> Margaret: {'present' if grant_count else 'MISSING'}")


if __name__ == "__main__":
    seed()
    verify()
