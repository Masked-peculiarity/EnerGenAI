"""Account/document persistence compatible with existing PostgreSQL accounts."""
import os
import sqlite3
from contextlib import contextmanager
from urllib.parse import urlsplit
from app.config import RUNTIME_DIR

class Store:
    def __init__(self,sqlite_path=None):
        url = os.getenv("DATABASE_URL","")
        configured = bool(url and (urlsplit(url).hostname or "").lower() not in {"","host"})
        self.postgres = sqlite_path is None and os.getenv("PERSISTENCE_BACKEND","postgres" if configured else "sqlite")=="postgres"
        self.url, self.path = url, sqlite_path or RUNTIME_DIR/"accounts.sqlite3"
        if not self.postgres:
            self.path.parent.mkdir(parents=True,exist_ok=True)
            with self.connection() as connection:
                connection.executescript("""CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY,password TEXT NOT NULL);
                    CREATE TABLE IF NOT EXISTS knowledge_chunks (id INTEGER PRIMARY KEY,username TEXT NOT NULL REFERENCES users(username),
                    source_name TEXT NOT NULL,chunk_index INTEGER NOT NULL,content TEXT NOT NULL,created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(username,source_name,chunk_index));""")

    @contextmanager
    def connection(self):
        if self.postgres:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            connection = psycopg2.connect(self.url,sslmode="require",cursor_factory=RealDictCursor,connect_timeout=10)
        else:
            connection = sqlite3.connect(self.path,timeout=10)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys=ON")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def execute(self,connection,sql,values=()):
        cursor = connection.cursor()
        cursor.execute(sql.replace("?","%s") if self.postgres else sql,values)
        return cursor

    def user(self,username):
        with self.connection() as connection:
            row = self.execute(connection,"SELECT username,password FROM users WHERE username=?",(username,)).fetchone()
            return dict(row) if row else None

    def add_user(self,username,password_hash):
        with self.connection() as connection:
            self.execute(connection,"INSERT INTO users (username,password) VALUES (?,?)",(username,password_hash))

    def chunks(self,username):
        with self.connection() as connection:
            rows = self.execute(connection,"SELECT source_name,chunk_index,content FROM knowledge_chunks WHERE username=? ORDER BY source_name,chunk_index LIMIT 1000",(username,)).fetchall()
            return [dict(row) for row in rows]

    def index_document(self,username,filename,text):
        cleaned = " ".join(text.split())[:200000]
        chunks = [cleaned[start:start+1400] for start in range(0,len(cleaned),1220)]
        if not chunks:
            raise ValueError("Document contains no readable text; image-only PDFs need OCR")
        with self.connection() as connection:
            self.execute(connection,"DELETE FROM knowledge_chunks WHERE username=? AND source_name=?",(username,filename))
            for index,chunk in enumerate(chunks):
                self.execute(connection,"INSERT INTO knowledge_chunks (username,source_name,chunk_index,content) VALUES (?,?,?,?)",(username,filename,index,chunk))
        return len(chunks)

    def delete_document(self,username,filename):
        with self.connection() as connection:
            return self.execute(connection,"DELETE FROM knowledge_chunks WHERE username=? AND source_name=?",(username,filename)).rowcount
