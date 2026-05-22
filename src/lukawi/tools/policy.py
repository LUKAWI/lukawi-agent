from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from typing import Any

from lukawi.tools.base import ToolDefinition
from lukawi.config.models import ToolPolicyConfig, ToolProfileConfig


@dataclass
class PolicyContext:
    profile: str = "default"
    user_id: str = "default"
    session_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class ToolPolicy:
    def __init__(self, config: ToolPolicyConfig):
        self.config = config
    
    def filter_tools(
        self,
        tools: list[ToolDefinition],
        context: PolicyContext
    ) -> list[ToolDefinition]:
        profile = self.config.profiles.get(
            context.profile,
            self.config.profiles.get(self.config.default_profile)
        )
        
        if not profile:
            return tools
        
        result = []
        for tool in tools:
            if self._is_tool_allowed(tool.name, profile):
                result.append(tool)
        
        return result
    
    def is_allowed(
        self,
        tool_name: str,
        context: PolicyContext
    ) -> bool:
        profile = self.config.profiles.get(
            context.profile,
            self.config.profiles.get(self.config.default_profile)
        )
        
        if not profile:
            return True
        
        return self._is_tool_allowed(tool_name, profile)
    
    def _is_tool_allowed(
        self,
        tool_name: str,
        profile: ToolProfileConfig
    ) -> bool:
        for pattern in profile.denied_tools:
            if fnmatch.fnmatch(tool_name, pattern):
                return False
        
        for pattern in profile.allowed_tools:
            if pattern == "*" or fnmatch.fnmatch(tool_name, pattern):
                return True
        
        return False
