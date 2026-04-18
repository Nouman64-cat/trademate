"""
app/logger.py — Shared logging configuration.

Import `get_logger` anywhere to get a consistently-formatted logger.
"""

import logging
import sys


def configure_logging() -> None:
    """Call once at application startup. Forces configuration and simple formatting."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(name)s: %(message)s",
        force=True
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
