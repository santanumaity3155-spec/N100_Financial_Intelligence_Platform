"""
cashflow_kpis.py

Cash Flow KPI Engine for the N100 Financial Intelligence Platform.

This module provides production-quality functions to calculate cash flow quality metrics
including Free Cash Flow, FCF Margin, Cash Conversion, CapEx Intensity, and more.

All functions are modular, reusable, well-documented, type-hinted, and fully logged.
"""

import logging
from typing import Optional, Dict, Any, List
import pandas as pd
import numpy as np

from src.config.logging_config import get_logger
from src.analytics.cagr import calculate_cagr, CAGR_WINDOWS

logger = get_logger(__name__)


# =============================================================================
# CONSTANTS
# =============================================================================

# Cash Flow column names
OCF_COLUMN = "cash_from_operating_activity"
OCF_ALT_COLUMN = "operating_activity"
CAPEX_COLUMN = "cash_from_investing_activity"
FCF_COLUMN = "free_cash_flow"
SALES_COLUMN = "sales"
NET_PROFIT_COLUMN = "net_profit"
TOTAL_ASSETS_COLUMN = "total_assets"
PERIOD_COLUMN = "period"

# Cash Conversion thresholds
CASH_CONVERSION_EXCELLENT = 100.0
CASH_CONVERSION_GOOD = 80.0
CASH_CONVERSION_AVERAGE = 50.0

# CapEx Intensity threshold
CAPEX_INTENSITY_EXCELLENT = 50.0

# Capital Allocation Ratings
RATING_EXCELLENT = "EXCELLENT"
RATING_GOOD = "GOOD"
RATING_MODERATE = "MODERATE"
RATING_WEAK = "WEAK"
RATING_DISTRESSED = "DISTRESSED"

VALID_RATINGS = [
    RATING_EXCELLENT,
    RATING_GOOD,
    RATING_MODERATE,
    RATING_WEAK,
    RATING_DISTRESSED
]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _validate_numeric(value: Any, name: str) -> bool:
    """
    Validate that a value is numeric and not NaN or infinite.

    Parameters
    ----------
    value : Any
        Value to validate
    name : str
        Name of the value for logging

    Returns
    -------
    bool
        True if valid, False otherwise
    """
    if value is None or pd.isna(value):
        logger.warning(f"Invalid input: {name} is None or NaN")
        return False
    
    if isinstance(value, (int, float)):
        if np.isinf(value):
            logger.warning(f"Invalid input: {name} is infinite")
            return False
    
    return True


def _validate_dataframe(df: pd.DataFrame, required_columns: List[str], context: str = "") -> bool:
    """
    Validate DataFrame has required columns and sufficient data.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to validate
    required_columns : List[str]
        List of required column names
    context : str, optional
        Context for logging

    Returns
    -------
    bool
        True if valid, False otherwise
    """
    if df.empty:
        logger.warning(f"Data validation{context}: Empty dataframe provided")
        return False
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        logger.warning(f"Data validation{context}: Missing columns: {missing_columns}")
        return False
    
    return True


def _validate_time_series(df: pd.DataFrame, period_column: str = PERIOD_COLUMN) -> Optional[List[str]]:
    """
    Validate time series data for duplicates, sorting, and missing values.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to validate
    period_column : str, optional
        Name of the period column, by default "period"

    Returns
    -------
    Optional[List[str]]
        Sorted list of unique periods if valid, None otherwise
    """
    if period_column not in df.columns:
        logger.warning(f"Time series validation: Period column '{period_column}' not found")
        return None
    
    periods = df[period_column].dropna().tolist()
    
    # Check for duplicates
    if len(periods) != len(set(periods)):
        duplicates = [p for p in set(periods) if periods.count(p) > 1]
        logger.warning(f"Time series validation: Duplicate periods found: {duplicates}")
        return None
    
    # Check if sorted
    if periods != sorted(periods):
        logger.warning("Time series validation: Periods are not in chronological order")
        return None
    
    return sorted(periods)


def _safe_get_value(df: pd.DataFrame, column: str, default: Any = None) -> Any:
    """
    Safely extract a value from a DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to extract value from
    column : str
        Column name to extract
    default : Any, optional
        Default value if column not found or value is NaN

    Returns
    -------
    Any
        Extracted value or default
    """
    if df.empty:
        return default
    
    series = df.get(column, pd.Series([default]))
    if hasattr(series, 'iloc') and len(series) > 0:
        value = series.iloc[0]
        return value if not pd.isna(value) else default
    return default


def _get_operating_cash_flow(cf_data: pd.DataFrame) -> Optional[float]:
    """
    Extract Operating Cash Flow from cash flow data.

    Parameters
    ----------
    cf_data : pd.DataFrame
        Cash Flow data

    Returns
    -------
    Optional[float]
        Operating Cash Flow value or None
    """
    # Try primary column name first
    ocf = _safe_get_value(cf_data, OCF_COLUMN)
    
    # If not available, try alternative column name
    if ocf is None:
        ocf = _safe_get_value(cf_data, OCF_ALT_COLUMN)
    
    if ocf is not None:
        logger.debug(f"Operating Cash Flow extracted: {ocf:.2f}")
    else:
        logger.warning("Operating Cash Flow: Missing data")
    
    return ocf


def _get_capital_expenditure(cf_data: pd.DataFrame) -> float:
    """
    Extract Capital Expenditure from cash flow data.

    Parameters
    ----------
    cf_data : pd.DataFrame
        Cash Flow data

    Returns
    -------
    float
        Capital Expenditure value (absolute value, typically negative in statements)
    """
    capex = _safe_get_value(cf_data, CAPEX_COLUMN, 0)
    
    # Capex is typically negative (cash outflow), return absolute value
    if capex is not None and capex < 0:
        capex = abs(capex)
    
    return capex if capex else 0


# =============================================================================
# CORE CASH FLOW KPI FUNCTIONS
# =============================================================================

def calculate_free_cash_flow(cf_data: pd.DataFrame) -> Optional[float]:
    """
    Calculate Free Cash Flow (FCF).

    Formula: FCF = Operating Cash Flow - Capital Expenditure

    Parameters
    ----------
    cf_data : pd.DataFrame
        Cash Flow data with operating and investing activity columns

    Returns
    -------
    Optional[float]
        Free Cash Flow value, or None if calculation not possible

    Examples
    --------
    >>> cf_data = pd.DataFrame({
    ...     'cash_from_operating_activity': [1000],
    ...     'cash_from_investing_activity': [-300]
    ... })
    >>> calculate_free_cash_flow(cf_data)
    700.0
    """
    logger.debug("Calculating Free Cash Flow")
    
    if not _validate_dataframe(cf_data, [OCF_COLUMN, CAPEX_COLUMN], " for FCF"):
        return None
    
    ocf = _get_operating_cash_flow(cf_data)
    capex = _get_capital_expenditure(cf_data)
    
    if ocf is None or not _validate_numeric(ocf, "operating_cash_flow"):
        logger.warning("Free Cash Flow calculation: Missing or invalid OCF")
        return None
    
    if not _validate_numeric(capex, "capital_expenditure"):
        logger.warning("Free Cash Flow calculation: Invalid CapEx")
        return None
    
    try:
        # FCF = OCF - CapEx (CapEx is already positive from _get_capital_expenditure)
        fcf = ocf - capex
        
        logger.debug(f"Free Cash Flow calculated: {fcf:.2f} (OCF={ocf:.2f}, CapEx={capex:.2f})")
        return round(fcf, 2)
    
    except Exception as e:
        logger.error(f"Free Cash Flow calculation failed: {str(e)}")
        return None


def calculate_fcf_margin(cf_data: pd.DataFrame, pl_data: pd.DataFrame) -> Optional[float]:
    """
    Calculate FCF Margin.

    Formula: FCF Margin = (FCF / Sales) × 100

    Parameters
    ----------
    cf_data : pd.DataFrame
        Cash Flow data
    pl_data : pd.DataFrame
        Profit & Loss data

    Returns
    -------
    Optional[float]
        FCF Margin percentage, or None if Sales == 0 or data missing

    Examples
    --------
    >>> cf_data = pd.DataFrame({'cash_from_operating_activity': [1000], 'cash_from_investing_activity': [-300]})
    >>> pl_data = pd.DataFrame({'sales': [5000]})
    >>> calculate_fcf_margin(cf_data, pl_data)
    14.0
    """
    logger.debug("Calculating FCF Margin")
    
    if not _validate_dataframe(cf_data, [OCF_COLUMN, CAPEX_COLUMN], " for FCF Margin"):
        return None
    
    if not _validate_dataframe(pl_data, [SALES_COLUMN], " for FCF Margin"):
        return None
    
    fcf = calculate_free_cash_flow(cf_data)
    sales = _safe_get_value(pl_data, SALES_COLUMN)
    
    if fcf is None:
        logger.warning("FCF Margin calculation: FCF is None")
        return None
    
    if sales is None or not _validate_numeric(sales, "sales"):
        logger.warning("FCF Margin calculation: Missing or invalid sales")
        return None
    
    if sales == 0:
        logger.warning("FCF Margin calculation: Sales is zero")
        return None
    
    try:
        margin = (fcf / sales) * 100
        logger.debug(f"FCF Margin calculated: {margin:.2f}%")
        return round(margin, 2)
    
    except Exception as e:
        logger.error(f"FCF Margin calculation failed: {str(e)}")
        return None


def calculate_cash_conversion(cf_data: pd.DataFrame, pl_data: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate Cash Conversion ratio.

    Formula: Cash Conversion = (Operating Cash Flow / Net Profit) × 100

    Parameters
    ----------
    cf_data : pd.DataFrame
        Cash Flow data
    pl_data : pd.DataFrame
        Profit & Loss data

    Returns
    -------
    Dict[str, Any]
        Dictionary containing:
        - "value": Cash Conversion percentage or None
        - "flag": Status flag (None or "INVALID_PROFIT")

    Examples
    --------
    >>> cf_data = pd.DataFrame({'cash_from_operating_activity': [1000]})
    >>> pl_data = pd.DataFrame({'net_profit': [800]})
    >>> calculate_cash_conversion(cf_data, pl_data)
    {"value": 125.0, "flag": None}
    """
    logger.debug("Calculating Cash Conversion")
    
    if not _validate_dataframe(cf_data, [OCF_COLUMN], " for Cash Conversion"):
        return {"value": None, "flag": "INVALID_PROFIT"}
    
    if not _validate_dataframe(pl_data, [NET_PROFIT_COLUMN], " for Cash Conversion"):
        return {"value": None, "flag": "INVALID_PROFIT"}
    
    ocf = _get_operating_cash_flow(cf_data)
    net_profit = _safe_get_value(pl_data, NET_PROFIT_COLUMN)
    
    if ocf is None or not _validate_numeric(ocf, "operating_cash_flow"):
        logger.warning("Cash Conversion calculation: Missing or invalid OCF")
        return {"value": None, "flag": "INVALID_PROFIT"}
    
    if net_profit is None or not _validate_numeric(net_profit, "net_profit"):
        logger.warning("Cash Conversion calculation: Missing or invalid net profit")
        return {"value": None, "flag": "INVALID_PROFIT"}
    
    if net_profit <= 0:
        logger.warning(f"Cash Conversion calculation: Net profit is {net_profit} (<= 0)")
        return {"value": None, "flag": "INVALID_PROFIT"}
    
    try:
        conversion = (ocf / net_profit) * 100
        logger.debug(f"Cash Conversion calculated: {conversion:.2f}%")
        return {"value": round(conversion, 2), "flag": None}
    
    except Exception as e:
        logger.error(f"Cash Conversion calculation failed: {str(e)}")
        return {"value": None, "flag": "INVALID_PROFIT"}


def calculate_capex_intensity(cf_data: pd.DataFrame) -> Optional[float]:
    """
    Calculate CapEx Intensity.

    Formula: CapEx Intensity = (Capital Expenditure / Operating Cash Flow) × 100

    Parameters
    ----------
    cf_data : pd.DataFrame
        Cash Flow data

    Returns
    -------
    Optional[float]
        CapEx Intensity percentage, or None if OCF == 0 or data missing

    Examples
    --------
    >>> cf_data = pd.DataFrame({'cash_from_operating_activity': [1000], 'cash_from_investing_activity': [-300]})
    >>> calculate_capex_intensity(cf_data)
    30.0
    """
    logger.debug("Calculating CapEx Intensity")
    
    if not _validate_dataframe(cf_data, [OCF_COLUMN, CAPEX_COLUMN], " for CapEx Intensity"):
        return None
    
    ocf = _get_operating_cash_flow(cf_data)
    capex = _get_capital_expenditure(cf_data)
    
    if ocf is None or not _validate_numeric(ocf, "operating_cash_flow"):
        logger.warning("CapEx Intensity calculation: Missing or invalid OCF")
        return None
    
    if not _validate_numeric(capex, "capital_expenditure"):
        logger.warning("CapEx Intensity calculation: Invalid CapEx")
        return None
    
    if ocf == 0:
        logger.warning("CapEx Intensity calculation: OCF is zero")
        return None
    
    try:
        intensity = (capex / ocf) * 100
        logger.debug(f"CapEx Intensity calculated: {intensity:.2f}%")
        return round(intensity, 2)
    
    except Exception as e:
        logger.error(f"CapEx Intensity calculation failed: {str(e)}")
        return None


def calculate_cash_reinvestment_ratio(cf_data: pd.DataFrame) -> Optional[float]:
    """
    Calculate Cash Reinvestment Ratio.

    Formula: Cash Reinvestment Ratio = Capital Expenditure / Operating Cash Flow

    Parameters
    ----------
    cf_data : pd.DataFrame
        Cash Flow data

    Returns
    -------
    Optional[float]
        Cash Reinvestment Ratio, or None if calculation not possible

    Examples
    --------
    >>> cf_data = pd.DataFrame({'cash_from_operating_activity': [1000], 'cash_from_investing_activity': [-300]})
    >>> calculate_cash_reinvestment_ratio(cf_data)
    0.3
    """
    logger.debug("Calculating Cash Reinvestment Ratio")
    
    if not _validate_dataframe(cf_data, [OCF_COLUMN, CAPEX_COLUMN], " for Cash Reinvestment Ratio"):
        return None
    
    ocf = _get_operating_cash_flow(cf_data)
    capex = _get_capital_expenditure(cf_data)
    
    if ocf is None or not _validate_numeric(ocf, "operating_cash_flow"):
        logger.warning("Cash Reinvestment Ratio calculation: Missing or invalid OCF")
        return None
    
    if not _validate_numeric(capex, "capital_expenditure"):
        logger.warning("Cash Reinvestment Ratio calculation: Invalid CapEx")
        return None
    
    if ocf == 0:
        logger.warning("Cash Reinvestment Ratio calculation: OCF is zero")
        return None
    
    try:
        ratio = capex / ocf
        logger.debug(f"Cash Reinvestment Ratio calculated: {ratio:.2f}")
        return round(ratio, 2)
    
    except Exception as e:
        logger.error(f"Cash Reinvestment Ratio calculation failed: {str(e)}")
        return None


def calculate_cash_return_on_assets(cf_data: pd.DataFrame, bs_data: pd.DataFrame) -> Optional[float]:
    """
    Calculate Cash Return on Assets.

    Formula: Cash ROA = (Operating Cash Flow / Total Assets) × 100

    Parameters
    ----------
    cf_data : pd.DataFrame
        Cash Flow data
    bs_data : pd.DataFrame
        Balance Sheet data

    Returns
    -------
    Optional[float]
        Cash ROA percentage, or None if Total Assets == 0 or data missing

    Examples
    --------
    >>> cf_data = pd.DataFrame({'cash_from_operating_activity': [1000]})
    >>> bs_data = pd.DataFrame({'total_assets': [10000]})
    >>> calculate_cash_return_on_assets(cf_data, bs_data)
    10.0
    """
    logger.debug("Calculating Cash Return on Assets")
    
    if not _validate_dataframe(cf_data, [OCF_COLUMN], " for Cash ROA"):
        return None
    
    if not _validate_dataframe(bs_data, [TOTAL_ASSETS_COLUMN], " for Cash ROA"):
        return None
    
    ocf = _get_operating_cash_flow(cf_data)
    total_assets = _safe_get_value(bs_data, TOTAL_ASSETS_COLUMN)
    
    if ocf is None or not _validate_numeric(ocf, "operating_cash_flow"):
        logger.warning("Cash ROA calculation: Missing or invalid OCF")
        return None
    
    if total_assets is None or not _validate_numeric(total_assets, "total_assets"):
        logger.warning("Cash ROA calculation: Missing or invalid total assets")
        return None
    
    if total_assets == 0:
        logger.warning("Cash ROA calculation: Total assets is zero")
        return None
    
    try:
        roa = (ocf / total_assets) * 100
        logger.debug(f"Cash ROA calculated: {roa:.2f}%")
        return round(roa, 2)
    
    except Exception as e:
        logger.error(f"Cash ROA calculation failed: {str(e)}")
        return None


def calculate_operating_cashflow_growth(
    cf_data: pd.DataFrame,
    company_id: Optional[str] = None,
    period: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculate Operating Cash Flow Growth using CAGR.

    Reuses the CAGR engine from Module 2.

    Parameters
    ----------
    cf_data : pd.DataFrame
        Cash Flow data with multiple periods
    company_id : str, optional
        Company identifier for logging
    period : str, optional
        Financial period for logging

    Returns
    -------
    Dict[str, Any]
        Dictionary containing OCF CAGR values and flags for all windows
    """
    logger.info(f"Calculating OCF Growth for company_id={company_id}, period={period}")
    
    if not _validate_dataframe(cf_data, [OCF_COLUMN, PERIOD_COLUMN], " for OCF Growth"):
        return _get_empty_cagr_result("ocf")
    
    # Validate time series
    valid_periods = _validate_time_series(cf_data)
    if valid_periods is None:
        return _get_empty_cagr_result("ocf")
    
    # Calculate CAGR for each window
    results = {}
    ocf_data = cf_data[[PERIOD_COLUMN, OCF_COLUMN]].dropna().sort_values(PERIOD_COLUMN)
    
    for window in CAGR_WINDOWS:
        cagr_result = _calculate_cagr_for_window(
            ocf_data,
            OCF_COLUMN,
            window,
            f"ocf_{window}yr",
            company_id,
            period
        )
        
        results[f"ocf_cagr_{window}yr"] = cagr_result
        results[f"ocf_cagr_{window}yr_flag"] = cagr_result["flag"]
    
    return results


def _calculate_cagr_for_window(
    data: pd.DataFrame,
    column: str,
    window_years: int,
    metric_name: str,
    company_id: Optional[str],
    period: Optional[str]
) -> Dict[str, Any]:
    """
    Calculate CAGR for a specific time window.

    Parameters
    ----------
    data : pd.DataFrame
        Time series data
    column : str
        Column name containing values
    window_years : int
        Number of years for window
    metric_name : str
        Name for logging
    company_id : Optional[str]
        Company identifier
    period : Optional[str]
        Financial period

    Returns
    -------
    Dict[str, Any]
        Dictionary with "value" and "flag" keys
    """
    if len(data) < 2:
        logger.warning(f"CAGR calculation: Insufficient data points for {metric_name}")
        return {"value": None, "flag": "INSUFFICIENT"}
    
    start_value = data[column].iloc[0]
    end_value = data[column].iloc[-1]
    
    # Calculate actual years
    try:
        start_period = data[PERIOD_COLUMN].iloc[0]
        end_period = data[PERIOD_COLUMN].iloc[-1]
        
        start_year = int(str(start_period).replace("FY", "").strip())
        end_year = int(str(end_period).replace("FY", "").strip())
        actual_years = end_year - start_year
        
        if actual_years <= 0:
            logger.warning(f"CAGR calculation: Invalid year range for {metric_name}")
            return {"value": None, "flag": "INSUFFICIENT"}
        
        years = min(actual_years, window_years)
        
    except (ValueError, IndexError) as e:
        logger.warning(f"CAGR calculation: Could not parse periods for {metric_name}: {str(e)}")
        years = window_years
    
    return calculate_cagr(start_value, end_value, years, metric_name)


def _get_empty_cagr_result(metric_type: str) -> Dict[str, Any]:
    """
    Get empty CAGR result for all windows.

    Parameters
    ----------
    metric_type : str
        Type of metric

    Returns
    -------
    Dict[str, Any]
        Dictionary with None values and INSUFFICIENT flags
    """
    results = {}
    for window in CAGR_WINDOWS:
        results[f"{metric_type}_cagr_{window}yr"] = {"value": None, "flag": "INSUFFICIENT"}
        results[f"{metric_type}_cagr_{window}yr_flag"] = "INSUFFICIENT"
    return results


# =============================================================================
# CAPITAL ALLOCATION CLASSIFIER
# =============================================================================

def classify_capital_allocation(
    fcf: Optional[float],
    cash_conversion: Optional[float],
    capex_intensity: Optional[float],
    ocf: Optional[float] = None
) -> str:
    """
    Classify company's capital allocation quality.

    Classification Logic:
    - EXCELLENT: Positive FCF, Cash Conversion >100%, CapEx Intensity <50%
    - GOOD: Positive FCF, Cash Conversion >80%
    - MODERATE: Positive FCF, Cash Conversion >50%
    - WEAK: Positive FCF, Cash Conversion <50%
    - DISTRESSED: Negative FCF, Negative OCF, or heavy debt signals

    Parameters
    ----------
    fcf : Optional[float]
        Free Cash Flow value
    cash_conversion : Optional[float]
        Cash Conversion percentage
    capex_intensity : Optional[float]
        CapEx Intensity percentage
    ocf : Optional[float]
        Operating Cash Flow value

    Returns
    -------
    str
        Capital allocation rating

    Examples
    --------
    >>> classify_capital_allocation(500, 120, 40, 1000)
    'EXCELLENT'
    
    >>> classify_capital_allocation(-100, 90, 60, 500)
    'DISTRESSED'
    """
    logger.debug("Classifying capital allocation")
    
    # Check for distressed signals
    if fcf is None or ocf is None:
        logger.warning("Capital allocation classification: Missing FCF or OCF data")
        return RATING_DISTRESSED
    
    # Negative FCF or negative OCF indicates distress
    if fcf < 0 or ocf < 0:
        logger.info(f"Capital allocation classification: DISTRESSED (FCF={fcf}, OCF={ocf})")
        return RATING_DISTRESSED
    
    # If cash_conversion is None, we can't fully classify
    if cash_conversion is None:
        logger.warning("Capital allocation classification: Missing cash conversion")
        return RATING_MODERATE
    
    # Excellent: Positive FCF, Cash Conversion >100%, CapEx Intensity <50%
    if cash_conversion > CASH_CONVERSION_EXCELLENT:
        if capex_intensity is not None and capex_intensity < CAPEX_INTENSITY_EXCELLENT:
            logger.info(f"Capital allocation classification: EXCELLENT (conversion={cash_conversion:.2f}%, capex_intensity={capex_intensity:.2f}%)")
            return RATING_EXCELLENT
        else:
            logger.info(f"Capital allocation classification: GOOD (conversion={cash_conversion:.2f}%)")
            return RATING_GOOD
    
    # Good: Positive FCF, Cash Conversion >80%
    if cash_conversion > CASH_CONVERSION_GOOD:
        logger.info(f"Capital allocation classification: GOOD (conversion={cash_conversion:.2f}%)")
        return RATING_GOOD
    
    # Moderate: Positive FCF, Cash Conversion >50%
    if cash_conversion > CASH_CONVERSION_AVERAGE:
        logger.info(f"Capital allocation classification: MODERATE (conversion={cash_conversion:.2f}%)")
        return RATING_MODERATE
    
    # Weak: Positive FCF, Cash Conversion <50%
    logger.info(f"Capital allocation classification: WEAK (conversion={cash_conversion:.2f}%)")
    return RATING_WEAK


# =============================================================================
# HIGH-LEVEL CALCULATION FUNCTIONS
# =============================================================================

def calculate_all_cashflow_kpis(
    cf_data: pd.DataFrame,
    pl_data: pd.DataFrame,
    bs_data: pd.DataFrame,
    company_id: Optional[str] = None,
    period: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculate all cash flow KPIs for a company.

    Parameters
    ----------
    cf_data : pd.DataFrame
        Cash Flow data
    pl_data : pd.DataFrame
        Profit & Loss data
    bs_data : pd.DataFrame
        Balance Sheet data
    company_id : str, optional
        Company identifier for logging
    period : str, optional
        Financial period for logging

    Returns
    -------
    Dict[str, Any]
        Dictionary containing all calculated cash flow KPIs
    """
    logger.info(f"Calculating all cash flow KPIs for company_id={company_id}, period={period}")
    
    results = {
        "company_id": company_id,
        "period": period
    }
    
    # Calculate basic KPIs
    fcf = calculate_free_cash_flow(cf_data)
    results["free_cash_flow"] = fcf
    
    fcf_margin = calculate_fcf_margin(cf_data, pl_data)
    results["fcf_margin"] = fcf_margin
    
    cash_conv_result = calculate_cash_conversion(cf_data, pl_data)
    results["cash_conversion"] = cash_conv_result["value"]
    results["cash_conversion_flag"] = cash_conv_result["flag"]
    
    capex_intensity = calculate_capex_intensity(cf_data)
    results["capex_intensity"] = capex_intensity
    
    cash_reinvestment = calculate_cash_reinvestment_ratio(cf_data)
    results["cash_reinvestment_ratio"] = cash_reinvestment
    
    cash_roa = calculate_cash_return_on_assets(cf_data, bs_data)
    results["cash_return_on_assets"] = cash_roa
    
    # Calculate OCF growth using CAGR engine
    ocf_growth = calculate_operating_cashflow_growth(cf_data, company_id, period)
    results.update(ocf_growth)
    
    # Classify capital allocation
    ocf = _get_operating_cash_flow(cf_data)
    rating = classify_capital_allocation(fcf, cash_conv_result["value"], capex_intensity, ocf)
    results["capital_allocation_rating"] = rating
    
    # Count calculated metrics
    calculated_count = len([v for k, v in results.items() 
                           if k not in ["company_id", "period", "capital_allocation_rating"] 
                           and v is not None])
    
    logger.info(f"Calculated {calculated_count} cash flow KPIs for {company_id}, period {period}")
    logger.info(f"Capital allocation rating: {rating}")
    
    return results


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_cashflow_descriptions() -> Dict[str, str]:
    """
    Get descriptions for all cash flow KPIs.

    Returns
    -------
    Dict[str, str]
        Dictionary mapping KPI names to their descriptions
    """
    return {
        "free_cash_flow": "Free Cash Flow - cash available after capital expenditures",
        "fcf_margin": "FCF Margin - FCF as percentage of sales",
        "cash_conversion": "Cash Conversion - efficiency of converting net profit to cash",
        "capex_intensity": "CapEx Intensity - CapEx as percentage of OCF",
        "cash_reinvestment_ratio": "Cash Reinvestment Ratio - proportion of OCF reinvested",
        "cash_return_on_assets": "Cash ROA - OCF as percentage of total assets",
        "ocf_cagr_3yr": "OCF CAGR over 3 years",
        "ocf_cagr_5yr": "OCF CAGR over 5 years",
        "ocf_cagr_10yr": "OCF CAGR over 10 years",
        "capital_allocation_rating": "Capital Allocation Rating - overall assessment",
    }


def get_cashflow_formulas() -> Dict[str, str]:
    """
    Get formulas for all cash flow KPIs.

    Returns
    -------
    Dict[str, str]
        Dictionary mapping KPI names to their formulas
    """
    return {
        "free_cash_flow": "FCF = Operating Cash Flow - Capital Expenditure",
        "fcf_margin": "FCF Margin = (FCF / Sales) × 100",
        "cash_conversion": "Cash Conversion = (Operating Cash Flow / Net Profit) × 100",
        "capex_intensity": "CapEx Intensity = (Capital Expenditure / Operating Cash Flow) × 100",
        "cash_reinvestment_ratio": "Cash Reinvestment Ratio = Capital Expenditure / Operating Cash Flow",
        "cash_return_on_assets": "Cash ROA = (Operating Cash Flow / Total Assets) × 100",
        "ocf_cagr": "OCF CAGR = ((Ending OCF / Beginning OCF)^(1/n) - 1) × 100",
    }


def get_capital_allocation_descriptions() -> Dict[str, str]:
    """
    Get descriptions for capital allocation ratings.

    Returns
    -------
    Dict[str, str]
        Dictionary mapping ratings to their descriptions
    """
    return {
        RATING_EXCELLENT: "Excellent - Positive FCF, Cash Conversion >100%, CapEx Intensity <50%",
        RATING_GOOD: "Good - Positive FCF, Cash Conversion >80%",
        RATING_MODERATE: "Moderate - Positive FCF, Cash Conversion >50%",
        RATING_WEAK: "Weak - Positive FCF, Cash Conversion <50%",
        RATING_DISTRESSED: "Distressed - Negative FCF or negative OCF",
    }


def generate_capital_allocation_csv(
    results: List[Dict[str, Any]],
    output_path: str
) -> None:
    """
    Generate capital allocation CSV file.

    Parameters
    ----------
    results : List[Dict[str, Any]]
        List of calculation results
    output_path : str
        Path to output CSV file

    Returns
    -------
    None
    """
    import csv
    from pathlib import Path
    
    logger.info(f"Generating capital allocation CSV: {output_path}")
    
    if not results:
        logger.warning("No results to write to CSV")
        return
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Define columns
    fieldnames = [
        "company_id",
        "company_name",
        "period",
        "free_cash_flow",
        "fcf_margin",
        "cash_conversion",
        "capex_intensity",
        "cash_return_on_assets",
        "cash_reinvestment_ratio",
        "operating_cashflow_growth",
        "capital_allocation_rating"
    ]
    
    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in results:
                row = {
                    "company_id": result.get("company_id", ""),
                    "company_name": result.get("company_name", ""),
                    "period": result.get("period", ""),
                    "free_cash_flow": result.get("free_cash_flow", ""),
                    "fcf_margin": result.get("fcf_margin", ""),
                    "cash_conversion": result.get("cash_conversion", ""),
                    "capex_intensity": result.get("capex_intensity", ""),
                    "cash_return_on_assets": result.get("cash_return_on_assets", ""),
                    "cash_reinvestment_ratio": result.get("cash_reinvestment_ratio", ""),
                    "operating_cashflow_growth": result.get("ocf_cagr_3yr", {}).get("value", "") if result.get("ocf_cagr_3yr") else "",
                    "capital_allocation_rating": result.get("capital_allocation_rating", "")
                }
                writer.writerow(row)
        
        logger.info(f"Successfully generated CSV with {len(results)} records")
    
    except Exception as e:
        logger.error(f"Failed to generate CSV: {str(e)}")