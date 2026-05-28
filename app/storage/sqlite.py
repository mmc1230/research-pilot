import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from app.config import get_settings


def _connect() -> sqlite3.Connection:
    db_path = get_settings().database_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_conn() -> Iterator[sqlite3.Connection]:
    conn = _connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                doc_type TEXT NOT NULL,
                collection_name TEXT NOT NULL,
                chunk_count INTEGER DEFAULT 0,
                metadata_json TEXT DEFAULT '{}',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                vector_id TEXT NOT NULL,
                section TEXT,
                source TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(document_id) REFERENCES documents(id)
            );
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                source_type TEXT,
                source_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS tool_calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                tool_name TEXT NOT NULL,
                args_json TEXT NOT NULL,
                result_summary TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """
        )


def create_document(
    filename: str,
    file_path: Path | str,
    doc_type: str,
    collection_name: str,
    chunk_count: int = 0,
    metadata: dict[str, Any] | None = None,
) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO documents(filename, file_path, doc_type, collection_name, chunk_count, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                filename,
                str(file_path),
                doc_type,
                collection_name,
                chunk_count,
                json.dumps(metadata or {}),
            ),
        )
        return int(cur.lastrowid)


def update_document_chunk_count(document_id: int, chunk_count: int) -> None:
    with get_conn() as conn:
        conn.execute("UPDATE documents SET chunk_count = ? WHERE id = ?", (chunk_count, document_id))


def add_chunk_metadata(
    document_id: int,
    chunk_index: int,
    vector_id: str,
    section: str | None,
    source: str,
) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO chunks(document_id, chunk_index, vector_id, section, source)
            VALUES (?, ?, ?, ?, ?)
            """,
            (document_id, chunk_index, vector_id, section, source),
        )


def list_documents() -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM documents ORDER BY created_at DESC").fetchall()
        return [dict(row) for row in rows]


def get_document(document_id: int | str) -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM documents WHERE id = ?", (str(document_id),)).fetchone()
        return dict(row) if row else None


def create_session(session_id: str, source_type: str, source_id: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO sessions(id, source_type, source_id) VALUES (?, ?, ?)",
            (session_id, source_type, source_id),
        )


def add_message(session_id: str, role: str, content: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO messages(session_id, role, content) VALUES (?, ?, ?)",
            (session_id, role, content),
        )


def add_tool_call(
    session_id: str,
    tool_name: str,
    args: dict[str, Any],
    result_summary: str,
) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO tool_calls(session_id, tool_name, args_json, result_summary)
            VALUES (?, ?, ?, ?)
            """,
            (session_id, tool_name, json.dumps(args, ensure_ascii=False), result_summary[:2000]),
        )


def get_logs(session_id: str) -> dict[str, list[dict[str, Any]]]:
    with get_conn() as conn:
        messages = conn.execute(
            "SELECT role, content, created_at FROM messages WHERE session_id = ? ORDER BY id",
            (session_id,),
        ).fetchall()
        tools = conn.execute(
            "SELECT tool_name, args_json, result_summary, created_at FROM tool_calls WHERE session_id = ? ORDER BY id",
            (session_id,),
        ).fetchall()
        return {
            "messages": [dict(row) for row in messages],
            "tool_calls": [dict(row) for row in tools],
        }
