"""Session manager with in-memory message storage (model context) and SQLite session metadata."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

import aiosqlite

from lukawi.llm.base import Message


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
        now = datetime.now(UTC).isoformat()

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
            "SELECT id, name, created_at, updated_at FROM sessions ORDER BY updated_at DESC"
        ) as cursor:
            rows = await cursor.fetchall()

        return [self._row_to_session_info(row) for row in rows]

    async def get_session(self, session_id: str) -> SessionInfo | None:
        if not self._db:
            raise RuntimeError("Database not initialized")

        async with self._db.execute(
            "SELECT id, name, created_at, updated_at FROM sessions WHERE id = ?",
            (session_id,)
        ) as cursor:
            row = await cursor.fetchone()

        if row is None:
            return None

        return self._row_to_session_info(row)

    async def rename_session(self, session_id: str, name: str) -> bool:
        if not self._db:
            raise RuntimeError("Database not initialized")

        now = datetime.now(UTC).isoformat()
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

        now = datetime.now(UTC).isoformat()
        await self._db.execute(
            "UPDATE sessions SET updated_at = ? WHERE id = ?",
            (now, session_id)
        )
        await self._db.commit()

    async def load_messages(self, session_id: str) -> list[Message]:
        if not self._db:
            raise RuntimeError("Database not initialized")

        return list(self._messages_cache.get(session_id, []))

    async def get_message_count(self, session_id: str) -> int:
        if not self._db:
            raise RuntimeError("Database not initialized")

        return len(self._messages_cache.get(session_id, []))

    def _row_to_session_info(self, row: aiosqlite.Row) -> SessionInfo:
        sid = row["id"]
        return SessionInfo(
            id=sid,
            name=row["name"],
            message_count=len(self._messages_cache.get(sid, [])),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
