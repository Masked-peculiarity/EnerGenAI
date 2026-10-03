"""Explicit additive initialization. Never drops existing tables or account data."""
from app.storage import Store

def initialize(store=None):
    store=store or Store()
    if store.postgres:
        with store.connection() as connection:
            cursor=connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY, password TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                CREATE TABLE IF NOT EXISTS knowledge_chunks (
                    id BIGSERIAL PRIMARY KEY,
                    username TEXT NOT NULL REFERENCES users(username) ON DELETE CASCADE,
                    source_name TEXT NOT NULL, chunk_index INTEGER NOT NULL,
                    content TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE (username, source_name, chunk_index)
                );
                CREATE INDEX IF NOT EXISTS knowledge_chunks_user_idx ON knowledge_chunks(username);
            """)
    print("Account/document schema ready ("+("PostgreSQL" if store.postgres else "SQLite")+"). Existing data preserved.")

if __name__=="__main__":
    initialize()
