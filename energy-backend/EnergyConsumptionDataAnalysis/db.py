import os
from urllib.parse import urlsplit

import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL not set")

    if (urlsplit(DATABASE_URL).hostname or "").lower() == "host":
        raise RuntimeError(
            "DATABASE_URL still contains the HOST placeholder. Replace it in the "
            "repository root .env with the hostname from your PostgreSQL provider "
            "before running init_db.py."
        )

    return psycopg2.connect(
        DATABASE_URL,
        sslmode="require",
        cursor_factory=RealDictCursor
    )

