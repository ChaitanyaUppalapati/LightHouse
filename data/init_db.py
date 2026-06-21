"""Apply data/schema.sql to the Lighthouse database.

Idempotent: schema.sql uses CREATE TABLE IF NOT EXISTS, so running this many
times is safe. Importable (apply_schema) so seed.py and tests can ensure the
tables exist, and runnable directly:  python data/init_db.py
"""

import os
from contextlib import closing

from db import get_connection

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


def apply_schema():
    """Create all Lighthouse tables if they don't already exist."""
    with open(SCHEMA_PATH, "r") as f:
        ddl = f.read()
    # closing() guarantees the connection is closed; the inner `with conn`
    # context only handles the transaction (commit/rollback), not the close.
    with closing(get_connection()) as conn:
        with conn.cursor() as cur:
            cur.execute(ddl)
        conn.commit()


if __name__ == "__main__":
    apply_schema()
    print("Schema applied (tables created if missing).")
