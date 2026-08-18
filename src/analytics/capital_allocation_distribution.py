"""
capital_allocation_distribution.py

Module 4B: Latest-Year Capital Allocation Pattern Distribution
N100 Financial Intelligence Platform (Sprint 5)

This module calculates the distribution of companies across all 8 supported
Capital Allocation patterns for the dynamically determined latest financial year.
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import numpy as np

from src.config.constants import OUTPUT_DIR
from src.config.logging_config import get_logger
from src.database.connection import get_connection
from src.analytics.cashflow_kpis import (
    classify_capital_allocation,
    _get_operating_cash_flow,
    _get_capital_expenditure,
)

logger = get_logger(__name__)

# Supported 8 Capital Allocation Patterns
SUPPORTED_PATTERNS: List[str] = [
    "Reinvestor",
    "Shareholder Returns",
    "Liquidating Assets",
    "Distress Signal",
    "Growth Funded by Debt",
    "Cash Accumulator",
    "Pre-Revenue",
    "Mixed",
]

# Rating to Pattern Mapping
RATING_TO_PATTERN_MAP: Dict[str, str] = {
    "EXCELLENT": "Reinvestor",
    "GOOD": "Shareholder Returns",
    "MODERATE": "Mixed",
    "WEAK": "Cash Accumulator",
    "DISTRESSED": "Distress Signal",
}


def parse_year_from_period(period_str: Any) -> Optional[int]:
    """
    Extract four-digit financial year from a period string.

    Examples:
    - 'Mar 2024' -> 2024
    - 'Dec 2023' -> 2023
    - 'Mar-24'   -> 2024
    - '2024'     -> 2024
    """
    if period_str is None or pd.isna(period_str):
        return None

    s = str(period_str).strip()
    m = re.search(r"(\d{4})", s)
    if m:
        return int(m.group(1))

    m = re.search(r"-(\d{2})$", s)
    if m:
        return 2000 + int(m.group(1))

    return None


def determine_latest_year(cf_df: pd.DataFrame, pl_df: pd.DataFrame) -> int:
    """
    Dynamically determine the latest financial year from data.
    """
    years = []
    if not cf_df.empty and "period" in cf_df.columns:
        cf_years = cf_df["period"].apply(parse_year_from_period).dropna().astype(int)
        years.extend(cf_years.tolist())

    if not pl_df.empty and "period" in pl_df.columns:
        pl_years = pl_df["period"].apply(parse_year_from_period).dropna().astype(int)
        years.extend(pl_years.tolist())

    if not years:
        logger.warning("No valid period/year found in financial statements, falling back to 2024")
        return 2024

    latest = int(max(years))
    logger.info(f"Latest Capital Allocation year dynamically determined: {latest}")
    return latest


def map_rating_to_pattern(rating: Optional[str]) -> str:
    """
    Convert capital allocation rating to supported 8-pattern label.
    """
    if rating is None or pd.isna(rating):
        return "Mixed"
    return RATING_TO_PATTERN_MAP.get(str(rating).upper(), "Mixed")


def compute_latest_year_classifications(
    conn: Optional[Any] = None,
) -> Tuple[int, pd.DataFrame]:
    """
    Process all authoritative companies for the dynamically detected latest year
    and calculate capital allocation ratings & pattern classifications.

    Returns
    -------
    Tuple[int, pd.DataFrame]
        Latest year and DataFrame of company classifications.
    """
    should_close = False
    if conn is None:
        conn = get_connection()
        should_close = False

    try:
        companies_df = pd.read_sql(
            "SELECT company_id, company_name, sector FROM companies ORDER BY company_id",
            conn,
        )
        if companies_df.empty:
            logger.error("No companies found in authoritative companies table")
            return 2024, pd.DataFrame()

        cf_df = pd.read_sql("SELECT * FROM cash_flow", conn)
        pl_df = pd.read_sql("SELECT * FROM profit_loss", conn)

        cf_df["year"] = cf_df["period"].apply(parse_year_from_period)
        pl_df["year"] = pl_df["period"].apply(parse_year_from_period)

        latest_year = determine_latest_year(cf_df, pl_df)

        cf_latest = cf_df[cf_df["year"] == latest_year]
        pl_latest = pl_df[pl_df["year"] == latest_year]

        records = []
        for _, co in companies_df.iterrows():
            cid = co["company_id"]
            cname = co["company_name"]
            sector = co["sector"]

            c_cf = cf_latest[cf_latest["company_id"] == cid]
            c_pl = pl_latest[pl_latest["company_id"] == cid]

            if c_cf.empty:
                logger.warning(
                    f"Company {cid} ({cname}) has missing cash flow data for year {latest_year}"
                )
                rating = classify_capital_allocation(None, None, None, None)
                pattern = map_rating_to_pattern(rating)
                records.append(
                    {
                        "company_id": cid,
                        "company_name": cname,
                        "sector": sector,
                        "latest_year": latest_year,
                        "capital_allocation_rating": rating,
                        "capital_allocation_pattern": pattern,
                        "has_data": False,
                    }
                )
                continue

            cf_row = c_cf.iloc[0]
            pl_row = c_pl.iloc[0] if not c_pl.empty else pd.Series()

            ocf = cf_row.get("cash_from_operating_activity")
            if pd.isna(ocf) or ocf is None:
                ocf = cf_row.get("operating_activity")

            capex = cf_row.get("cash_from_investing_activity")
            if pd.isna(capex) or capex is None:
                capex = cf_row.get("investing_activity")

            if pd.notna(capex) and capex is not None and capex < 0:
                capex = abs(capex)
            elif pd.isna(capex) or capex is None:
                capex = 0.0

            fcf = (ocf - capex) if (pd.notna(ocf) and ocf is not None) else None

            net_profit = pl_row.get("net_profit") if "net_profit" in pl_row else None
            sales = pl_row.get("sales") if "sales" in pl_row else None

            if pd.isna(net_profit):
                net_profit = None
            if pd.isna(sales):
                sales = None

            cash_conversion = (
                (fcf / net_profit * 100.0)
                if (net_profit is not None and net_profit != 0 and fcf is not None)
                else None
            )
            capex_intensity = (
                (capex / ocf * 100.0)
                if (ocf is not None and ocf != 0)
                else None
            )

            rating = classify_capital_allocation(
                fcf, cash_conversion, capex_intensity, ocf
            )
            pattern = map_rating_to_pattern(rating)

            records.append(
                {
                    "company_id": cid,
                    "company_name": cname,
                    "sector": sector,
                    "latest_year": latest_year,
                    "capital_allocation_rating": rating,
                    "capital_allocation_pattern": pattern,
                    "has_data": True,
                }
            )

        df_out = pd.DataFrame(records)
        return latest_year, df_out

    except Exception as e:
        logger.error(f"Error computing classifications: {str(e)}", exc_info=True)
        return 2024, pd.DataFrame()


def generate_distribution_summary(
    latest_year: int, classifications_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Generate 8-pattern distribution table from classifications.
    Ensures zero-count patterns are present.
    """
    total_valid_companies = len(classifications_df)

    if total_valid_companies == 0:
        counts = {p: 0 for p in SUPPORTED_PATTERNS}
    else:
        counts = {
            p: int((classifications_df["capital_allocation_pattern"] == p).sum())
            for p in SUPPORTED_PATTERNS
        }

    rows = []
    for pattern in SUPPORTED_PATTERNS:
        count = counts[pattern]
        pct = (
            round((count / total_valid_companies) * 100.0, 2)
            if total_valid_companies > 0
            else 0.0
        )
        rows.append(
            {
                "latest_year": latest_year,
                "pattern": pattern,
                "company_count": count,
                "percentage": pct,
            }
        )

    dist_df = pd.DataFrame(rows)
    return dist_df


def run_module4b_pipeline(output_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Run complete Module 4B pipeline to generate distribution summary and detailed files.
    """
    if output_dir is None:
        output_dir = OUTPUT_DIR

    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Starting Module 4B Pipeline...")
    latest_year, class_df = compute_latest_year_classifications()

    total_companies = len(class_df)
    valid_companies = len(class_df)

    print(f"Latest Capital Allocation year: {latest_year}")
    print(f"Authoritative companies evaluated: {total_companies}")

    dist_df = generate_distribution_summary(latest_year, class_df)

    dist_path = output_dir / "capital_allocation_distribution.csv"
    dist_df.to_csv(dist_path, index=False)
    logger.info(f"Saved distribution summary to {dist_path}")

    latest_path = output_dir / "capital_allocation_latest_year.csv"
    latest_cols = [
        "company_id",
        "company_name",
        "sector",
        "latest_year",
        "capital_allocation_rating",
        "capital_allocation_pattern",
    ]
    class_df[latest_cols].to_csv(latest_path, index=False)
    logger.info(f"Saved detailed latest year classifications to {latest_path}")

    return {
        "latest_year": latest_year,
        "total_companies": total_companies,
        "valid_companies": valid_companies,
        "distribution_df": dist_df,
        "classifications_df": class_df,
        "distribution_path": dist_path,
        "latest_year_path": latest_path,
    }


if __name__ == "__main__":
    run_module4b_pipeline()
