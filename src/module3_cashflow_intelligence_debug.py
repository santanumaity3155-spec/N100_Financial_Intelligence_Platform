"""
Module 3: Cash Flow Intelligence Engine
Sprint 5 — Intelligence, NLP & PDF Reports

This module computes cash flow intelligence metrics for all companies in the
authoritative companies table and outputs the results to Excel and CSV.

Metrics computed:
- CFO Quality (average CFO/PAT over latest 5 years)
- CapEx Intensity (abs(investing_activity)/sales * 100 for latest year)
- FCF CAGR (5-year CAGR of FCF)
- FCF Conversion (FCF/PAT * 100 for latest year)
- Distress Flag (latest CFO < 0 AND latest CFF > 0)
- Deleveraging Flag (latest CFF < 0 AND borrowings declining year-over-year)
- Capital Allocation Label (reuse existing classify_capital_allocation)

Outputs:
- output/cashflow_intelligence.xlsx (one row per company)
- output/distress_alerts.csv (companies with distress_flag == True)

"""

import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

# Add the project root to the Python path to allow imports from src
PROJECT_ROOT = Path(__file__).resolve().parents[2]
print(f"DEBUG: __file__ = {__file__}")
print(f"DEBUG: PROJECT_ROOT = {PROJECT_ROOT}")
print(f"DEBUG: PROJECT_ROOT exists = {PROJECT_ROOT.exists()}")
sys.path.append(str(PROJECT_ROOT))
print(f"DEBUG: sys.path = {sys.path}")
print(f"DEBUG: sys.path[-1] = {sys.path[-1] if sys.path else None}")

# Try to import and see what happens
try:
    print("DEBUG: Attempting to import src.analytics...")
    import src.analytics

    print("DEBUG: Import succeeded!")
except Exception as e:
    print(f"DEBUG: Import failed with error: {e}")
    print(f"DEBUG: Error type: {type(e)}")
    import traceback

    traceback.print_exc()

    # Let's also try to manually load the file
    try:
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "src.analytics",
            r"D:\New Project\Bluestock_Projects\Nifty 100\N100 Financial Intelligence Platform\N100_Financial_Intelligence_Platform\src\analytics\__init__.py",
        )
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            print("DEBUG: Manual import via importlib succeeded!")
        else:
            print("DEBUG: Could not create spec for manual import")
    except Exception as e2:
        print(f"DEBUG: Manual import also failed: {e2}")
        traceback.print_exc()

# Import existing project utilities
from src.database.connection import get_connection
from src.analytics.cashflow_kpis import (
    calculate_free_cash_flow,
    _get_operating_cash_flow,
    _safe_get_value,
    classify_capital_allocation,
    RATING_EXCELLENT,
    RATING_GOOD,
    RATING_MODERATE,
    RATING_WEAK,
    RATING_DISTRESSED,
)
from src.analytics.cagr import (
    calculate_cagr,
    FLAG_NORMAL,
    FLAG_ZERO_BASE,
    FLAG_DECLINE_TO_LOSS,
    FLAG_TURNAROUND,
    FLAG_BOTH_NEGATIVE,
    FLAG_INSUFFICIENT,
)

# Configure logger
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def fetch_company_data(conn, company_id):
    """Fetch latest cash flow, profit loss, and balance sheet data for a company."""
    cursor = conn.cursor()

    # Get latest period for this company
    cursor.execute(
        """
        SELECT period FROM cash_flow
        WHERE company_id = ?
        ORDER BY
            CASE
                WHEN substr(period, 7, 4) || '-' ||
                     CASE substr(period, 1, 3)
                        WHEN 'Jan' THEN '01'
                        WHEN 'Feb' THEN '02'
                        WHEN 'Mar' THEN '03'
                        WHEN 'Apr' THEN '04'
                        WHEN 'May' THEN '05'
                        WHEN 'Jun' THEN '06'
                        WHEN 'Jul' THEN '07'
                        WHEN 'Aug' THEN '08'
                        WHEN 'Sep' THEN '09'
                        WHEN 'Oct' THEN '10'
                        WHEN 'Nov' THEN '11'
                        WHEN 'Dec' THEN '12'
                     END || '-01' DESC
            LIMIT 1
    """,
        (company_id,),
    )
    period_row = cursor.fetchone()
    if not period_row:
        return None, None, None
    period = period_row[0]

    # Cash flow data
    cursor.execute(
        """
        SELECT * FROM cash_flow
        WHERE company_id = ? AND period = ?
    """,
        (company_id, period),
    )
    cf_row = cursor.fetchone()
    if cf_row:
        cursor.execute("PRAGMA table_info(cash_flow);")
        cf_columns = [desc[1] for desc in cursor.fetchall()]
        cf_data = dict(zip(cf_columns, cf_row))
    else:
        cf_data = {}

    # Profit loss data
    cursor.execute(
        """
        SELECT * FROM profit_loss
        WHERE company_id = ? AND period = ?
    """,
        (company_id, period),
    )
    pl_row = cursor.fetchone()
    if pl_row:
        cursor.execute("PRAGMA table_info(profit_loss);")
        pl_columns = [desc[1] for desc in cursor.fetchall()]
        pl_data = dict(zip(pl_columns, pl_row))
    else:
        pl_data = {}

    # Balance sheet data
    cursor.execute(
        """
        SELECT * FROM balance_sheet
        WHERE company_id = ? AND period = ?
    """,
        (company_id, period),
    )
    bs_row = cursor.fetchone()
    if bs_row:
        cursor.execute("PRAGMA table_info(balance_sheet);")
        bs_columns = [desc[1] for desc in cursor.fetchall()]
        bs_data = dict(zip(bs_columns, bs_row))
    else:
        bs_data = {}

    return cf_data, pl_data, bs_data


def compute_cfo_quality(cf_data_list, pl_data_list):
    """Compute CFO Quality ratio (average CFO/PAT over available years)."""
    ratios = []
    for cf_data, pl_data in zip(cf_data_list, pl_data_list):
        cfo = cf_data.get("cash_from_operating_activity") or cf_data.get(
            "operating_activity"
        )
        net_profit = pl_data.get("net_profit")
        if cfo is not None and net_profit is not None and net_profit != 0:
            ratios.append(cfo / net_profit)
    return sum(ratios) / len(ratios) if ratios else None


def compute_capex_intensity_latest(cf_data, pl_data):
    """Compute CapEx Intensity for latest year."""
    investing_activity = abs(
        cf_data.get("cash_from_investing_activity")
        or cf_data.get("investing_activity")
        or 0
    )
    sales = pl_data.get("sales") or 0
    return (investing_activity / sales * 100) if sales != 0 else None


def compute_fcf_cagr_5yr(cf_data_list, pl_data_list):
    """Compute 5-year CAGR of Free Cash Flow."""
    fcf_values = []
    for cf_data, pl_data in zip(cf_data_list, pl_data_list):
        ocf = (
            cf_data.get("cash_from_operating_activity")
            or cf_data.get("operating_activity")
            or 0
        )
        capex = abs(
            cf_data.get("cash_from_investing_activity")
            or cf_data.get("investing_activity")
            or 0
        )
        fcf = ocf - capex
        fcf_values.append(fcf)

    # Filter out None values and ensure we have at least 2 points for CAGR
    valid_fcf = [fcf for fcf in fcf_values if fcf is not None]
    if len(valid_fcf) >= 2:
        # Use the earliest and latest values for 5-year CAGR
        start_value = valid_fcf[0]
        end_value = valid_fcf[-1]
        num_years = len(valid_fcf) - 1
        if start_value != 0:  # Avoid division by zero
            return (end_value / start_value) ** (1 / num_years) - 1
    return None


def compute_fcf_conversion_latest(cf_data, pl_data):
    """Compute FCF Conversion for latest year."""
    ocf = (
        cf_data.get("cash_from_operating_activity")
        or cf_data.get("operating_activity")
        or 0
    )
    capex = abs(
        cf_data.get("cash_from_investing_activity")
        or cf_data.get("investing_activity")
        or 0
    )
    fcf = ocf - capex
    net_profit = pl_data.get("net_profit") or 0
    return (fcf / net_profit * 100) if net_profit != 0 else None


def compute_distress_flag_latest(cf_data):
    """Compute Distress Flag for latest year (CFO < 0 AND CFF > 0)."""
    cfo = cf_data.get("cash_from_operating_activity") or cf_data.get(
        "operating_activity"
    )
    cff = cf_data.get("cash_from_financing_activity") or cf_data.get(
        "financing_activity"
    )
    return bool(cfo is not None and cff is not None and cfo < 0 and cff > 0)


def compute_deleveraging_flag_latest(cf_data_list, bs_data_list):
    """Compute Deleveraging Flag (CFF < 0 AND borrowings declining year-over-year)."""
    if len(cf_data_list) < 2 or len(bs_data_list) < 2:
        return False

    # Check latest year
    latest_cf = cf_data_list[-1]
    latest_bs = bs_data_list[-1]
    cff = latest_cf.get("cash_from_financing_activity") or latest_cf.get(
        "financing_activity"
    )
    borrowings = latest_bs.get("borrowings")

    if cff is None or borrowings is None:
        return False

    # Check if CFF < 0
    if cff >= 0:
        return False

    # Check if borrowings are declining compared to previous year
    prev_bs = bs_data_list[-2]
    prev_borrowings = prev_bs.get("borrowings")

    if prev_borrowings is None:
        return False

    return borrowings < prev_borrowings


def compute_capital_allocation_label_latest(cf_data, pl_data):
    """Compute Capital Allocation Label by reusing existing classify_capital_allocation."""
    ocf = (
        cf_data.get("cash_from_operating_activity")
        or cf_data.get("operating_activity")
        or 0
    )
    capex = abs(
        cf_data.get("cash_from_investing_activity")
        or cf_data.get("investing_activity")
        or 0
    )
    fcf = ocf - capex
    net_profit = pl_data.get("net_profit") or 0
    sales = pl_data.get("sales") or 0

    cash_conversion = (fcf / net_profit * 100) if net_profit != 0 else 0
    capex_intensity = (capex / sales * 100) if sales != 0 else 0

    return classify_capital_allocation(fcf, cash_conversion, capex_intensity, ocf)


def process_company(company_id):
    """Process a single company and return computed metrics."""
    conn = get_connection()
    try:
        # Fetch historical data (up to 5 years)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT period FROM cash_flow
            WHERE company_id = ?
            ORDER BY
                CASE
                    WHEN substr(period, 7, 4) || '-' ||
                         CASE substr(period, 1, 3)
                            WHEN 'Jan' THEN '01'
                            WHEN 'Feb' THEN '02'
                            WHEN 'Mar' THEN '03'
                            WHEN 'Apr' THEN '04'
                            WHEN 'May' THEN '05'
                            WHEN 'Jun' THEN '06'
                            WHEN 'Jul' THEN '07'
                            WHEN 'Aug' THEN '08'
                            WHEN 'Sep' THEN '09'
                            WHEN 'Oct' THEN '10'
                            WHEN 'Nov' THEN '11'
                            WHEN 'Dec' THEN '12'
                         END || '-01' DESC
                LIMIT 5
        """,
            (company_id,),
        )
        periods = [row[0] for row in cursor.fetchall()]

        if not periods:
            return None

        # Fetch data for each period
        cf_data_list = []
        pl_data_list = []
        bs_data_list = []

        for period in periods:
            cf_data, pl_data, bs_data = fetch_company_data(conn, company_id)
            cf_data_list.append(cf_data)
            pl_data_list.append(pl_data)
            bs_data_list.append(bs_data)

        # Compute metrics
        result = {
            "company_id": company_id,
            "cfo_quality": compute_cfo_quality(cf_data_list, pl_data_list),
            "capex_intensity_latest": (
                compute_capex_intensity_latest(cf_data_list[-1], pl_data_list[-1])
                if cf_data_list and pl_data_list
                else None
            ),
            "fcf_cagr_5yr": compute_fcf_cagr_5yr(cf_data_list, pl_data_list),
            "fcf_conversion_latest": (
                compute_fcf_conversion_latest(cf_data_list[-1], pl_data_list[-1])
                if cf_data_list and pl_data_list
                else None
            ),
            "distress_flag_latest": (
                compute_distress_flag_latest(cf_data_list[-1]) if cf_data_list else None
            ),
            "deleveraging_flag_latest": compute_deleveraging_flag_latest(
                cf_data_list, bs_data_list
            ),
            "capital_allocation_label_latest": (
                compute_capital_allocation_label_latest(
                    cf_data_list[-1], pl_data_list[-1]
                )
                if cf_data_list and pl_data_list
                else None
            ),
        }

        return result

    finally:
        conn.close()


def main():
    """Main function to process all companies and generate output files."""
    logger.info("Starting Module 3: Cash Flow Intelligence Engine")

    # Ensure output directory exists
    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get all companies from the authoritative companies table
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT company_id FROM companies")
        companies = [row[0] for row in cursor.fetchall()]
        logger.info(f"Found {len(companies)} companies in companies table")
    finally:
        conn.close()

    # Process each company
    results = []
    for i, company_id in enumerate(companies):
        if i % 10 == 0:
            logger.info(f"Processing company {i+1}/{len(companies)}: {company_id}")
        result = process_company(company_id)
        if result:
            results.append(result)

    if not results:
        logger.error("No companies processed successfully")
        return

    # Convert to DataFrame
    df = pd.DataFrame(results)

    # Reorder columns for clarity
    column_order = [
        "company_id",
        "cfo_quality",
        "capex_intensity_latest",
        "fcf_cagr_5yr",
        "fcf_conversion_latest",
        "distress_flag_latest",
        "deleveraging_flag_latest",
        "capital_allocation_label_latest",
    ]
    df = df[column_order]

    # Save to Excel
    excel_path = output_dir / "cashflow_intelligence.xlsx"
    df.to_excel(excel_path, index=False)
    logger.info(f"Saved cash flow intelligence to {excel_path}")

    # Filter for distressed companies and save to CSV
    distressed_df = df[df["distress_flag_latest"] == True].copy()
    csv_path = output_dir / "distress_alerts.csv"
    distressed_df.to_csv(csv_path, index=False)
    logger.info(f"Saved distress alerts to {csv_path} ({len(distressed_df)} companies)")

    logger.info("Module 3 processing complete")


if __name__ == "__main__":
    main()
