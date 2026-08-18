"""
Dashboard utilities module.

This module provides shared utilities for the N100 Financial Intelligence Platform
dashboard, including database connections and query functions.
"""

from .db import (
    get_connection,
    get_companies,
    get_ratios,
    get_pl,
    get_bs,
    get_cf,
    get_sectors,
    get_peers,
    get_valuation,
    get_raw_statement,
    get_company_financial_health,
    get_company_pros_cons_signals,
    get_company_capital_allocation_detail,
    get_company_valuation_detail,
    get_company_peer_percentiles,
)

__all__ = [
    "get_connection",
    "get_companies",
    "get_ratios",
    "get_pl",
    "get_bs",
    "get_cf",
    "get_sectors",
    "get_peers",
    "get_valuation",
    "get_raw_statement",
    "get_company_financial_health",
    "get_company_pros_cons_signals",
    "get_company_capital_allocation_detail",
    "get_company_valuation_detail",
    "get_company_peer_percentiles",
]

__version__ = "1.0.0"