"""Helper functions for Lukawi Agent Framework."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def safe_path(path: str | Path) -> Path:
    """Convert to absolute resolved Path (Windows compatible).
    
    Args:
        path: String or Path object
    
    Returns:
        Resolved absolute Path
    """
    return Path(path).resolve()


def read_text(path: str | Path, encoding: str = "utf-8") -> str:
    """Read text from file.
    
    Args:
        path: File path
        encoding: File encoding
    
    Returns:
        File content as string
    
    Raises:
        FileNotFoundError: If file doesn't exist
        PermissionError: If no read permission
    """
    return safe_path(path).read_text(encoding=encoding)


def write_text(
    path: str | Path,
    content: str,
    encoding: str = "utf-8",
    create_parents: bool = True
) -> None:
    """Write text to file.
    
    Args:
        path: File path
        content: Content to write
        encoding: File encoding
        create_parents: Whether to create parent directories
    """
    file_path = safe_path(path)
    if create_parents:
        file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding=encoding)


def truncate_text(text: str, max_length: int = 1000, suffix: str = "...") -> str:
    """Truncate text to maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length including suffix
        suffix: Suffix to add when truncated
    
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def parse_json(text: str) -> Any | None:
    """Safely parse JSON string.
    
    Args:
        text: JSON string to parse
    
    Returns:
        Parsed object or None if invalid
    """
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None


def extract_json_from_text(text: str) -> dict | None:
    """Extract JSON object from text (may contain other content).
    
    Args:
        text: Text potentially containing JSON
    
    Returns:
        First JSON object found, or None
    """
    # Try to find JSON between curly braces
    start = text.find("{")
    if start == -1:
        return None
    
    # Find matching closing brace
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:i + 1])
                except json.JSONDecodeError:
                    return None
    
    return None
