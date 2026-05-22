from __future__ import annotations

import asyncio
import copy
from dataclasses import dataclass
from typing import Any, Callable, Awaitable

from lukawi.tools.base import ToolDefinition, ToolResult


@dataclass
class HookDecision:
    allow: bool = True
    modified_params: dict[str, Any] | None = None
    reason: str = ""


PreHook = Callable[[ToolDefinition, dict[str, Any]], Awaitable[HookDecision]]
PostHook = Callable[[ToolDefinition, dict[str, Any], ToolResult], Awaitable[None]]


class ToolHooks:
    def __init__(self):
        self._pre_hooks: list[PreHook] = []
        self._post_hooks: list[PostHook] = []

    def add_pre_hook(self, hook: PreHook) -> None:
        self._pre_hooks.append(hook)

    def add_post_hook(self, hook: PostHook) -> None:
        self._post_hooks.append(hook)

    async def run_pre_hooks(
        self,
        definition: ToolDefinition,
        params: dict[str, Any],
    ) -> HookDecision:
        current_params = copy.deepcopy(params)

        for hook in self._pre_hooks:
            decision = await hook(definition, current_params)

            if not decision.allow:
                return decision

            if decision.modified_params is not None:
                current_params = decision.modified_params

        return HookDecision(allow=True, modified_params=current_params)

    async def run_post_hooks(
        self,
        definition: ToolDefinition,
        params: dict[str, Any],
        result: ToolResult,
    ) -> None:
        for hook in self._post_hooks:
            await hook(definition, params, result)


class ToolExecutor:
    def __init__(self, hooks: ToolHooks | None = None):
        self.hooks = hooks or ToolHooks()

    async def execute(
        self,
        definition: ToolDefinition,
        handler: Callable[..., Awaitable[ToolResult]],
        parameters: dict[str, Any],
        timeout: float = 30.0,
    ) -> ToolResult:
        decision = await self.hooks.run_pre_hooks(definition, parameters)

        if not decision.allow:
            return ToolResult.denied(decision.reason or "Execution denied by hook")

        params = parameters if decision.modified_params is None else decision.modified_params

        known_names = {p.name for p in definition.parameters}
        filtered = {k: v for k, v in params.items() if k in known_names}

        for param in definition.parameters:
            if param.required and param.name not in filtered:
                return ToolResult.error(f"Missing required parameter: {param.name}")
            if not param.required and param.name not in filtered and param.default is not None:
                filtered[param.name] = param.default

        try:
            result = await asyncio.wait_for(
                handler(**filtered),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            return ToolResult.timeout(f"Tool execution timed out after {timeout}s")
        except Exception as e:
            return ToolResult.error(f"Tool execution error: {str(e)}")

        await self.hooks.run_post_hooks(definition, params, result)

        return result
