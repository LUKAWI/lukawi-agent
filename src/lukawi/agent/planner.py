"""Task planner for breaking down user requests into sub-tasks."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class SubTask:
    description: str
    status: TaskStatus = TaskStatus.PENDING
    result: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class TaskPlanner:

    def __init__(self, max_subtasks: int = 10):
        self.max_subtasks = max_subtasks

    def decompose(self, instruction: str) -> list[SubTask]:
        return []

    def next_pending(self, tasks: list[SubTask]) -> SubTask | None:
        for task in tasks:
            if task.status == TaskStatus.PENDING:
                return task
        return None
