"""Tests for long-term memory."""

import pytest
from lukawi.memory.longterm import LongTermMemory, Memory


@pytest.fixture
async def memory():
    mem = LongTermMemory(db_path=":memory:")
    await mem.initialize()
    yield mem
    await mem.close()


class TestLongTermMemory:
    @pytest.mark.asyncio
    async def test_add_and_get(self, memory):
        memory_id = await memory.add(
            content="User likes Python",
            metadata={"source": "conversation"},
            user_id="user1"
        )

        assert memory_id is not None

        results = await memory.search("Python", user_id="user1")
        assert len(results) == 1
        assert results[0].content == "User likes Python"

    @pytest.mark.asyncio
    async def test_search(self, memory):
        await memory.add("User likes Python", user_id="user1")
        await memory.add("User likes JavaScript", user_id="user1")
        await memory.add("User likes Python", user_id="user2")

        results = await memory.search("Python")
        assert len(results) == 2

        results = await memory.search("Python", user_id="user1")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_get_all(self, memory):
        await memory.add("Memory 1", user_id="user1")
        await memory.add("Memory 2", user_id="user1")
        await memory.add("Memory 3", user_id="user2")

        all_memories = await memory.get_all()
        assert len(all_memories) == 3

        user1_memories = await memory.get_all(user_id="user1")
        assert len(user1_memories) == 2

    @pytest.mark.asyncio
    async def test_update(self, memory):
        memory_id = await memory.add("Original content")

        success = await memory.update(memory_id, "Updated content")
        assert success is True

        results = await memory.search("Updated")
        assert len(results) == 1
        assert results[0].content == "Updated content"

    @pytest.mark.asyncio
    async def test_delete(self, memory):
        memory_id = await memory.add("To be deleted")

        success = await memory.delete(memory_id)
        assert success is True

        results = await memory.search("deleted")
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_clear_all(self, memory):
        await memory.add("Memory A", user_id="user1")
        await memory.add("Memory B", user_id="user1")
        await memory.add("Memory C", user_id="user2")

        await memory.clear()
        results = await memory.get_all()
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_clear_by_user(self, memory):
        await memory.add("Memory A", user_id="user1")
        await memory.add("Memory B", user_id="user2")

        await memory.clear(user_id="user1")
        results = await memory.get_all()
        assert len(results) == 1
        assert results[0].user_id == "user2"
