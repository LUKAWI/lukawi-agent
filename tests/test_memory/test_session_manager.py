"""Tests for session manager."""

import pytest
from lukawi.llm.base import FunctionCall, Message, MessageRole, ToolCall
from lukawi.memory.session_manager import SessionManager


@pytest.fixture
async def manager():
    mgr = SessionManager(db_path=":memory:")
    await mgr.initialize()
    yield mgr
    await mgr.close()


class TestSessionManager:
    @pytest.mark.asyncio
    async def test_create_session(self, manager):
        session = await manager.create_session(name="Test Session")

        assert session.id is not None
        assert session.name == "Test Session"
        assert session.message_count == 0
        assert session.created_at is not None
        assert session.updated_at is not None

    @pytest.mark.asyncio
    async def test_list_sessions(self, manager):
        await manager.create_session(name="Session A")
        await manager.create_session(name="Session B")

        sessions = await manager.list_sessions()
        assert len(sessions) == 2

        names = [s.name for s in sessions]
        assert "Session A" in names
        assert "Session B" in names

    @pytest.mark.asyncio
    async def test_get_session(self, manager):
        created = await manager.create_session(name="My Session")

        fetched = await manager.get_session(created.id)
        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.name == "My Session"
        assert fetched.message_count == 0

    @pytest.mark.asyncio
    async def test_get_session_non_existent(self, manager):
        result = await manager.get_session("non-existent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_rename_session(self, manager):
        session = await manager.create_session(name="Old Name")

        success = await manager.rename_session(session.id, "New Name")
        assert success is True

        fetched = await manager.get_session(session.id)
        assert fetched is not None
        assert fetched.name == "New Name"

    @pytest.mark.asyncio
    async def test_rename_session_non_existent(self, manager):
        success = await manager.rename_session("non-existent", "New Name")
        assert success is False

    @pytest.mark.asyncio
    async def test_delete_session(self, manager):
        session = await manager.create_session(name="To Delete")

        success = await manager.delete_session(session.id)
        assert success is True

        fetched = await manager.get_session(session.id)
        assert fetched is None

    @pytest.mark.asyncio
    async def test_delete_session_non_existent(self, manager):
        success = await manager.delete_session("non-existent")
        assert success is False

    @pytest.mark.asyncio
    async def test_save_and_load_messages(self, manager):
        session = await manager.create_session(name="Chat Session")

        messages = [
            Message(role=MessageRole.USER, content="Hello"),
            Message(role=MessageRole.ASSISTANT, content="Hi there!"),
            Message(role=MessageRole.USER, content="How are you?"),
        ]
        await manager.save_messages(session.id, messages)

        loaded = await manager.load_messages(session.id)
        assert len(loaded) == 3
        assert loaded[0].role == MessageRole.USER
        assert loaded[0].content == "Hello"
        assert loaded[1].role == MessageRole.ASSISTANT
        assert loaded[1].content == "Hi there!"
        assert loaded[2].role == MessageRole.USER
        assert loaded[2].content == "How are you?"

    @pytest.mark.asyncio
    async def test_save_messages_updates_session_timestamp(self, manager):
        session = await manager.create_session(name="Chat")
        original_updated = session.updated_at

        messages = [Message(role=MessageRole.USER, content="Hi")]
        await manager.save_messages(session.id, messages)

        fetched = await manager.get_session(session.id)
        assert fetched is not None
        assert fetched.updated_at > original_updated

    @pytest.mark.asyncio
    async def test_save_messages_to_non_existent_session(self, manager):
        messages = [Message(role=MessageRole.USER, content="Hi")]

        with pytest.raises(ValueError, match="does not exist"):
            await manager.save_messages("non-existent", messages)

    @pytest.mark.asyncio
    async def test_get_message_count(self, manager):
        session = await manager.create_session(name="Counter Test")

        count = await manager.get_message_count(session.id)
        assert count == 0

        messages = [
            Message(role=MessageRole.USER, content="Hello"),
            Message(role=MessageRole.ASSISTANT, content="World"),
        ]
        await manager.save_messages(session.id, messages)

        count = await manager.get_message_count(session.id)
        assert count == 2

    @pytest.mark.asyncio
    async def test_cascade_delete(self, manager):
        session = await manager.create_session(name="Cascade Test")

        messages = [
            Message(role=MessageRole.USER, content="Msg 1"),
            Message(role=MessageRole.ASSISTANT, content="Msg 2"),
        ]
        await manager.save_messages(session.id, messages)

        assert await manager.get_message_count(session.id) == 2

        await manager.delete_session(session.id)

        loaded = await manager.load_messages(session.id)
        assert len(loaded) == 0

    @pytest.mark.asyncio
    async def test_save_and_load_with_tool_calls(self, manager):
        session = await manager.create_session(name="Tool Call Test")

        messages = [
            Message(
                role=MessageRole.ASSISTANT,
                content="Let me search for that",
                tool_calls=[
                    ToolCall(
                        id="call_123",
                        type="function",
                        function=FunctionCall(
                            name="web_fetch",
                            arguments='{"url": "https://example.com/news"}',
                        ),
                    ),
                ],
            ),
            Message(
                role=MessageRole.TOOL,
                content='{"results": ["news 1", "news 2"]}',
                tool_call_id="call_123",
            ),
            Message(
                role=MessageRole.ASSISTANT,
                reasoning_content="I found some news",
                content="Here are the latest news...",
            ),
        ]
        await manager.save_messages(session.id, messages)

        loaded = await manager.load_messages(session.id)
        assert len(loaded) == 3

        assert loaded[0].tool_calls is not None
        assert len(loaded[0].tool_calls) == 1
        assert loaded[0].tool_calls[0].id == "call_123"
        assert loaded[0].tool_calls[0].function.name == "web_fetch"
        assert loaded[0].tool_calls[0].function.arguments == '{"url": "https://example.com/news"}'

        assert loaded[1].tool_call_id == "call_123"
        assert loaded[1].content == '{"results": ["news 1", "news 2"]}'

        assert loaded[2].reasoning_content == "I found some news"
        assert loaded[2].content == "Here are the latest news..."

    @pytest.mark.asyncio
    async def test_message_count_in_session_info(self, manager):
        session = await manager.create_session(name="Count Test")

        fetched = await manager.get_session(session.id)
        assert fetched is not None
        assert fetched.message_count == 0

        messages = [Message(role=MessageRole.USER, content="M1")]
        await manager.save_messages(session.id, messages)

        fetched = await manager.get_session(session.id)
        assert fetched is not None
        assert fetched.message_count == 1

        messages = [Message(role=MessageRole.ASSISTANT, content="M2")]
        await manager.save_messages(session.id, messages)

        fetched = await manager.get_session(session.id)
        assert fetched is not None
        assert fetched.message_count == 2

    @pytest.mark.asyncio
    async def test_multiple_sessions_isolation(self, manager):
        s1 = await manager.create_session(name="Session 1")
        s2 = await manager.create_session(name="Session 2")

        await manager.save_messages(s1.id, [
            Message(role=MessageRole.USER, content="Hello from S1"),
        ])
        await manager.save_messages(s2.id, [
            Message(role=MessageRole.USER, content="Hello from S2"),
            Message(role=MessageRole.ASSISTANT, content="Reply in S2"),
        ])

        assert await manager.get_message_count(s1.id) == 1
        assert await manager.get_message_count(s2.id) == 2

        s1_fetched = await manager.get_session(s1.id)
        s2_fetched = await manager.get_session(s2.id)
        assert s1_fetched is not None
        assert s2_fetched is not None
        assert s1_fetched.message_count == 1
        assert s2_fetched.message_count == 2
