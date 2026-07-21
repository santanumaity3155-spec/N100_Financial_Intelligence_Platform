"""
constants.py

Global constants used throughout the N100 Financial Intelligence Platform.
Avoid hardcoding values in other modules.
"""

from pathlib import Path

# =============================================================================
# PROJECT ROOT
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# =============================================================================
# DATA DIRECTORIES
# =============================================================================

DATA_DIR = PROJECT_ROOT / "data"

RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EXPORT_DIR = DATA_DIR / "exports"
DATABASE_DIR = DATA_DIR / "database"

# =============================================================================
# DATABASE
# =============================================================================

DATABASE_NAME = "n100.db"
DATABASE_PATH = DATABASE_DIR / DATABASE_NAME

# =============================================================================
# REPORTS
# =============================================================================

REPORTS_DIR = PROJECT_ROOT / "reports"

COMPANY_REPORT_DIR = REPORTS_DIR / "company_reports"
SECTOR_REPORT_DIR = REPORTS_DIR / "sector_reports"
EXCEL_REPORT_DIR = REPORTS_DIR / "excel"
CHARTS_DIR = REPORTS_DIR / "charts"
SCREENSHOT_DIR = REPORTS_DIR / "screenshots"

# =============================================================================
# LOGS
# =============================================================================

LOG_DIR = PROJECT_ROOT / "logs"

# =============================================================================
# OUTPUT
# =============================================================================

OUTPUT_DIR = PROJECT_ROOT / "output"

# =============================================================================
# DOCUMENTATION
# =============================================================================

DOCS_DIR = PROJECT_ROOT / "docs"

# =============================================================================
# ASSETS
# =============================================================================

ASSETS_DIR = PROJECT_ROOT / "assets"

# =============================================================================
# STREAMLIT
# =============================================================================

STREAMLIT_PORT = 8501

# =============================================================================
# DATASET FILENAMES
# =============================================================================

RAW_DATASETS = {
    "companies": "companies.xlsx",
    "profit_loss": "profitandloss.xlsx",
    "balance_sheet": "balancesheet.xlsx",
    "cash_flow": "cashflow.xlsx",
    "analysis": "analysis.xlsx",
    "documents": "documents.xlsx",
    "pros_cons": "prosandcons.xlsx",
    "sectors": "sectors.xlsx",
    "stock_prices": "stock_prices.xlsx",
    "market_cap": "market_cap.xlsx",
    "financial_ratios": "financial_ratios.xlsx",
    "peer_groups": "peer_groups.xlsx",
}

# =============================================================================
# KPI CONFIGURATION
# =============================================================================

HEALTH_SCORE_MIN = 0
HEALTH_SCORE_MAX = 100

EXCELLENT_SCORE = 80
GOOD_SCORE = 65
AVERAGE_SCORE = 50
WEAK_SCORE = 35

# =============================================================================
# SUPPORTED FILE TYPES
# =============================================================================

EXCEL_EXTENSIONS = [".xlsx", ".xls"]

CSV_EXTENSION = ".csv"
