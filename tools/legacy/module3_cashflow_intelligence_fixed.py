"""
src/module3_cashflow_intelligence_fixed.py

Module 3: Cash Flow Intelligence Engine (Legacy Fixed Helper Module)
"""

import sys
import sqlite3
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

import pandas as pd
import numpy as np

from src.config.constants import DATABASE_DIR
from src.config.settings import SQLITE_DATABASE

# Cash Flow column names
OCF_COLUMN = "cash_from_operating_activity"
OCF_ALT_COLUMN = "operating_activity"
CAPEX_COLUMN = "cash_from_investing_activity"
CAPEX_ALT_COLUMN = "investing_activity"
FCF_COLUMN = "free_cash_flow"
SALES_COLUMN = "sales"
NET_PROFIT_COLUMN = "net_profit"

# Capital Allocation Ratings
RATING_EXCELLENT = "EXCELLENT"
RATING_GOOD = "GOOD"
RATING_MODERATE = "MODERATE"
RATING_WEAK = "WEAK"
RATING_DISTRESSED = "DISTRESSED"


def _validate_numeric(value: Any, name: str) -> bool:
    """Validate that a value is numeric and not NaN or infinite."""
    if value is None or pd.isna(value):
        return False
    if isinstance(value, (int, float)):
        if np.isinf(value):
            return False
    return True


def calculate_free_cash_flow(cf_data: Dict[str, Any]) -> Optional[float]:
    """Calculate Free Cash Flow (FCF)."""
    ocf = cf_data.get(OCF_COLUMN) or cf_data.get(OCF_ALT_COLUMN)
    capex = cf_data.get(CAPEX_COLUMN) or cf_data.get(CAPEX_ALT_COLUMN) or 0
    if ocf is None:
        return None
    return round(float(ocf) - abs(float(capex)), 2)
