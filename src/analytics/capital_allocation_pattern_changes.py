"""
capital_allocation_pattern_changes.py

Module 4C: Year-over-Year Capital Allocation Pattern Changes
N100 Financial Intelligence Platform (Sprint 5)

This module identifies companies whose Capital Allocation pattern changed
between their previous valid year and latest valid year.
"""

import logging
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from pathlib import Path

from src.database.connection import get_connection
from src.config.logging_config import get_logger
from src.analytics.cashflow_kpis import (
    classify_capital_allocation,
    _get_operating_cash_flow,
    _get_capital_expenditure,
)
from src.analytics.capital_allocation_distribution import (
    parse_year_from_period,
    map_rating_to_pattern,
    SUPPORTED_PATTERNS,
)

logger = get_logger(__name__)


def get_available_years(conn=None) -> List[int]:
    """
    Get all distinct financial years from cash_flow and profit_loss tables.

    Parameters
    ----------
    conn : sqlite3.Connection, optional
        Database connection

    Returns
    -------
    List[int]
        Sorted list of distinct years (descending order)
    """
    if conn is None:
        conn = get_connection()
    try:
        # Get years from cash_flow table
        cf_query = "SELECT DISTINCT period FROM cash_flow WHERE period IS NOT NULL"
        cf_df = pd.read_sql(cf_query, conn)
        cf_years = (
            cf_df["period"].apply(parse_year_from_period).dropna().astype(int).tolist()
        )

        # Get years from profit_loss table
        pl_query = "SELECT DISTINCT period FROM profit_loss WHERE period IS NOT NULL"
        pl_df = pd.read_sql(pl_query, conn)
        pl_years = (
            pl_df["period"].apply(parse_year_from_period).dropna().astype(int).tolist()
        )

        # Union of years, sorted descending
        all_years = sorted(list(set(cf_years + pl_years)), reverse=True)
        logger.info(f"Available years: {all_years}")
        return all_years
    except Exception as e:
        logger.error(f"Error getting available years: {str(e)}", exc_info=True)
        return []


def compute_year_classifications(year: int, conn=None) -> pd.DataFrame:
    """
    Compute Capital Allocation classifications for all authoritative companies for a given year.

    Parameters
    ----------
    year : int
        Financial year to compute classifications for
    conn : sqlite3.Connection, optional
        Database connection

    Returns
    -------
    pd.DataFrame
        DataFrame with columns: company_id, company_name, sector, year,
        capital_allocation_rating, capital_allocation_pattern, has_data
    """
    if conn is None:
        conn = get_connection()
    try:
        # Get authoritative companies
        companies_df = pd.read_sql(
            "SELECT company_id, company_name, sector FROM companies ORDER BY company_id",
            conn,
        )
        if companies_df.empty:
            logger.error("No companies found in authoritative companies table")
            return pd.DataFrame()

        # Get cash_flow and profit_loss data for the given year
        cf_df = pd.read_sql("SELECT * FROM cash_flow", conn)
        pl_df = pd.read_sql("SELECT * FROM profit_loss", conn)

        # Add year column to cash_flow and profit_loss
        cf_df["year"] = cf_df["period"].apply(parse_year_from_period)
        pl_df["year"] = pl_df["period"].apply(parse_year_from_period)

        # Filter to the given year
        cf_year = cf_df[cf_df["year"] == year]
        pl_year = pl_df[pl_df["year"] == year]

        records = []
        for _, co in companies_df.iterrows():
            cid = co["company_id"]
            cname = co["company_name"]
            sector = co["sector"]

            c_cf = cf_year[cf_year["company_id"] == cid]
            c_pl = pl_year[pl_year["company_id"] == cid]

            has_data = not c_cf.empty  # Consider has_data if we have cash flow data

            if c_cf.empty:
                logger.warning(
                    f"Company {cid} ({cname}) has missing cash flow data for year {year}"
                )
                # Classify as DISTRESSED due to missing data
                rating = classify_capital_allocation(None, None, None, None)
                pattern = map_rating_to_pattern(rating)
                records.append(
                    {
                        "company_id": cid,
                        "company_name": cname,
                        "sector": sector,
                        "year": year,
                        "capital_allocation_rating": rating,
                        "capital_allocation_pattern": pattern,
                        "has_data": False,
                    }
                )
                continue

            # Extract cash flow data
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
                (capex / ocf * 100.0) if (ocf is not None and ocf != 0) else None
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
                    "year": year,
                    "capital_allocation_rating": rating,
                    "capital_allocation_pattern": pattern,
                    "has_data": True,
                }
            )

        df_out = pd.DataFrame(records)
        logger.info(
            f"Computed classifications for year {year}: {len(df_out)} companies"
        )
        return df_out
    except Exception as e:
        logger.error(
            f"Error computing classifications for year {year}: {str(e)}", exc_info=True
        )
        return pd.DataFrame()


def compute_pattern_changes(conn=None) -> Tuple[pd.DataFrame, Dict]:
    """
    Compute year-over-year pattern changes for all authoritative companies.

    Parameters
    ----------
    conn : sqlite3.Connection, optional
        Database connection

    Returns
    -------
    Tuple[pd.DataFrame, Dict]
        DataFrame of pattern changes and summary statistics
    """
    if conn is None:
        conn = get_connection()
    try:
        # Get available years
        years = get_available_years(conn)
        if not years:
            logger.warning("No years available, returning empty results")
            return pd.DataFrame(), {}

        # We need at least two years to compute changes
        if len(years) < 2:
            logger.warning(
                "Less than two years available, cannot compute year-over-year changes"
            )
            return pd.DataFrame(), {}

        # Compute classifications for each year (we'll store in a dict year -> DataFrame)
        yearly_classifications = {}
        for year in years:
            yearly_classifications[year] = compute_year_classifications(year, conn)

        # For each company, find the latest two years with has_data=True
        changes_records = []
        company_summary = {
            "total_companies": 0,
            "companies_with_previous_year": 0,
            "companies_unchanged_pattern": 0,
            "companies_changed_pattern": 0,
            "companies_insufficient_history": 0,
        }

        # Get list of company IDs from the authoritative companies table
        companies_df = pd.read_sql(
            "SELECT company_id FROM companies ORDER BY company_id",
            conn,
        )
        company_ids = companies_df["company_id"].tolist()
        company_summary["total_companies"] = len(company_ids)

        for cid in company_ids:
            # Get the company's name and sector (from any year, they are constant)
            company_name = None
            sector = None

            # Find the latest two years with has_data=True
            valid_years = (
                []
            )  # List of (year, pattern, has_data) for years where has_data is True

            for year in years:  # years are in descending order
                df_year = yearly_classifications.get(year)
                if df_year is not None and not df_year.empty:
                    company_row = df_year[df_year["company_id"] == cid]
                    if not company_row.empty:
                        row = company_row.iloc[0]
                        if company_name is None:
                            company_name = row["company_name"]
                            sector = row["sector"]
                        if row["has_data"]:
                            valid_years.append(
                                (year, row["capital_allocation_pattern"], True)
                            )

            # If we have at least two years with actual data, compute change
            if len(valid_years) >= 2:
                company_summary["companies_with_previous_year"] += 1
                latest_year, latest_pattern, _ = valid_years[0]
                previous_year, previous_pattern, _ = valid_years[1]

                changed = previous_pattern != latest_pattern

                if changed:
                    company_summary["companies_changed_pattern"] += 1
                    changes_records.append(
                        {
                            "company_id": cid,
                            "company_name": company_name,
                            "sector": sector,
                            "previous_year": previous_year,
                            "previous_pattern": previous_pattern,
                            "latest_year": latest_year,
                            "latest_pattern": latest_pattern,
                            "changed": True,
                        }
                    )
                else:
                    company_summary["companies_unchanged_pattern"] += 1
                    # We do not add unchanged companies to the changes output (as per spec)
            else:
                company_summary["companies_insufficient_history"] += 1
                # Do not add to changes output

        # Create DataFrame from changes records
        changes_df = pd.DataFrame(changes_records)

        # Calculate transition matrix if there are changes
        transition_matrix = {}
        if not changes_df.empty:
            # Group by previous_pattern and latest_pattern
            transition = (
                changes_df.groupby(["previous_pattern", "latest_pattern"])
                .size()
                .reset_index(name="count")
            )
            # Convert to nested dictionary: previous_pattern -> {latest_pattern -> count}
            for _, row in transition.iterrows():
                prev = row["previous_pattern"]
                curr = row["latest_pattern"]
                cnt = row["count"]
                if prev not in transition_matrix:
                    transition_matrix[prev] = {}
                transition_matrix[prev][curr] = cnt

        summary = {
            **company_summary,
            "transition_matrix": transition_matrix,
            "years_analyzed": years,
        }

        return changes_df, summary
    except Exception as e:
        logger.error(f"Error computing pattern changes: {str(e)}", exc_info=True)
        return pd.DataFrame(), {}


def generate_output_files(
    changes_df: pd.DataFrame, summary: Dict, output_dir: Optional[Path] = None
) -> Dict[str, Path]:
    """
    Generate output CSV files for pattern changes and optionally summary.

    Parameters
    ----------
    changes_df : pd.DataFrame
        DataFrame of pattern changes
    summary : Dict
        Summary statistics
    output_dir : pathlib.Path, optional
        Output directory (defaults to src.config.constants.OUTPUT_DIR)

    Returns
    -------
    Dict[str, Path]
        Dictionary mapping output names to file paths
    """
    if output_dir is None:
        from src.config.constants import OUTPUT_DIR

        output_dir = OUTPUT_DIR

    output_dir.mkdir(parents=True, exist_ok=True)

    output_files = {}

    # Output pattern_changes.csv
    if not changes_df.empty:
        # Ensure we have the required columns
        required_cols = [
            "company_id",
            "company_name",
            "sector",
            "previous_year",
            "previous_pattern",
            "latest_year",
            "latest_pattern",
            "changed",
        ]
        # Only include columns that exist
        cols_to_use = [col for col in required_cols if col in changes_df.columns]
        changes_output_df = changes_df[cols_to_use].copy()
    else:
        # Create empty DataFrame with required columns
        changes_output_df = pd.DataFrame(
            columns=[
                "company_id",
                "company_name",
                "sector",
                "previous_year",
                "previous_pattern",
                "latest_year",
                "latest_pattern",
                "changed",
            ]
        )

    changes_path = output_dir / "pattern_changes.csv"
    changes_output_df.to_csv(changes_path, index=False)
    logger.info(f"Saved pattern changes to {changes_path}")
    output_files["pattern_changes"] = changes_path

    # Optionally generate transition summary CSV
    transition_matrix = summary.get("transition_matrix", {})
    if transition_matrix:
        # Flatten the transition matrix
        transition_rows = []
        for prev_pattern, next_dict in transition_matrix.items():
            for latest_pattern, count in next_dict.items():
                transition_rows.append(
                    {
                        "previous_pattern": prev_pattern,
                        "latest_pattern": latest_pattern,
                        "company_count": count,
                    }
                )

        if transition_rows:
            transition_df = pd.DataFrame(transition_rows)
            transition_path = output_dir / "pattern_change_summary.csv"
            transition_df.to_csv(transition_path, index=False)
            logger.info(f"Saved pattern change summary to {transition_path}")
            output_files["pattern_change_summary"] = transition_path

    return output_files


def run_module4c_pipeline(output_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Run complete Module 4C pipeline to generate pattern changes and summary files.

    Parameters
    ----------
    output_dir : pathlib.Path, optional
        Output directory (defaults to src.config.constants.OUTPUT_DIR)

    Returns
    -------
    Dict[str, Any]
        Dictionary with results and file paths
    """
    logger.info("Starting Module 4C Pipeline...")

    changes_df, summary = compute_pattern_changes()

    total_companies = summary.get("total_companies", 0)
    companies_with_prev_year = summary.get("companies_with_previous_year", 0)
    changed_count = summary.get("companies_changed_pattern", 0)
    unchanged_count = summary.get("companies_unchanged_pattern", 0)
    insufficient_history = summary.get("companies_insufficient_history", 0)

    logger.info(f"Total companies: {total_companies}")
    logger.info(f"Companies with previous year data: {companies_with_prev_year}")
    logger.info(f"Companies with unchanged pattern: {unchanged_count}")
    logger.info(f"Companies with changed pattern: {changed_count}")
    logger.info(f"Companies with insufficient history: {insufficient_history}")

    output_files = generate_output_files(changes_df, summary, output_dir)

    return {
        "changes_df": changes_df,
        "summary": summary,
        "output_files": output_files,
    }


if __name__ == "__main__":
    run_module4c_pipeline()
