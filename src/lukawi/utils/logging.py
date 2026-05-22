"""Logging setup for Lukawi Agent Framework."""

import logging
import sys
from pathlib import Path

from rich.logging import RichHandler


def setup_logging(
    level: str = "INFO",
    log_file: str | None = None,
    rich: bool = True
) -> None:
    """Set up logging configuration.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for log output
        rich: Whether to use Rich formatting
    """
    root = logging.getLogger()
    if root.handlers:
        return

    handlers: list[logging.Handler] = []
    
    if rich:
        handlers.append(
            RichHandler(
                rich_tracebacks=True,
                show_time=True,
                show_path=False
            )
        )
    else:
        handlers.append(logging.StreamHandler(sys.stdout))
    
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(str(log_path), encoding="utf-8"))
    
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(message)s" if rich else "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        logging.Logger instance
    """
    return logging.getLogger(name)
