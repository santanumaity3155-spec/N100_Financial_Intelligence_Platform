"""
Module 3: Cash Flow Intelligence Engine
Sprint 5 — Intelligence, NLP & PDF Reports

Clean version that imports from src.analytics and uses fresh connections
to avoid singleton connection issues.
"""

import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import sqlite3

# Add the project root to the Python path to allow imports from src
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

# Import from src.analytics (now that __init__.py is fixed)
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
from src.analytics.cagr import calculate_cagr, FLAG_NORMAL, FLAG_ZERO_BASE, FLAG_DECLINE_TO_LOSS, FLAG_TURNAROUND, FLAG_BOTH_NEGATIVE, FLAG_INSUFFICIENT

# Import database configuration
from src.config.constants import DATABASE_DIR
from src.config.settings import SQLITE_DATABASE

# Configure logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def fetch_company_data(conn, company_id):
    """Fetch latest cash flow, profit loss, and balance sheet data for a company."""
    cursor = conn.cursor()
    cursor.execute("""
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
    """, (company_id,))
    period_row = cursor.fetchone()
    if not period_row:
        cursor.close()
        return None, None, None
    period = period_row[0]
    cursor.close()

    # Cash flow data
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM cash_flow
        WHERE company_id = ? AND period = ?
    """, (company_id, period))
    cf_row = cursor.fetchone()
    if cf_row:
        cursor.execute("PRAGMA table_info(cash_flow);")
        cf_columns = [desc[1] for desc in cursor.fetchall()]
        cf_data = dict(zip(cf_columns, cf_row))
    else:
        cf_data = {}
    cursor.close()

    # Profit loss data
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM profit_loss
        WHERE company_id = ? AND period = ?
    """, (company_id, period))
    pl_row = cursor.fetchone()
    if pl_row:
        cursor.execute("PRAGMA table_info(profit_loss);")
        pl_columns = [desc[1] for desc in cursor.fetchall()]
        pl_data = dict(zip(pl_columns, pl_row))
    else:
        pl_data = {}
    cursor.close()

    # Balance sheet data
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM balance_sheet
        WHERE company_id = ? AND period = ?
    """, (company_id, period))
    bs_row = cursor.fetchone()
    if bs_row:
        cursor.execute("PRAGMA table_info(balance_sheet);")
        bs_columns = [desc[1] for desc in cursor.fetchall()]
        bs_data = dict(zip(bs_columns, bs_row))
    else:
        bs_data = {}
    cursor.close()

    return cf_data, pl_data, bs_data


def compute_cfo_quality(cf_data_list, pl_data_list):
    """Compute CFO Quality ratio (average CFO/PAT over available years)."""
    ratios = []
    for cf_data, pl_data in zip(cf_data_list, pl_data_list):
        cfo = _get_operating_cash_flow(cf_data)
        net_profit = pl_data.get('net_profit')
        if cfo is not None and net_profit is not None and net_profit != 0:
            ratios.append(cfo / net_profit)
    return sum(ratios) / len(ratios) if ratios else None


def compute_capex_intensity_latest(cf_data, pl_data):
    """Compute CapEx Intensity for latest year."""
    investing_activity = _safe_get_value(cf_data, "cash_from_investing_activity", 0)
    if investing_activity == 0:  # Try alternative column name
        investing_activity = _safe_get_value(cf_data, "investing_activity", 0)
    # Capex is typically negative (cash outflow), return absolute value
    if investing_activity < 0:
        investing_activity = abs(investing_activity)
    sales = _safe_get_value(pl_data, 'sales', 0)
    return (investing_activity / sales * 100) if sales != 0 else None


def compute_fcf_cagr_5yr(cf_data_list, pl_data_list):
    """Compute 5-year CAGR of Free Cash Flow."""
    fcf_values = []
    for cf_data, pl_data in zip(cf_data_list, pl_data_list):
        ocf = _get_operating_cash_flow(cf_data)
        capex = _safe_get_value(cf_data, "cash_from_investing_activity", 0)
        if capex == 0:  # Try alternative column name
            capex = _safe_get_value(cf_data, "investing_activity", 0)
        # Capex is typically negative (cash outflow), convert to positive for FCF calculation
        if capex < 0:
            capex = abs(capex)
        fcf = ocf - capex if ocf is not None else None
        fcf_values.append(fcf)

    # Filter out None values and ensure we have at least 2 points for CAGR
    valid_fcf = [fcf for fcf in fcf_values if fcf is not None]
    if len(valid_fcf) >= 2:
        # Use the earliest and latest values for 5-year CAGR
        start_value = valid_fcf[0]
        end_value = valid_fcf[-1]
        num_years = len(valid_fcf) - 1
        if start_value != 0:  # Avoid division by zero
            result = calculate_cagr(start_value, end_value, num_years, "FCF")
            return result["value"]
    return None


def compute_fcf_conversion_latest(cf_data, pl_data):
    """Compute FCF Conversion for latest year."""
    ocf = _get_operating_cash_flow(cf_data)
    capex = _safe_get_value(cf_data, "cash_from_investing_activity", 0)
    if capex == 0:  # Try alternative column name
        capex = _safe_get_value(cf_data, "investing_activity", 0)
    # Capex is typically negative (cash outflow), convert to positive for FCF calculation
    if capex < 0:
        capex = abs(capex)
    fcf = ocf - capex if ocf is not None else None
    net_profit = _safe_get_value(pl_data, 'net_profit', 0)
    return (fcf / net_profit * 100) if net_profit != 0 and fcf is not None else None


def compute_distress_flag_latest(cf_data):
    """Compute Distress Flag for latest year (CFO < 0 AND CFF > 0)."""
    cfo = _get_operating_cash_flow(cf_data)
    cff = cf_data.get('cash_from_financing_activity') or cf_data.get('financing_activity')
    return bool(cfo is not None and cff is not None and cfo < 0 and cff > 0)


def compute_deleveraging_flag_latest(cf_data_list, bs_data_list):
    """Compute Deleveraging Flag (CFF < 0 AND borrowings declining year-over-year)."""
    if len(cf_data_list) < 2 or len(bs_data_list) < 2:
        return False

    # Check latest year
    latest_cf = cf_data_list[-1]
    latest_bs = bs_data_list[-1]
    cff = latest_cf.get('cash_from_financing_activity') or latest_cf.get('financing_activity')
    borrowings = latest_bs.get('borrowings')

    if cff is None or borrowings is None:
        return False

    # Check if CFF < 0
    if cff >= 0:
        return False

    # Check if borrowings are declining compared to previous year
    prev_bs = bs_data_list[-2]
    prev_borrowings = prev_bs.get('borrowings')

    if prev_borrowings is None:
        return False

    return borrowings < prev_borrowings


def compute_capital_allocation_label_latest(cf_data, pl_data):
    """Compute Capital Allocation Label by reusing existing classify_capital_allocation."""
    ocf = _get_operating_cash_flow(cf_data)
    capex = _safe_get_value(cf_data, "cash_from_investing_activity", 0)
    if capex == 0:  # Try alternative column name
        capex = _safe_get_value(cf_data, "investing_activity", 0)
    # Capex is typically negative (cash outflow), return absolute value
    if capex < 0:
        capex = abs(capex)
    fcf = ocf - capex if ocf is not None else None
    net_profit = _safe_get_value(pl_data, 'net_profit', 0)
    sales = _safe_get_value(pl_data, 'sales', 0)

    cash_conversion = (fcf / net_profit * 100) if net_profit != 0 and fcf is not None else 0
    capex_intensity = (capex / sales * 100) if sales != 0 else 0

    return classify_capital_allocation(fcf, cash_conversion, capex_intensity, ocf)


def process_company(company_id):
    """Process a single company and return computed metrics."""
    conn = None
    try:
        # Create a fresh connection for this company to avoid singleton issues
        DATABASE_DIR.mkdir(parents=True, exist_ok=True)
        database_path = SQLITE_DATABASE
        conn = sqlite3.connect(database_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        logger.debug(f"Successfully got fresh connection for company {company_id}")

        # Fetch historical data (up to 5 years)
        cursor = conn.cursor()
        cursor.execute("""
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
        """, (company_id,))
        periods = [row[0] for row in cursor.fetchall()]
        cursor.close()

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
            'company_id': company_id,
            'cfo_quality': compute_cfo_quality(cf_data_list, pl_data_list),
            'capex_intensity_latest': compute_capex_intensity_latest(cf_data_list[-1], pl_data_list[-1]) if cf_data_list and pl_data_list else None,
            'fcf_cagr_5yr': compute_fcf_cagr_5yr(cf_data_list, pl_data_list),
            'fcf_conversion_latest': compute_fcf_conversion_latest(cf_data_list[-1], pl_data_list[-1]) if cf_data_list and pl_data_list else None,
            'distress_flag_latest': compute_distress_flag_latest(cf_data_list[-1]) if cf_data_list else None,
            'deleveraging_flag_latest': compute_deleveraging_flag_latest(cf_data_list, bs_data_list),
            'capital_allocation_label_latest': compute_capital_allocation_label_latest(cf_data_list[-1], pl_data_list[-1]) if cf_data_list and pl_data_list else None,
        }

        return result

    except Exception as e:
        logger.error(f"Error processing company {company_id}: {e}")
        return None
    finally:
        # Close the connection for this company
        if conn:
            conn.close()


def main():
    """Main function to process all companies and generate output files."""
    logger.info("Starting Module 3: Cash Flow Intelligence Engine (Clean Version)")

    # Ensure output directory exists
    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get all companies from the authoritative companies table
    conn = None
    try:
        # Create a fresh connection for getting companies list
        DATABASE_DIR.mkdir(parents=True, exist_ok=True)
        database_path = SQLITE_DATABASE
        conn = sqlite3.connect(database_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")

        cursor = conn.cursor()
        cursor.execute("SELECT company_id FROM companies")
        companies = [row[0] for row in cursor.fetchall()]
        cursor.close()
        logger.info(f"Found {len(companies)} companies in companies table")
    except Exception as e:
        logger.error(f"Failed to get companies list: {e}")
        return
    finally:
        if conn:
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
        'company_id',
        'cfo_quality',
        'capex_intensity_latest',
        'fcf_cagr_5yr',
        'fcf_conversion_latest',
        'distress_flag_latest',
        'deleveraging_flag_latest',
        'capital_allocation_label_latest',
    ]
    df = df[column_order]

    # Save to Excel
    excel_path = output_dir / "cashflow_intelligence.xlsx"
    df.to_excel(excel_path, index=False)
    logger.info(f"Saved cash flow intelligence to {excel_path}")

    # Filter for distressed companies and save to CSV
    distressed_df = df[df['distress_flag_latest'] == True].copy()
    csv_path = output_dir / "distress_alerts.csv"
    distressed_df.to_csv(csv_path, index=False)
    logger.info(f"Saved distress alerts to {csv_path} ({len(distressed_df)} companies)")

    logger.info("Module 3 processing complete")


if __name__ == "__main__":
    main()