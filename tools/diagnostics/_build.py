#!/usr/bin/env python3
"""Write the complete pros_cons_generator.py module in chunks."""

chunks = []

chunks.append(r'''
"""
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

chunks.append(r'''

# =============================================================================
# DATA LOADING
# =============================================================================


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

chunks.append(r'''

# =============================================================================
# PERIOD HELPERS
# =============================================================================


def _parse_period_year(period: Optional[str]) -> Optional[int]:
    """Extract year integer from period string."""
    if not period:
        return None
    period = str(period).strip()
    for part in period.split():
        if part.isdigit() and len(part) == 4:
            return int(part)
    if "-" in period:
        for part in period.split("-"):
            part = part.strip()
            if part.isdigit():
                year = int(part)
                return 2000 + year if year < 100 else year
    return None


def _deduplicate_annual(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Keep only the latest entry per year."""
    year_map: Dict[int, Dict[str, Any]] = {}
    for rec in records:
        year = _parse_period_year(rec.get("period"))
        if year is None:
            continue
        if year not in year_map:
            year_map[year] = rec
    result = sorted(
        year_map.values(),
        key=lambda r: _parse_period_year(r.get("period")) or 0,
        reverse=True,
    )
    return result


# =============================================================================
# VALUE HELPERS
# =============================================================================


def _safe_float(value: Any) -> Optional[float]:
    """Safely convert value to float, returning None for invalid input."""
    if value is None:
        return None
    try:
        v = float(value)
        return v if not (np.isnan(v) or np.isinf(v)) else None
    except (TypeError, ValueError):
        return None


def _get_numeric(records: List[Dict[str, Any]], key: str, index: int = 0) -> Optional[float]:
    """Get a numeric value from records at a given index (0 = newest)."""
    if index < 0 or index >= len(records):
        return None
    return _safe_float(records[index].get(key))


def _extract_annual_trend(
    records: List[Dict[str, Any]], key: str, n_years: int

chunks.append(r'''

# =============================================================================
# CONFIDENCE SCORING
# =============================================================================


def calculate_confidence(
    value: Optional[float],
    threshold: float,
    *,
    higher_is_better: bool = True,
    distance_factor: float = CONFIDENCE_DISTANCE_FACTOR,
) -> Optional[float]:
    """
    Compute deterministic confidence score for a threshold-based rule.
    confidence = clamp(CONFIDENCE_BASE + raw_distance * distance_factor, 61, 95)
    """
    if value is None:
        return None
    raw_distance = (value - threshold) / max(abs(threshold), 1e-9)
    if not higher_is_better:
        raw_distance = -raw_distance
    confidence = CONFIDENCE_BASE + raw_distance * distance_factor
    confidence = max(CONFIDENCE_MIN, min(CONFIDENCE_MAX, confidence))
    return round(confidence, 2)


def calculate_trend_confidence(
    values: List[Optional[float]],
    *,
    improving: bool = True,
) -> Optional[float]:
    """Compute confidence for a trend rule using average YoY relative change."""
    valid = [v for v in values if v is not None]
    if len(valid) < 2:
        return None
    changes = []
    for i in range(len(valid) - 1):
        older = valid[i + 1]
        newer = valid[i]
        if older == 0:
            changes.append(1.0 if newer > 0 else -1.0)
        else:
            changes.append((newer - older) / abs(older))
    if improving:
        avg_change = sum(changes) / len(changes)
    else:
        avg_change = sum(changes) / len(changes)
    if not improving:
        avg_change = -avg_change
    confidence = CONFIDENCE_BASE + avg_change * CONFIDENCE_DISTANCE_FACTOR
    confidence = max(CONFIDENCE_MIN, min(CONFIDENCE_MAX, confidence))
    return round(confidence, 2)


# =============================================================================
# PRO RULES (1-6)
# =============================================================================


def _pro_01_roe_sustained(data):
    """PRO_01: ROE > 20% sustained for 3+ consecutive years."""
    roe_values = _extract_annual_trend(data["annual_kpis"], "roe", PRO_01_ROE_YEARS)
    valid = [v for v in roe_values if v is not None]
    if len(valid) < PRO_01_ROE_YEARS:
        return None
    if all(v > PRO_01_ROE_THRESHOLD for v in valid):
        confidence = calculate_confidence(valid[0], PRO_01_ROE_THRESHOLD, higher_is_better=True)
        return {"rule_id": "PRO_01", "text": "Consistently high return on equity above 20% demonstrates exceptional capital efficiency", "confidence_pct": confidence}
    return None


def _pro_02_fcf_positive_5yr(data):
    """PRO_02: FCF positive for 5+ consecutive years."""
    fcf_values = _extract_annual_trend(data["annual_kpis"], "free_cash_flow", PRO_02_FCF_YEARS)
    valid_fcf = [v for v in fcf_values if v is not None]
    if len(valid_fcf) < PRO_02_FCF_YEARS:
        cf_values = _extract_annual_trend(data["cash_flow"], "free_cash_flow", PRO_02_FCF_YEARS)
        valid_fcf = [v for v in cf_values if v is not None]
    if len(valid_fcf) < PRO_02_FCF_YEARS:
        return None
    if all(v > 0 for v in valid_fcf):
        confidence = calculate_confidence(valid_fcf[0], 0, higher_is_better=True)
        return {"rule_id": "PRO_02", "text": "Strong free cash flow generation over 5 years signals healthy business fundamentals", "confidence_pct": confidence}
    return None


def _pro_03_debt_free(data):
    """PRO_03: Latest-year D/E = 0 (debt-free)."""
    de = _get_numeric(data["annual_kpis"], "debt_to_equity", 0)
    if de is None:
        bs = _deduplicate_annual(data["annual_bs"])
        if bs:
            borrowings = _safe_float(bs[0].get("borrowings"))
            if borrowings is not None and borrowings == 0:
                de = 0.0
    if de is not None and de == 0.0:
        return {"rule_id": "PRO_03", "text": "Debt-free balance sheet provides financial flexibility and eliminates interest burden", "confidence_pct": CONFIDENCE_MAX}
    return None


def _pro_04_revenue_cagr_5yr(data):
    """PRO_04: Revenue CAGR > 15% over 5 years (from TTM row)."""
    ttm = data.get("ttm_kpis")
    if not ttm:
        return None
    cagr = _safe_float(ttm.get("revenue_cagr"))
    if cagr is None:
        return None
    if cagr > PRO_04_REVENUE_CAGR_THRESHOLD:
        confidence = calculate_confidence(cagr, PRO_04_REVENUE_CAGR_THRESHOLD, higher_is_better=True)
        return {"rule_id": "PRO_04", "text": "Revenue growing at above 15% CAGR over 5 years reflects strong business momentum", "confidence_pct": confidence}
    return None


def _pro_05_opm_latest(data):
    """PRO_05: Latest-year OPM > 25%."""
    opm = _get_numeric(data["annual_kpis"], "operating_margin", 0)
    if opm is None:
        opm = _get_numeric(data["annual_pl"], "opm_percentage", 0)
    if opm is not None and opm > PRO_05_OPM_THRESHOLD:

chunks.append(r'''

def _pro_07_icr_high_or_debt_free(data):
    """PRO_07: ICR > 10 OR Debt Free."""
    de = _get_numeric(data["annual_kpis"], "debt_to_equity", 0)
    if de is None:
        bs = _deduplicate_annual(data["annual_bs"])
        if bs:
            borrowings = _safe_float(bs[0].get("borrowings"))
            if borrowings is not None and borrowings == 0:
                de = 0.0
    if de is not None and de == 0.0:
        return {"rule_id": "PRO_07", "text": "Very high interest coverage ratio reflects negligible financial stress from debt servicing", "confidence_pct": CONFIDENCE_MAX}
    icr = _get_numeric(data["annual_kpis"], "interest_coverage", 0)
    if icr is not None and icr > PRO_07_ICR_THRESHOLD:
        confidence = calculate_confidence(icr, PRO_07_ICR_THRESHOLD, higher_is_better=True)
        return {"rule_id": "PRO_07", "text": "Very high interest coverage ratio reflects negligible financial stress from debt servicing", "confidence_pct": confidence}
    return None


def _pro_08_dividend_yield_fcf(data):
    """PRO_08: Dividend Yield > 2% AND FCF positive."""
    ttm = data.get("ttm_kpis")
    if not ttm:
        return None
    div_yield = _safe_float(ttm.get("dividend_yield"))
    if div_yield is None or div_yield <= PRO_08_DIV_YIELD_THRESHOLD:
        return None
    fcf_values = _extract_annual_trend(data["annual_kpis"], "free_cash_flow", 1)
    valid_fcf = [v for v in fcf_values if v is not None]
    if not valid_fcf:
        cf_values = _extract_annual_trend(data["cash_flow"], "free_cash_flow", 1)
        valid_fcf = [v for v in cf_values if v is not None]
    if not valid_fcf or valid_fcf[0] <= 0:
        return None
    confidence = calculate_confidence(div_yield, PRO_08_DIV_YIELD_THRESHOLD, higher_is_better=True)
    return {"rule_id": "PRO_08", "text": "Consistent dividend yield above 2% backed by positive free cash flow", "confidence_pct": confidence}


def _pro_09_eps_cagr_5yr(data):
    """PRO_09: EPS CAGR > 15% over 5 years (from TTM row)."""
    ttm = data.get("ttm_kpis")
    if not ttm:
        return None
    cagr = _safe_float(ttm.get("eps_cagr"))
    if cagr is None:
        return None
    if cagr > PRO_09_EPS_CAGR_THRESHOLD:
        confidence = calculate_confidence(cagr, PRO_09_EPS_CAGR_THRESHOLD, higher_is_better=True)
        return {"rule_id": "PRO_09", "text": "Earnings per share growing above 15% CAGR indicates strong earnings quality and compounding", "confidence_pct": confidence}
    return None


def _pro_10_roe_improving_3yr(data):
    """PRO_10: ROE improving for 3 consecutive years."""
    roe_values = _extract_annual_trend(data["annual_kpis"], "roe", PRO_10_ROE_IMPROVE_YEARS)
    valid = [v for v in roe_values if v is not None]
    if len(valid) < PRO_10_ROE_IMPROVE_YEARS:
        return None
    improving = all(valid[i] > valid[i + 1] for i in range(len(valid) - 1))
    if improving:
        confidence = calculate_trend_confidence(valid, improving=True)
        return {"rule_id": "PRO_10", "text": "Return on equity improving for 3 consecutive years shows strengthening business quality", "confidence_pct": confidence}
    return None


def _pro_11_revenue_cagr_gt_pat_cagr(data):
    """
    PRO_11: Revenue CAGR > PAT CAGR.
    NOTE: Condition implemented as stated; text may contradict condition.
    """
    ttm = data.get("ttm_kpis")
    if not ttm:
        return None
    rev_cagr = _safe_float(ttm.get("revenue_cagr"))
    pat_cagr = _safe_float(ttm.get("profit_cagr"))
    if rev_cagr is None or pat_cagr is None:
        return None
    if rev_cagr > pat_cagr:
        diff = rev_cagr - pat_cagr
        raw_distance = diff / max(abs(pat_cagr), 1e-9)
        confidence = CONFIDENCE_BASE + raw_distance * CONFIDENCE_DISTANCE_FACTOR
        confidence = max(CONFIDENCE_MIN, min(CONFIDENCE_MAX, confidence))
        confidence = round(confidence, 2)
        return {"rule_id": "PRO_11", "text": "Revenue growing slower than profits shows improving operating leverage and scale benefits", "confidence_pct": confidence}
    return None


def _pro_12_assets_growing_debt_declining(data):
    """PRO_12: Balance sheet assets growing with declining debt."""
    bs = _deduplicate_annual(data["annual_bs"])
    if len(bs) < 2:
        return None
    assets = [_safe_float(bs[i].get("total_assets")) for i in range(2)]
    borrowings = [_safe_float(bs[i].get("borrowings")) for i in range(2)]
    if any(v is None for v in assets + borrowings):
        return None
    if assets[0] > assets[1] and borrowings[0] < borrowings[1]:
        asset_change = (assets[0] - assets[1]) / max(abs(assets[1]), 1e-9)
        debt_change = (borrowings[1] - borrowings[0]) / max(abs(borrowings[1]), 1e-9)
        raw_distance = (asset_change + debt_change) / 2
        confidence = CONFIDENCE_BASE + raw_distance * CONFIDENCE_DISTANCE_FACTOR
        confidence = max(CONFIDENCE_MIN, min(CONFIDENCE_MAX, confidence))

chunks.append(r'''

# =============================================================================
# CON RULES (1-6)
# =============================================================================


def _con_01_de_high_non_financial(data, conn):
    """CON_01: D/E > 2.0 AND NOT Financials."""
    if data.get("is_financial", False):
        return None
    de = _get_numeric(data["annual_kpis"], "debt_to_equity", 0)
    if de is None:
        bs = _deduplicate_annual(data["annual_bs"])
        if bs:
            borrowings = _safe_float(bs[0].get("borrowings"))
            equity = _safe_float(bs[0].get("equity_capital")) or 0
            reserves = _safe_float(bs[0].get("reserves")) or 0
            total_equity = equity + reserves
            if total_equity > 0 and borrowings is not None:
                de = borrowings / total_equity
    if de is not None and de > CON_01_DE_THRESHOLD:
        confidence = calculate_confidence(de, CON_01_DE_THRESHOLD, higher_is_better=False)
        de_str = f"{de:.2f}"
        return {"rule_id": "CON_01", "text": f"Debt-to-equity ratio of {de_str} is elevated for a non-financial company and warrants monitoring", "confidence_pct": confidence}
    return None


def _con_02_fcf_negative_3yr(data):
    """CON_02: FCF negative for 3 consecutive years."""
    fcf_values = _extract_annual_trend(data["annual_kpis"], "free_cash_flow", CON_02_FCF_YEARS)
    valid_fcf = [v for v in fcf_values if v is not None]
    if len(valid_fcf) < CON_02_FCF_YEARS:
        cf_values = _extract_annual_trend(data["cash_flow"], "free_cash_flow", CON_02_FCF_YEARS)
        valid_fcf = [v for v in cf_values if v is not None]
    if len(valid_fcf) < CON_02_FCF_YEARS:
        return None
    if all(v < 0 for v in valid_fcf):
        confidence = calculate_confidence(valid_fcf[0], 0, higher_is_better=False)
        return {"rule_id": "CON_02", "text": "Free cash flow negative for 3 consecutive years raises concern about cash generation quality", "confidence_pct": confidence}
    return None


def _con_03_opm_declining_3yr(data):
    """CON_03: OPM declining for 3 consecutive years."""
    opm_values = _extract_annual_trend(data["annual_kpis"], "operating_margin", CON_03_OPM_DECLINE_YEARS)
    valid_opm = [v for v in opm_values if v is not None]
    if len(valid_opm) < CON_03_OPM_DECLINE_YEARS:
        opm_values_pl = _extract_annual_trend(data["annual_pl"], "opm_percentage", CON_03_OPM_DECLINE_YEARS)
        valid_opm = [v for v in opm_values_pl if v is not None]
    if len(valid_opm) < CON_03_OPM_DECLINE_YEARS:
        return None
    declining = all(valid_opm[i] < valid_opm[i + 1] for i in range(len(valid_opm) - 1))
    if declining:
        confidence = calculate_trend_confidence(valid_opm, improving=False)
        return {"rule_id": "CON_03", "text": "Operating margins declining for 3 consecutive years suggest pricing or cost pressure", "confidence_pct": confidence}
    return None


def _con_04_net_loss_latest(data):
    """CON_04: Latest-year net profit < 0."""
    net_profit = _get_numeric(data["annual_pl"], "net_profit", 0)
    if net_profit is not None and net_profit < 0:
        confidence = calculate_confidence(net_profit, 0, higher_is_better=False)
        return {"rule_id": "CON_04", "text": "Company reported a net loss in the most recent financial year", "confidence_pct": confidence}
    return None


def _con_05_revenue_declining_2yr(data):
    """CON_05: Revenue declining for 2+ years."""
    revenue_values = _extract_annual_trend(data["annual_pl"], "sales", CON_05_REVENUE_DECLINE_YEARS + 1)
    valid = [v for v in revenue_values if v is not None]
    if len(valid) < CON_05_REVENUE_DECLINE_YEARS + 1:
        return None
    declining = all(valid[i] < valid[i + 1] for i in range(CON_05_REVENUE_DECLINE_YEARS))
    if declining:
        confidence = calculate_trend_confidence(valid[: CON_05_REVENUE_DECLINE_YEARS + 1], improving=False)

chunks.append(r'''

# =============================================================================
# CON RULES (7-12)
# =============================================================================


def _con_07_dividend_payout_over_100(data):
    """CON_07: Dividend payout > 100%."""
    payout = _get_numeric(data["annual_pl"], "dividend_payout", 0)
    if payout is not None and payout > 100:
        confidence = calculate_confidence(payout, 100, higher_is_better=False)
        return {"rule_id": "CON_07", "text": "Dividend payout ratio above 100% means the company is paying dividends from reserves, which is unsustainable", "confidence_pct": confidence}
    return None


def _con_08_de_rising_3yr(data):
    """CON_08: D/E rising for 3 consecutive years."""
    de_values = _extract_annual_trend(data["annual_kpis"], "debt_to_equity", CON_08_DE_RISE_YEARS)
    valid = [v for v in de_values if v is not None]
    if len(valid) < CON_08_DE_RISE_YEARS:
        bs = _deduplicate_annual(data["annual_bs"])
        if len(bs) >= CON_08_DE_RISE_YEARS:
            computed = []
            for i in range(CON_08_DE_RISE_YEARS):
                borrowings = _safe_float(bs[i].get("borrowings"))
                equity = _safe_float(bs[i].get("equity_capital")) or 0
                reserves = _safe_float(bs[i].get("reserves")) or 0
                total_equity = equity + reserves
                if total_equity > 0 and borrowings is not None:
                    computed.append(borrowings / total_equity)
            valid = computed
    if len(valid) < CON_08_DE_RISE_YEARS:
        return None
    rising = all(valid[i] > valid[i + 1] for i in range(len(valid) - 1))
    if rising:
        confidence = calculate_trend_confidence(valid, improving=True)
        return {"rule_id": "CON_08", "text": "Rising debt-to-equity ratio over 3 years suggests increasing financial leverage risk", "confidence_pct": confidence}
    return None


def _con_09_eps_declining_3yr(data):
    """CON_09: EPS declining for 3 consecutive years."""
    eps_values = _extract_annual_trend(data["annual_pl"], "eps", CON_09_EPS_DECLINE_YEARS)
    valid = [v for v in eps_values if v is not None]
    if len(valid) < CON_09_EPS_DECLINE_YEARS:
        eps_values_fk = _extract_annual_trend(data["annual_kpis"], "eps", CON_09_EPS_DECLINE_YEARS)
        valid = [v for v in eps_values_fk if v is not None]
    if len(valid) < CON_09_EPS_DECLINE_YEARS:
        return None
    declining = all(valid[i] < valid[i + 1] for i in range(len(valid) - 1))
    if declining:
        confidence = calculate_trend_confidence(valid, improving=False)
        return {"rule_id": "CON_09", "text": "Earnings per share declining for 3 consecutive years reflects deteriorating profitability", "confidence_pct": confidence}
    return None


def _con_10_roce_low(data):
    """CON_10: ROCE < 10%."""
    roce = _get_numeric(data["annual_kpis"], "roce", 0)
    if roce is not None and roce < CON_10_ROCE_THRESHOLD:
        confidence = calculate_confidence(roce, CON_10_ROCE_THRESHOLD, higher_is_better=False)
        return {"rule_id": "CON_10", "text": "Return on capital employed below 10% suggests the business is not generating sufficient returns on invested capital", "confidence_pct": confidence}
    return None


def _con_11_net_debt_high(data):
    """CON_11: Net Debt > 3 x EBITDA."""
    bs = _deduplicate_annual(data["annual_bs"])
    if not bs:
        return None
    borrowings = _safe_float(bs[0].get("borrowings"))
    investments = _safe_float(bs[0].get("investments"))
    net_debt = (borrowings or 0) - (investments or 0)
    pl = data["annual_pl"]
    if not pl:
        return None

chunks.append(r'''

# =============================================================================
# EVALUATION
# =============================================================================


def evaluate_pro_rules(data, conn):
    """Evaluate all 12 Pro rules for a single company."""
    results = []
    for rule_fn in PRO_RULE_FUNCTIONS:
        try:
            result = rule_fn(data)
            if result:
                results.append(result)
        except Exception as exc:
            logger.warning("Pro rule %s failed for %s: %s", rule_fn.__name__, data.get("company_id"), exc)
    return results


def evaluate_con_rules(data, conn):
    """Evaluate all 12 Con rules for a single company."""
    results = []
    for rule_fn in CON_RULE_FUNCTIONS:
        try:
            result = rule_fn(data, conn)
            if result:
                results.append(result)
        except Exception as exc:
            logger.warning("Con rule %s failed for %s: %s", rule_fn.__name__, data.get("company_id"), exc)
    return results


def generate_company_pros_cons(company_id, conn):
    """Generate Pros and Cons for a single company."""
    data = load_company_data(company_id, conn)
    pros = evaluate_pro_rules(data, conn)
    cons = evaluate_con_rules(data, conn)
    return pros, cons


# =============================================================================
# PIPELINE
# =============================================================================


def generate_all_pros_cons(db_path=DEFAULT_DB_PATH):
    """Generate Pros and Cons for all companies. Returns (pros_df, cons_df, stats)."""
    overall_start = time.time()
    logger.info("=" * 80)
    logger.info("Starting Pros/Cons generation for all companies")
    logger.info("=" * 80)
    conn = get_connection(db_path)
    try:
        cursor = conn.execute("SELECT company_id FROM companies ORDER BY company_id")
        all_company_ids = [row["company_id"] for row in cursor.fetchall()]
        total_companies = len(all_company_ids)
        logger.info("Found %d companies", total_companies)
        all_rows = []
        companies_with_pros = set()
        companies_with_cons = set()
        companies_no_output = set()
        rule_trigger_counts = {}
        for idx, company_id in enumerate(all_company_ids):
            if (idx + 1) % 20 == 0 or (idx + 1) == total_companies:
                logger.info("Processing %d/%d: %s", idx + 1, total_companies, company_id)
            try:
                pros, cons = generate_company_pros_cons(company_id, conn)
                for rule in pros:
                    rule["company_id"] = company_id
                    rule["type"] = "pro"
                    all_rows.append(rule)
                    companies_with_pros.add(company_id)
                    rule_trigger_counts[rule["rule_id"]] = rule_trigger_counts.get(rule["rule_id"], 0) + 1
                for rule in cons:
                    rule["company_id"] = company_id
                    rule["type"] = "con"
                    all_rows.append(rule)
                    companies_with_cons.add(company_id)
                    rule_trigger_counts[rule["rule_id"]] = rule_trigger_counts.get(rule["rule_id"], 0) + 1
                if not pros and not cons:
                    companies_no_output.add(company_id)
            except Exception as exc:
                logger.error("Error processing %s: %s", company_id, exc)
                companies_no_output.add(company_id)
        conn.close()
        if all_rows:
            df = pd.DataFrame(all_rows)
            df = df[df["confidence_pct"] > 60].copy()
            df = df[["company_id", "type", "rule_id", "text", "confidence_pct"]]
            df = df.drop_duplicates(subset=["company_id", "type", "rule_id"], keep="first")
            df = df.sort_values(by=["company_id", "type", "rule_id"]).reset_index(drop=True)
        else:
            df = pd.DataFrame(columns=["company_id", "type", "rule_id", "text", "confidence_pct"])
        pros_df = df[df["type"] == "pro"].copy().reset_index(drop=True)
        cons_df = df[df["type"] == "con"].copy().reset_index(drop=True)
        elapsed = time.time() - overall_start
        stats = {
            "total_companies": total_companies,

chunks.append(r'''

# =============================================================================
# VALIDATION
# =============================================================================


def validate_company_coverage(df, db_path=DEFAULT_DB_PATH):
    """Validate every company has >=1 Pro AND >=1 Con."""
    conn = get_connection(db_path)
    try:
        cursor = conn.execute("SELECT company_id FROM companies ORDER BY company_id")
        all_companies = {row["company_id"] for row in cursor.fetchall()}
    finally:
        conn.close()
    companies_with_pros = set(df[df["type"] == "pro"]["company_id"].unique())
    companies_with_cons = set(df[df["type"] == "con"]["company_id"].unique())
    missing_pros = sorted(all_companies - companies_with_pros)
    missing_cons = sorted(all_companies - companies_with_cons)
    no_output = sorted(all_companies - set(df["company_id"].unique()))
    rule_counts = df["rule_id"].value_counts().to_dict() if not df.empty else {}
    confidence_stats = {}
    if not df.empty:
        confidence_stats = {"mean": round(df["confidence_pct"].mean(), 2), "min": round(df["confidence_pct"].min(), 2), "max": round(df["confidence_pct"].max(), 2)}
    duplicate_count = int(df.duplicated(subset=["company_id", "type", "rule_id"], keep=False).sum())
    result = {
        "total_companies": len(all_companies),
        "companies_with_pros": len(companies_with_pros),
        "companies_with_cons": len(companies_with_cons),
        "companies_missing_pros": missing_pros,
        "companies_missing_cons": missing_cons,
        "companies_no_output": no_output,
        "missing_pros_count": len(missing_pros),
        "missing_cons_count": len(missing_cons),
        "no_output_count": len(no_output),
        "rule_trigger_counts": dict(sorted(rule_counts.items())),
        "confidence_stats": confidence_stats,
        "duplicate_count": duplicate_count,
        "coverage_valid": len(missing_pros) == 0 and len(missing_cons) == 0,
    }
    logger.info("=" * 80)
    logger.info("COVERAGE VALIDATION")
    logger.info("  Total companies:         %d", result["total_companies"])
    logger.info("  Companies with Pros:     %d", result["companies_with_pros"])
    logger.info("  Companies with Cons:     %d", result["companies_with_cons"])
    logger.info("  Missing Pros:            %d", result["missing_pros_count"])
    logger.info("  Missing Cons:            %d", result["missing_cons_count"])
    logger.info("  No output at all:        %d", result["no_output_count"])
    logger.info("  Duplicate rows:          %d", result["duplicate_count"])
    logger.info("  Coverage valid:          %s", result["coverage_valid"])
    logger.info("=" * 80)
    return result
''')

            "companies_with_pros": len(companies_with_pros),
            "companies_with_cons": len(companies_with_cons),
            "companies_no_output": len(companies_no_output),
            "companies_missing_pros": sorted(cid for cid in all_company_ids if cid not in companies_with_pros),
            "companies_missing_cons": sorted(cid for cid in all_company_ids if cid not in companies_with_cons),
            "total_pro_rows": len(pros_df),
            "total_con_rows": len(cons_df),
            "total_rows": len(df),
            "rule_trigger_counts": dict(sorted(rule_trigger_counts.items())),
            "execution_time_seconds": round(elapsed, 3),
        }
        return pros_df, cons_df, stats
    except Exception as exc:
        conn.close()
        logger.error("Fatal error: %s", exc)
        raise
''')

    op_profit = _safe_float(pl[0].get("operating_profit")) or 0
    depreciation = _safe_float(pl[0].get("depreciation")) or 0
    other_income = _safe_float(pl[0].get("other_income")) or 0
    ebitda = op_profit + depreciation + other_income
    if ebitda == 0:

chunks.append(r'''

# =============================================================================
# OUTPUT
# =============================================================================


def save_output(pros_df, cons_df, output_path=PROS_CONS_CSV_PATH):
    """Save the combined pros and cons to a CSV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    combined = pd.concat([pros_df, cons_df], ignore_index=True)
    combined = combined[["company_id", "type", "rule_id", "text", "confidence_pct"]]
    combined = combined.sort_values(by=["company_id", "type", "rule_id"]).reset_index(drop=True)
    combined.to_csv(output_path, index=False)
    logger.info("Saved pros/cons CSV to %s (%d rows)", output_path, len(combined))
    return output_path


def validate_output_schema(df):
    """Validate the output DataFrame has the required schema."""
    errors = []
    required_columns = {"company_id", "type", "rule_id", "text", "confidence_pct"}
    actual_columns = set(df.columns)
    if actual_columns != required_columns:
        errors.append(f"Column mismatch. Required: {required_columns}, Got: {actual_columns}")
    if not df.empty:
        invalid_types = df[~df["type"].isin(["pro", "con"])]
        if not invalid_types.empty:
            errors.append(f"Invalid type values: {invalid_types["type"].unique().tolist()}")
        invalid_conf = df[(df["confidence_pct"] < 0) | (df["confidence_pct"] > 100)]
        if not invalid_conf.empty:
            errors.append(f"Confidence out of range: {invalid_conf["confidence_pct"].tolist()}")
        duplicates = df.duplicated(subset=["company_id", "type", "rule_id"], keep=False)
        if duplicates.any():
            errors.append(f"Found {duplicates.sum()} duplicate rows")
    return errors
''')

        return None
    net_debt_to_ebitda = net_debt / ebitda
    if net_debt_to_ebitda > CON_11_NET_DEBT_EBITDA_RATIO:
        confidence = calculate_confidence(net_debt_to_ebitda, CON_11_NET_DEBT_EBITDA_RATIO, higher_is_better=False)
        return {"rule_id": "CON_11", "text": "Net debt exceeding 3 times EBITDA is a high leverage ratio and limits financial flexibility", "confidence_pct": confidence}
    return None


def _con_12_revenue_cagr_low(data):
    """CON_12: Revenue CAGR < 5% over 5 years (from TTM row)."""
    ttm = data.get("ttm_kpis")
    if not ttm:
        return None
    cagr = _safe_float(ttm.get("revenue_cagr"))
    if cagr is None:
        return None

chunks.append(r'''

# =============================================================================
# MAIN
# =============================================================================


def main(db_path=DEFAULT_DB_PATH):
    """Main entry point for the Pros/Cons Generator."""
    logger.info("NLP Pros/Cons Generator - Module 2")
    logger.info("Timestamp: %s", datetime.now().isoformat())
    pros_df, cons_df, gen_stats = generate_all_pros_cons(db_path)
    output_path = save_output(pros_df, cons_df)
    combined_df = pd.concat([pros_df, cons_df], ignore_index=True)
    schema_errors = validate_output_schema(combined_df)
    if schema_errors:
        for err in schema_errors:
            logger.error("Schema error: %s", err)
    else:
        logger.info("Output schema validation: PASSED")
    coverage = validate_company_coverage(combined_df, db_path)
    summary = {
        "status": "success" if not schema_errors and coverage["coverage_valid"] else "completed_with_warnings",
        "timestamp": datetime.now().isoformat(),
        "output_path": str(output_path),
        "generation": gen_stats,
        "coverage": coverage,
        "schema_errors": schema_errors,
        "pro_11_contradiction_documented": True,
        "pro_11_contradiction_note": (
            "PRO_11 condition is Revenue CAGR > PAT CAGR but text says revenue growing slower than profits. "
            "Condition implemented exactly as stated in specification."
        ),
    }
    logger.info("=" * 80)
    logger.info("FINAL SUMMARY")
    logger.info("  Status:                  %s", summary["status"])
    logger.info("  Total rows generated:    %d", gen_stats["total_rows"])
    logger.info("  Pro rows:                %d", gen_stats["total_pro_rows"])
    logger.info("  Con rows:                %d", gen_stats["total_con_rows"])
    logger.info("  Companies missing Pros:  %d", coverage["missing_pros_count"])
    logger.info("  Companies missing Cons:  %d", coverage["missing_cons_count"])
    logger.info("  Output file:             %s", output_path)
    logger.info("=" * 80)
    return summary


if __name__ == "__main__":
    result = main()
    print(f"\\nModule 2 Pros/Cons Generator completed: {result["status"]}")
    print(f"Output: {result["output_path"]}")
    print(f"Total rows: {result["generation"]["total_rows"]}")
    if result["coverage"]["companies_missing_pros"]:
        print(f"WARNING: Companies missing Pros: {result["coverage"]["companies_missing_pros"]}")
    if result["coverage"]["companies_missing_cons"]:
        print(f"WARNING: Companies missing Cons: {result["coverage"]["companies_missing_cons"]}")
''')

print('All chunks prepared')

    if cagr < CON_12_REVENUE_CAGR_THRESHOLD:
        confidence = calculate_confidence(cagr, CON_12_REVENUE_CAGR_THRESHOLD, higher_is_better=False)
        return {"rule_id": "CON_12", "text": "Revenue growing at below 5% over 5 years lags inflation and suggests limited business momentum", "confidence_pct": confidence}
    return None


CON_RULE_FUNCTIONS = [
    _con_01_de_high_non_financial,
    _con_02_fcf_negative_3yr,
    _con_03_opm_declining_3yr,
    _con_04_net_loss_latest,
    _con_05_revenue_declining_2yr,
    _con_06_icr_low,
    _con_07_dividend_payout_over_100,
    _con_08_de_rising_3yr,
    _con_09_eps_declining_3yr,
    _con_10_roce_low,
    _con_11_net_debt_high,
    _con_12_revenue_cagr_low,
]
''')

        return {"rule_id": "CON_05", "text": "Revenue contraction over 2 consecutive years indicates demand weakness or market share loss", "confidence_pct": confidence}
    return None


def _con_06_icr_low(data):
    """CON_06: ICR < 1.5."""
    icr = _get_numeric(data["annual_kpis"], "interest_coverage", 0)
    if icr is None:
        return None
    if icr < CON_06_ICR_THRESHOLD:
        confidence = calculate_confidence(icr, CON_06_ICR_THRESHOLD, higher_is_better=False)
        return {"rule_id": "CON_06", "text": "Interest coverage ratio below 1.5x indicates the company is at risk of not meeting its debt obligations", "confidence_pct": confidence}
    return None
''')

        confidence = round(confidence, 2)
        return {"rule_id": "PRO_12", "text": "Growing asset base funded by internal accruals reflects self-sustaining growth", "confidence_pct": confidence}
    return None


PRO_RULE_FUNCTIONS = [
    _pro_01_roe_sustained,
    _pro_02_fcf_positive_5yr,
    _pro_03_debt_free,
    _pro_04_revenue_cagr_5yr,
    _pro_05_opm_latest,
    _pro_06_pat_cagr_5yr,
    _pro_07_icr_high_or_debt_free,
    _pro_08_dividend_yield_fcf,
    _pro_09_eps_cagr_5yr,
    _pro_10_roe_improving_3yr,
    _pro_11_revenue_cagr_gt_pat_cagr,
    _pro_12_assets_growing_debt_declining,
]
''')

        confidence = calculate_confidence(opm, PRO_05_OPM_THRESHOLD, higher_is_better=True)
        return {"rule_id": "PRO_05", "text": "Operating profit margin above 25% indicates strong pricing power and cost discipline", "confidence_pct": confidence}
    return None


def _pro_06_pat_cagr_5yr(data):
    """PRO_06: PAT CAGR > 20% over 5 years (from TTM row)."""
    ttm = data.get("ttm_kpis")
    if not ttm:
        return None
    cagr = _safe_float(ttm.get("profit_cagr"))
    if cagr is None:
        return None
    if cagr > PRO_06_PAT_CAGR_THRESHOLD:
        confidence = calculate_confidence(cagr, PRO_06_PAT_CAGR_THRESHOLD, higher_is_better=True)
        return {"rule_id": "PRO_06", "text": "Net profit compounding at above 20% over 5 years creates significant shareholder value", "confidence_pct": confidence}
    return None
''')

) -> List[Optional[float]]:
    """Extract up to n_years numeric values (newest -> oldest)."""
    values = []
    for i in range(min(n_years, len(records))):
        values.append(_safe_float(records[i].get(key)))
    return values
''')

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
''')

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
''')
