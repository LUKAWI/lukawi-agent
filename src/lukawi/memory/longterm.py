"""Long-term memory with SQLite storage."""

# NOTE: LongTermMemory is deprecated in favor of RAGManager with ChromaDB.
# It is retained as a fallback when rag.enabled=False in config.
# New code should use RAGManager via MemoryManager.rag.

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import aiosqlite


@dataclass
class Memory:
    id: str
    content: str
    metadata: dict[str, Any]
    user_id: str
    agent_id: str
    created_at: datetime
    updated_at: datetime
    score: float | None = None


class LongTermMemory:

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._db: aiosqlite.Connection | None = None

    async def initialize(self) -> None:
        self._db = await aiosqlite.connect(self.db_path)
        self._db.row_factory = aiosqlite.Row

        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                metadata TEXT,
                user_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await self._db.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_id ON memories(user_id)
        """)

        await self._db.execute("""
            CREATE INDEX IF NOT EXISTS idx_agent_id ON memories(agent_id)
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

    async def add(
        self,
        content: str,
        metadata: dict[str, Any] | None = None,
        user_id: str = "default",
        agent_id: str = "lukawi"
    ) -> str:
        if not self._db:
            raise RuntimeError("Database not initialized")

        memory_id = str(uuid.uuid4())
        now = datetime.now(UTC).replace(tzinfo=None).isoformat()

        await self._db.execute(
            """
            INSERT INTO memories (id, content, metadata, user_id, agent_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (memory_id, content, json.dumps(metadata or {}), user_id, agent_id, now, now)
        )

        await self._db.commit()
        return memory_id

    async def search(
        self,
        query: str,
        user_id: str | None = None,
        agent_id: str | None = None,
        limit: int = 10
    ) -> list[Memory]:
        if not self._db:
            raise RuntimeError("Database not initialized")

        safe_query = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        sql = "SELECT * FROM memories WHERE content LIKE ? ESCAPE '\\'"
        params: list[Any] = [f"%{safe_query}%"]

        if user_id:
            sql += " AND user_id = ?"
            params.append(user_id)

        if agent_id:
            sql += " AND agent_id = ?"
            params.append(agent_id)

        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        async with self._db.execute(sql, params) as cursor:
            rows = await cursor.fetchall()

        return [self._row_to_memory(row) for row in rows]

    async def get_all(
        self,
        user_id: str | None = None,
        agent_id: str | None = None,
        limit: int = 100
    ) -> list[Memory]:
        if not self._db:
            raise RuntimeError("Database not initialized")

        sql = "SELECT * FROM memories"
        params: list[Any] = []
        conditions = []

        if user_id:
            conditions.append("user_id = ?")
            params.append(user_id)

        if agent_id:
            conditions.append("agent_id = ?")
            params.append(agent_id)

        if conditions:
            sql += " WHERE " + " AND ".join(conditions)

        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        async with self._db.execute(sql, params) as cursor:
            rows = await cursor.fetchall()

        return [self._row_to_memory(row) for row in rows]

    async def update(self, memory_id: str, content: str) -> bool:
        if not self._db:
            raise RuntimeError("Database not initialized")

        now = datetime.now(UTC).replace(tzinfo=None).isoformat()

        cursor = await self._db.execute(
            "UPDATE memories SET content = ?, updated_at = ? WHERE id = ?",
            (content, now, memory_id)
        )

        await self._db.commit()
        return cursor.rowcount > 0

    async def delete(self, memory_id: str) -> bool:
        if not self._db:
            raise RuntimeError("Database not initialized")

        cursor = await self._db.execute(
            "DELETE FROM memories WHERE id = ?",
            (memory_id,)
        )

        await self._db.commit()
        return cursor.rowcount > 0

    async def clear(self, user_id: str | None = None) -> None:
        if not self._db:
            raise RuntimeError("Database not initialized")

        if user_id:
            await self._db.execute(
                "DELETE FROM memories WHERE user_id = ?",
                (user_id,)
            )
        else:
            await self._db.execute("DELETE FROM memories")

        await self._db.commit()

    def _row_to_memory(self, row: aiosqlite.Row) -> Memory:
        return Memory(
            id=row["id"],
            content=row["content"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            user_id=row["user_id"],
            agent_id=row["agent_id"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
