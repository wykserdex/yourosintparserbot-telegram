"""Structured logging configuration."""

import logging
import sys


def setup_logging(level: str = "INFO", json_format: bool = False) -> None:
    """Configures root logger with consistent formatting."""
    log_format = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )
