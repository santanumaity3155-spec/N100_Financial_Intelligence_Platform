#!/usr/bin/env python3
import os
os.makedirs("src/nlp", exist_ok=True)

MODULE = '''"""
pros_cons_generator.py

NLP Auto Pros/Cons Generator for the N100 Financial Intelligence Platform.

Sprint 5 - Module 2

Output:
    output/pros_cons_generated.csv
"""

from __future__ import annotations

import logging
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from src.config.constants import DATABASE_DIR, OUTPUT_DIR
from src.config.logging_config import get_logger

logger = get_logger(__name__)


DEFAULT_DB_PATH = OUTPUT_DIR / "n100_data.db"
PROS_CONS_CSV_PATH = OUTPUT_DIR / "pros_cons_generated.csv"

CONFIDENCE_BASE = 65.0
CONFIDENCE_MIN = 61.0
CONFIDENCE_MAX = 95.0
CONFIDENCE_DISTANCE_FACTOR = 30.0

FINANCIAL_SUB_SECTORS = {
    "Banks", "Financial Services", "NBFC",
    "Insurance - Life", "Insurance - General",
}

PRO_01_ROE_YEARS = 3
PRO_01_ROE_THRESHOLD = 20.0
PRO_02_FCF_YEARS = 5
PRO_04_REVENUE_CAGR_THRESHOLD = 15.0
PRO_05_OPM_THRESHOLD = 25.0
PRO_06_PAT_CAGR_THRESHOLD = 20.0
PRO_07_ICR_THRESHOLD = 10.0
PRO_08_DIV_YIELD_THRESHOLD = 2.0
PRO_09_EPS_CAGR_THRESHOLD = 15.0
PRO_10_ROE_IMPROVE_YEARS = 3

CON_01_DE_THRESHOLD = 2.0
CON_02_FCF_YEARS = 3
CON_03_OPM_DECLINE_YEARS = 3
CON_05_REVENUE_DECLINE_YEARS = 2
CON_06_ICR_THRESHOLD = 1.5
CON_08_DE_RISE_YEARS = 3

PART2 = '''

def load_company_data(company_id: str, conn: sqlite3.Connection) -> Dict[str, Any]:
    """Load all required financial data for a single company."""
    data: Dict[str, Any] = {
        "company_id": company_id,
        "sector": None,
        "sub_sector": None,
        "is_financial": False,
        "annual_kpis": [],
        "annual_pl": [],
        "annual_bs": [],
        "ttm_kpis": None,
        "cash_flow": [],
    }

    sub_sector = get_company_sector(company_id, conn)
    data["sub_sector"] = sub_sector
    data["is_financial"] = (
        sub_sector in FINANCIAL_SUB_SECTORS if sub_sector else False
    )

    try:
        cursor = conn.execute(
            """
            SELECT period, roe, roce, operating_margin,
                   debt_to_equity, interest_coverage, free_cash_flow,
                   dividend_yield, revenue_cagr, profit_cagr, eps_cagr
            FROM financial_kpis
            WHERE company_id = ? AND period != "TTM"
            ORDER BY period DESC
            """,
            (company_id,),
        )
        data["annual_kpis"] = [dict(row) for row in cursor.fetchall()]
    except Exception as exc:
        logger.warning("Failed to load financial_kpis for %s: %s", company_id, exc)

    try:
        cursor = conn.execute(
            """
            SELECT period, roe, roce, operating_margin,
                   debt_to_equity, interest_coverage, free_cash_flow,
                   dividend_yield, revenue_cagr, profit_cagr, eps_cagr
            FROM financial_kpis
            WHERE company_id = ? AND period = "TTM"
            LIMIT 1
            """,
            (company_id,),
        )
        row = cursor.fetchone()
        data["ttm_kpis"] = dict(row) if row else None
    except Exception as exc:
        logger.warning("Failed to load TTM KPIs for %s: %s", company_id, exc)

    try:
        cursor = conn.execute(
            """
            SELECT period, sales, operating_profit, opm_percentage,
                   other_income, interest, depreciation,
                   net_profit, eps, dividend_payout
            FROM profit_loss
            WHERE company_id = ?
            ORDER BY period DESC
            """,
            (company_id,),
        )
        data["annual_pl"] = [dict(row) for row in cursor.fetchall()]
    except Exception as exc:
        logger.warning("Failed to load profit_loss for %s: %s", company_id, exc)

    try:
        cursor = conn.execute(
            """
            SELECT period, borrowings, investments, total_assets,
                   equity_capital, reserves
            FROM balance_sheet
            WHERE company_id = ?
              AND period NOT LIKE "Sep%"
              AND period NOT LIKE "Jun%"
              AND period NOT LIKE "Dec%"
            ORDER BY period DESC
            """,
            (company_id,),
        )
        data["annual_bs"] = [dict(row) for row in cursor.fetchall()]
    except Exception as exc:
        logger.warning("Failed to load balance_sheet for %s: %s", company_id, exc)

    try:
        cursor = conn.execute(
            """
            SELECT period, cash_from_operating_activity,
                   cash_from_investing_activity, cash_from_financing_activity,
                   free_cash_flow
            FROM cash_flow
            WHERE company_id = ?
            ORDER BY period DESC
            """,
            (company_id,),
        )
        data["cash_flow"] = [dict(row) for row in cursor.fetchall()]
    except Exception as exc:
        logger.warning("Failed to load cash_flow for %s: %s", company_id, exc)

    return data

'''

with open('src/nlp/pros_cons_generator.py', 'a', encoding='utf-8') as f:
    f.write(PART2)
print('Part 2 written')

CON_09_EPS_DECLINE_YEARS = 3
CON_10_ROCE_THRESHOLD = 10.0
CON_11_NET_DEBT_EBITDA_RATIO = 3.0
CON_12_REVENUE_CAGR_THRESHOLD = 5.0


def get_connection(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def get_company_sector(company_id: str, conn: sqlite3.Connection) -> Optional[str]:
    try:
        cursor = conn.execute(
            "SELECT sub_sector FROM companies WHERE company_id = ? LIMIT 1",
            (company_id,),
        )
        row = cursor.fetchone()
        return row["sub_sector"] if row else None
    except Exception:
        return None

'''

with open('src/nlp/pros_cons_generator.py', 'w', encoding='utf-8') as f:
    f.write(MODULE)
print('Part 1 written')

print("started")
