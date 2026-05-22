from __future__ import annotations

from enum import Enum
from typing import Any, Callable, Awaitable
from pydantic import BaseModel, Field


class ToolParameterType(str, Enum):
    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


class ToolParameter(BaseModel):
    name: str
    type: ToolParameterType
    description: str
    required: bool = True
    default: Any = None
    enum: list[Any] | None = None


class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: list[ToolParameter] = Field(default_factory=list)
    category: str = "general"
    tags: list[str] = Field(default_factory=list)
    
    def to_openai_schema(self) -> dict[str, Any]:
        properties = {}
        required = []
        
        for param in self.parameters:
            prop: dict[str, Any] = {
                "type": param.type.value,
                "description": param.description
            }
            if param.enum:
                prop["enum"] = param.enum
            if param.default is not None:
                prop["default"] = param.default
            
            properties[param.name] = prop
            if param.required:
                required.append(param.name)
        
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }


class ToolResultStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    DENIED = "denied"


class ToolResult(BaseModel):
    status: ToolResultStatus
    result: Any = None
    error_message: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    
    @classmethod
    def success(cls, result: Any, **kwargs: Any) -> ToolResult:
        return cls(status=ToolResultStatus.SUCCESS, result=result, **kwargs)
    
    @classmethod
    def error(cls, error: str, **kwargs: Any) -> ToolResult:
        return cls(status=ToolResultStatus.ERROR, error_message=error, **kwargs)
    
    @classmethod
    def timeout(cls, error: str = "Tool execution timeout", **kwargs: Any) -> ToolResult:
        return cls(status=ToolResultStatus.TIMEOUT, error_message=error, **kwargs)
    
    @classmethod
    def denied(cls, reason: str = "Tool execution denied", **kwargs: Any) -> ToolResult:
        return cls(status=ToolResultStatus.DENIED, error_message=reason, **kwargs)


ToolHandler = Callable[..., Awaitable[ToolResult]]