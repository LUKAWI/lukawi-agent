"""Tests for memory manager."""

import pytest
from lukawi.memory.manager import MemoryManager
from lukawi.llm.base import Message, MessageRole


@pytest.fixture
async def manager():
    mem = MemoryManager(db_path=":memory:")
    await mem.initialize()
    yield mem
    await mem.close()


class TestMemoryManager:
    @pytest.mark.asyncio
    async def test_add_message(self, manager):
        msg = Message(role=MessageRole.USER, content="Hello")
        manager.add_message(msg)
        
        assert manager.session.message_count == 1
    
    @pytest.mark.asyncio
    async def test_save_conversation(self, manager):
        manager.add_message(Message(role=MessageRole.USER, content="Hello"))
        manager.add_message(Message(role=MessageRole.ASSISTANT, content="Hi!"))
        
        memory_id = await manager.save_conversation(user_id="test_user")
        
        assert memory_id is not None
        
        results = await manager.recall("conversation", user_id="test_user")
        assert len(results) == 1
    
    @pytest.mark.asyncio
    async def test_recall_empty(self, manager):
        results = await manager.recall("anything")
        assert results == []
    
    def test_get_context(self, manager):
        manager.add_message(Message(role=MessageRole.USER, content="Hello"))
        manager.add_message(Message(role=MessageRole.ASSISTANT, content="Hi!"))
        
        context = manager.get_context()
        assert len(context) == 2
    
    def test_clear_session(self, manager):
        manager.add_message(Message(role=MessageRole.USER, content="Hello"))
        manager.clear_session()
        
        assert manager.session.message_count == 0


class TestMemoryManagerDisabled:
    @pytest.mark.asyncio
    async def test_longterm_disabled(self):
        manager = MemoryManager(longterm_enabled=False)
        
        manager.add_message(Message(role=MessageRole.USER, content="Hello"))
        
        result = await manager.save_conversation()
        assert result is None
        
        results = await manager.recall("anything")
        assert results == []
