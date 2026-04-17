"""SQLite-backed paper store for production deployment.

Replaces the in-memory _paper_store dict so state survives container restarts.
"""

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path

_db_path = os.environ.get("PAPER_DB_PATH", "/data/papers.db")
Path(_db_path).parent.mkdir(parents=True, exist_ok=True)

_conn = sqlite3.connect(_db_path, check_same_thread=False)
_conn.row_factory = sqlite3.Row


def init_db():
    _conn.execute("""
        CREATE TABLE IF NOT EXISTS papers (
            paper_id   TEXT PRIMARY KEY,
            state_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    _conn.commit()


def save(paper_id: str, state: dict):
    now = datetime.utcnow().isoformat()
    state_json = json.dumps(state, ensure_ascii=False)
    _conn.execute(
        """
        INSERT INTO papers (paper_id, state_json, created_at, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(paper_id) DO UPDATE SET state_json=excluded.state_json, updated_at=excluded.updated_at
        """,
        (paper_id, state_json, now, now),
    )
    _conn.commit()


def load(paper_id: str) -> dict | None:
    row = _conn.execute(
        "SELECT state_json FROM papers WHERE paper_id = ?", (paper_id,)
    ).fetchone()
    if row is None:
        return None
    return json.loads(row["state_json"])


def list_ids() -> list[str]:
    rows = _conn.execute("SELECT paper_id FROM papers ORDER BY created_at DESC").fetchall()
    return [r["paper_id"] for r in rows]


init_db()
