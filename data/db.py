"""Database connection helper for the Lighthouse data/ track.

Every data-track module (seed, the FastAPI feed, the ledger, the approval bridge)
opens its connection through here so there is one place that knows how to reach
Postgres. Reads DATABASE_URL from the environment (.env), falling back to the
local docker-compose default so a fresh clone runs out of the box.
"""

import os

import psycopg2
from dotenv import load_dotenv

# Load .env from the repo root (one level up from data/). Safe if .env is absent.
load_dotenv()

# Matches docker-compose.yml (image pgvector/pgvector:pg16, user/pw/db = lighthouse).
DEFAULT_DATABASE_URL = "postgresql://lighthouse:lighthouse@localhost:5432/lighthouse"

DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)


def get_connection():
    """Open a new psycopg2 connection to the Lighthouse database.

    Caller owns the connection (use it as a context manager or close it).
    """
    return psycopg2.connect(DATABASE_URL)
