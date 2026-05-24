from __future__ import annotations

from pathlib import Path
from typing import Any

from lukawi.tools.base import (
    ToolDefinition, ToolResult, ToolParameter, ToolParameterType
)

# Default denied directories for safety
DENIED_DIRS = [
    "/etc", "/sys", "/proc", "/dev",
    "C:\\Windows", "C:\\Windows\\System32",
]
ALLOWED_DIRS: list[str] = []  # Empty = all allowed (except denied)


def _check_path_access(target: Path) -> str | None:
    """Check if a path is allowed. Returns error message or None if OK."""
    resolved = str(target.resolve()).replace("\\", "/").lower()
    for denied in DENIED_DIRS:
        if resolved.startswith(denied.replace("\\", "/").lower()):
            return f"Access denied: '{target}' is in restricted directory"
    if ALLOWED_DIRS:
        for allowed in ALLOWED_DIRS:
            if resolved.startswith(allowed.replace("\\", "/").lower()):
                return None
        return f"Access denied: '{target}' is not in allowed directories"
    return None


READ_FILE_TOOL = ToolDefinition(
    name="read_file",
    description="Read content from a file",
    parameters=[
        ToolParameter(
            name="path",
            type=ToolParameterType.STRING,
            description="File path to read"
        ),
        ToolParameter(
            name="encoding",
            type=ToolParameterType.STRING,
            description="File encoding",
            required=False,
            default="utf-8"
        )
    ],
    category="filesystem",
    tags=["file", "read"]
)

WRITE_FILE_TOOL = ToolDefinition(
    name="write_file",
    description="Write content to a file",
    parameters=[
        ToolParameter(
            name="path",
            type=ToolParameterType.STRING,
            description="File path to write"
        ),
        ToolParameter(
            name="content",
            type=ToolParameterType.STRING,
            description="Content to write"
        ),
        ToolParameter(
            name="encoding",
            type=ToolParameterType.STRING,
            description="File encoding",
            required=False,
            default="utf-8"
        )
    ],
    category="filesystem",
    tags=["file", "write"]
)

EDIT_FILE_TOOL = ToolDefinition(
    name="edit_file",
    description="Edit a file by replacing text",
    parameters=[
        ToolParameter(
            name="path",
            type=ToolParameterType.STRING,
            description="File path to edit"
        ),
        ToolParameter(
            name="old_text",
            type=ToolParameterType.STRING,
            description="Text to replace"
        ),
        ToolParameter(
            name="new_text",
            type=ToolParameterType.STRING,
            description="Replacement text"
        ),
        ToolParameter(
            name="encoding",
            type=ToolParameterType.STRING,
            description="File encoding",
            required=False,
            default="utf-8"
        )
    ],
    category="filesystem",
    tags=["file", "edit"]
)

LIST_DIR_TOOL = ToolDefinition(
    name="list_dir",
    description="List directory contents",
    parameters=[
        ToolParameter(
            name="path",
            type=ToolParameterType.STRING,
            description="Directory path"
        ),
        ToolParameter(
            name="recursive",
            type=ToolParameterType.BOOLEAN,
            description="Recursive listing",
            required=False,
            default=False
        )
    ],
    category="filesystem",
    tags=["directory", "list"]
)


async def read_file_handler(
    path: str,
    encoding: str = "utf-8"
) -> ToolResult:
    try:
        file_path = Path(path).resolve()

        deny_reason = _check_path_access(file_path)
        if deny_reason:
            return ToolResult.denied(deny_reason)

        if not file_path.exists():
            return ToolResult.error(f"File not found: {path}")

        if not file_path.is_file():
            return ToolResult.error(f"Not a file: {path}")

        content = file_path.read_text(encoding=encoding)

        return ToolResult.success(
            result=content,
            metadata={"path": str(file_path), "size": len(content)}
        )

    except PermissionError:
        return ToolResult.error(f"Permission denied: {path}")
    except Exception as e:
        return ToolResult.error(f"Failed to read {path}: {str(e)}")


async def write_file_handler(
    path: str,
    content: str,
    encoding: str = "utf-8"
) -> ToolResult:
    try:
        file_path = Path(path).resolve()

        deny_reason = _check_path_access(file_path)
        if deny_reason:
            return ToolResult.denied(deny_reason)

        file_path.parent.mkdir(parents=True, exist_ok=True)

        file_path.write_text(content, encoding=encoding)

        return ToolResult.success(
            result=f"Wrote {len(content)} bytes to {path}",
            metadata={"path": str(file_path), "size": len(content)}
        )

    except PermissionError:
        return ToolResult.error(f"Permission denied: {path}")
    except Exception as e:
        return ToolResult.error(f"Failed to write {path}: {str(e)}")


async def edit_file_handler(
    path: str,
    old_text: str,
    new_text: str,
    encoding: str = "utf-8"
) -> ToolResult:
    try:
        file_path = Path(path).resolve()

        deny_reason = _check_path_access(file_path)
        if deny_reason:
            return ToolResult.denied(deny_reason)

        if not file_path.exists():
            return ToolResult.error(f"File not found: {path}")

        content = file_path.read_text(encoding=encoding)

        if old_text not in content:
            return ToolResult.error(f"Text not found in {path}")

        new_content = content.replace(old_text, new_text)
        file_path.write_text(new_content, encoding=encoding)

        return ToolResult.success(
            result=f"Replaced text in {path}",
            metadata={"path": str(file_path), "replacements": 1}
        )

    except PermissionError:
        return ToolResult.error(f"Permission denied: {path}")
    except Exception as e:
        return ToolResult.error(f"Failed to edit {path}: {str(e)}")


async def list_dir_handler(
    path: str,
    recursive: bool = False
) -> ToolResult:
    try:
        dir_path = Path(path).resolve()

        deny_reason = _check_path_access(dir_path)
        if deny_reason:
            return ToolResult.denied(deny_reason)

        if not dir_path.exists():
            return ToolResult.error(f"Directory not found: {path}")

        if not dir_path.is_dir():
            return ToolResult.error(f"Not a directory: {path}")

        entries = []

        if recursive:
            for item in dir_path.rglob("*"):
                entries.append({
                    "name": item.name,
                    "path": str(item),
                    "type": "directory" if item.is_dir() else "file"
                })
        else:
            for item in dir_path.iterdir():
                entries.append({
                    "name": item.name,
                    "path": str(item),
                    "type": "directory" if item.is_dir() else "file"
                })

        return ToolResult.success(
            result=entries,
            metadata={"path": str(dir_path), "count": len(entries)}
        )

    except PermissionError:
        return ToolResult.error(f"Permission denied: {path}")
    except Exception as e:
        return ToolResult.error(f"Failed to list {path}: {str(e)}")


def register_file_ops(registry: ToolRegistry) -> None:
    registry.register(READ_FILE_TOOL, read_file_handler)
    registry.register(WRITE_FILE_TOOL, write_file_handler)
    registry.register(EDIT_FILE_TOOL, edit_file_handler)
    registry.register(LIST_DIR_TOOL, list_dir_handler)
