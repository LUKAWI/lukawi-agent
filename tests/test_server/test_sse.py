"""Tests for SSE chat streaming endpoint — ensuring no traceback leaks."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from lukawi.server.sse import create_sse_router


class MockState:
    """Minimal mock state for SSE router testing."""

    def __init__(self, agent=None):
        self.agent = agent
        self.skill_loader = None
        self.active_skills = {}
        self.memory_manager = None
        self.model_registry = MagicMock()
        self.mcp_manager = MagicMock()


class ErrorAgent:
    """Mock agent whose run() raises an exception on first iteration."""

    async def run(self, message, history=None):
        raise RuntimeError("Agent internal error detail")
        yield  # pragma: no cover — makes this an async generator


def _parse_sse_events(text: str) -> list[dict]:
    """Parse raw SSE text into a list of event dicts.

    Each block between double-newlines is treated as one event.
    """
    events: list[dict] = []
    for block in text.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        event_data: dict = {}
        for line in block.split("\n"):
            if line.startswith("event: "):
                event_data["event"] = line[7:]
            elif line.startswith("data: "):
                event_data["data"] = json.loads(line[6:])
        if event_data:
            events.append(event_data)
    return events


class TestSseErrorEvents:
    """SSE error events must never leak full tracebacks to the frontend."""

    def test_command_error_no_traceback(self):
        """Command error event should contain only simple error, not traceback."""
        state = MockState(agent=MagicMock())
        router = create_sse_router(state)

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        with patch(
            "lukawi.server.sse._dispatch_command",
            side_effect=ValueError("Something went wrong"),
        ):
            response = client.post("/api/chat", json={"message": "/invalid-command"})

        assert response.status_code == 200
        events = _parse_sse_events(response.text)

        error_events = [e for e in events if e.get("event") == "error"]
        assert len(error_events) == 1, (
            f"Expected 1 error event, got {len(error_events)}"
        )

        error_msg = error_events[0]["data"]["error"]
        assert "Something went wrong" in error_msg
        assert "Traceback" not in error_msg
        assert "format_exc" not in error_msg

    def test_agent_run_error_no_traceback(self):
        """Agent run error event should contain only str(e), not traceback."""
        agent = ErrorAgent()
        state = MockState(agent=agent)
        router = create_sse_router(state)

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        response = client.post("/api/chat", json={"message": "hello"})

        assert response.status_code == 200
        events = _parse_sse_events(response.text)

        error_events = [e for e in events if e.get("event") == "error"]
        assert len(error_events) == 1, (
            f"Expected 1 error event, got {len(error_events)}"
        )

        error_msg = error_events[0]["data"]["error"]
        assert "Agent internal error detail" in error_msg
        assert "Traceback" not in error_msg
        assert "format_exc" not in error_msg
