"""
cagr.py

CAGR (Compound Annual Growth Rate) Engine for the N100 Financial Intelligence Platform.

This module provides production-quality functions to calculate CAGR for Revenue, PAT, and EPS
over 3-year, 5-year, and 10-year periods with comprehensive edge case handling.

All functions are modular, reusable, well-documented, type-hinted, and fully logged.
"""

import logging
from typing import Optional, Dict, Any, List, Tuple
import pandas as pd
import numpy as np

from src.config.logging_config import get_logger

logger = get_logger(__name__)


# =============================================================================
# CONSTANTS
# =============================================================================

# CAGR calculation windows in years
CAGR_WINDOWS = [3, 5, 10]

# Financial metric column names
REVENUE_COLUMN = "sales"
PAT_COLUMN = "net_profit"
EPS_COLUMN = "eps"

# CAGR flag constants
FLAG_NORMAL = None
FLAG_DECLINE_TO_LOSS = "DECLINE_TO_LOSS"
FLAG_TURNAROUND = "TURNAROUND"
FLAG_BOTH_NEGATIVE = "BOTH_NEGATIVE"
FLAG_ZERO_BASE = "ZERO_BASE"
FLAG_INSUFFICIENT = "INSUFFICIENT"

# Valid flag values
VALID_FLAGS = [
    FLAG_NORMAL,
    FLAG_DECLINE_TO_LOSS,
    FLAG_TURNAROUND,
    FLAG_BOTH_NEGATIVE,
    FLAG_ZERO_BASE,
    FLAG_INSUFFICIENT
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


def _validate_dataframe(df: pd.DataFrame, required_columns: List[str]) -> bool:
    """
    Validate DataFrame has required columns and sufficient data.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to validate
    required_columns : List[str]
        List of required column names

    Returns
    -------
    bool
        True if valid, False otherwise
    """
    if df.empty:
        logger.warning("Data validation: Empty dataframe provided")
        return False
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        logger.warning(f"Data validation: Missing columns: {missing_columns}")
        return False
    
    return True


def _validate_time_series(df: pd.DataFrame, period_column: str = "period") -> Optional[List[str]]:
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


def _get_cagr_value(start_value: float, end_value: float, years: int) -> Tuple[Optional[float], str]:
    """
    Calculate CAGR value with edge case handling.

    Parameters
    ----------
    start_value : float
        Starting value
    end_value : float
        Ending value
    years : int
        Number of years

    Returns
    -------
    Tuple[Optional[float], str]
        Tuple of (CAGR percentage, flag) or (None, flag) if calculation not possible
    """
    # Validate inputs
    if not _validate_numeric(start_value, "start_value"):
        return None, FLAG_INSUFFICIENT
    
    if not _validate_numeric(end_value, "end_value"):
        return None, FLAG_INSUFFICIENT
    
    if years <= 0:
        logger.warning(f"CAGR calculation: Invalid years={years}")
        return None, FLAG_INSUFFICIENT
    
    # Edge case: Zero base
    if start_value == 0:
        logger.warning(f"CAGR calculation: Zero base value (start_value=0)")
        return None, FLAG_ZERO_BASE
    
    # Edge case: Positive to Negative
    if start_value > 0 and end_value < 0:
        logger.warning(
            f"CAGR calculation: Decline to loss detected "
            f"(start={start_value:.2f}, end={end_value:.2f})"
        )
        return None, FLAG_DECLINE_TO_LOSS
    
    # Edge case: Negative to Positive
    if start_value < 0 and end_value > 0:
        logger.info(
            f"CAGR calculation: Turnaround detected "
            f"(start={start_value:.2f}, end={end_value:.2f})"
        )
        return None, FLAG_TURNAROUND
    
    # Edge case: Both Negative
    if start_value < 0 and end_value < 0:
        logger.warning(
            f"CAGR calculation: Both values negative "
            f"(start={start_value:.2f}, end={end_value:.2f})"
        )
        return None, FLAG_BOTH_NEGATIVE
    
    # Normal calculation: Positive to Positive
    try:
        cagr = ((end_value / start_value) ** (1 / years)) - 1
        cagr_pct = cagr * 100
        
        # Validate result
        if np.isinf(cagr_pct) or np.isnan(cagr_pct):
            logger.error(f"CAGR calculation: Invalid result (cagr={cagr_pct})")
            return None, FLAG_INSUFFICIENT
        
        logger.debug(f"CAGR calculated: {cagr_pct:.2f}% over {years} years")
        return round(cagr_pct, 2), FLAG_NORMAL
    
    except Exception as e:
        logger.error(f"CAGR calculation failed: {str(e)}")
        return None, FLAG_INSUFFICIENT


# =============================================================================
# CORE CAGR CALCULATION FUNCTIONS
# =============================================================================

def calculate_cagr(
    start_value: float,
    end_value: float,
    years: int,
    metric_name: str = "value"
) -> Dict[str, Any]:
    """
    Calculate CAGR (Compound Annual Growth Rate) for any financial metric.

    Formula: CAGR = ((End Value / Start Value)^(1 / Years) - 1) × 100

    Parameters
    ----------
    start_value : float
        Starting value (beginning of period)
    end_value : float
        Ending value (end of period)
    years : int
        Number of years between start and end
    metric_name : str, optional
        Name of the metric for logging, by default "value"

    Returns
    -------
    Dict[str, Any]
        Dictionary containing:
        - "value": CAGR percentage (float) or None if calculation not possible
        - "flag": Status flag (None or one of the flag constants)

    Examples
    --------
    >>> calculate_cagr(100, 200, 5)
    {"value": 14.87, "flag": None}

    >>> calculate_cagr(100, -50, 5)
    {"value": None, "flag": "DECLINE_TO_LOSS"}
    """
    logger.debug(
        f"Calculating CAGR for {metric_name}: "
        f"start={start_value}, end={end_value}, years={years}"
    )
    
    # Validate inputs
    if not _validate_numeric(start_value, f"{metric_name}_start"):
        return {"value": None, "flag": FLAG_INSUFFICIENT}
    
    if not _validate_numeric(end_value, f"{metric_name}_end"):
        return {"value": None, "flag": FLAG_INSUFFICIENT}
    
    if years <= 0:
        logger.warning(f"CAGR calculation: Invalid years={years} for {metric_name}")
        return {"value": None, "flag": FLAG_INSUFFICIENT}
    
    # Calculate CAGR
    cagr_value, flag = _get_cagr_value(start_value, end_value, years)
    
    result = {
        "value": cagr_value,
        "flag": flag
    }
    
    logger.debug(f"CAGR result for {metric_name}: {result}")
    return result


def calculate_revenue_cagr(
    pl_data: pd.DataFrame,
    company_id: Optional[str] = None,
    period: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculate Revenue CAGR for specified time windows.

    Parameters
    ----------
    pl_data : pd.DataFrame
        Profit & Loss data with 'sales' and 'period' columns
    company_id : str, optional
        Company identifier for logging
    period : str, optional
        Financial period for logging

    Returns
    -------
    Dict[str, Any]
        Dictionary containing CAGR values and flags for 3, 5, and 10 year windows
        Format: {
            "revenue_cagr_3yr": {"value": float, "flag": str},
            "revenue_cagr_3yr_flag": str,
            ...
        }
    """
    logger.info(f"Calculating Revenue CAGR for company_id={company_id}, period={period}")
    
    # Validate input
    if not _validate_dataframe(pl_data, [REVENUE_COLUMN, "period"]):
        return _get_empty_cagr_result("revenue")
    
    # Validate time series
    valid_periods = _validate_time_series(pl_data)
    if valid_periods is None:
        return _get_empty_cagr_result("revenue")
    
    # Calculate CAGR for each window
    results = {}
    sales_data = pl_data[["period", REVENUE_COLUMN]].dropna().sort_values("period")
    
    for window in CAGR_WINDOWS:
        cagr_result = _calculate_cagr_for_window(
            sales_data,
            REVENUE_COLUMN,
            window,
            f"revenue_{window}yr",
            company_id,
            period
        )
        
        results[f"revenue_cagr_{window}yr"] = cagr_result
        results[f"revenue_cagr_{window}yr_flag"] = cagr_result["flag"]
    
    return results


def calculate_pat_cagr(
    pl_data: pd.DataFrame,
    company_id: Optional[str] = None,
    period: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculate PAT (Profit After Tax) CAGR for specified time windows.

    Parameters
    ----------
    pl_data : pd.DataFrame
        Profit & Loss data with 'net_profit' and 'period' columns
    company_id : str, optional
        Company identifier for logging
    period : str, optional
        Financial period for logging

    Returns
    -------
    Dict[str, Any]
        Dictionary containing CAGR values and flags for 3, 5, and 10 year windows
    """
    logger.info(f"Calculating PAT CAGR for company_id={company_id}, period={period}")
    
    # Validate input
    if not _validate_dataframe(pl_data, [PAT_COLUMN, "period"]):
        return _get_empty_cagr_result("pat")
    
    # Validate time series
    valid_periods = _validate_time_series(pl_data)
    if valid_periods is None:
        return _get_empty_cagr_result("pat")
    
    # Calculate CAGR for each window
    results = {}
    pat_data = pl_data[["period", PAT_COLUMN]].dropna().sort_values("period")
    
    for window in CAGR_WINDOWS:
        cagr_result = _calculate_cagr_for_window(
            pat_data,
            PAT_COLUMN,
            window,
            f"pat_{window}yr",
            company_id,
            period
        )
        
        results[f"pat_cagr_{window}yr"] = cagr_result
        results[f"pat_cagr_{window}yr_flag"] = cagr_result["flag"]
    
    return results


def calculate_eps_cagr(
    pl_data: pd.DataFrame,
    company_id: Optional[str] = None,
    period: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculate EPS (Earnings Per Share) CAGR for specified time windows.

    Parameters
    ----------
    pl_data : pd.DataFrame
        Profit & Loss data with 'eps' and 'period' columns
    company_id : str, optional
        Company identifier for logging
    period : str, optional
        Financial period for logging

    Returns
    -------
    Dict[str, Any]
        Dictionary containing CAGR values and flags for 3, 5, and 10 year windows
    """
    logger.info(f"Calculating EPS CAGR for company_id={company_id}, period={period}")
    
    # Validate input
    if not _validate_dataframe(pl_data, [EPS_COLUMN, "period"]):
        return _get_empty_cagr_result("eps")
    
    # Validate time series
    valid_periods = _validate_time_series(pl_data)
    if valid_periods is None:
        return _get_empty_cagr_result("eps")
    
    # Calculate CAGR for each window
    results = {}
    eps_data = pl_data[["period", EPS_COLUMN]].dropna().sort_values("period")
    
    for window in CAGR_WINDOWS:
        cagr_result = _calculate_cagr_for_window(
            eps_data,
            EPS_COLUMN,
            window,
            f"eps_{window}yr",
            company_id,
            period
        )
        
        results[f"eps_cagr_{window}yr"] = cagr_result
        results[f"eps_cagr_{window}yr_flag"] = cagr_result["flag"]
    
    return results


def calculate_all_cagr(
    pl_data: pd.DataFrame,
    company_id: Optional[str] = None,
    period: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculate all CAGR metrics (Revenue, PAT, EPS) for all time windows.

    Parameters
    ----------
    pl_data : pd.DataFrame
        Profit & Loss data with required columns
    company_id : str, optional
        Company identifier for logging
    period : str, optional
        Financial period for logging

    Returns
    -------
    Dict[str, Any]
        Dictionary containing all CAGR calculations
    """
    logger.info(f"Calculating all CAGR metrics for company_id={company_id}, period={period}")
    
    results = {
        "company_id": company_id,
        "period": period
    }
    
    # Calculate Revenue CAGR
    revenue_results = calculate_revenue_cagr(pl_data, company_id, period)
    results.update(revenue_results)
    
    # Calculate PAT CAGR
    pat_results = calculate_pat_cagr(pl_data, company_id, period)
    results.update(pat_results)
    
    # Calculate EPS CAGR
    eps_results = calculate_eps_cagr(pl_data, company_id, period)
    results.update(eps_results)
    
    # Count calculated metrics
    calculated_count = len([v for k, v in results.items() 
                           if k not in ["company_id", "period"] and v is not None])
    
    logger.info(f"Calculated {calculated_count} CAGR metrics for {company_id}, period {period}")
    
    return results


# =============================================================================
# INTERNAL HELPER FUNCTIONS
# =============================================================================

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
        Time series data with period and value columns
    column : str
        Column name containing the values
    window_years : int
        Number of years for the window
    metric_name : str
        Name of the metric for logging
    company_id : Optional[str]
        Company identifier for logging
    period : Optional[str]
        Financial period for logging

    Returns
    -------
    Dict[str, Any]
        Dictionary with "value" and "flag" keys
    """
    # Check if we have enough data points
    if len(data) < 2:
        logger.warning(
            f"CAGR calculation: Insufficient data points for {metric_name} "
            f"(have {len(data)}, need at least 2)"
        )
        return {"value": None, "flag": FLAG_INSUFFICIENT}
    
    # Get start and end values
    start_value = data[column].iloc[0]
    end_value = data[column].iloc[-1]
    
    # Calculate actual years between periods
    try:
        start_period = data["period"].iloc[0]
        end_period = data["period"].iloc[-1]
        
        # Extract years from period strings (assumes format like "FY2020" or "2020")
        start_year = int(str(start_period).replace("FY", "").strip())
        end_year = int(str(end_period).replace("FY", "").strip())
        actual_years = end_year - start_year
        
        if actual_years <= 0:
            logger.warning(
                f"CAGR calculation: Invalid year range for {metric_name} "
                f"(start={start_period}, end={end_period})"
            )
            return {"value": None, "flag": FLAG_INSUFFICIENT}
        
        # Use actual years, but cap at window size
        years = min(actual_years, window_years)
        
    except (ValueError, IndexError) as e:
        logger.warning(
            f"CAGR calculation: Could not parse periods for {metric_name}: {str(e)}"
        )
        # Fallback to window size
        years = window_years
    
    # Calculate CAGR
    return calculate_cagr(start_value, end_value, years, metric_name)


def _get_empty_cagr_result(metric_type: str) -> Dict[str, Any]:
    """
    Get empty CAGR result for all windows.

    Parameters
    ----------
    metric_type : str
        Type of metric ("revenue", "pat", or "eps")

    Returns
    -------
    Dict[str, Any]
        Dictionary with None values and INSUFFICIENT flags for all windows
    """
    results = {}
    for window in CAGR_WINDOWS:
        results[f"{metric_type}_cagr_{window}yr"] = {"value": None, "flag": FLAG_INSUFFICIENT}
        results[f"{metric_type}_cagr_{window}yr_flag"] = FLAG_INSUFFICIENT
    return results


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_cagr_descriptions() -> Dict[str, str]:
    """
    Get descriptions for all CAGR metrics.

    Returns
    -------
    Dict[str, str]
        Dictionary mapping metric names to their descriptions
    """
    return {
        "revenue_cagr_3yr": "Revenue CAGR over 3 years",
        "revenue_cagr_5yr": "Revenue CAGR over 5 years",
        "revenue_cagr_10yr": "Revenue CAGR over 10 years",
        "pat_cagr_3yr": "PAT CAGR over 3 years",
        "pat_cagr_5yr": "PAT CAGR over 5 years",
        "pat_cagr_10yr": "PAT CAGR over 10 years",
        "eps_cagr_3yr": "EPS CAGR over 3 years",
        "eps_cagr_5yr": "EPS CAGR over 5 years",
        "eps_cagr_10yr": "EPS CAGR over 10 years",
    }


def get_cagr_formulas() -> Dict[str, str]:
    """
    Get formulas for all CAGR metrics.

    Returns
    -------
    Dict[str, str]
        Dictionary mapping metric names to their formulas
    """
    return {
        "revenue_cagr": "Revenue CAGR = ((Ending Revenue / Beginning Revenue)^(1/n) - 1) × 100",
        "pat_cagr": "PAT CAGR = ((Ending PAT / Beginning PAT)^(1/n) - 1) × 100",
        "eps_cagr": "EPS CAGR = ((Ending EPS / Beginning EPS)^(1/n) - 1) × 100",
    }


def get_cagr_flag_descriptions() -> Dict[str, str]:
    """
    Get descriptions for all CAGR flags.

    Returns
    -------
    Dict[str, str]
        Dictionary mapping flag names to their descriptions
    """
    return {
        FLAG_NORMAL: "Normal CAGR calculated successfully",
        FLAG_DECLINE_TO_LOSS: "Company went from profit to loss during the period",
        FLAG_TURNAROUND: "Company went from loss to profit during the period",
        FLAG_BOTH_NEGATIVE: "Both start and end values are negative",
        FLAG_ZERO_BASE: "Starting value is zero, cannot calculate growth",
        FLAG_INSUFFICIENT: "Insufficient data or invalid inputs for calculation",
    }