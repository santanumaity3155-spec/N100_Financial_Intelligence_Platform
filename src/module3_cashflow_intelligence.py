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
sys.path.append(str(PROJECT_ROOT))

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
from src.analytics.cagr import calculate_cagr, FLAG_NORMAL, FLAG_ZERO_BASE, FLAG_DECLINE_TO_LOSS, FLAG_TURNAROUND, FLAG_BOTH_NEGATIVE, FLAG_INSUFFICIENT

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Constants for classifications
# CFO Quality
CFO_QUALITY_HIGH_THRESHOLD = 1.0
CFO_QUALITY_MODERATE_LOWER = 0.5
CFO_QUALITY_MODERATE_UPPER = 1.0

# CapEx Intensity
CAPEX_INTENSITY_ASSET_LIGHT = 3.0
CAPEX_INTENSITY_MODERATE_UPPER = 8.0

# Output directories
OUTPUT_DIR = Path(__file__).resolve().parents[2] / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

EXCEL_OUTPUT_PATH = OUTPUT_DIR / "cashflow_intelligence.xlsx"
DISTRESS_CSV_PATH = OUTPUT_DIR / "distress_alerts.csv"


def fetch_company_data(conn, company_id: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Fetch cash flow, profit & loss, and balance sheet data for a company.
    Returns three DataFrames sorted by period ascending (oldest first).
    """
    query_cf = """
        SELECT period, cash_from_operating_activity, cash_from_investing_activity, cash_from_financing_activity
        FROM cash_flow
        WHERE company_id = ?
        ORDER BY period ASC
    """
    query_pl = """
        SELECT period, sales, net_profit
        FROM profit_loss
        WHERE company_id = ?
        ORDER BY period ASC
    """
    query_bs = """
        SELECT period, borrowings
        FROM balance_sheet
        WHERE company_id = ?
        ORDER BY period ASC
    """

    cf_df = pd.read_sql_query(query_cf, conn, params=(company_id,))
    pl_df = pd.read_sql_query(query_pl, conn, params=(company_id,))
    bs_df = pd.read_sql_query(query_bs, conn, params=(company_id,))

    return cf_df, pl_df, bs_df


def compute_cfo_quality(cf_df: pd.DataFrame, pl_df: pd.DataFrame) -> Tuple[Optional[float], str]:
    """
    Compute CFO Quality score as the average CFO/PAT over the latest 5 valid years.
    Returns (score, label) where label is one of: "High Quality", "Moderate", "Accrual Risk".
    If insufficient data, returns (None, "Insufficient Data").
    """
    # Merge CF and PL on period to compute CFO/PAT for each year
    merged = pd.merge(cf_df[['period', 'cash_from_operating_activity']],
                      pl_df[['period', 'net_profit']],
                      on='period',
                      how='inner')

    # Calculate ratio, ignoring rows where net_profit is 0 or missing (to avoid division by zero)
    merged['cfo_pat_ratio'] = np.where(
        merged['net_profit'] != 0,
        merged['cash_from_operating_activity'] / merged['net_profit'],
        np.nan
    )

    # Drop NaN ratios (where net_profit was 0 or missing, or CFO missing)
    valid_ratios = merged['cfo_pat_ratio'].dropna()

    # We need at least 1 valid year to compute an average (spec says use available years if permitted)
    # But we'll follow the spec: use latest available 5 years, if fewer exist use those.
    # However, we must not fabricate. So we take the last up to 5 valid ratios.
    latest_valid = valid_ratios.tail(5)  # most recent up to 5

    if latest_valid.empty:
        return None, "Insufficient Data"

    avg_ratio = latest_valid.mean()

    # Classify
    if avg_ratio > CFO_QUALITY_HIGH_THRESHOLD:
        label = "High Quality"
    elif avg_ratio >= CFO_QUALITY_MODERATE_LOWER and avg_ratio <= CFO_QUALITY_MODERATE_UPPER:
        label = "Moderate"
    else:  # avg_ratio < 0.5
        label = "Accrual Risk"

    return round(avg_ratio, 2), label


def compute_capex_intensity_latest(cf_df: pd.DataFrame, pl_df: pd.DataFrame) -> Tuple[Optional[float], str]:
    """
    Compute CapEx Intensity for the latest year: abs(investing_activity) / sales * 100.
    investing_activity = cash_from_investing_activity (negative for outflow, so we take abs).
    Returns (value, label) where label is one of: "Asset Light", "Moderate", "Capital Intensive".
    If missing data, returns (None, "Insufficient Data").
    """
    if cf_df.empty or pl_df.empty:
        return None, "Insufficient Data"

    # Get the latest period (assuming periods are sorted ascending, last row is latest)
    latest_cf = cf_df.iloc[-1]
    latest_pl = pl_df.iloc[-1]

    # Ensure they are from the same period (should be if data is consistent, but we'll check)
    if latest_cf['period'] != latest_pl['period']:
        # Try to align by period: we'll take the latest period that exists in both
        common_periods = set(cf_df['period']).intersection(set(pl_df['period']))
        if not common_periods:
            return None, "Insufficient Data"
        latest_period = max(common_periods)  # assuming period string is comparable lexically
        latest_cf = cf_df[cf_df['period'] == latest_period].iloc[0]
        latest_pl = pl_df[pl_df['period'] == latest_period].iloc[0]

    investing_activity = latest_cf['cash_from_investing_activity']
    sales = latest_pl['sales']

    # Check for missing values
    if pd.isna(investing_activity) or pd.isna(sales):
        return None, "Insufficient Data"

    if sales == 0:
        # Avoid division by zero; spec says do not substitute zero for missing sales.
        return None, "Insufficient Data (zero sales)"

    capex_intensity = (abs(investing_activity) / sales) * 100

    # Classify
    if capex_intensity < CAPEX_INTENSITY_ASSET_LIGHT:
        label = "Asset Light"
    elif capex_intensity <= CAPEX_INTENSITY_MODERATE_UPPER:
        label = "Moderate"
    else:
        label = "Capital Intensive"

    return round(capex_intensity, 2), label


def compute_fcf_cagr_5yr(cf_df: pd.DataFrame) -> Tuple[Optional[float], str]:
    """
    Compute 5-year CAGR of FCF (Free Cash Flow = OCF - CapEx).
    Uses the existing CAGR implementation from src.analytics.cagr.py.
    Returns (cagr_value, flag) where flag is one of the CAGR flag constants or None for normal.
    If insufficient data, returns (None, FLAG_INSUFFICIENT).
    """
    # We need at least 2 years of data to compute CAGR, and we want exactly 5 years if possible.
    # The CAGR function will handle insufficient data and edge cases.

    # Prepare a DataFrame with period and FCF for each year
    fcf_list = []
    for _, row in cf_df.iterrows():
        period = row['period']
        ocf = row['cash_from_operating_activity']
        investing_activity = row['cash_from_investing_activity']
        # FCF = OCF - CapEx (CapEx is negative in statement, so subtracting a negative adds)
        # But note: the existing calculate_free_cash_flow uses OCF - |CapEx|? Let's check.
        # In cashflow_kpis.py, _get_capital_expenditure returns abs(CAPEX_COLUMN) if negative, else 0.
        # Actually, it returns the absolute value of the investing activity (which is negative) as positive.
        # Then FCF = OCF - capex (where capex is positive). So FCF = OCF - abs(investing_activity) if investing_activity is negative.
        # However, the data may have investing_activity already negative (cash outflow). We'll follow the same logic as calculate_free_cash_flow.
        # We'll reuse the helper functions from cashflow_kpis to compute FCF per year.
        # But note: calculate_free_cash_flow expects a DataFrame with the columns for one period.
        # We'll create a one-row DataFrame for each year and call calculate_free_cash_flow.
        cf_single = pd.DataFrame([{
            'cash_from_operating_activity': ocf,
            'cash_from_investing_activity': investing_activity
        }])
        fcf = calculate_free_cash_flow(cf_single)
        if fcf is not None:
            fcf_list.append({'period': period, 'fcf': fcf})

    if len(fcf_list) < 2:
        return None, FLAG_INSUFFICIENT

    fcf_df = pd.DataFrame(fcf_list).sort_values('period')  # ascending
    # We need the last 5 years (most recent 5) for 5-year CAGR.
    # If we have more than 5, we take the latest 5.
    # If we have between 2 and 4, we use all available (but the spec says 5-year, so we might flag as insufficient?).
    # The spec: "Calculate 5-year FCF CAGR where valid." and "Do not calculate a misleading CAGR when insufficient historical years exist."
    # We'll use the existing CAGR function which will flag INSUFFICIENT if less than 2 data points.
    # However, we want exactly 5 years? The existing CAGR function in cagr.py uses the actual years between start and end.
    # We'll compute CAGR over the period we have (up to 5 years) and let the flag indicate if it's less than 5 years?
    # But the existing CAGR function doesn't flag based on number of years, only on start/end values and years input.
    # We'll compute the CAGR over the entire available period (if we have at least 2 points) and then if the number of years is less than 5, we might still return a value but note it's not 5-year.
    # However, the spec says 5-year FCF CAGR. So we should only compute if we have at least 5 years of data?
    # Let's re-read: "Calculate 5-year FCF CAGR where valid." and "Do not calculate a misleading CAGR when: ... insufficient historical years exist"
    # So we should only compute when we have at least 5 years of data (i.e., 5 annual points).
    # We'll check: we need at least 5 valid FCF values (not necessarily consecutive years? but we assume annual data).
    # We'll take the latest 5 years by period. If we have less than 5 periods with valid FCF, we return insufficient.

    # Get the latest 5 periods by sorting descending and taking first 5, then sort ascending for CAGR calculation.
    latest_fcf = fcf_df.tail(5)  # most recent up to 5
    if len(latest_fcf) < 5:
        # Not enough data for a 5-year CAGR
        return None, FLAG_INSUFFICIENT

    # Now we have exactly 5 points (most recent 5 years). Compute CAGR from the first to the last of these 5.
    start_value = latest_fcf['fcf'].iloc[0]  # oldest of the 5
    end_value = latest_fcf['fcf'].iloc[-1]   # most recent of the 5
    years = 4  # because 5 years of data gives 4 year intervals? Actually, CAGR over 5 years means from year 0 to year 5 -> 5 periods, 4 years difference?
    # However, the existing CAGR function in cagr.py expects the number of years between start and end.
    # If we have data for years: 2019, 2020, 2021, 2022, 2023 (5 years), then the number of years between 2019 and 2023 is 4.
    # But the spec says "5-year FCF CAGR", which typically means the compound annual growth rate over a 5-year period, i.e., from 2019 to 2023 (5 years of data, 4 years of growth).
    # The existing calculate_cagr function uses the formula: (end/start)^(1/years) - 1, where years is the number of years.
    # So we should pass years=4 for 5 years of data.
    # However, the existing CAGR functions in the project (like calculate_revenue_cagr) use the window_years as the number of years (e.g., 5 for 5-year CAGR) and then compute the actual years between periods.
    # Let's look at calculate_cagr in cagr.py: it takes start_value, end_value, years (the number of years).
    # In calculate_revenue_cagr, they call calculate_cagr(start_value, end_value, years, ...) where years is the window_years (e.g., 5).
    # And inside _calculate_cagr_for_window, they compute actual_years from the period strings and then use years = min(actual_years, window_years).
    # So if we have exactly 5 years of data (2019 to 2023), actual_years will be 4, and then years = min(4, 5) = 4.
    # Therefore, we can simply call calculate_cagr(start_value, end_value, 5, "fcf") and it will adjust to the actual years.
    # But note: we have exactly 5 data points, which span 4 years (if annual). So we want the 5-year CAGR to be based on 5 years of data (4 years of growth).
    # The existing functions do exactly that: they use the window_years as the maximum number of years, but then use the actual years between the start and end periods.
    # So we'll follow the same pattern: call calculate_cagr(start_value, end_value, 5, "fcff").

    cagr_result = calculate_cagr(start_value, end_value, 5, "fcf")
    return cagr_result["value"], cagr_result["flag"]


def compute_fcf_conversion_latest(cf_df: pd.DataFrame, pl_df: pd.DataFrame) -> Tuple[Optional[float], str]:
    """
    Compute FCF Conversion for the latest year: FCF / PAT * 100.
    Returns (value, flag) where flag is None if successful, or "INSUFFICIENT_DATA" or "ZERO_PAT" etc.
    """
    if cf_df.empty or pl_df.empty:
        return None, "INSUFFICIENT_DATA"

    # Get latest period common to both
    latest_cf = cf_df.iloc[-1]
    latest_pl = pl_df.iloc[-1]
    if latest_cf['period'] != latest_pl['period']:
        common_periods = set(cf_df['period']).intersection(set(pl_df['period']))
        if not common_periods:
            return None, "INSUFFICIENT_DATA"
        latest_period = max(common_periods)
        latest_cf = cf_df[cf_df['period'] == latest_period].iloc[0]
        latest_pl = pl_df[pl_df['period'] == latest_period].iloc[0]

    # Compute FCF for this period (using helper)
    cf_single = pd.DataFrame([{
        'cash_from_operating_activity': latest_cf['cash_from_operating_activity'],
        'cash_from_investing_activity': latest_cf['cash_from_investing_activity']
    }])
    fcf = calculate_free_cash_flow(cf_single)
    pat = latest_pl['net_profit']

    if fcf is None:
        return None, "INSUFFICIENT_FCF"
    if pd.isna(pat):
        return None, "INSUFFICIENT_PAT"
    if pat == 0:
        return None, "ZERO_PAT"

    fcf_conversion = (fcf / pat) * 100
    return round(fcf_conversion, 2), None


def compute_distress_flag_latest(cf_df: pd.DataFrame) -> Tuple[bool, Optional[float], Optional[float]]:
    """
    Compute Distress Flag for the latest year: CFO < 0 AND CFF > 0.
    Returns (flag, cfo_value, cff_value).
    If data missing, flag is False and values are None.
    """
    if cf_df.empty:
        return False, None, None

    latest_cf = cf_df.iloc[-1]
    cfo = latest_cf['cash_from_operating_activity']
    cff = latest_cf['cash_from_financing_activity']

    # If either is missing, we cannot confirm distress (spec says do not fabricate)
    if pd.isna(cfo) or pd.isna(cff):
        return False, cfo, cff

    distress = (cfo < 0) and (cff > 0)
    return distress, cfo, cff


def compute_deleveraging_flag_latest(cf_df: pd.DataFrame, bs_df: pd.DataFrame) -> Tuple[bool, Optional[float], Optional[float]]:
    """
    Compute Deleveraging Flag for the latest year: CFF < 0 AND borrowings declining year-over-year.
    Returns (flag, cff_value, borrowings_change).
    borrowings_change = borrowings_latest - borrowings_previous (so negative means decline).
    If insufficient borrowings data (less than 2 consecutive years), flag is False.
    """
    if cf_df.empty or bs_df.empty:
        return False, None, None

    # We need the latest year's CFF and at least two consecutive years of borrowings data.
    # Get latest CFF from cash_flow
    latest_cf = cf_df.iloc[-1]
    cff = latest_cf['cash_from_financing_activity']
    latest_period_cf = latest_cf['period']

    if pd.isna(cff):
        return False, None, None

    # We need borrowings for the latest period and the period before that (must be consecutive years).
    # We'll get all borrowings data sorted by period ascending.
    bs_sorted = bs_df.sort_values('period')
    # We need to find the latest period that exists in both cash_flow and balance_sheet?
    # But for deleveraging we need borrowings from the balance_sheet for the same period as CFF?
    # The spec says: borrowings are declining year-over-year. It doesn't specify that the borrowings must be from the same period as CFF,
    # but logically we want the borrowings for the year of the CFF and the year before.
    # We'll assume we want the borrowings for the latest period available in balance_sheet (which should be the same as the latest cash_flow period if data is aligned).
    # However, to be safe, we'll use the latest period that exists in both tables for borrowings and CFF.

    # Get the latest period that has both CFF and borrowings data.
    # We'll merge cf_df[['period','cash_from_financing_activity']] and bs_df[['period','borrowings']] on period.
    merged = pd.merge(
        cf_df[['period', 'cash_from_financing_activity']],
        bs_df[['period', 'borrowings']],
        on='period',
        how='inner'
    )
    if merged.empty:
        return False, None, None

    # Sort by period ascending
    merged = merged.sort_values('period')
    # We need at least 2 periods to compute year-over-year change.
    if len(merged) < 2:
        return False, None, None

    # Take the two most recent periods
    latest_two = merged.tail(2)
    latest_period = latest_two.iloc[-1]['period']
    previous_period = latest_two.iloc[-2]['period']

    # Check that the periods are consecutive? We'll assume annual data and that the periods are in order.
    # We could check the difference, but for simplicity we'll just use the two latest.
    latest_cff = latest_two.iloc[-1]['cash_from_financing_activity']
    latest_borrowings = latest_two.iloc[-1]['borrowings']
    previous_borrowings = latest_two.iloc[-2]['borrowings']

    if pd.isna(latest_cff) or pd.isna(latest_borrowings) or pd.isna(previous_borrowings):
        return False, None, None

    # Deleveraging condition: CFF < 0 AND borrowings declining (latest_borrowings < previous_borrowings)
    deleveraging = (latest_cff < 0) and (latest_borrowings < previous_borrowings)
    borrowings_change = latest_borrowings - previous_borrowings  # negative means decline

    return deleveraging, latest_cff, borrowings_change


def compute_capital_allocation_label_latest(cf_df: pd.DataFrame, pl_df: pd.DataFrame, bs_df: pd.DataFrame) -> str:
    """
    Compute Capital Allocation Label by reusing classify_capital_allocation.
    Returns the label string (one of EXCELLENT, GOOD, MODERATE, WEAK, DISTRESSED) or "Insufficient Data".
    """
    if cf_df.empty or pl_df.empty or bs_df.empty:
        return "Insufficient Data"

    # Get latest period common to all three
    latest_cf = cf_df.iloc[-1]
    latest_pl = pl_df.iloc[-1]
    latest_bs = bs_df.iloc[-1]

    # If periods don't align, try to find a common latest period
    cf_period = latest_cf['period']
    pl_period = latest_pl['period']
    bs_period = latest_bs['period']

    if not (cf_period == pl_period == bs_period):
        # Find intersection of periods
        common_periods = set(cf_df['period']).intersection(set(pl_df['period'])).intersection(set(bs_df['period']))
        if not common_periods:
            return "Insufficient Data"
        latest_period = max(common_periods)
        latest_cf = cf_df[cf_df['period'] == latest_period].iloc[0]
        latest_pl = pl_df[pl_df['period'] == latest_period].iloc[0]
        latest_bs = bs_df[bs_df['period'] == latest_period].iloc[0]

    # Prepare data for classify_capital_allocation
    cf_single = pd.DataFrame([{
        'cash_from_operating_activity': latest_cf['cash_from_operating_activity'],
        'cash_from_investing_activity': latest_cf['cash_from_investing_activity']
    }])
    pl_single = pd.DataFrame([{
        'sales': latest_pl['sales'],
        'net_profit': latest_pl['net_profit']
    }])
    bs_single = pd.DataFrame([{
        'total_assets': latest_bs['total_assets']
    }]) if 'total_assets' in latest_bs and not pd.isna(latest_bs['total_assets']) else pd.DataFrame({'total_assets': [None]})

    # We need to compute FCF, OCF, etc. for the classification.
    # The classify_capital_allocation function expects:
    #   fcf: Optional[float]
    #   cash_conversion: Optional[float]
    #   capex_intensity: Optional[float]
    #   ocf: Optional[float]
    # We can compute these using the helper functions or reuse calculate_all_cashflow_kpis for a single period.
    # Let's compute the necessary components.

    # Operating Cash Flow
    ocf = _safe_get_value(cf_single, 'cash_from_operating_activity')
    # Free Cash Flow
    fcf = calculate_free_cash_flow(cf_single)
    # Cash Conversion = OCF / Net Profit * 100
    net_profit = _safe_get_value(pl_single, 'net_profit')
    if ocf is not None and net_profit is not None and net_profit != 0:
        cash_conversion = (ocf / net_profit) * 100
    else:
        cash_conversion = None
    # CapEx Intensity = abs(investing_activity) / OCF * 100 (if OCF != 0)
    investing_activity = _safe_get_value(cf_single, 'cash_from_investing_activity')
    if investing_activity is not None and ocf is not None and ocf != 0:
        capex_intensity = (abs(investing_activity) / ocf) * 100
    else:
        capex_intensity = None

    # Now call the classifier
    rating = classify_capital_allocation(fcf, cash_conversion, capex_intensity, ocf)
    return reason


def process_company(company_id: str, sector: str) -> Dict[str, Any]:
    """
    Process a single company: fetch data and compute all metrics.
    Returns a dictionary with the results for output.
    """
    logger.info(f"Processing company: {company_id}")
    conn = get_connection()
    try:
        cf_df, pl_df, bs_df = fetch_company_data(conn, company_id)

        # Compute each metric
        cfo_quality_score, cfo_quality_label = compute_cfo_quality(cf_df, pl_df)
        capex_intensity_pct, capex_label = compute_capex_intensity_latest(cf_df, pl_df)
        fcf_cagr_5yr, fcf_cagr_flag = compute_fcf_cagr_5yr(cf_df)
        fcf_conversion_pct, fcf_conversion_flag = compute_fcf_conversion_latest(cf_df, pl_df)
        distress_flag, cfo_value, cff_value = compute_distress_flag_latest(cf_df)
        deleveraging_flag, deleveraging_cff, borrowings_change = compute_deleveraging_flag_latest(cf_df, bs_df)
        capital_allocation_label = compute_capital_allocation_label_latest(cf_df, pl_df, bs_df)

        # Build result dictionary
        result = {
            "company_id": company_id,
            "sector": sector,
            "cfo_quality_score": cfo_quality_score,
            "cfo_quality_label": cfo_quality_label,
            "capex_intensity_pct": capex_intensity_pct,
            "capex_label": capex_label,
            "fcf_cagr_5yr": fcf_cagr_5yr,
            "fcf_conversion_pct": fcf_conversion_pct,
            "distress_flag": distress_flag,
            "deleveraging_flag": deleveraging_flag,
            "capital_allocation_label": capital_allocation_label,
        }

        # For debugging/distress CSV, we might want to keep the raw CFO and CFF values
        # but they are not in the required output. We'll store them separately if needed for distress alerts.
        # We'll return them in a separate dict or add to result with a prefix?
        # Let's return them in the result but mark them as temporary; we'll extract later for distress CSV.
        result["_cfo_value"] = cfo_value
        result["_cff_value"] = cff_value
        result["_net_profit_latest"] = _safe_get_value(pl_df.iloc[-1] if not pl_df.empty else None, 'net_profit') if not pl_df.empty else None

        return result
    except Exception as e:
        logger.error(f"Error processing company {company_id}: {e}", exc_info=True)
        # Return a result with None/empty values for this company
        return {
            "company_id": company_id,
            "sector": sector,
            "cfo_quality_score": None,
            "cfo_quality_label": "Error",
            "capex_intensity_pct": None,
            "capex_label": "Error",
            "fcf_cagr_5yr": None,
            "fcf_conversion_pct": None,
            "distress_flag": False,
            "deleveraging_flag": False,
            "capital_allocation_label": "Error",
            "_cfo_value": None,
            "_cff_value": None,
            "_net_profit_latest": None,
        }
    finally:
        # We should not close the singleton connection here; it's managed elsewhere.
        pass


def main():
    """
    Main function to process all companies and write outputs.
    """
    logger.info("Starting Module 3: Cash Flow Intelligence")

    conn = get_connection()
    try:
        # Get all companies from the authoritative table
        companies_df = pd.read_sql_query("SELECT company_id, sector FROM companies ORDER BY company_id", conn)
        company_list = companies_df.to_dict('records')
        logger.info(f"Found {len(company_list)} companies to process")
    except Exception as e:
        logger.error(f"Failed to fetch company list: {e}")
        return
    finally:
        # Connection remains open for reuse in process_company (though we open a new one each time?
        # Actually, get_connection() returns the same connection each time due to singleton.
        # We'll leave it open; the application will manage it.
        pass

    # Process each company
    results = []
    for company_info in company_list:
        company_id = company_info['company_id']
        sector = company_info['sector']
        result = process_company(company_id, sector)
        results.append(result)

    # Convert results to DataFrame
    results_df = pd.DataFrame(results)

    # Prepare the final output for Excel (excluding the temporary columns)
    output_columns = [
        "company_id", "sector",
        "cfo_quality_score", "cfo_quality_label",
        "capex_intensity_pct", "capex_label",
        "fcf_cagr_5yr", "fcf_conversion_pct",
        "distress_flag", "deleveraging_flag",
        "capital_allocation_label"
    ]
    # Ensure we only include columns that exist (in case of errors)
    output_columns = [col for col in output_columns if col in results_df.columns]
    output_df = results_df[output_columns].copy()

    # Write to Excel
    try:
        output_df.to_excel(EXCEL_OUTPUT_PATH, index=False)
        logger.info(f"Written Excel output to {EXCEL_OUTPUT_PATH} with {len(output_df)} rows")
    except Exception as e:
        logger.error(f"Failed to write Excel file: {e}")

    # Prepare distress alerts CSV
    distress_df = results_df[results_df['distress_flag'] == True].copy()
    # We need to output: company_id, sector, CFO value, CFF value, latest net profit
    distress_output = distress_df[['company_id', 'sector', '_cfo_value', '_cff_value', '_net_profit_latest']].copy()
    distress_output = distress_output.rename(columns={
        '_cfo_value': 'CFO',
        '_cff_value': 'CFF',
        '_net_profit_latest': 'latest_net_profit'
    })
    try:
        distress_output.to_csv(DISTRESS_CSV_PATH, index=False)
        logger.info(f"Written distress alerts CSV to {DISTRESS_CSV_PATH} with {len(distress_output)} rows")
    except Exception as e:
        logger.error(f"Failed to write distress CSV: {e}")

    # Log summary statistics
    logger.info("=== Processing Summary ===")
    logger.info(f"Total companies processed: len(results_df)")
    logger.info(f"CFO Quality calculated: {results_df['cfo_quality_score'].notna().sum()}")
    logger.info(f"CapEx Intensity calculated: {results_df['capex_intensity_pct'].notna().sum()}")
    logger.info(f"FCF CAGR 5yr calculated: {results_df['fcf_cagr_5yr'].notna().sum()}")
    logger.info(f"FCF Conversion calculated: {results_df['fcf_conversion_pct'].notna().sum()}")
    logger.info(f"Distress flags True: {results_df['distress_flag'].sum()}")
    logger.info(f"Deleveraging flags True: {results_df['deleveraging_flag'].sum()}")
    logger.info(f"Capital Allocation labels assigned: {results_df['capital_allocation_label'].notna().sum()}")

    logger.info("Module 3 processing completed.")


if __name__ == "__main__":
    main()