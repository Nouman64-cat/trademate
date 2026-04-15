"""
app/logger.py — Shared logging configuration.

Import `get_logger` anywhere to get a consistently-formatted logger.
"""

import logging
import sys


def configure_logging() -> None:
    """Call once at application startup."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        datefmt="%H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
