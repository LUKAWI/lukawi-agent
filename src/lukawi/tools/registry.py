"""Tool registry for managing tool registration and discovery."""

from __future__ import annotations

from typing import Callable

from lukawi.tools.base import ToolDefinition, ToolHandler


class ToolNotFoundError(Exception):
    pass


class ToolAlreadyRegisteredError(Exception):
    pass


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}
        self._handlers: dict[str, ToolHandler] = {}
    
    def register(
        self,
        definition: ToolDefinition,
        handler: ToolHandler
    ) -> None:
        if definition.name in self._tools:
            raise ToolAlreadyRegisteredError(
                f"Tool '{definition.name}' already registered"
            )
        
        self._tools[definition.name] = definition
        self._handlers[definition.name] = handler
    
    def register_decorator(
        self,
        definition: ToolDefinition
    ) -> Callable[[ToolHandler], ToolHandler]:
        def decorator(handler: ToolHandler) -> ToolHandler:
            self.register(definition, handler)
            return handler
        return decorator
    
    def get(self, name: str) -> tuple[ToolDefinition, ToolHandler]:
        if name not in self._tools:
            raise ToolNotFoundError(f"Tool '{name}' not found")
        
        return self._tools[name], self._handlers[name]
    
    def list_tools(self) -> list[ToolDefinition]:
        return list(self._tools.values())
    
    def has(self, name: str) -> bool:
        return name in self._tools
    
    def to_openai_schema(self) -> list[dict]:
        return [tool.to_openai_schema() for tool in self._tools.values()]
    
    def unregister(self, name: str) -> None:
        if name not in self._tools:
            raise ToolNotFoundError(f"Tool '{name}' not found")

        del self._tools[name]
        del self._handlers[name]

    def clear(self) -> None:
        self._tools.clear()
        self._handlers.clear()
    
    @property
    def count(self) -> int:
        return len(self._tools)
