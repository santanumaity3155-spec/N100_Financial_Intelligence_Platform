"""
cashflow_intelligence.py

Sprint 5 — Module 3: Cash Flow Intelligence Engine
N100 Financial Intelligence Platform

This module computes cash-flow intelligence metrics for every company in the
authoritative ``companies`` table and writes:

* ``output/cashflow_intelligence.xlsx`` — one row per company
* ``output/distress_alerts.csv``        — companies satisfying the distress signal

Metrics (per the Sprint 5 specification):

1. CFO Quality Score      - average of (CFO / PAT) over the latest 5 available years
2. CapEx Intensity        - abs(investing_activity) / sales * 100  (latest year)
3. FCF CAGR (5 year)      - CAGR of FCF = OCF - |investing_activity|
4. FCF Conversion         - FCF / PAT * 100                        (latest year)
5. Distress Signal        - CFO < 0 AND CFF > 0                    (latest year)
6. Deleveraging Flag      - CFF < 0 AND borrowings declining year-over-year
7. Capital Allocation     - reused from cashflow_kpis.classify_capital_allocation

DATA REALITY / DESIGN NOTES
---------------------------
* The database ``cash_flow`` table stores the statement figures in the
  ``operating_activity``, ``investing_activity``, ``financing_activity`` and
  ``net_cash_flow`` columns.  The canonical-named columns
  (``cash_from_operating_activity`` etc.) exist in the schema but are empty
  (NULL) for every row.  Extraction therefore prefers the populated columns
  and falls back to the canonical names when they are the ones populated.
* Periods are calendar-fiscal strings such as ``Mar 2024`` (``%b %Y``) and
  legacy ``Mar-24`` rows.  Periods are canonicalised and de-duplicated so a
  company-year is counted exactly once.  Non-annual rows (``TTM``,
  ``Mar 2016 9m``, ``Mar 2023 15``, half-year ``Sep YYYY`` / ``YYYY.5``
  balance-sheet rows) are excluded from year-based calculations.
* Missing financial values are never converted to zero.  Metrics that cannot
  be computed return ``None`` and their label/flag is ``"Insufficient Data"``.
* FCF reuses ``cashflow_kpis.calculate_free_cash_flow`` (FCF = OCF - CapEx
  with CapEx = |investing_activity|), so both engines always agree.
* The capital-allocation label reuses ``cashflow_kpis.classify_capital_allocation``
  with that engine's native inputs (cash conversion = OCF/PAT*100 and the
  OCF-based CapEx intensity).  When FCF/OCF are missing the label is
  ``"Insufficient Data"`` instead of the engine's default ``DISTRESSED`` so
  that missing data is never reported as distress.
"""

import re
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from src.config.constants import OUTPUT_DIR
from src.config.logging_config import get_logger
from src.database.connection import get_connection
from src.analytics.cagr import calculate_cagr, FLAG_INSUFFICIENT
from src.analytics.cashflow_kpis import (
    calculate_free_cash_flow,
    calculate_cash_conversion,
    calculate_capex_intensity as calculate_capex_intensity_ocf,
    _get_operating_cash_flow,
    classify_capital_allocation,
    RATING_EXCELLENT,
    RATING_GOOD,
    RATING_MODERATE,
    RATING_WEAK,
    RATING_DISTRESSED,
)

logger = get_logger(__name__)


# =============================================================================
# CONSTANTS
# =============================================================================

# CFO Quality classification thresholds (Sprint 5 specification)
CFO_QUALITY_HIGH_THRESHOLD = 1.0  # ratio > 1.0            -> High Quality
CFO_QUALITY_MODERATE_LOWER = 0.5  # 0.5 <= ratio <= 1.0    -> Moderate
# ratio < 0.5                            -> Accrual Risk

# CapEx Intensity classification thresholds (Sprint 5 specification)
CAPEX_INTENSITY_ASSET_LIGHT = 3.0  # < 3%   -> Asset Light
CAPEX_INTENSITY_MODERATE_UPPER = 8.0  # 3-8%   -> Moderate (3.0 and 8.0 inclusive)
# > 8%   -> Capital Intensive

# Number of latest years used for CFO quality
CFO_QUALITY_YEARS = 5

# CAGR window for FCF
FCF_CAGR_WINDOW_YEARS = 5

# Labels
LABEL_INSUFFICIENT_DATA = "Insufficient Data"
LABEL_HIGH_QUALITY = "High Quality"
LABEL_MODERATE = "Moderate"
LABEL_ACCRUAL_RISK = "Accrual Risk"
LABEL_ASSET_LIGHT = "Asset Light"
LABEL_CAPITAL_INTENSIVE = "Capital Intensive"

VALID_CFO_QUALITY_LABELS = [
    LABEL_HIGH_QUALITY,
    LABEL_MODERATE,
    LABEL_ACCRUAL_RISK,
    LABEL_INSUFFICIENT_DATA,
]

VALID_CAPEX_LABELS = [
    LABEL_ASSET_LIGHT,
    LABEL_MODERATE,
    LABEL_CAPITAL_INTENSIVE,
    LABEL_INSUFFICIENT_DATA,
]

VALID_CAPITAL_ALLOCATION_LABELS = [
    RATING_EXCELLENT,
    RATING_GOOD,
    RATING_MODERATE,
    RATING_WEAK,
    RATING_DISTRESSED,
    LABEL_INSUFFICIENT_DATA,
]

# Output columns (exact order used for the Excel file)
OUTPUT_COLUMNS = [
    "company_id",
    "sector",
    "cfo_quality_score",
    "cfo_quality_label",
    "capex_intensity_pct",
    "capex_label",
    "fcf_cagr_5yr",
    "fcf_conversion_pct",
    "distress_flag",
    "deleveraging_flag",
    "capital_allocation_label",
]

# Distress CSV column names (Sprint 5 specification)
DISTRESS_CSV_COLUMNS = [
    "company_id",
    "sector",
    "CFO",
    "CFF",
    "latest_net_profit",
]

EXCEL_OUTPUT_FILENAME = "cashflow_intelligence.xlsx"
DISTRESS_CSV_FILENAME = "distress_alerts.csv"

# Period parsing helpers
_MONTHS = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}
_ANNUAL_PERIOD_RE = re.compile(r"^([A-Za-z]{3})\s+(\d{4})$")
_LEGACY_PERIOD_RE = re.compile(r"^([A-Za-z]{3})-(\d{2})$")
_YEAR_ONLY_RE = re.compile(r"^(\d{4})$")
# =============================================================================
# PERIOD HELPERS
# =============================================================================


def parse_period(period: Any) -> Optional[Tuple[int, int]]:
    """
    Parse a financial period string into a sortable ``(year, month)`` tuple.

    Supported formats:
    * ``Mar 2013``, ``Sep 2024``  -> (year, month)
    * ``Mar-13`` (legacy)         -> (year, month)
    * ``2013`` (year only)        -> (2013, 12)

    Non-annual or unparsable periods (``TTM``, ``Mar 2016 9m``,
    ``Mar 2023 15``, half-year ``2024.5``) return ``None`` and are excluded
    from year-based calculations.

    Parameters
    ----------
    period : Any
        Period string to parse.

    Returns
    -------
    Optional[Tuple[int, int]]
        ``(year, month)`` tuple, or ``None`` when not a valid annual period.
    """
    if period is None:
        return None
    s = str(period).strip()

    m = _ANNUAL_PERIOD_RE.match(s)
    if m:
        month = _MONTHS.get(m.group(1).lower())
        if month is None:
            return None
        return (int(m.group(2)), month)

    m = _LEGACY_PERIOD_RE.match(s)
    if m:
        month = _MONTHS.get(m.group(1).lower())
        if month is None:
            return None
        return (2000 + int(m.group(2)), month)

    m = _YEAR_ONLY_RE.match(s)
    if m:
        return (int(m.group(1)), 12)

    return None


def is_valid_annual_period(period: Any) -> bool:
    """Return ``True`` when ``period`` is a valid, parseable annual period."""
    return parse_period(period) is not None


# =============================================================================
# DATA EXTRACTION HELPERS
# =============================================================================


def _col_value(row: pd.Series, *columns: str) -> Optional[float]:
    """
    Return the first non-null value found among ``columns`` in ``row``.

    This lets the engine read whichever column family the database actually
    populates (``operating_activity``/``investing_activity``/
    ``financing_activity`` or ``cash_from_operating_activity``/...).
    """
    for col in columns:
        if col not in row.index:
            continue
        v = row[col]
        if v is None:
            continue
        try:
            if pd.isna(v):
                continue
        except (TypeError, ValueError):
            pass
        try:
            return float(v)
        except (TypeError, ValueError):
            continue
    return None


def _normalize_cashflow(cf_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Normalise raw cash-flow rows into sorted, de-duplicated records.

    Returns a list of dicts sorted by ``(year, month)`` with keys:
    ``key``, ``period``, ``ocf``, ``cfi``, ``cff``.  Duplicate company-period
    rows (e.g. legacy ``Mar-13`` + canonical ``Mar 2013`` for TCS) are
    collapsed into a single record.
    """
    if cf_df is None or cf_df.empty:
        return []

    records: Dict[Tuple[int, int], Dict[str, Any]] = {}
    for _, row in cf_df.iterrows():
        key = parse_period(row.get("period"))
        if key is None:
            continue
        ocf = _col_value(row, "cash_from_operating_activity", "operating_activity")
        cfi = _col_value(row, "cash_from_investing_activity", "investing_activity")
        cff = _col_value(row, "cash_from_financing_activity", "financing_activity")
        rec = {
            "key": key,
            "period": str(row["period"]),
            "ocf": ocf,
            "cfi": cfi,
            "cff": cff,
        }

        existing = records.get(key)
        if existing is None:
            records[key] = rec
        else:
            # Merge: prefer non-null values from the later row if the first
            # occurrence carried only NULLs.
            for field in ("ocf", "cfi", "cff"):
                if existing[field] is None and rec[field] is not None:
                    existing[field] = rec[field]

    return sorted(records.values(), key=lambda r: r["key"])


def _normalize_profit_loss(pl_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Normalise raw profit-loss rows into sorted, de-duplicated records.

    Each record has keys ``key``, ``period``, ``sales``, ``net_profit``.
    Non-annual rows (``TTM``, ``Mar 2016 9m``, ``Mar 2023 15``) are excluded.
    """
    if pl_df is None or pl_df.empty:
        return []

    records: Dict[Tuple[int, int], Dict[str, Any]] = {}
    for _, row in pl_df.iterrows():
        key = parse_period(row.get("period"))
        if key is None:
            continue
        rec = {
            "key": key,
            "period": str(row["period"]),
            "sales": _col_value(row, "sales"),
            "net_profit": _col_value(row, "net_profit"),
        }
        existing = records.get(key)
        if existing is None:
            records[key] = rec
        else:
            for field in ("sales", "net_profit"):
                if existing[field] is None and rec[field] is not None:
                    existing[field] = rec[field]

    return sorted(records.values(), key=lambda r: r["key"])


def _normalize_balance_sheet(bs_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Normalise raw balance-sheet rows into sorted, de-duplicated records.

    Each record has keys ``key``, ``period``, ``borrowings``.  Half-year stub
    periods (``Sep YYYY`` appended after a full-year row, ``YYYY.5``) are
    excluded through :func:`parse_period` where applicable.
    """
    if bs_df is None or bs_df.empty:
        return []

    records: Dict[Tuple[int, int], Dict[str, Any]] = {}
    for _, row in bs_df.iterrows():
        key = parse_period(row.get("period"))
        if key is None:
            continue
        rec = {
            "key": key,
            "period": str(row["period"]),
            "borrowings": _col_value(row, "borrowings"),
        }
        existing = records.get(key)
        if existing is None:
            records[key] = rec
        else:
            if existing["borrowings"] is None and rec["borrowings"] is not None:
                existing["borrowings"] = rec["borrowings"]

    return sorted(records.values(), key=lambda r: r["key"])


def _single_cf_df(ocf: float, cfi: float) -> pd.DataFrame:
    """Build a single-row cash-flow DataFrame using canonical column names."""
    return pd.DataFrame(
        [
            {
                "cash_from_operating_activity": ocf,
                "cash_from_investing_activity": cfi,
            }
        ]
    )


def _latest_net_profit(pl_df: pd.DataFrame) -> Optional[float]:
    """Latest valid annual net profit for a company."""
    rows = _normalize_profit_loss(pl_df)
    if not rows:
        return None
    return rows[-1]["net_profit"]


# =============================================================================
# METRIC FUNCTIONS
# =============================================================================


def compute_cfo_quality(cf_df: pd.DataFrame, pl_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute the CFO Quality Score.

    For each available year:  ratio = CFO / PAT
    Score = average of the latest 5 available annual ratios.

    Classification:
    * ratio > 1.0                  -> "High Quality"
    * 0.5 <= ratio <= 1.0          -> "Moderate" (boundaries inclusive)
    * ratio < 0.5 (incl. negative) -> "Accrual Risk"

    Years with ``PAT == 0``, missing CFO or missing PAT are skipped; they are
    never silently treated as zero.

    Returns
    -------
    Dict[str, Any]
        Keys: ``score`` (float or None), ``label`` (str), ``years_used`` (int).
    """
    cf_rows = _normalize_cashflow(cf_df)
    pl_by_key = {r["key"]: r for r in _normalize_profit_loss(pl_df)}

    ratios: List[Tuple[Tuple[int, int], float]] = []
    for cf_row in cf_rows:
        pl_row = pl_by_key.get(cf_row["key"])
        if pl_row is None:
            continue
        ocf = cf_row["ocf"]
        pat = pl_row["net_profit"]
        if ocf is None or pat is None:
            continue
        if pat == 0:
            continue  # division by zero is not meaningful; never fabricate
        ratios.append((cf_row["key"], ocf / pat))

    ratios.sort(key=lambda x: x[0])
    latest_ratios = [value for _, value in ratios[-CFO_QUALITY_YEARS:]]

    if not latest_ratios:
        return {"score": None, "label": LABEL_INSUFFICIENT_DATA, "years_used": 0}

    score = round(sum(latest_ratios) / len(latest_ratios), 2)
    if score > CFO_QUALITY_HIGH_THRESHOLD:
        label = LABEL_HIGH_QUALITY
    elif score >= CFO_QUALITY_MODERATE_LOWER:
        label = LABEL_MODERATE
    else:
        label = LABEL_ACCRUAL_RISK

    return {"score": score, "label": label, "years_used": len(latest_ratios)}


def compute_capex_intensity(cf_df: pd.DataFrame, pl_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute CapEx Intensity for the latest year.

    Formula (Sprint 5):  abs(investing_activity) / sales * 100

    This deliberately uses sales as the denominator (NOT the OCF-based
    ``cashflow_kpis.calculate_capex_intensity`` which uses operating cash
    flow as the denominator).

    Classification:
    * value < 3%              -> "Asset Light"
    * 3% <= value <= 8%       -> "Moderate" (3.0 and 8.0 inclusive)
    * value > 8%              -> "Capital Intensive"

    Returns
    -------
    Dict[str, Any]
        Keys: ``value`` (float or None), ``label`` (str).
    """
    cf_rows = _normalize_cashflow(cf_df)
    pl_by_key = {r["key"]: r for r in _normalize_profit_loss(pl_df)}

    common = [(r, pl_by_key[r["key"]]) for r in cf_rows if r["key"] in pl_by_key]
    if not common:
        return {"value": None, "label": LABEL_INSUFFICIENT_DATA}

    cf_row, pl_row = common[-1]  # latest year present in both statements
    investing = cf_row["cfi"]
    sales = pl_row["sales"]

    if investing is None or sales is None:
        return {"value": None, "label": LABEL_INSUFFICIENT_DATA}
    if sales == 0:
        return {"value": None, "label": LABEL_INSUFFICIENT_DATA}

    value = round((abs(investing) / sales) * 100, 2)

    if value < CAPEX_INTENSITY_ASSET_LIGHT:
        label = LABEL_ASSET_LIGHT
    elif value <= CAPEX_INTENSITY_MODERATE_UPPER:
        label = LABEL_MODERATE
    else:
        label = LABEL_CAPITAL_INTENSIVE

    return {"value": value, "label": label}


def compute_fcf_cagr_5yr(cf_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute the 5-year Free Cash Flow CAGR.

    FCF per year = OCF - |investing_activity| (reusing
    ``cashflow_kpis.calculate_free_cash_flow``).

    The CAGR is computed between the latest annual FCF point and the point
    closest to 5 years earlier (or the earliest point when fewer than 6 valid
    annual points exist), using the actual calendar-year span capped at 5
    years — consistent with the existing ``cagr.calculate_cagr`` conventions.

    Edge cases (zero base, negative base, decline to loss, turnaround,
    both-negative, insufficient history) are delegated to
    ``cagr.calculate_cagr``.

    Returns
    -------
    Dict[str, Any]
        Keys: ``value`` (float or None), ``flag`` (str or None), ``years_used``.
    """
    cf_rows = _normalize_cashflow(cf_df)

    fcf_series: List[Tuple[Tuple[int, int], float]] = []
    for cf_row in cf_rows:
        ocf = cf_row["ocf"]
        cfi = cf_row["cfi"]
        if ocf is None or cfi is None:
            continue  # FCF is not meaningful when either input is missing
        fcf = calculate_free_cash_flow(_single_cf_df(ocf, cfi))
        if fcf is None:
            continue
        fcf_series.append((cf_row["key"], fcf))

    if len(fcf_series) < 2:
        return {"value": None, "flag": FLAG_INSUFFICIENT, "years_used": len(fcf_series)}

    end_key, end_fcf = fcf_series[-1]
    start_key, start_fcf = (
        fcf_series[-(FCF_CAGR_WINDOW_YEARS + 1)]
        if len(fcf_series) >= FCF_CAGR_WINDOW_YEARS + 1
        else fcf_series[0]
    )

    years = min(end_key[0] - start_key[0], FCF_CAGR_WINDOW_YEARS)
    if years <= 0:
        return {"value": None, "flag": FLAG_INSUFFICIENT, "years_used": len(fcf_series)}

    result = calculate_cagr(start_fcf, end_fcf, years, "fcf")
    return {
        "value": result["value"],
        "flag": result["flag"],
        "years_used": len(fcf_series),
    }


def compute_fcf_conversion(cf_df: pd.DataFrame, pl_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute FCF Conversion for the latest year:  FCF / PAT * 100.

    ``PAT == 0`` or missing data returns ``None`` (never a fabricated value).

    Returns
    -------
    Dict[str, Any]
        Keys: ``value`` (float or None), ``flag`` (str or None).
    """
    cf_rows = _normalize_cashflow(cf_df)
    pl_by_key = {r["key"]: r for r in _normalize_profit_loss(pl_df)}

    common = [(r, pl_by_key[r["key"]]) for r in cf_rows if r["key"] in pl_by_key]
    if not common:
        return {"value": None, "flag": "INSUFFICIENT_DATA"}

    cf_row, pl_row = common[-1]
    if cf_row["ocf"] is None or cf_row["cfi"] is None:
        return {"value": None, "flag": "INSUFFICIENT_FCF"}

    fcf = calculate_free_cash_flow(_single_cf_df(cf_row["ocf"], cf_row["cfi"]))
    if fcf is None:
        return {"value": None, "flag": "INSUFFICIENT_FCF"}

    pat = pl_row["net_profit"]
    if pat is None:
        return {"value": None, "flag": "INSUFFICIENT_PAT"}
    if pat == 0:
        return {"value": None, "flag": "ZERO_PAT"}

    return {"value": round((fcf / pat) * 100, 2), "flag": None}


def compute_distress_flag(cf_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute the Distress Signal for the latest year.

    Signal:  CFO < 0 AND CFF > 0  ->  True, otherwise False.

    Missing CFO/CFF never produce ``True`` (no fabrication).

    Returns
    -------
    Dict[str, Any]
        Keys: ``flag`` (bool), ``cfo``, ``cff`` (float or None), ``period``.
    """
    cf_rows = _normalize_cashflow(cf_df)
    if not cf_rows:
        return {"flag": False, "cfo": None, "cff": None, "period": None}

    latest = cf_rows[-1]
    cfo = latest["ocf"]
    cff = latest["cff"]
    if cfo is None or cff is None:
        return {"flag": False, "cfo": cfo, "cff": cff, "period": latest["period"]}

    return {
        "flag": bool(cfo < 0 and cff > 0),
        "cfo": cfo,
        "cff": cff,
        "period": latest["period"],
    }


def _fiscal_month(bs_rows: List[Dict[str, Any]]) -> Optional[int]:
    """
    Determine the dominant fiscal year-end month from balance-sheet periods.

    Companies that publish an extra half-year row (``Sep YYYY``) in addition to
    their full-year rows keep their real fiscal month (Mar for most N100
    companies).  Companies whose fiscal year actually ends in September
    (e.g. SIEMENS) keep September.
    """
    months = [r["key"][1] for r in bs_rows]
    if not months:
        return None
    return max(set(months), key=months.count)


def compute_deleveraging_flag(
    cf_df: pd.DataFrame, bs_df: pd.DataFrame
) -> Dict[str, Any]:
    """
    Compute the Deleveraging Flag for the latest year.

    Flag is ``True`` when all of the following hold:
    * latest-year CFF < 0, AND
    * borrowings are declining year-over-year using the latest two valid
      annual balance-sheet periods consistent with the company's fiscal
      year-end month.

    Missing borrowings are never treated as zero; if fewer than two valid
    annual borrowings points exist the flag is ``False``.

    Returns
    -------
    Dict[str, Any]
        Keys: ``flag`` (bool), ``cff`` (float or None), ``borrowings_change``.
    """
    cf_rows = _normalize_cashflow(cf_df)
    bs_rows = _normalize_balance_sheet(bs_df)

    if not cf_rows:
        return {"flag": False, "cff": None, "borrowings_change": None}

    latest_cff = cf_rows[-1]["cff"]
    if latest_cff is None:
        return {"flag": False, "cff": None, "borrowings_change": None}

    fiscal_month = _fiscal_month(bs_rows)
    if fiscal_month is None:
        return {"flag": False, "cff": latest_cff, "borrowings_change": None}

    annual_borrowings = [
        r
        for r in bs_rows
        if r["key"][1] == fiscal_month and r["borrowings"] is not None
    ]
    if len(annual_borrowings) < 2:
        return {"flag": False, "cff": latest_cff, "borrowings_change": None}

    previous = annual_borrowings[-2]["borrowings"]
    latest = annual_borrowings[-1]["borrowings"]
    borrowings_change = latest - previous  # negative -> declining

    return {
        "flag": bool(latest_cff < 0 and borrowings_change < 0),
        "cff": latest_cff,
        "borrowings_change": borrowings_change,
    }


def compute_capital_allocation_label(cf_df: pd.DataFrame, pl_df: pd.DataFrame) -> str:
    """
    Compute the Capital Allocation Label by reusing the existing engine.

    The existing ``cashflow_kpis.classify_capital_allocation`` engine is called
    with its native inputs:

    * ``fcf``             = OCF - |investing_activity|
    * ``cash_conversion`` = OCF / PAT * 100
    * ``capex_intensity`` = |investing_activity| / OCF * 100 (OCF-based,
                           the convention the existing engine was designed for)
    * ``ocf``             = operating cash flow

    When FCF or OCF are missing the label is ``"Insufficient Data"`` rather
    than the engine's default ``DISTRESSED`` (missing data must never be
    reported as distress).
    """
    cf_rows = _normalize_cashflow(cf_df)
    pl_by_key = {r["key"]: r for r in _normalize_profit_loss(pl_df)}

    common = [(r, pl_by_key[r["key"]]) for r in cf_rows if r["key"] in pl_by_key]
    if not common:
        return LABEL_INSUFFICIENT_DATA

    cf_row, pl_row = common[-1]
    if cf_row["ocf"] is None or cf_row["cfi"] is None:
        return LABEL_INSUFFICIENT_DATA

    cf_single = _single_cf_df(cf_row["ocf"], cf_row["cfi"])
    pl_single = pd.DataFrame(
        [
            {
                "sales": pl_row["sales"],
                "net_profit": pl_row["net_profit"],
            }
        ]
    )

    fcf = calculate_free_cash_flow(cf_single)
    ocf = _get_operating_cash_flow(cf_single)
    if fcf is None or ocf is None:
        return LABEL_INSUFFICIENT_DATA

    cash_conversion = calculate_cash_conversion(cf_single, pl_single)["value"]
    capex_intensity = calculate_capex_intensity_ocf(cf_single)

    return classify_capital_allocation(fcf, cash_conversion, capex_intensity, ocf)
