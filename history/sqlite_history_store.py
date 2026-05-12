import json
import sqlite3
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional
from uuid import uuid4

from history.base_history_store import BaseHistoryStore


class SQLiteHistoryStore(BaseHistoryStore):
    name = "SQLiteHistoryStore"
    description = "SQLite 历史会话存储适配器"

    def __init__(self, db_path: str = "./data/history.sqlite3"):
        self.db_path = Path(db_path)
        self._lock = Lock()
        self._ensure_schema()

    def create_session(self, title: Optional[str] = None) -> Dict[str, Any]:
        now = self._now()
        session_id = str(uuid4())
        session = {
            "id": session_id,
            "title": title or "新会话",
            "summary": "",
            "status": "active",
            "last_model": "",
            "last_skill": "",
            "created_at": now,
            "updated_at": now,
        }
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO sessions (
                    id, title, summary, status, last_model, last_skill, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session["id"],
                    session["title"],
                    session["summary"],
                    session["status"],
                    session["last_model"],
                    session["last_skill"],
                    session["created_at"],
                    session["updated_at"],
                ),
            )
        return session

    def list_sessions(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, title, summary, status, last_model, last_skill, created_at, updated_at
                FROM sessions
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._session_from_row(row) for row in rows]

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            session_row = conn.execute(
                """
                SELECT id, title, summary, status, last_model, last_skill, created_at, updated_at
                FROM sessions
                WHERE id = ?
                """,
                (session_id,),
            ).fetchone()
            if not session_row:
                return None

            message_rows = conn.execute(
                """
                SELECT id, session_id, role, content, thinking, run_config, attachments, created_at
                FROM messages
                WHERE session_id = ?
                ORDER BY created_at ASC, rowid ASC
                """,
                (session_id,),
            ).fetchall()

        session = self._session_from_row(session_row)
        session["messages"] = [self._message_from_row(row) for row in message_rows]
        return session

    def delete_session(self, session_id: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        return cursor.rowcount > 0

    def append_message(
        self,
        session_id: str,
        role: str,
        content: str,
        thinking: str = "",
        run_config: Optional[Dict[str, Any]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        now = self._now()
        message = {
            "id": str(uuid4()),
            "session_id": session_id,
            "role": role,
            "content": content,
            "thinking": thinking,
            "run_config": run_config or {},
            "attachments": attachments or [],
            "created_at": now,
        }
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO messages (
                    id, session_id, role, content, thinking, run_config, attachments, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    message["id"],
                    message["session_id"],
                    message["role"],
                    message["content"],
                    message["thinking"],
                    json.dumps(message["run_config"], ensure_ascii=False),
                    json.dumps(message["attachments"], ensure_ascii=False),
                    message["created_at"],
                ),
            )
            conn.execute(
                "UPDATE sessions SET updated_at = ? WHERE id = ?",
                (now, session_id),
            )
        return message

    def update_session(
        self,
        session_id: str,
        title: Optional[str] = None,
        summary: Optional[str] = None,
        status: Optional[str] = None,
        last_model: Optional[str] = None,
        last_skill: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        changes = {
            "title": title,
            "summary": summary,
            "status": status,
            "last_model": last_model,
            "last_skill": last_skill,
            "updated_at": self._now(),
        }
        filtered = {key: value for key, value in changes.items() if value is not None}
        assignments = ", ".join(f"{key} = ?" for key in filtered)
        values = list(filtered.values()) + [session_id]
        with self._connect() as conn:
            conn.execute(
                f"UPDATE sessions SET {assignments} WHERE id = ?",
                values,
            )
        return self.get_session(session_id)

    def health_check(self) -> Dict[str, Any]:
        try:
            with self._connect() as conn:
                conn.execute("SELECT 1").fetchone()
            return {"status": "ok", "store": self.name, "db_path": str(self.db_path)}
        except Exception as exc:
            return {
                "status": "degraded",
                "store": self.name,
                "db_path": str(self.db_path),
                "error": str(exc),
            }

    def as_dict(self) -> Dict[str, Any]:
        return {"description": self.description, "db_path": str(self.db_path)}

    def _ensure_schema(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with self._connect() as conn:
                conn.executescript(
                    """
                    PRAGMA foreign_keys = ON;

                    CREATE TABLE IF NOT EXISTS sessions (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        summary TEXT NOT NULL DEFAULT '',
                        status TEXT NOT NULL DEFAULT 'active',
                        last_model TEXT NOT NULL DEFAULT '',
                        last_skill TEXT NOT NULL DEFAULT '',
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    );

                    CREATE TABLE IF NOT EXISTS messages (
                        id TEXT PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL DEFAULT '',
                        thinking TEXT NOT NULL DEFAULT '',
                        run_config TEXT NOT NULL DEFAULT '{}',
                        attachments TEXT NOT NULL DEFAULT '[]',
                        created_at TEXT NOT NULL,
                        FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
                    );

                    CREATE INDEX IF NOT EXISTS idx_messages_session_created
                    ON messages(session_id, created_at);
                    """
                )

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    @staticmethod
    def _now() -> str:
        return datetime.utcnow().isoformat() + "Z"

    @staticmethod
    def _session_from_row(row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "id": row["id"],
            "title": row["title"],
            "summary": row["summary"],
            "status": row["status"],
            "last_model": row["last_model"],
            "last_skill": row["last_skill"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    @staticmethod
    def _message_from_row(row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "id": row["id"],
            "session_id": row["session_id"],
            "role": row["role"],
            "content": row["content"],
            "thinking": row["thinking"],
            "run_config": json.loads(row["run_config"] or "{}"),
            "attachments": json.loads(row["attachments"] or "[]"),
            "created_at": row["created_at"],
        }
