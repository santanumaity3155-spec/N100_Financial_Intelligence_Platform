"""
pros_cons_generator.py

Sprint 5 – Module 2A: Auto Pros/Cons Generator FOUNDATION
=========================================================

This module builds the *architecture* required to later implement the
12 Pro rules (Module 2B) and 12 Con rules (Module 2C).

In Module 2A we deliberately do NOT implement any financial rule. We only
provide:

1. A reusable data-access layer over the real N100 database schema.
2. A normalized per-company financial context (latest + historical series).
3. Safe numeric/NaN/inf/zero-denominator handling helpers.
4. Generic historical trend helpers (improving/declining/consecutive/CAGR).
5. A generic rule engine (RuleResult + FinancialRule) with empty registries.
6. A confidence framework (validation + formatting + threshold).
7. Output-schema validation and company-coverage validation.
8. A financial-sector classification helper.
9. Structured logging and defensive error handling throughout.

No Pros/Cons are generated and no rule thresholds are encoded here.
"""

from __future__ import annotations

from collections import Counter
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from src.config.constants import DATABASE_DIR, OUTPUT_DIR, PROJECT_ROOT
from src.config.logging_config import get_logger
from src.database.connection import get_connection

logger = get_logger(__name__)

# =============================================================================
# CONSTANTS
# =============================================================================

# Output schema required by the eventual generator (company_id, type, rule_id,
# text, confidence_pct).
OUTPUT_COLUMNS: List[str] = [
    "company_id",
    "type",
    "rule_id",
    "text",
    "confidence_pct",
]

# Output row types
TYPE_PRO: str = "pro"
TYPE_CON: str = "con"
VALID_TYPES: Tuple[str, str] = (TYPE_PRO, TYPE_CON)

# Output file paths for Module 2D
PROS_CONS_GENERATED_CSV_PATH: Path = OUTPUT_DIR / "pros_cons_generated.csv"
PROS_CONS_COVERAGE_FAILURES_CSV_PATH: Path = OUTPUT_DIR / "pros_cons_coverage_failures.csv"

# Confidence framework
CONFIDENCE_MIN: float = 0.0
CONFIDENCE_MAX: float = 100.0
CONFIDENCE_THRESHOLD: float = 60.0  # default threshold for later rules
CONFIDENCE_DECIMALS: int = 2

# Table names used by the data layer
TABLE_COMPANIES: str = "companies"
TABLE_SECTORS: str = "sectors"
TABLE_PROFIT_LOSS: str = "profit_loss"
TABLE_BALANCE_SHEET: str = "balance_sheet"
TABLE_CASH_FLOW: str = "cash_flow"
TABLE_ANALYSIS: str = "analysis"
TABLE_FINANCIAL_KPIS: str = "financial_kpis"
TABLE_FINANCIAL_RATIOS: str = "financial_ratios"
TABLE_MARKET_CAP: str = "market_cap"

# Period sentinel used for trailing (non-annual) values.
PERIOD_TTM: str = "TTM"

# Regex to extract a calendar year from a period string like "Mar 2024".
_YEAR_REGEX: re.Pattern = re.compile(r"(?<!\d)(\d{4})(?!\d)")

# -----------------------------------------------------------------------------
# Financial sub-sectors
#
# The `sectors.broad_sector` column is NULL in the live database, so financial
# classification must rely on `sectors.sub_sector`. This set reflects the
# actual sub_sector values present in the DB plus common alternate labels so
# the helper stays robust if the source data changes.
# -----------------------------------------------------------------------------
FINANCIAL_SUB_SECTORS: frozenset = frozenset({
    "Private Banks",
    "Public Sector Banks",
    "Consumer Finance",
    "Speciality Finance",
    "Diversified Financials",
    "Life Insurance",
    "General Insurance",
    # Common alternate labels (defensive)
    "Banks",
    "NBFC",
    "Insurance - Life",
    "Insurance - General",
    "Financial Services",
    "Asset Management",
})

# -----------------------------------------------------------------------------
# Primary metric → candidate source columns (highest priority first).
#
# For every metric that future Pro/Con rules may consult, we list the candidate
# (table, column) locations from which the value may be drawn. The context
# builder picks the first non-null candidate found for the relevant period.
# Source order reflects the project's data-quality reality.
# -----------------------------------------------------------------------------
METRIC_SOURCES: Dict[str, List[Tuple[str, str]]] = {
    "roe": [
        (TABLE_FINANCIAL_KPIS, "roe"),
        (TABLE_FINANCIAL_RATIOS, "roe"),
        (TABLE_COMPANIES, "roe_percentage"),
    ],
    "roce": [
        (TABLE_FINANCIAL_KPIS, "roce"),
        (TABLE_COMPANIES, "roce_percentage"),
    ],
    "debt_to_equity": [
        (TABLE_FINANCIAL_KPIS, "debt_to_equity"),
        (TABLE_FINANCIAL_RATIOS, "debt_to_equity"),
    ],
    "interest_coverage": [(TABLE_FINANCIAL_KPIS, "interest_coverage")],
    "free_cash_flow": [
        (TABLE_CASH_FLOW, "free_cash_flow"),
        (TABLE_FINANCIAL_KPIS, "free_cash_flow"),
    ],
    "revenue": [(TABLE_PROFIT_LOSS, "sales")],
    "net_profit": [(TABLE_PROFIT_LOSS, "net_profit")],
    "operating_profit": [(TABLE_PROFIT_LOSS, "operating_profit")],
    "opm": [(TABLE_PROFIT_LOSS, "opm_percentage")],
    "eps": [(TABLE_PROFIT_LOSS, "eps")],
    "dividend_payout": [(TABLE_PROFIT_LOSS, "dividend_payout")],
    "dividend_yield": [
        (TABLE_MARKET_CAP, "dividend_yield"),
        (TABLE_FINANCIAL_KPIS, "dividend_yield"),
    ],
    "borrowings": [(TABLE_BALANCE_SHEET, "borrowings")],
    "total_assets": [(TABLE_BALANCE_SHEET, "total_assets")],
    "reserves": [(TABLE_BALANCE_SHEET, "reserves")],
    "equity_capital": [(TABLE_BALANCE_SHEET, "equity_capital")],
    "investments": [(TABLE_BALANCE_SHEET, "investments")],
    "depreciation": [(TABLE_PROFIT_LOSS, "depreciation")],
    "cfo": [(TABLE_CASH_FLOW, "cash_from_operating_activity")],
    "cff": [(TABLE_CASH_FLOW, "cash_from_financing_activity")],
    "net_debt": [(TABLE_BALANCE_SHEET, "net_debt")],  # computed in merge
    "ebitda": [(TABLE_PROFIT_LOSS, "ebitda")],        # computed in merge
    "revenue_cagr": [(TABLE_FINANCIAL_KPIS, "revenue_cagr")],
    "profit_cagr": [(TABLE_FINANCIAL_KPIS, "profit_cagr")],
    "eps_cagr": [(TABLE_FINANCIAL_KPIS, "eps_cagr")],
}

# Manually derived metrics (computed at merge time from raw columns)
_DERIVED_METRICS: Dict[str, Tuple[str, str, str]] = {
    # metric: (left_operand, right_operand, kind)
    "net_debt": ("borrowings", "investments", "subtract"),
    "ebitda": ("operating_profit", "depreciation", "add"),
}

# Minimum number of distinct years a company needs to expose its history
# (used by has_minimum_history / coverage reporting only).
MIN_HISTORY_YEARS: int = 3

# =============================================================================
# CONNECTION HELPERS
# =============================================================================


def _get_connection_safe():
    """Return the shared connection or ``None`` if the database is unavailable.

    Never raises: suitable for graceful degradation across the data layer.
    """
    try:
        return get_connection()
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Database connection unavailable: %s", exc)
        return None


# =============================================================================
# GENERIC DATA FRAME LOADER
# =============================================================================


def _load_table(
    table: str,
    columns: Optional[Sequence[str]] = None,
    conn: Optional[Any] = None,
) -> pd.DataFrame:
    """Load a table into a DataFrame, returning an empty frame on any failure.

    Parameters
    ----------
    table : str
        Name of the table to load.
    columns : Sequence[str], optional
        Columns to select. If provided, missing columns are dropped gracefully.
    conn : sqlite3.Connection, optional
        Connection to use; defaults to the shared connection.

    Returns
    -------
    pd.DataFrame
        Loaded data, or an empty DataFrame when the table/columns are missing
        or the database is unavailable.
    """
    start = time.time()
    conn = conn if conn is not None else _get_connection_safe()
    if conn is None:
        logger.warning("Cannot load table '%s': no database connection", table)
        return pd.DataFrame()

    select_cols = "*"
    all_cols: List[str] = []

    if columns:
        # Discover which requested columns actually exist.
        try:
            info = conn.execute(f"PRAGMA table_info('{table}')").fetchall()
            existing = {row[1] for row in info}
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Could not inspect table '%s': %s", table, exc)
            existing = set()
        available = [c for c in columns if c in existing]
        all_cols = available
        if not available:
            logger.warning("Table '%s' has none of the requested columns %s", table, list(columns))
            return pd.DataFrame(columns=list(columns))
        select_cols = ", ".join(f'"{c}"' for c in available)

    query = f'SELECT {select_cols} FROM "{table}"'
    try:
        df = pd.read_sql_query(query, conn)
    except Exception as exc:
        logger.warning("Failed to load table '%s': %s", table, exc)
        # Return a frame with the requested (but empty) columns when possible.
        wanted = list(columns) if columns else []
        return pd.DataFrame(columns=wanted)

    logger.info(
        "Loaded %d rows from '%s' in %.3fs",
        len(df), table, time.time() - start,
    )
    return df


def _check_table_exists(table: str, conn: Optional[Any] = None) -> bool:
    """Return True if *table* exists in the database (False on any error)."""
    conn = conn if conn is not None else _get_connection_safe()
    if conn is None:
        return False
    try:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        ).fetchone()
        return row is not None
    except Exception:
        return False


# =============================================================================
# DOMAIN-SPECIFIC LOADERS
# =============================================================================


def _empty_frame(columns: Sequence[str]) -> pd.DataFrame:
    """Return an empty DataFrame with the given columns (deterministic)."""
    return pd.DataFrame(columns=list(columns))


def load_companies(conn: Optional[Any] = None) -> pd.DataFrame:
    """Load the company master table.

    Returns company identification columns used to build a company context:
    ``company_id, company_name, sector, industry, roce_percentage,
    roe_percentage``. Returns an empty DataFrame when the table is missing.
    """
    cols = [
        "company_id", "company_name", "sector", "industry",
        "roce_percentage", "roe_percentage",
    ]
    df = _load_table(TABLE_COMPANIES, cols, conn=conn)
    if df.empty:
        logger.warning("No company records loaded")
        return _empty_frame(cols)
    df["company_id"] = df["company_id"].astype(str).str.strip().str.upper()
    logger.info("Loaded %d companies", len(df))
    return df


def load_sectors(conn: Optional[Any] = None) -> pd.DataFrame:
    """Load sector classification (broad_sector + sub_sector)."""
    cols = ["company_id", "broad_sector", "sub_sector"]
    df = _load_table(TABLE_SECTORS, cols, conn=conn)
    if df.empty:
        logger.warning("No sector records loaded")
        return _empty_frame(cols)
    df["company_id"] = df["company_id"].astype(str).str.strip().str.upper()
    logger.info("Loaded %d sector records", len(df))
    return df


def load_analysis_data(conn: Optional[Any] = None) -> pd.DataFrame:
    """Load textual analysis metrics (Sprint 5 Module 1 raw source).

    Columns: ``company_id, period, compounded_sales_growth,
    compounded_profit_growth, roe, stock_price_cagr``.
    """
    cols = [
        "company_id", "period",
        "compounded_sales_growth", "compounded_profit_growth",
        "roe", "stock_price_cagr",
    ]
    df = _load_table(TABLE_ANALYSIS, cols, conn=conn)
    if df.empty:
        logger.info("No analysis records loaded (empty analysis table)")
        return _empty_frame(cols)
    df["company_id"] = df["company_id"].astype(str).str.strip().str.upper()
    logger.info("Loaded %d analysis records (Module 1 source)", len(df))
    return df


def load_cashflow_data(conn: Optional[Any] = None) -> pd.DataFrame:
    """Load cash-flow statement data.

    Columns: ``company_id, period, cash_from_operating_activity,
    cash_from_financing_activity, free_cash_flow, net_cash_flow``.
    """
    cols = [
        "company_id", "period",
        "cash_from_operating_activity", "cash_from_financing_activity",
        "free_cash_flow", "net_cash_flow",
    ]
    df = _load_table(TABLE_CASH_FLOW, cols, conn=conn)
    if df.empty:
        logger.warning("No cash-flow records loaded")
        return _empty_frame(cols)
    df["company_id"] = df["company_id"].astype(str).str.strip().str.upper()
    logger.info("Loaded %d cash-flow records", len(df))
    return df


def load_ratio_data(conn: Optional[Any] = None) -> pd.DataFrame:
    """Load the rich ratio/KPI table, preferring ``financial_kpis`` but falling back to
    ``financial_ratios`` for missing data.

    Provides ROE, ROCE, leverage, interest coverage, CAGR and dividend metrics
    with per-period granularity.
    """
    # Target columns we want in the final dataframe
    target_cols = [
        "company_id", "period", "roe", "roce", "roa", "debt_to_equity",
        "interest_coverage", "free_cash_flow", "operating_cash_flow",
        "dividend_yield", "revenue_cagr", "profit_cagr", "eps_cagr",
    ]

    # Load financial_kpis with target columns (missing columns will be added as None)
    df_kpis = _load_table(TABLE_FINANCIAL_KPIS, target_cols, conn=conn)
    if not df_kpis.empty:
        df_kpis["company_id"] = df_kpis["company_id"].astype(str).str.strip().str.upper()
        # Ensure all target columns exist (they should, but safe)
        for col in target_cols:
            if col not in df_kpis.columns:
                df_kpis[col] = None

    # Load financial_ratios with its specific columns, then map to target columns
    ratio_cols = [
        "company_id", "period", "roe", "roa", "debt_to_equity", "dividend_yield"
    ]
    df_ratios = _load_table(TABLE_FINANCIAL_RATIOS, ratio_cols, conn=conn)
    if not df_ratios.empty:
        df_ratios["company_id"] = df_ratios["company_id"].astype(str).str.strip().str.upper()
        # Ensure all target columns exist, filling missing with None
        for col in target_cols:
            if col not in df_ratios.columns:
                df_ratios[col] = None
        # Keep only target columns (in case extra columns exists)
        df_ratios = df_ratios[target_cols]
    else:
        df_ratios = pd.DataFrame(columns=target_cols)

    # Combine: prefer kpis rows, then ratios rows for missing (company_id, period)
    if df_kpis.empty and df_ratios.empty:
        logger.warning("No ratio/KPI records loaded")
        return pd.DataFrame(columns=target_cols)

    # Tag source for logging (optional)
    if not df_kpis.empty:
        df_kpis = df_kpis.assign(_source=0)
    if not df_ratios.empty:
        df_ratios = df_ratios.assign(_source=1)

    # Concatenate and sort by source so kpis comes first
    combined = pd.concat([df_kpis, df_ratios], ignore_index=True)
    # Sort by company_id, period, and _source so that kpis (0) comes before ratios (1) for same key
    combined = combined.sort_values(
        ["company_id", "period", "_source"],
        na_position='last'
    ).reset_index(drop=True)
    # Drop duplicates keeping the first (which is from kpis if available)
    combined = combined.drop_duplicates(subset=["company_id", "period"], keep="first")
    # Drop the helper column
    combined = combined.drop(columns=["_source"], errors='ignore')

    logger.info(
        "Loaded ratio data: %d financial_kpis, %d financial_ratios, %d combined",
        len(df_kpis) if not df_kpis.empty else 0,
        len(df_ratios) if not df_ratios.empty else 0,
        len(combined)
    )
    return combined


def load_balance_sheet(conn: Optional[Any] = None) -> pd.DataFrame:
    """Load balance-sheet data.

    Columns: ``company_id, period, borrowings, reserves, equity_capital,
    share_capital, investments, total_assets``.
    """
    cols = [
        "company_id", "period", "borrowings", "reserves", "equity_capital",
        "share_capital", "investments", "total_assets",
    ]
    df = _load_table(TABLE_BALANCE_SHEET, cols, conn=conn)
    if df.empty:
        logger.warning("No balance-sheet records loaded")
        return _empty_frame(cols)
    df["company_id"] = df["company_id"].astype(str).str.strip().str.upper()
    logger.info("Loaded %d balance-sheet records", len(df))
    return df


def load_market_cap(conn: Optional[Any] = None) -> pd.DataFrame:
    """Load market-cap data, the preferred source of dividend yield."""
    cols = ["company_id", "period", "dividend_yield"]
    df = _load_table(TABLE_MARKET_CAP, cols, conn=conn)
    if df.empty:
        logger.info("No market-cap records loaded")
        return _empty_frame(cols)
    df["company_id"] = df["company_id"].astype(str).str.strip().str.upper()
    logger.info("Loaded %d market-cap records", len(df))
    return df


def load_profit_loss(conn: Optional[Any] = None) -> pd.DataFrame:
    """Load profit & loss data.

    Columns: ``company_id, period, sales, operating_profit, net_profit,
    opm_percentage, eps, dividend_payout, depreciation, interest``.
    """
    cols = [
        "company_id", "period", "sales", "operating_profit", "net_profit",
        "opm_percentage", "eps", "dividend_payout", "depreciation", "interest",
    ]
    df = _load_table(TABLE_PROFIT_LOSS, cols, conn=conn)
    if df.empty:
        logger.warning("No profit & loss records loaded")
        return _empty_frame(cols)
    df["company_id"] = df["company_id"].astype(str).str.strip().str.upper()
    logger.info("Loaded %d profit & loss records", len(df))
    return df


def load_financial_data(conn: Optional[Any] = None) -> Dict[str, pd.DataFrame]:
    """Load every financial dataset used by the pros/cons foundation.

    Parameters
    ----------
    conn : sqlite3.Connection, optional
        Connection to use.

    Returns
    -------
    Dict[str, pd.DataFrame]
        Mapping of logical dataset name → DataFrame. Missing datasets map to
        empty frames rather than raising.
    """
    return {
        "companies": load_companies(conn),
        "sectors": load_sectors(conn),
        "profit_loss": load_profit_loss(conn),
        "balance_sheet": load_balance_sheet(conn),
        "cash_flow": load_cashflow_data(conn),
        "ratios": load_ratio_data(conn),
        "market_cap": load_market_cap(conn),
        "analysis": load_analysis_data(conn),
    }


# =============================================================================
# PERIOD PARSING
# =============================================================================


def parse_period(period: Any) -> Optional[int]:
    """Extract a calendar year from a financial period string.

    Handles formats observed in the database:
    - ``"Mar 2024"`` / ``"Sep 2024"`` → 2024
    - ``"2024"``                     → 2024
    - ``"Mar 2023 15"`` (artifact)   → 2023
    - ``"TTM"`` / ``None`` / NaN     → ``None`` (trailing, non-annual)

    Parameters
    ----------
    period : Any
        Raw period value.

    Returns
    -------
    Optional[int]
        The calendar year, or ``None`` when it cannot be determined or the
        period is a trailing (non-annual) value.
    """
    if period is None or (isinstance(period, float) and np.isnan(period)):
        return None
    raw = str(period).strip()
    if not raw or raw.upper() == PERIOD_TTM:
        return None
    match = _YEAR_REGEX.search(raw)
    if not match:
        return None
    try:
        return int(match.group(1))
    except (ValueError, TypeError):
        return None


# =============================================================================
# SAFE DATA HANDLING
# =============================================================================


def safe_float(value: Any) -> Optional[float]:
    """Convert *value* to a float, returning ``None`` for any invalid input.

    Treats ``None``, ``NaN``, ``+/-inf``, empty strings and non-numeric values
    as invalid. **Missing financial data is never coerced to zero** here; callers
    that need a zero fallback must pass an explicit default.
    """
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        if value == "":
            return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if np.isnan(number) or np.isinf(number):
        return None
    return number


def is_valid_number(value: Any) -> bool:
    """Return True if *value* is a finite, non-NaN numeric value."""
    return safe_float(value) is not None


def safe_divide(numerator: Any, denominator: Any) -> Optional[float]:
    """Divide *numerator* by *denominator*, guarding zero/NaN/inf denominators.

    Returns ``None`` instead of raising when the denominator is zero or invalid,
    or when the numerator is invalid. Do NOT convert a zero denominator into a
    fabricated ratio.
    """
    num = safe_float(numerator)
    den = safe_float(denominator)
    if num is None or den is None or den == 0.0:
        return None
    result = num / den
    if np.isinf(result) or np.isnan(result):
        return None
    return result


def get_latest_value(values: Sequence[Any]) -> Optional[float]:
    """Return the last *valid* numeric value in *values* (None if none valid).

    Iterates from the end, skipping ``NaN``/``None``/invalid entries so a gap
    in recent data does not yield ``None`` when an earlier valid value exists.
    """
    for value in reversed(list(values)):
        number = safe_float(value)
        if number is not None:
            return number
    return None


def get_historical_values(
    values: Sequence[Any],
    max_len: Optional[int] = None,
) -> List[float]:
    """Return the ordered list of valid numeric values from *values*.

    Parameters
    ----------
    values : Sequence[Any]
        Source values in chronological (oldest → newest) order.
    max_len : int, optional
        If given, keep only the most recent ``max_len`` values.

    Returns
    -------
    List[float]
        Empty list when there are no valid numeric values.
    """
    cleaned: List[float] = []
    for value in values:
        number = safe_float(value)
        if number is not None:
            cleaned.append(number)
    if max_len is not None:
        cleaned = cleaned[-max_len:]
    return cleaned


def has_minimum_history(values: Sequence[Any], min_years: int = MIN_HISTORY_YEARS) -> bool:
    """Return True when *values* contain at least ``min_years`` valid numbers."""
    return len(get_historical_values(values)) >= min_years


def has_consecutive_years(years: Sequence[int], required: int,
                          step: int = 1) -> bool:
    """Return True when *years* contain ``required`` consecutive values.

    Parameters
    ----------
    years : Sequence[int]
        Sorted (or unsorted) collection of calendar years.
    required : int
        Number of consecutive years required (e.g. 3 or 5).
    step : int, optional
        Gap between consecutive years (normally 1).

    Returns
    -------
    bool
        True if any run of ``required`` years with step *step* exists.
    """
    if required <= 0:
        return True
    distinct = sorted(set(int(y) for y in years))
    if len(distinct) < required:
        return False
    run = 1
    for prev, curr in zip(distinct, distinct[1:]):
        run = run + 1 if curr - prev == step else 1
        if run >= required:
            return True
    return False


# =============================================================================
# HISTORICAL TREND HELPERS
#
# These helpers evaluate *generic* historical patterns only. No financial
# threshold (e.g. "ROE > 20%") may be encoded here; those belong to the
# individual rule implementations (Modules 2B/2C).
# =============================================================================


def get_last_n_years(years: Sequence[int], n: int) -> List[int]:
    """Return the ``n`` most recent distinct years, oldest first.

    Parameters
    ----------
    years : Sequence[int]
        Collection of calendar years (any order).
    n : int
        Number of most recent years to return.

    Returns
    -------
    List[int]
        Sorted list of up to ``n`` distinct years.
    """
    distinct = sorted(set(int(y) for y in years))
    return distinct[-n:]


def get_metric_history(
    context: Any,
    metric: str,
    years: Optional[Sequence[int]] = None,
    max_len: Optional[int] = None,
) -> List[float]:
    """Extract a company's metric history from a ``CompanyContext``.

    Parameters
    ----------
    context : CompanyContext
        Context exposing ``context.history`` / ``context.latest``.
    metric : str
        Metric key (e.g. ``"roe"``, ``"revenue"``, ``"borrowings"``).
    years : Sequence[int], optional
        If given, restrict the history to these years.
    max_len : int, optional
        If given, keep only the most recent ``max_len`` valid values.

    Returns
    -------
    List[float]
        Valid numeric values in chronological order (may be empty).
    """
    series = getattr(context, "history", {}).get(metric, [])
    if years is not None:
        allowed = set(int(y) for y in years)
        by_year = getattr(context, "history_years", [])
        series = [v for y, v in zip(by_year, series) if y in allowed]
    return get_historical_values(series, max_len=max_len)


def check_consecutive_condition(
    values: Sequence[Any],
    predicate: Callable[[float], bool],
    required: int,
    max_len: Optional[int] = None,
) -> bool:
    """Return True when ``required`` *consecutive* values satisfy *predicate*.

    An invalid value (``None``, ``NaN``) will break the consecutive run.

    Parameters
    ----------
    values : Sequence[Any]
        Values in chronological order (invalid entries are skipped).
    predicate : Callable[[float], bool]
        Boolean condition tested over valid numeric values.
    required : int
        Number of consecutive satisfied values required.
    max_len : int, optional
        If given, evaluate only the most recent ``max_len`` valid values.

    Returns
    -------
    bool
        True if any run of length ``required`` satisfies the predicate.
    """
    if required <= 0:
        return True

    series = list(values)
    if max_len is not None:
        series = series[-max_len:]

    if len(series) < required:
        return False

    run = 0
    for raw_value in series:
        value = safe_float(raw_value)
        if value is not None and predicate(value):
            run += 1
        else:
            run = 0
        if run >= required:
            return True
    return False


def is_improving(values: Sequence[Any], periods: int = 3) -> bool:
    """Return True when the most recent ``periods`` values are increasing.

    Compare each year against the previous one; every consecutive step must be
    strictly upward. An invalid value (``None``, ``NaN``) in the sequence will
    cause this to return False. Returns False when insufficient history exists.
    """
    if len(values) < periods:
        return False

    recent_raw = list(values)[-periods:]
    recent_safe = [safe_float(v) for v in recent_raw]

    # Any invalid value in the sequence breaks the trend.
    if any(v is None for v in recent_safe):
        return False

    return all(next_val > prev for prev, next_val in zip(recent_safe, recent_safe[1:]))


def is_declining(values: Sequence[Any], periods: int = 3) -> bool:
    """Return True when the most recent ``periods`` values are decreasing.

    Compare each year against the previous one; every consecutive step must be
    strictly downward. An invalid value (``None``, ``NaN``) in the sequence will
    cause this to return False. Returns False when insufficient history exists.
    """
    if len(values) < periods:
        return False

    recent_raw = list(values)[-periods:]
    recent_safe = [safe_float(v) for v in recent_raw]

    # Any invalid value in the sequence breaks the trend.
    if any(v is None for v in recent_safe):
        return False

    return all(next_val < prev for prev, next_val in zip(recent_safe, recent_safe[1:]))


def count_consecutive_positive(values: Sequence[Any], max_len: Optional[int] = None) -> int:
    """Count the length of the longest *trailing* run of positive values."""
    cleaned = get_historical_values(values, max_len=max_len)
    count = 0
    for value in reversed(cleaned):
        if value > 0:
            count += 1
        else:
            break
    return count


def count_consecutive_negative(values: Sequence[Any], max_len: Optional[int] = None) -> int:
    """Count the length of the longest *trailing* run of negative values."""
    cleaned = get_historical_values(values, max_len=max_len)
    count = 0
    for value in reversed(cleaned):
        if value < 0:
            count += 1
        else:
            break
    return count


def calculate_cagr(start_value: Any, end_value: Any, years: int) -> Optional[float]:
    """Compute a basic CAGR percentage from start/end values.

    Guards against invalid inputs, zero/negative start values and non-positive
    year spans. Returns ``None`` rather than fabricating a growth figure.
    """
    start = safe_float(start_value)
    end = safe_float(end_value)
    if start is None or end is None:
        return None
    if years <= 0 or start <= 0:
        return None
    if end < 0:
        return None
    try:
        cagr = (end / start) ** (1.0 / years) - 1.0
    except (ValueError, ZeroDivisionError, OverflowError):
        return None
    if np.isinf(cagr) or np.isnan(cagr):
        return None
    return cagr * 100.0


# =============================================================================
# COMPANY FINANCIAL CONTEXT
# =============================================================================


@dataclass
class CompanyContext:
    """Normalized internal representation of one company's financial data.

    This is the data model future Pro/Con rules (Modules 2B/2C) will consume.
    It exposes both latest-year values and chronological metric series:

    - ``context.latest["roe"]``             → latest year ROE (or None)
    - ``context.history["roe"]``            → ROE per history_year (oldest first)
    - ``context.latest_year``               → latest annual calendar year
    - ``context.history_years``             → years aligned with each metric series
    - ``context.trailing["revenue_cagr"]``  → trailing (TTM-level) metrics

    No rule thresholds or Pros/Cons are computed in this module.
    """

    company_id: str
    company_name: str
    sector: Optional[str]
    sub_sector: Optional[str]
    broad_sector: Optional[str]
    is_financial: bool
    latest_period: Optional[str]
    latest_year: Optional[int]
    history_years: List[int]
    latest: Dict[str, Optional[float]] = field(default_factory=dict)
    history: Dict[str, List[Optional[float]]] = field(default_factory=dict)
    trailing: Dict[str, Optional[float]] = field(default_factory=dict)
    history_df: Optional[pd.DataFrame] = None

    # ------------------------------------------------------------------
    def required_metric(self, metric: str) -> Optional[float]:
        """Return the latest value for *metric* (None when unavailable)."""
        return self.latest.get(metric)

    # ------------------------------------------------------------------
    def metric_history(self, metric: str) -> List[float]:
        """Return the valid numeric history for *metric* (chronological)."""
        return get_historical_values(self.history.get(metric, []))

    # ------------------------------------------------------------------
    def has_history(self, min_years: int = MIN_HISTORY_YEARS) -> bool:
        """True when the company exposes at least ``min_years`` of history."""
        return len(self.history_years) >= min_years

    # ------------------------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        """Serialize the context to a plain dictionary (for logging/reports)."""
        payload = asdict(self)
        payload["history_df"] = None  # DataFrames are not JSON-serializable
        return payload


def _resolve_metric_row(row: pd.Series) -> None:
    """Resolve metric candidates in-place for a merged per-period row.

    For each metric in ``METRIC_SOURCES`` the row is expected to contain one
    candidate column per (table, column) entry, named ``<metric>__<table>``.
    The first non-null candidate becomes ``row[<metric>]``. Missing metrics are
    left as pandas NA. Derived metrics (net_debt/ebitda) are computed too.
    """
    for metric, candidates in METRIC_SOURCES.items():
        for table, column in candidates:
            col = f"{metric}__{table}"
            if col not in row.index:
                continue
            value = row.get(col)
            number = safe_float(value)
            if number is not None:
                row[metric] = number
                break

    # Derived metrics
    for metric, (left, right, kind) in _DERIVED_METRICS.items():
        lv = safe_float(row.get(left))
        rv = safe_float(row.get(right))
        if kind == "subtract" and lv is not None and rv is not None:
            row[metric] = lv - rv
        elif kind == "add" and lv is not None and rv is not None:
            row[metric] = lv + rv


def prepare_company_history(
    company_id: str,
    conn: Optional[Any] = None,
    data: Optional[Dict[str, pd.DataFrame]] = None,
) -> pd.DataFrame:
    """Merge every financial dataset into one per-period row for a company.

    The returned DataFrame is keyed by ``period`` with a resolved ``year``
    column (annual periods only) and one column per metric from
    ``METRIC_SOURCES`` plus derived ``net_debt``/``ebitda``.

    Parameters
    ----------
    company_id : str
        Company identifier (case-insensitive).
    conn : sqlite3.Connection, optional
        Connection to use.
    data : Dict[str, pd.DataFrame], optional
        Pre-loaded dataset mapping from :func:`load_financial_data`. When not
        provided the datasets are loaded on demand.

    Returns
    -------
    pd.DataFrame
        Merged history, or an empty DataFrame when no data is available.
    """
    cid = str(company_id).strip().upper()
    if data is None:
        data = load_financial_data(conn)

    # Per-period datasets for the company.
    period_frames: List[pd.DataFrame] = []
    for key in ("profit_loss", "balance_sheet", "cash_flow", "ratios", "market_cap"):
        frame = data.get(key)
        if frame is None or frame.empty or "company_id" not in frame.columns:
            continue
        sub = frame[frame["company_id"] == cid].copy()
        if "period" in sub.columns:
            sub = sub.dropna(subset=["period"])
        period_frames.append(sub)

    if not period_frames:
        logger.warning("No financial data found for company '%s'", cid)
        return pd.DataFrame()

    # Outer-merge on period so late/early statements are all retained.
    merged = period_frames[0]
    for frame in period_frames[1:]:
        keep_cols = [c for c in frame.columns if c not in ("company_id", "id")]
        if not keep_cols:
            continue
        merged = merged.merge(
            frame[keep_cols],
            on="period",
            how="outer",
            suffixes=("", "_dup"),
        )
        # Drop duplicated / _dup-suffixed columns generated by the merge.
        seen: set = set()
        drop_cols: List[str] = []
        for col in merged.columns:
            if col.endswith("_dup"):
                drop_cols.append(col)
            elif col in seen:
                drop_cols.append(col)
            else:
                seen.add(col)
        if drop_cols:
            merged = merged.drop(columns=drop_cols)

    if merged.empty:
        return merged

    # Rename candidate metric columns to <metric>__<table>.
    for metric, candidates in METRIC_SOURCES.items():
        for table, column in candidates:
            if table == TABLE_COMPANIES:
                continue  # company-level columns have no period
            if column in merged.columns and f"{metric}__{table}" not in merged.columns:
                merged = merged.rename(columns={column: f"{metric}__{table}"})

    # Resolve metrics per row and keep only resolved + key columns.
    resolved_rows = [row for _, row in merged.iterrows()]
    for row in resolved_rows:
        _resolve_metric_row(row)
    merged = pd.DataFrame(resolved_rows)

    metric_names = list(METRIC_SOURCES.keys()) + ["period", "company_id"]
    keep = [c for c in metric_names if c in merged.columns]
    merged = merged[keep].copy()

    merged["year"] = merged["period"].apply(parse_period)
    merged = merged[merged["year"].notna()].copy()
    merged = merged.sort_values("year")

    # Some datasets report two periods for the same calendar year (e.g.
    # "Mar 2024" fiscal year-end plus a "Sep 2024" interim release). Combine
    # rows sharing a year by filling values within the group and keeping the
    # most complete row, so annual metrics are not lost to a partial period.
    def _combine_year(group: pd.DataFrame) -> pd.Series:
        return group.bfill().ffill().iloc[0]

    merged = (
        merged.groupby("year", sort=True)
              .apply(_combine_year, include_groups=False)
              .reset_index()
    )

    if not merged.empty:
        logger.info(
            "Prepared history for '%s': %d years (%d .. %d)",
            cid, len(merged), int(merged["year"].min()), int(merged["year"].max()),
        )
    return merged


def prepare_latest_year_data(
    company_id: str,
    history_df: Optional[pd.DataFrame] = None,
    conn: Optional[Any] = None,
    data: Optional[Dict[str, pd.DataFrame]] = None,
) -> Tuple[Optional[str], Optional[int], Dict[str, Optional[float]]]:
    """Return ``(latest_period, latest_year, latest_metrics)`` for a company.

    ``latest_metrics`` resolves each metric to its *latest annual* value using
    the first non-null candidate across the merged history row.
    """
    if history_df is None:
        history_df = prepare_company_history(company_id, conn=conn, data=data)
    if history_df.empty or "year" not in history_df.columns:
        return None, None, {}

    latest_row = history_df.loc[history_df["year"].idxmax()]
    latest_year = int(latest_row["year"])
    latest_period = (
        str(latest_row.get("period"))
        if latest_row.get("period") is not None else None
    )
    latest_metrics: Dict[str, Optional[float]] = {}
    for metric in METRIC_SOURCES:
        if metric in latest_row.index:
            latest_metrics[metric] = safe_float(latest_row[metric])
    return latest_period, latest_year, latest_metrics


def _resolve_trailing(
    company_id: str,
    data: Optional[Dict[str, pd.DataFrame]] = None,
) -> Dict[str, Optional[float]]:
    """Resolve trailing (TTM-level) metrics: revenue/profit/eps CAGR and yield.

    Trailing metrics exist on non-annual rows (``TTM``) and are therefore not
    part of the annual history series. Values are taken from the first non-null
    candidate, preferring TTM rows.
    """
    trails: Dict[str, Optional[float]] = {
        "revenue_cagr": None,
        "profit_cagr": None,
        "eps_cagr": None,
        "dividend_yield": None,
    }
    if data is None:
        data = load_financial_data()
    cid = str(company_id).strip().upper()

    ratios = data.get("ratios")
    if ratios is not None and not ratios.empty:
        sub = ratios[ratios["company_id"] == cid]
        for metric, col in (
            ("revenue_cagr", "revenue_cagr"),
            ("profit_cagr", "profit_cagr"),
            ("eps_cagr", "eps_cagr"),
            ("dividend_yield", "dividend_yield"),
        ):
            if col not in sub.columns:
                continue
            ttm = sub[sub.get("period") == PERIOD_TTM]
            frame = ttm if not ttm.empty else sub
            value = get_latest_value(frame[col].tolist())
            trails[metric] = value

    if trails["dividend_yield"] is None:
        market = data.get("market_cap")
        if market is not None and not market.empty:
            sub = market[market["company_id"] == cid]
            if "dividend_yield" in sub.columns:
                value = get_latest_value(sub["dividend_yield"].tolist())
                if value is not None:
                    trails["dividend_yield"] = value

    return trails


def get_company_context(
    company_id: str,
    conn: Optional[Any] = None,
    data: Optional[Dict[str, pd.DataFrame]] = None,
) -> CompanyContext:
    """Build the normalized financial context for one company.

    The returned :class:`CompanyContext` never raises for missing data: missing
    companies/metrics surface as ``None`` values and empty history rather than
    exceptions.

    Parameters
    ----------
    company_id : str
        Company identifier (case-insensitive).
    conn : sqlite3.Connection, optional
        Connection to use.
    data : Dict[str, pd.DataFrame], optional
        Pre-loaded dataset mapping from :func:`load_financial_data`.

    Returns
    -------
    CompanyContext
        Populated context for the company.
    """
    cid = str(company_id).strip().upper()
    if data is None:
        data = load_financial_data(conn)

    company_name: Optional[str] = None
    company_sector: Optional[str] = None
    companies = data.get("companies")
    if companies is not None and not companies.empty:
        match = companies[companies["company_id"] == cid]
        if not match.empty:
            row = match.iloc[0]
            company_name = row.get("company_name")
            company_sector = row.get("sector")

    sub_sector: Optional[str] = None
    broad_sector: Optional[str] = None
    sectors = data.get("sectors")
    if sectors is not None and not sectors.empty:
        smatch = sectors[sectors["company_id"] == cid]
        if not smatch.empty:
            srow = smatch.iloc[0]
            sub_sector = srow.get("sub_sector")
            broad_sector = srow.get("broad_sector")

    is_financial = is_financial_sector(sub_sector)

    history_df = prepare_company_history(cid, conn=conn, data=data)
    latest_period, latest_year, latest_metrics = prepare_latest_year_data(
        cid, history_df=history_df, conn=conn, data=data,
    )

    history_years: List[int] = []
    history: Dict[str, List[Optional[float]]] = {}
    if not history_df.empty and "year" in history_df.columns:
        history_years = [int(y) for y in history_df["year"].tolist()]
        for metric in METRIC_SOURCES:
            if metric in history_df.columns:
                history[metric] = [
                    safe_float(v) for v in history_df[metric].tolist()
                ]
            else:
                history[metric] = [None] * len(history_years)

    trailing = _resolve_trailing(cid, data)

    context = CompanyContext(
        company_id=cid,
        company_name=company_name,
        sector=company_sector,
        sub_sector=sub_sector,
        broad_sector=broad_sector,
        is_financial=is_financial,
        latest_period=latest_period,
        latest_year=latest_year,
        history_years=history_years,
        latest=latest_metrics,
        history=history,
        trailing=trailing,
        history_df=history_df,
    )
    logger.info(
        "Built context for '%s' (latest year=%s, %d history years, financial=%s)",
        cid, latest_year, len(history_years), is_financial,
    )
    return context


# =============================================================================
# FINANCIAL SECTOR SUPPORT
# =============================================================================


def is_financial_sector(sub_sector: Optional[str]) -> bool:
    """Return True when a sub-sector belongs to the financials classification.

    Used later by rules that must exclude financial companies (e.g. a D/E rule
    stated only for non-financials). Comparison is case-insensitive.
    """
    if not sub_sector:
        return False
    return str(sub_sector).strip().lower() in {
        s.lower() for s in FINANCIAL_SUB_SECTORS
    }


def get_sub_sector(
    company_id: str,
    conn: Optional[Any] = None,
    sectors: Optional[pd.DataFrame] = None,
) -> Optional[str]:
    """Return the sub-sector label for a company (None when unavailable)."""
    cid = str(company_id).strip().upper()
    if sectors is None:
        sectors = load_sectors(conn)
    if sectors is None or sectors.empty or "company_id" not in sectors.columns:
        return None
    match = sectors[sectors["company_id"] == cid]
    if match.empty or "sub_sector" not in match.columns:
        return None
    value = match.iloc[0]["sub_sector"]
    return str(value).strip() if value is not None else None


# =============================================================================
# RULE ENGINE ARCHITECTURE
#
# Module 2A provides the *generic* rule representation only. The actual
# PRO_01..PRO_12 and CON_01..CON_12 financial conditions are implemented in
# Modules 2B/2C by subclassing FinancialRule and registering the instances.
# =============================================================================


@dataclass
class RuleResult:
    """Output of evaluating one rule for one company.

    Attributes
    ----------
    company_id : str
        Company identifier.
    rule_id : str
        Stable rule identifier (e.g. ``"PRO_01"`` in later modules).
    rule_type : str
        ``"pro"`` or ``"con"``.
    triggered : bool
        Whether the underlying condition matched.
    text : str
        Human-readable statement (empty when not triggered).
    confidence_pct : float
        Confidence score in ``[0, 100]``.
    reason : str
        Machine-readable explanation / data used.
    """

    company_id: str
    rule_id: str
    rule_type: str
    triggered: bool
    text: str = ""
    confidence_pct: float = 0.0
    reason: str = ""

    # ------------------------------------------------------------------
    def validate(self) -> List[str]:
        """Validate the result, returning a list of violation messages."""
        issues: List[str] = []
        if not self.company_id or (
            isinstance(self.company_id, float) and np.isnan(self.company_id)
        ):
            issues.append("company_id is null/empty")
        if not self.rule_id:
            issues.append("rule_id is null/empty")
        if self.rule_type not in VALID_TYPES:
            issues.append(
                f"rule_type must be one of {VALID_TYPES} (got {self.rule_type!r})"
            )
        if not validate_confidence(self.confidence_pct):
            issues.append(
                f"confidence_pct must be between {CONFIDENCE_MIN} and "
                f"{CONFIDENCE_MAX} (got {self.confidence_pct!r})"
            )
        return issues

    # ------------------------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a dict matching the final output schema."""
        return {
            "company_id": self.company_id,
            "type": self.rule_type,
            "rule_id": self.rule_id,
            "text": self.text,
            "confidence_pct": format_confidence(self.confidence_pct),
        }


class FinancialRule(ABC):
    """Abstract base class for all future Pro/Con rules.

    Concrete rules (Modules 2B/2C) implement :meth:`evaluate`, which receives
    the normalized :class:`CompanyContext` and returns a :class:`RuleResult`.
    The engine never needs to know rule internals, so new rules can be added by
    subclassing + registering without touching the engine.
    """

    rule_id: str = ""
    rule_type: str = ""
    name: str = ""
    description: str = ""

    def __init__(self) -> None:
        if not self.rule_id or not self.rule_type:
            raise ValueError(
                "FinancialRule subclasses must define rule_id and rule_type"
            )

    @abstractmethod
    def evaluate(self, context: CompanyContext, conn: Optional[Any] = None) -> RuleResult:
        """Evaluate the rule against *context*.

        Parameters
        ----------
        context : CompanyContext
            Normalized company data (see :class:`CompanyContext`).
        conn : sqlite3.Connection, optional
            Optional connection for rules that need extra queries.

        Returns
        -------
        RuleResult
            The rule outcome for this company.
        """

    # ------------------------------------------------------------------
    def to_placeholder_result(self, context: CompanyContext) -> RuleResult:
        """Return an untriggered placeholder result (safe default)."""
        return RuleResult(
            company_id=context.company_id,
            rule_id=self.rule_id,
            rule_type=self.rule_type,
            triggered=False,
            text="",
            confidence_pct=0.0,
            reason=(
                f"Rule '{self.rule_id}' not yet implemented"
                " (foundation placeholder)"
            ),
        )


# =============================================================================
# RULE REGISTRY
#
# Registries start EMPTY in Module 2A. Modules 2B/2C register PRO_01..PRO_12
# and CON_01..CON_12 instances here; the engine iterates these lists.
# =============================================================================

PRO_RULES: List[FinancialRule] = []
CON_RULES: List[FinancialRule] = []


def register_pro_rule(rule: FinancialRule) -> None:
    """Register a Pro rule in the global registry."""
    if rule.rule_type != TYPE_PRO:
        raise ValueError(
            f"Pro registry requires rule_type='pro', got '{rule.rule_type}'"
        )
    if any(existing.rule_id == rule.rule_id for existing in PRO_RULES):
        logger.warning("Pro rule '%s' already registered; skipping", rule.rule_id)
        return
    PRO_RULES.append(rule)
    logger.info("Registered pro rule '%s' (%s)", rule.rule_id, rule.name or "-")


def register_con_rule(rule: FinancialRule) -> None:
    """Register a Con rule in the global registry."""
    if rule.rule_type != TYPE_CON:
        raise ValueError(
            f"Con registry requires rule_type='con', got '{rule.rule_type}'"
        )
    if any(existing.rule_id == rule.rule_id for existing in CON_RULES):
        logger.warning("Con rule '%s' already registered; skipping", rule.rule_id)
        return
    CON_RULES.append(rule)
    logger.info("Registered con rule '%s' (%s)", rule.rule_id, rule.name or "-")


# =============================================================================
# MODULE 2B — PRO RULE REGISTRATION
# =============================================================================
# Pro rules are imported from the dedicated pro_rules module and registered here
# so the existing evaluate_rules_for_company() engine can discover them.
# (Placed after register_pro_rule/register_con_rule so the call resolves. The
# pro_rules module also self-registers idempotently, so the registry is
# populated regardless of import order.)

try:
    from src.nlp.pro_rules import get_pro_rule_instances  # noqa: E402

    _registered_ids = {r.rule_id for r in PRO_RULES}
    for _pro_rule in get_pro_rule_instances():
        if _pro_rule.rule_id not in _registered_ids:
            register_pro_rule(_pro_rule)
            _registered_ids.add(_pro_rule.rule_id)
except Exception as _exc:  # pragma: no cover - defensive
    logger.warning("Could not register Pro rules: %s", _exc)


# =============================================================================
# MODULE 2C — CON RULE REGISTRATION
# =============================================================================

try:
    from src.nlp.con_rules import get_con_rule_instances  # noqa: E402

    _registered_ids_con = {r.rule_id for r in CON_RULES}
    for _con_rule in get_con_rule_instances():
        if _con_rule.rule_id not in _registered_ids_con:
            register_con_rule(_con_rule)
            _registered_ids_con.add(_con_rule.rule_id)
except Exception as _exc:  # pragma: no cover - defensive
    logger.warning("Could not register Con rules: %s", _exc)


def get_registered_rules() -> Dict[str, List[FinancialRule]]:
    """Return the current rule registries (``{"pro": [...], "con": [...]}``)."""
    return {"pro": list(PRO_RULES), "con": list(CON_RULES)}


def evaluate_rules_for_company(
    context: CompanyContext,
    conn: Optional[Any] = None,
) -> List[RuleResult]:
    """Evaluate every registered rule against one company context.

    In Module 2A the registries are empty, so this returns ``[]``. The function
    is the single entry point future rule phases will rely on.
    """
    results: List[RuleResult] = []
    for rules in (PRO_RULES, CON_RULES):
        for rule in rules:
            try:
                results.append(rule.evaluate(context, conn))
            except Exception as exc:  # a rule must never crash a full run
                logger.exception(
                    "Rule '%s' failed for '%s': %s",
                    rule.rule_id, context.company_id, exc,
                )
    logger.info(
        "Evaluated %d registered rules for '%s' (pro=%d, con=%d)",
        len(results), context.company_id, len(PRO_RULES), len(CON_RULES)
    )
    return results


# =============================================================================
# CONFIDENCE FRAMEWORK
#
# Module 2A implements the *plumbing*: validation, formatting and threshold
# configuration. The actual signal-strength formulas for each rule will be
# implemented together with the rules in Modules 2B/2C. No arbitrary financial
# confidence score is invented here.
# =============================================================================


def validate_confidence(confidence_pct: Any) -> bool:
    """Return True when *confidence_pct* is numeric and within [0, 100]."""
    value = safe_float(confidence_pct)
    if value is None:
        return False
    return CONFIDENCE_MIN <= value <= CONFIDENCE_MAX


def format_confidence(confidence_pct: Any) -> float:
    """Normalize a confidence value to a rounded float in ``[0, 100]``.

    Invalid inputs are clamped to 0.0 so downstream schema validation never
    receives out-of-range or non-numeric confidence values.
    """
    value = safe_float(confidence_pct)
    if value is None:
        value = CONFIDENCE_MIN
    value = min(max(value, CONFIDENCE_MIN), CONFIDENCE_MAX)
    return round(value, CONFIDENCE_DECIMALS)


def calculate_confidence(
    factors: Sequence[Any],
    weights: Optional[Sequence[float]] = None,
) -> Optional[float]:
    """Compute a generic weighted confidence from 0–100 *factors*.

    This is *infrastructure only*: rules supply their own factor/strength logic
    in Modules 2B/2C. It returns ``None`` when any factor is missing or
    out-of-range so callers can fall back to a neutral confidence instead of
    inventing a value.

    Parameters
    ----------
    factors : Sequence[Any]
        Signal-strength values, each conceived in ``[0, 100]``.
    weights : Sequence[float], optional
        Non-negative weights aligned with *factors* (defaults to equal weights).

    Returns
    -------
    Optional[float]
        Weighted mean rounded to ``CONFIDENCE_DECIMALS``, or ``None`` if the
        input is invalid.
    """
    cleaned = [safe_float(f) for f in factors]
    if not cleaned or any(f is None for f in cleaned):
        return None
    if any(not (CONFIDENCE_MIN <= f <= CONFIDENCE_MAX) for f in cleaned):
        return None

    if weights is None:
        weights = [1.0] * len(cleaned)
    cleaned_weights = [safe_float(w) for w in weights]
    if any(w is None or w < 0 for w in cleaned_weights):
        return None
    if len(cleaned_weights) != len(cleaned):
        return None

    total_weight = sum(cleaned_weights)
    if total_weight == 0:
        return None
    score = sum(f * w for f, w in zip(cleaned, cleaned_weights)) / total_weight
    return round(min(max(score, CONFIDENCE_MIN), CONFIDENCE_MAX), CONFIDENCE_DECIMALS)


# =============================================================================
# OUTPUT SCHEMA VALIDATION
#
# The final generator output must follow the schema:
#     company_id | type | rule_id | text | confidence_pct
# =============================================================================


def validate_output_schema(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """Validate a result DataFrame against the final output schema.

    The final output must only contain triggered Pro/Con signals with
    ``confidence_pct > 60`` and valid rule identifiers.
    """
    issues: List[str] = []
    if df is None or not isinstance(df, pd.DataFrame):
        return False, ["input is not a DataFrame"]

    missing = [c for c in OUTPUT_COLUMNS if c not in df.columns]
    if missing:
        issues.append(f"missing required columns: {missing}")
        return False, issues

    if df.empty:
        return True, []

    bad_types = df[~df["type"].isin(VALID_TYPES)]
    if not bad_types.empty:
        bogus = bad_types["type"].dropna().astype(str).unique().tolist()
        issues.append(f"invalid type value(s): {bogus[:5]}")

    for idx, raw in df["confidence_pct"].items():
        value = safe_float(raw)
        if value is None:
            issues.append(f"row {idx}: confidence_pct invalid or NaN ({raw!r})")
            continue
        if not (0.0 <= value <= 100.0):
            issues.append(
                f"row {idx}: confidence_pct out of range ({value!r})"
            )
        if value <= 60.0:
            issues.append(
                f"row {idx}: confidence_pct must be strictly greater than 60.0 ({value!r})"
            )

    null_company = df["company_id"].isna() | (
        df["company_id"].astype(str).str.strip() == ""
    )
    if null_company.any():
        rows = df.index[null_company].tolist()
        issues.append(f"null/empty company_id at rows: {rows[:5]}")

    null_rule = df["rule_id"].isna() | (df["rule_id"].astype(str).str.strip() == "")
    if null_rule.any():
        rows = df.index[null_rule].tolist()
        issues.append(f"null/empty rule_id at rows: {rows[:5]}")

    valid_rule_ids = {
        "PRO_01", "PRO_02", "PRO_03", "PRO_04", "PRO_05", "PRO_06",
        "PRO_07", "PRO_08", "PRO_09", "PRO_10", "PRO_11", "PRO_12",
        "CON_01", "CON_02", "CON_03", "CON_04", "CON_05", "CON_06",
        "CON_07", "CON_08", "CON_09", "CON_10", "CON_11", "CON_12",
    }
    bad_rule_ids = df[~df["rule_id"].astype(str).str.strip().isin(valid_rule_ids)]
    if not bad_rule_ids.empty:
        bogus_rules = sorted({str(x) for x in bad_rule_ids["rule_id"].astype(str).tolist()})[:10]
        issues.append(f"invalid rule_id value(s): {bogus_rules}")

    dup_mask = df.duplicated(subset=["company_id", "type", "rule_id"], keep=False)
    if dup_mask.any():
        count = int(dup_mask.sum())
        dup_groups = df.loc[dup_mask, ["company_id", "type", "rule_id"]]
        sample = list(
            dup_groups.drop_duplicates()[:3].itertuples(index=False, name=None)
        )
        issues.append(
            f"{count} duplicate (company_id, type, rule_id) rows; first: {sample}"
        )

    if issues:
        logger.warning(
            "Output schema validation failed with %d issue(s)", len(issues)
        )
        for issue in issues[:10]:
            logger.warning("  - %s", issue)
    else:
        logger.info(
            "Output schema validation passed for %d row(s)", len(df)
        )
    return not issues, issues


def validate_company_coverage(
    companies: Sequence[str],
    results_df: Optional[pd.DataFrame] = None,
) -> Dict[str, Any]:
    """Measure Pro/Con coverage across companies.

    Checks the eventual invariant: every company has ≥1 Pro and ≥1 Con. In
    Module 2A the rule-result table is empty or absent, so the correct output
    is *all* companies missing both a Pro and a Con — that is expected, and no
    rows are fabricated to mask it.

    Parameters
    ----------
    companies : Sequence[str]
        Company identifiers that must be covered.
    results_df : pd.DataFrame, optional
        Output-schema DataFrame of generated results (empty/None allowed).

    Returns
    -------
    Dict[str, Any]
        Coverage statistics.
    """
    company_list = sorted({str(c).strip().upper() for c in companies if c})
    total = len(company_list)

    if results_df is None or not isinstance(results_df, pd.DataFrame) or results_df.empty:
        stats: Dict[str, Any] = {
            "companies_total": total,
            "results_total": 0,
            "companies_with_pro": 0,
            "companies_with_con": 0,
            "companies_fully_covered": 0,
            "missing_pro": total,
            "missing_con": total,
            "expected_incomplete_module_2a": True,
        }
        logger.info(
            "Coverage (Module 2A, no rules): missing_pro=%d, missing_con=%d",
            stats["missing_pro"], stats["missing_con"],
        )
        return stats

    req = ["company_id", "type"]
    if not all(c in results_df.columns for c in req):
        stats = validate_company_coverage(company_list, None)
        stats["coverage_error"] = "results_df missing company_id/type columns"
        return stats

    pro_ids = {
        str(c).strip().upper()
        for c in results_df.loc[results_df["type"] == TYPE_PRO, "company_id"]
    }
    con_ids = {
        str(c).strip().upper()
        for c in results_df.loc[results_df["type"] == TYPE_CON, "company_id"]
    }

    missing_pro = [c for c in company_list if c not in pro_ids]
    missing_con = [c for c in company_list if c not in con_ids]
    covered = [c for c in company_list if c in pro_ids and c in con_ids]

    stats = {
        "companies_total": total,
        "results_total": int(len(results_df)),
        "companies_with_pro": len(pro_ids & set(company_list)),
        "companies_with_con": len(con_ids & set(company_list)),
        "companies_fully_covered": len(covered),
        "missing_pro": len(missing_pro),
        "missing_con": len(missing_con),
        "expected_incomplete_module_2a": len(covered) < total,
    }
    logger.info(
        "Coverage: companies=%d, with_pro=%d, with_con=%d, fully_covered=%d",
        total, stats["companies_with_pro"], stats["companies_with_con"],
        stats["companies_fully_covered"],
    )
    return stats


# =============================================================================
# MODULE 2A FOUNDATION REPORT
#
# A smoke run that loads the data layer, builds contexts and reports coverage.
# It deliberately does NOT generate any Pros/Cons or run any rule.
# =============================================================================


def run_foundation_report(
    conn: Optional[Any] = None,
    limit: Optional[int] = None,
) -> Dict[str, Any]:
    """Run a Module 2A diagnostic over the data layer.

    Loads every dataset, builds a :class:`CompanyContext` for each company,
    logs coverage/missing-data statistics and returns a plain summary dict.
    No Pros/Cons are produced.

    Parameters
    ----------
    conn : sqlite3.Connection, optional
        Connection to use.
    limit : int, optional
        If set, only build contexts for the first ``limit`` companies (for
        quick smoke runs).

    Returns
    -------
    Dict[str, Any]
        Foundation diagnostics.
    """
    start = time.time()
    logger.info("=" * 80)
    logger.info("Module 2A — Pros/Cons Generator Foundation report")
    logger.info("=" * 80)

    data = load_financial_data(conn)
    companies = data.get("companies", pd.DataFrame())
    company_ids = sorted(companies["company_id"].tolist())

    report: Dict[str, Any] = {
        "status": "ok",
        "companies_total": len(company_ids),
        "datasets": {k: int(len(v)) for k, v in data.items()},
        "latest_year_by_company": {},
        "missing_roe_latest": [],
        "missing_3yr_history": [],
        "financial_companies": [],
        "rule_registry": {k: len(v) for k, v in get_registered_rules().items()},
        "execution_time_seconds": 0.0,
    }

    sample = company_ids if limit is None else company_ids[:limit]
    for cid in sample:
        context = get_company_context(cid, conn=conn, data=data)
        report["latest_year_by_company"][cid] = context.latest_year
        if context.latest.get("roe") is None:
            report["missing_roe_latest"].append(cid)
        if not context.has_history(min_years=MIN_HISTORY_YEARS):
            report["missing_3yr_history"].append(cid)
        if context.is_financial:
            report["financial_companies"].append(cid)

    report["execution_time_seconds"] = round(time.time() - start, 3)
    logger.info(
        "Companies: %d | latest_year: %d | missing ROE: %d | "
        "missing 3yr history: %d | financial: %d",
        len(company_ids),
        len([y for y in report["latest_year_by_company"].values() if y]),
        len(report["missing_roe_latest"]),
        len(report["missing_3yr_history"]),
        len(report["financial_companies"]),
    )
    logger.info("Registered rules: pro=%d con=%d", len(PRO_RULES), len(CON_RULES))
    logger.info("Module 2A foundation report completed in %.3fs", report["execution_time_seconds"])
    return report


def _run_foundation_report( # Renamed from main for Module 2A smoke run
    conn: Optional[Any] = None,
    limit: Optional[int] = None,
) -> Dict[str, Any]:
    """Run a Module 2A diagnostic over the data layer.

    Loads every dataset, builds a :class:`CompanyContext` for each company,
    logs coverage/missing-data statistics and returns a plain summary dict.
    No Pros/Cons are produced.

    Parameters
    ----------
    conn : sqlite3.Connection, optional
        Connection to use.
    limit : int, optional
        If set, only build contexts for the first ``limit`` companies (for
        quick smoke runs).

    Returns
    -------
    Dict[str, Any]
        Foundation diagnostics.
    """
    start = time.time()
    logger.info("=" * 80)
    logger.info("Module 2A — Pros/Cons Generator Foundation report")
    logger.info("=" * 80)

    data = load_financial_data(conn)
    companies = data.get("companies", pd.DataFrame())
    company_ids = sorted(companies["company_id"].tolist())

    report: Dict[str, Any] = {
        "status": "ok",
        "companies_total": len(company_ids),
        "datasets": {k: int(len(v)) for k, v in data.items()},
        "latest_year_by_company": {},
        "missing_roe_latest": [],
        "missing_3yr_history": [],
        "financial_companies": [],
        "rule_registry": {k: len(v) for k, v in get_registered_rules().items()},
        "execution_time_seconds": 0.0,
    }

    sample = company_ids if limit is None else company_ids[:limit]
    for cid in sample:
        context = get_company_context(cid, conn=conn, data=data)
        report["latest_year_by_company"][cid] = context.latest_year
        if context.latest.get("roe") is None:
            report["missing_roe_latest"].append(cid)
        if not context.has_history(min_years=MIN_HISTORY_YEARS):
            report["missing_3yr_history"].append(cid)
        if context.is_financial:
            report["financial_companies"].append(cid)

    report["execution_time_seconds"] = round(time.time() - start, 3)
    logger.info(
        "Companies: %d | latest_year: %d | missing ROE: %d | "
        "missing 3yr history: %d | financial: %d",
        len(company_ids),
        len([y for y in report["latest_year_by_company"].values() if y]),
        len(report["missing_roe_latest"]),
        len(report["missing_3yr_history"]),
        len(report["financial_companies"]),
    )
    logger.info("Registered rules: pro=%d con=%d", len(PRO_RULES), len(CON_RULES))
    logger.info("Module 2A foundation report completed in %.3fs", report["execution_time_seconds"])
    return report


MODULE_2D_COMPLETION_REPORT_PATH: Path = PROJECT_ROOT / "MODULE_2D_COMPLETION_REPORT.md"

def load_all_company_ids(conn: Any) -> Tuple[List[str], Dict[str, Any]]:
    """Load all company IDs from the 'companies' table with sanity checks."""
    company_ids: List[str] = []
    stats: Dict[str, Any] = {
        "total_companies_in_db": 0,
        "unique_company_ids": 0,
        "duplicate_company_ids": [],
        "companies_missing_id_fields": [],
    }
    try:
        df = _load_table(TABLE_COMPANIES, ["company_id", "company_name", "sector"], conn=conn)
        if df.empty:
            logger.error("No companies found in the database.")
            return [], stats

        stats["total_companies_in_db"] = len(df)

        # Check for duplicates
        duplicates = df[df.duplicated(subset=["company_id"], keep=False)]
        if not duplicates.empty:
            stats["duplicate_company_ids"] = duplicates["company_id"].unique().tolist()
            logger.warning("Found duplicate company_ids in 'companies' table: %s", stats["duplicate_company_ids"])

        # Check for missing identity fields
        missing_id_fields = df[df["company_id"].isna() | df["company_name"].isna()]
        if not missing_id_fields.empty:
            stats["companies_missing_id_fields"] = missing_id_fields["company_id"].tolist()
            logger.warning("Companies missing required identity fields: %s", stats["companies_missing_id_fields"])

        cleaned = df["company_id"].map(lambda v: str(v).strip().upper() if pd.notna(v) and str(v).strip() else None)
        company_ids = sorted({cid for cid in cleaned if cid is not None and cid != "NONE"})
        stats["unique_company_ids"] = len(company_ids)

        logger.info("Loaded %d unique company IDs from the database.", len(company_ids))
        return company_ids, stats
    except Exception as exc:
        logger.error("Failed to load company IDs: %s", exc)
        return [], stats

def generate_all_pros_cons(
    company_ids: List[str],
    conn: Any,
    confidence_threshold: float = CONFIDENCE_THRESHOLD,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Generate Pro/Con signals for every company and return filtered output.

    The final pipeline keeps only triggered rules whose raw confidence is strictly
    greater than the configured threshold. Duplicate signal rows are removed by
    ``(company_id, type, rule_id)`` before the result is returned.
    """
    all_results: List[Dict[str, Any]] = []
    processed_companies: List[str] = []
    failed_companies: List[Dict[str, Any]] = []
    rule_trigger_counts: Dict[str, int] = Counter()
    triggered_before_filter = 0

    total_companies = len(company_ids)
    logger.info("Starting Pros/Cons generation for %d companies.", total_companies)

    for idx, company_id in enumerate(company_ids):
        cid = str(company_id).strip().upper()
        if (idx + 1) % 10 == 0 or (idx + 1) == total_companies:
            logger.info("Processing company %d/%d: %s", idx + 1, total_companies, cid)

        try:
            context = get_company_context(cid, conn=conn)
            processed_companies.append(context.company_id)
            results = evaluate_rules_for_company(context, conn=conn)

            for result in results:
                if result.triggered:
                    triggered_before_filter += 1
                    if result.confidence_pct > confidence_threshold:
                        all_results.append(result.to_dict())
                        rule_trigger_counts[result.rule_id] += 1

        except Exception as exc:  # pragma: no cover - defensive but logged
            logger.exception("Failed processing company '%s': %s", cid, exc)
            failed_companies.append({
                "company_id": cid,
                "error": str(exc),
            })

    df = pd.DataFrame(all_results, columns=OUTPUT_COLUMNS)
    if not df.empty:
        df = df.drop_duplicates(subset=["company_id", "type", "rule_id"], keep="first")
        df = df.sort_values(["company_id", "type", "rule_id"]).reset_index(drop=True)
    else:
        df = pd.DataFrame(columns=OUTPUT_COLUMNS)

    pro_rows = df[df["type"] == TYPE_PRO].copy().reset_index(drop=True)
    con_rows = df[df["type"] == TYPE_CON].copy().reset_index(drop=True)

    stats: Dict[str, Any] = {
        "total_companies": total_companies,
        "processed_companies": len(processed_companies),
        "failed_companies": len(failed_companies),
        "failed_company_ids": [c["company_id"] for c in failed_companies],
        "triggered_before_filter": triggered_before_filter,
        "signals_after_filter": int(len(df)),
        "pro_signals": int(len(pro_rows)),
        "con_signals": int(len(con_rows)),
        "companies_with_pro": int(df[df["type"] == TYPE_PRO]["company_id"].nunique()),
        "companies_with_con": int(df[df["type"] == TYPE_CON]["company_id"].nunique()),
        "rule_trigger_counts": dict(sorted(rule_trigger_counts.items())),
        "confidence_threshold": confidence_threshold,
    }
    logger.info(
        "Finished generation: total_companies=%d, processed=%d, failed=%d, "
        "signals_after_filter=%d, pro=%d, con=%d, raw_triggered=%d",
        total_companies,
        stats["processed_companies"],
        stats["failed_companies"],
        stats["signals_after_filter"],
        stats["pro_signals"],
        stats["con_signals"],
        triggered_before_filter,
    )
    return df, stats


def write_coverage_failures_csv(
    failures_df: pd.DataFrame,
    output_path: Path = PROS_CONS_COVERAGE_FAILURES_CSV_PATH,
) -> Path:
    """Write company coverage failures to CSV when coverage is incomplete."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    required_cols = [
        "company_id",
        "company_name",
        "sector",
        "pro_count",
        "con_count",
        "failure_reason",
    ]
    if failures_df.empty:
        empty = pd.DataFrame(columns=required_cols)
        empty.to_csv(output_path, index=False)
        return output_path

    df = failures_df.copy()
    for col in required_cols:
        if col not in df.columns:
            df[col] = ""
    df = df[required_cols].copy()
    df.to_csv(output_path, index=False, encoding="utf-8")
    logger.info("Wrote coverage failures CSV to %s (%d rows)", output_path, len(df))
    return output_path


def build_company_coverage_report(
    company_ids: Sequence[str],
    results_df: Optional[pd.DataFrame],
    companies_df: Optional[pd.DataFrame] = None,
    sectors_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """Return a per-company coverage table with PASS/FAIL status."""
    companies_list = [str(c).strip().upper() for c in company_ids if str(c).strip()]
    company_map: Dict[str, str] = {}
    sector_map: Dict[str, str] = {}

    if companies_df is not None and not companies_df.empty:
        for _, row in companies_df.iterrows():
            cid = str(row.get("company_id", "")).strip().upper()
            if cid:
                company_map[cid] = str(row.get("company_name", "")).strip()
    if sectors_df is not None and not sectors_df.empty:
        for _, row in sectors_df.iterrows():
            cid = str(row.get("company_id", "")).strip().upper()
            if cid:
                sector_map[cid] = str(row.get("sector", row.get("sub_sector", ""))).strip()

    if results_df is None or results_df.empty:
        rows = []
        for cid in companies_list:
            rows.append({
                "company_id": cid,
                "company_name": company_map.get(cid, ""),
                "sector": sector_map.get(cid, ""),
                "pro_count": 0,
                "con_count": 0,
                "has_pro": False,
                "has_con": False,
                "coverage_status": "FAIL",
            })
        return pd.DataFrame(rows, columns=[
            "company_id", "company_name", "sector", "pro_count", "con_count",
            "has_pro", "has_con", "coverage_status",
        ])

    results = results_df.copy()
    pro_counts = (
        results[results["type"] == TYPE_PRO].groupby("company_id").size().to_dict()
    )
    con_counts = (
        results[results["type"] == TYPE_CON].groupby("company_id").size().to_dict()
    )

    rows = []
    for cid in companies_list:
        pro_count = int(pro_counts.get(cid, 0))
        con_count = int(con_counts.get(cid, 0))
        has_pro = pro_count > 0
        has_con = con_count > 0
        rows.append({
            "company_id": cid,
            "company_name": company_map.get(cid, ""),
            "sector": sector_map.get(cid, ""),
            "pro_count": pro_count,
            "con_count": con_count,
            "has_pro": has_pro,
            "has_con": has_con,
            "coverage_status": "PASS" if has_pro and has_con else "FAIL",
        })
    return pd.DataFrame(rows, columns=[
        "company_id", "company_name", "sector", "pro_count", "con_count",
        "has_pro", "has_con", "coverage_status",
    ])


def generate_coverage_failures(
    company_ids: Sequence[str],
    results_df: Optional[pd.DataFrame],
    companies_df: Optional[pd.DataFrame] = None,
    sectors_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """Return only companies failing the final Pro/Con coverage requirement."""
    coverage = build_company_coverage_report(company_ids, results_df, companies_df, sectors_df)
    failures = coverage[coverage["coverage_status"] == "FAIL"].copy()
    if failures.empty:
        return pd.DataFrame(columns=[
            "company_id", "company_name", "sector", "pro_count", "con_count", "failure_reason",
        ])

    failures["failure_reason"] = ""
    for idx, row in failures.iterrows():
        if row["pro_count"] == 0 and row["con_count"] == 0:
            reason = "No valid Pro or Con signals after >60 confidence filter"
        elif row["pro_count"] == 0:
            reason = "No valid Pro signal after >60 confidence filter"
        elif row["con_count"] == 0:
            reason = "No valid Con signal after >60 confidence filter"
        else:
            reason = "Coverage rule not satisfied"
        failures.at[idx, "failure_reason"] = reason
    return failures[[
        "company_id", "company_name", "sector", "pro_count", "con_count", "failure_reason",
    ]].reset_index(drop=True)


# Keep the final result consistent with the earlier validation helpers.
# ---------------------------------------------------------------------------
# Schema validation: the final output file must only contain triggered signals
# above the >60 threshold, and each result must have a valid rule id and
# non-empty company id.
# ---------------------------------------------------------------------------

