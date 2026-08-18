"""
health.py

Health monitoring router for the N100 Financial Intelligence Platform API.
"""

import time
import sqlite3
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status

from src.config.settings import VERSION
from src.config.logging_config import get_logger
from src.database.connection import get_connection

logger = get_logger(__name__)

router = APIRouter(tags=["Health"])

START_TIME = time.time()

# 10 Authoritative project tables as defined by schema & ETL specifications
AUTHORITATIVE_TABLES = [
    "companies",
    "profit_loss",
    "balance_sheet",
    "cash_flow",
    "analysis",
    "documents",
    "pros_cons",
    "sectors",
    "stock_prices",
    "market_cap",
]


def get_uptime_seconds() -> float:
    """
    Calculate application uptime in seconds.

    Returns
    -------
    float
        Uptime in seconds since application initialization.
    """
    return round(time.time() - START_TIME, 2)


@router.get("/health", summary="Get API and Database Health Status")
def get_health() -> Dict[str, Any]:
    """
    Returns health status of the API and database row counts.

    Returns
    -------
    Dict[str, Any]
        Dictionary containing status, db_row_counts, uptime_seconds, and version.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        db_row_counts: Dict[str, int] = {}
        for table in AUTHORITATIVE_TABLES:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                db_row_counts[table] = int(count)
            except sqlite3.Error as err:
                logger.warning(f"Could not query row count for table '{table}': {err}")
                db_row_counts[table] = 0

        cursor.close()

        return {
            "status": "ok",
            "db_row_counts": db_row_counts,
            "uptime_seconds": get_uptime_seconds(),
            "version": VERSION,
        }

    except Exception as exc:
        logger.exception("Health check failed due to unexpected error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection error",
        ) from exc
