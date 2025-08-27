"""
Utility functions for ETL CLI.
"""

import logging
from pathlib import Path
from typing import Optional

from rich.logging import RichHandler


def setup_logging(verbose: bool = False) -> None:
    """Setup console-only logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Add rich handler for console output only
    console_handler = RichHandler(rich_tracebacks=True)
    console_handler.setLevel(level)
    formatter = logging.Formatter("%(message)s", datefmt="[%X]")
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
