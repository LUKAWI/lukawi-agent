"""Session manager with SQLite-persisted session metadata and messages."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

import aiosqlite

from lukawi.llm.base import Message, MessageRole


@dataclass
class SessionInfo:
    id: str
    name: str
    message_count: int
    created_at: datetime
    updated_at: datetime


class SessionManager:

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._db: aiosqlite.Connection | None = None
        self._messages_cache: dict[str, list[Message]] = {}

    async def initialize(self) -> None:
        self._db = await aiosqlite.connect(self.db_path)
        self._db.row_factory = aiosqlite.Row

        await self._db.execute("PRAGMA foreign_keys = ON")

        await self._db.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT,
                tool_call_id TEXT,
                reasoning_content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_messages_session
                ON messages(session_id, id);
        """)

        await self._db.commit()

    async def close(self) -> None:
        if self._db:
            try:
                await self._db.commit()
            except Exception:
                pass
            await self._db.close()
            self._db = None

    async def create_session(self, name: str = "New Session") -> SessionInfo:
        if not self._db:
            raise RuntimeError("Database not initialized")

        session_id = str(uuid.uuid4())
        now = datetime.now(UTC).replace(tzinfo=None).isoformat()

        await self._db.execute(
            "INSERT INTO sessions (id, name, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (session_id, name, now, now)
        )

        await self._db.commit()
        return SessionInfo(
            id=session_id,
            name=name,
            message_count=0,
            created_at=datetime.fromisoformat(now),
            updated_at=datetime.fromisoformat(now),
        )

    async def list_sessions(self) -> list[SessionInfo]:
        if not self._db:
            raise RuntimeError("Database not initialized")

        async with self._db.execute(
            """SELECT s.id, s.name, s.created_at, s.updated_at,
                      (SELECT COUNT(*) FROM messages m WHERE m.session_id = s.id) AS message_count
               FROM sessions s
               ORDER BY s.updated_at DESC"""
        ) as cursor:
            rows = await cursor.fetchall()

        return [self._row_to_session_info(row) for row in rows]

    async def get_session(self, session_id: str) -> SessionInfo | None:
        if not self._db:
            raise RuntimeError("Database not initialized")

        async with self._db.execute(
            """SELECT s.id, s.name, s.created_at, s.updated_at,
                      (SELECT COUNT(*) FROM messages m WHERE m.session_id = s.id) AS message_count
               FROM sessions s WHERE s.id = ?""",
            (session_id,)
        ) as cursor:
            row = await cursor.fetchone()

        if row is None:
            return None

        return self._row_to_session_info(row)

    async def rename_session(self, session_id: str, name: str) -> bool:
        if not self._db:
            raise RuntimeError("Database not initialized")

        now = datetime.now(UTC).replace(tzinfo=None).isoformat()
        cursor = await self._db.execute(
            "UPDATE sessions SET name = ?, updated_at = ? WHERE id = ?",
            (name, now, session_id)
        )

        await self._db.commit()
        return cursor.rowcount > 0

    async def delete_session(self, session_id: str) -> bool:
        if not self._db:
            raise RuntimeError("Database not initialized")

        self._messages_cache.pop(session_id, None)

        await self._db.execute(
            "DELETE FROM messages WHERE session_id = ?",
            (session_id,)
        )
        cursor = await self._db.execute(
            "DELETE FROM sessions WHERE id = ?",
            (session_id,)
        )

        await self._db.commit()
        return cursor.rowcount > 0

    async def save_messages(
        self,
        session_id: str,
        messages: list[Message],
    ) -> None:
        if not self._db:
            raise RuntimeError("Database not initialized")

        session = await self.get_session(session_id)
        if session is None:
            raise ValueError(f"Session {session_id} does not exist")

        if session_id not in self._messages_cache:
            self._messages_cache[session_id] = []

        self._messages_cache[session_id].extend(messages)

        for msg in messages:
            await self._db.execute(
                "INSERT INTO messages (session_id, role, content, tool_call_id, reasoning_content) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    session_id,
                    msg.role.value,
                    msg.content,
                    msg.tool_call_id,
                    msg.reasoning_content,
                ),
            )

        now = datetime.now(UTC).replace(tzinfo=None).isoformat()
        await self._db.execute(
            "UPDATE sessions SET updated_at = ? WHERE id = ?",
            (now, session_id)
        )
        await self._db.commit()

    async def load_messages(self, session_id: str) -> list[Message]:
        if not self._db:
            raise RuntimeError("Database not initialized")

        if session_id in self._messages_cache:
            return list(self._messages_cache[session_id])

        async with self._db.execute(
            "SELECT role, content, tool_call_id, reasoning_content "
            "FROM messages WHERE session_id = ? ORDER BY id ASC",
            (session_id,),
        ) as cursor:
            rows = await cursor.fetchall()

        messages = [
            Message(
                role=MessageRole(row["role"]),
                content=row["content"],
                tool_call_id=row["tool_call_id"],
                reasoning_content=row["reasoning_content"],
            )
            for row in rows
        ]
        self._messages_cache[session_id] = messages
        return list(messages)

    async def get_message_count(self, session_id: str) -> int:
        if not self._db:
            raise RuntimeError("Database not initialized")

        if session_id in self._messages_cache:
            return len(self._messages_cache[session_id])

        async with self._db.execute(
            "SELECT COUNT(*) as cnt FROM messages WHERE session_id = ?",
            (session_id,),
        ) as cursor:
            row = await cursor.fetchone()
            return row["cnt"] if row else 0

    def get_all_cached_messages(self) -> dict[str, list[Message]]:
        """Return a copy of all cached messages organized by session ID.

        This provides read-only access to the in-memory message cache
        without exposing the internal _messages_cache attribute directly.
        """
        return {sid: list(msgs) for sid, msgs in self._messages_cache.items()}

    def _row_to_session_info(self, row: aiosqlite.Row) -> SessionInfo:
        sid = row["id"]
        return SessionInfo(
            id=sid,
            name=row["name"],
            message_count=row["message_count"] if "message_count" in row.keys() else 0,
            created_at=datetime.fromisoformat(row["created_at"]).replace(tzinfo=UTC),
            updated_at=datetime.fromisoformat(row["updated_at"]).replace(tzinfo=UTC),
        )
