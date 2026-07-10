"""
settings.py

Application configuration settings.
"""

from pathlib import Path

from .constants import (
    PROJECT_ROOT,
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    DATABASE_PATH,
)

# =============================================================================
# APPLICATION
# =============================================================================

APP_NAME = "N100 Financial Intelligence Platform"

VERSION = "1.0.0"

AUTHOR = "Bluestock Internship"

DEBUG = True

# =============================================================================
# DATABASE
# =============================================================================

SQLITE_DATABASE = DATABASE_PATH

# =============================================================================
# ETL SETTINGS
# =============================================================================

READ_HEADER_CORE = 1          # Core datasets
READ_HEADER_SUPPORT = 0       # Supporting datasets

DATE_FORMAT = "%Y-%m"

DROP_DUPLICATES = True

REMOVE_EMPTY_ROWS = True

NORMALIZE_COMPANY_ID = True

# =============================================================================
# DATA QUALITY
# =============================================================================

MAX_NULL_PERCENTAGE = 30

ALLOW_NEGATIVE_PROFIT = True

ALLOW_NEGATIVE_CASHFLOW = True

VALIDATION_TOLERANCE = 0.01

# =============================================================================
# REPORT SETTINGS
# =============================================================================

DEFAULT_PDF_PAGE_SIZE = "A4"

DEFAULT_EXCEL_SHEET = "Financial_Report"

# =============================================================================
# STREAMLIT SETTINGS
# =============================================================================

DEFAULT_COMPANY = "TCS"

DEFAULT_THEME = "light"

# =============================================================================
# LOGGING
# =============================================================================

LOG_LEVEL = "INFO"

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(message)s"

# =============================================================================
# RANDOM SEED
# =============================================================================

RANDOM_STATE = 42