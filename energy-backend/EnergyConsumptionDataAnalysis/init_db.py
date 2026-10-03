"""Apply the additive database schema from schema.sql."""

from contextlib import closing
from pathlib import Path

from config import BASE_DIR
from db import get_connection

def main():
    schema = (BASE_DIR / "schema.sql").read_text(encoding="utf-8")
    with closing(get_connection()) as connection, connection:
        with connection.cursor() as cursor:
            cursor.execute(schema)
    print("EnerGENAI tables and indexes are ready.")


if __name__ == "__main__":
    main()