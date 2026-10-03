"""Local document chunking and PostgreSQL full-text retrieval."""

import re
from contextlib import closing
from typing import Any

from db import get_connection

CHUNK_SIZE = 1400
CHUNK_OVERLAP = 180
MAX_DOCUMENT_CHARS = 200_000


def split_into_chunks(text: str) -> list[str]:
    cleaned = re.sub(r"\s+", " ", text).strip()[:MAX_DOCUMENT_CHARS]
    if not cleaned:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(cleaned):
        end = min(start + CHUNK_SIZE, len(cleaned))
        if end < len(cleaned):
            boundary = cleaned.rfind(". ", start + CHUNK_SIZE // 2, end)
            if boundary > start:
                end = boundary + 1
        value = cleaned[start:end].strip()
        if value:
            chunks.append(value)
        if end >= len(cleaned):
            break
        start = max(end - CHUNK_OVERLAP, start + 1)
    return chunks


def index_document(username: str, source_name: str, text: str) -> int:
    chunks = split_into_chunks(text)
    if not chunks:
        raise ValueError("The document contains no readable text")
    with closing(get_connection()) as connection, connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM knowledge_chunks WHERE username = %s AND source_name = %s",
                (username, source_name),
            )
            cursor.executemany(
                "INSERT INTO knowledge_chunks (username, source_name, chunk_index, content) VALUES (%s, %s, %s, %s)",
                [(username, source_name, index, chunk) for index, chunk in enumerate(chunks)],
            )
    return len(chunks)


def search_documents(username: str, query: str, limit: int = 5) -> list[dict[str, Any]]:
    terms = query.strip()[:500]
    if not terms:
        return []
    with closing(get_connection()) as connection, connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, source_name, chunk_index, content,
                       ts_rank(to_tsvector('english', content), plainto_tsquery('english', %s)) AS rank
                FROM knowledge_chunks
                WHERE username = %s
                  AND to_tsvector('english', content) @@ plainto_tsquery('english', %s)
                ORDER BY rank DESC, source_name, chunk_index
                LIMIT %s
                """,
                (terms, username, terms, max(1, min(limit, 8))),
            )
            return [dict(row) for row in cursor.fetchall()]


def list_documents(username: str) -> list[dict[str, Any]]:
    with closing(get_connection()) as connection, connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT source_name, COUNT(*) AS chunks, MAX(created_at) AS indexed_at
                FROM knowledge_chunks WHERE username = %s
                GROUP BY source_name ORDER BY source_name
                """,
                (username,),
            )
            return [dict(row) for row in cursor.fetchall()]


def delete_document(username: str, source_name: str) -> bool:
    with closing(get_connection()) as connection, connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM knowledge_chunks WHERE username = %s AND source_name = %s",
                (username, source_name),
            )
            return cursor.rowcount > 0
