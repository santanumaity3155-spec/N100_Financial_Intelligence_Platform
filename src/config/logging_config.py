"""
logging_config.py

Central logging configuration for the N100 Financial Intelligence Platform.
"""

import logging
from pathlib import Path

from .constants import LOG_DIR

# =============================================================================
# CREATE LOG DIRECTORY
# =============================================================================

LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "application.log"

# =============================================================================
# LOGGER CONFIGURATION
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# =============================================================================
# LOGGER FACTORY
# =============================================================================

def get_logger(name: str) -> logging.Logger:
    """
    Returns a configured logger.

    Parameters
    ----------
    name : str
        Usually __name__

    Returns
    -------
    logging.Logger
    """
    return logging.getLogger(name)