"""Tests for session memory."""

import pytest
from lukawi.memory.session import SessionMemory
from lukawi.llm.base import Message, MessageRole


@pytest.fixture
def memory():
    return SessionMemory(max_messages=10)


class TestSessionMemory:
    def test_add_message(self, memory):
        msg = Message(role=MessageRole.USER, content="Hello")
        memory.add(msg)
        
        assert memory.message_count == 1
        assert memory.get_history()[0].content == "Hello"
    
    def test_max_messages(self):
        memory = SessionMemory(max_messages=5)
        
        for i in range(10):
            memory.add(Message(role=MessageRole.USER, content=f"Msg {i}"))
        
        assert memory.message_count == 5
        assert memory.get_history()[0].content == "Msg 5"
    
    def test_preserves_system_message(self):
        memory = SessionMemory(max_messages=5)
        
        memory.add(Message(role=MessageRole.SYSTEM, content="System"))
        for i in range(10):
            memory.add(Message(role=MessageRole.USER, content=f"Msg {i}"))
        
        assert memory.message_count == 5
        assert memory.get_history()[0].role == MessageRole.SYSTEM
    
    def test_get_history_limit(self, memory):
        for i in range(5):
            memory.add(Message(role=MessageRole.USER, content=f"Msg {i}"))
        
        history = memory.get_history(limit=3)
        assert len(history) == 3
        assert history[0].content == "Msg 2"
    
    def test_get_context_window(self, memory):
        memory.add(Message(role=MessageRole.USER, content="Short"))
        memory.add(Message(role=MessageRole.ASSISTANT, content="A" * 1000))
        memory.add(Message(role=MessageRole.USER, content="Another"))
        
        context = memory.get_context_window(max_tokens=100)
        assert len(context) < 3
    
    def test_clear(self, memory):
        memory.add(Message(role=MessageRole.USER, content="Hello"))
        memory.clear()
        
        assert memory.message_count == 0
        assert memory.get_history() == []
    
    def test_len(self, memory):
        assert len(memory) == 0
        
        memory.add(Message(role=MessageRole.USER, content="Hello"))
        assert len(memory) == 1
