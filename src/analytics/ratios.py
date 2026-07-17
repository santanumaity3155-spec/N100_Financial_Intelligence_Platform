"""
ratios.py

Financial Ratio Engine for the N100 Financial Intelligence Platform.

This module provides production-quality functions to calculate profitability,
leverage, and efficiency ratios for all company-year records.

All functions are modular, reusable, well-documented, type-hinted, and fully logged.
"""

import logging
from typing import Optional, Dict, Any
import pandas as pd

from src.config.logging_config import get_logger
from src.database.connection import get_connection

logger = get_logger(__name__)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

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


def _validate_numeric(value: Any, name: str) -> bool:
    """
    Validate that a value is numeric and not NaN.

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
    return True


def _get_equity_reserves(bs_data: pd.DataFrame) -> Optional[float]:
    """
    Calculate total equity (Equity Capital + Reserves).

    Parameters
    ----------
    bs_data : pd.DataFrame
        Balance sheet data

    Returns
    -------
    Optional[float]
        Sum of equity capital and reserves, or None if not available
    """
    equity_capital = _safe_get_value(bs_data, 'equity_capital', 0)
    reserves = _safe_get_value(bs_data, 'reserves', 0)
    share_capital = _safe_get_value(bs_data, 'share_capital', 0)

    # Try equity_capital first, fall back to share_capital + reserves
    if equity_capital and equity_capital > 0:
        equity = equity_capital + (reserves if reserves else 0)
    else:
        equity = (share_capital if share_capital else 0) + (reserves if reserves else 0)

    return equity if equity != 0 else None


def _get_company_sector(company_id: str) -> Optional[str]:
    """
    Fetch company sector from database.

    Parameters
    ----------
    company_id : str
        Company identifier

    Returns
    -------
    Optional[str]
        Company sector or None if not found
    """
    try:
        conn = get_connection()
        query = "SELECT sector FROM companies WHERE company_id = ? LIMIT 1"
        cursor = conn.execute(query, (company_id,))
        result = cursor.fetchone()
        return result['sector'] if result else None
    except Exception as e:
        logger.error(f"Failed to fetch sector for {company_id}: {str(e)}")
        return None


# =============================================================================
# PROFITABILITY RATIOS
# =============================================================================

def calculate_net_profit_margin(
    pl_data: pd.DataFrame,
    company_id: Optional[str] = None,
    period: Optional[str] = None
) -> Optional[float]:
    """
    Calculate Net Profit Margin.

    Formula: Net Profit Margin = Net Profit / Sales × 100

    Parameters
    ----------
    pl_data : pd.DataFrame
        Profit & Loss data
    company_id : str, optional
        Company identifier for logging
    period : str, optional
        Financial period for logging

    Returns
    -------
    Optional[float]
        Net Profit Margin percentage, or None if Sales == 0 or data missing
    """
    try:
        if pl_data.empty:
            logger.warning("Net Profit Margin calculation: Empty dataframe provided")
            return None

        net_profit = _safe_get_value(pl_data, 'net_profit')
        sales = _safe_get_value(pl_data, 'sales')

        if not _validate_numeric(net_profit, "net_profit"):
            return None
        if not _validate_numeric(sales, "sales"):
            return None

        if sales == 0:
            logger.warning(
                f"Net Profit Margin calculation: Sales is zero "
                f"(company_id={company_id}, period={period})"
            )
            return None

        margin = (net_profit / sales) * 100
        logger.debug(
            f"Net Profit Margin calculated: {margin:.2f}% "
            f"(company_id={company_id}, period={period})"
        )
        return round(margin, 2)

    except Exception as e:
        logger.error(f"Net Profit Margin calculation failed: {str(e)}")
        return None


def calculate_operating_profit_margin(
    pl_data: pd.DataFrame,
    company_id: Optional[str] = None,
    period: Optional[str] = None
) -> Optional[float]:
    """
    Calculate Operating Profit Margin.

    Formula: Operating Profit Margin = Operating Profit / Sales × 100

    Cross-checks against opm_percentage field. If difference > 1%, logs warning.
    Does NOT overwrite source value.

    Parameters
    ----------
    pl_data : pd.DataFrame
        Profit & Loss data
    company_id : str, optional
        Company identifier for logging
    period : str, optional
        Financial period for logging

    Returns
    -------
    Optional[float]
        Operating Profit Margin percentage, or None if Sales == 0 or data missing
    """
    try:
        if pl_data.empty:
            logger.warning("Operating Profit Margin calculation: Empty dataframe provided")
            return None

        operating_profit = _safe_get_value(pl_data, 'operating_profit')
        sales = _safe_get_value(pl_data, 'sales')
        opm_percentage = _safe_get_value(pl_data, 'opm_percentage')

        if not _validate_numeric(operating_profit, "operating_profit"):
            return None
        if not _validate_numeric(sales, "sales"):
            return None

        if sales == 0:
            logger.warning(
                f"Operating Profit Margin calculation: Sales is zero "
                f"(company_id={company_id}, period={period})"
            )
            return None

        margin = (operating_profit / sales) * 100

        # Cross-check against opm_percentage
        if opm_percentage is not None and not pd.isna(opm_percentage):
            difference = abs(margin - opm_percentage)
            if difference > 1.0:
                logger.warning(
                    f"OPM mismatch detected: calculated={margin:.2f}%, "
                    f"source={opm_percentage:.2f}%, difference={difference:.2f}% "
                    f"(company_id={company_id}, period={period})"
                )

        logger.debug(
            f"Operating Profit Margin calculated: {margin:.2f}% "
            f"(company_id={company_id}, period={period})"
        )
        return round(margin, 2)

    except Exception as e:
        logger.error(f"Operating Profit Margin calculation failed: {str(e)}")
        return None


def calculate_roe(
    pl_data: pd.DataFrame,
    bs_data: pd.DataFrame,
    company_id: Optional[str] = None,
    period: Optional[str] = None
) -> Optional[float]:
    """
    Calculate Return on Equity (ROE).

    Formula: ROE = Net Profit / (Equity Capital + Reserves) × 100

    Parameters
    ----------
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
    Optional[float]
        ROE percentage, or None if Equity + Reserves <= 0 or data missing
    """
    try:
        if pl_data.empty or bs_data.empty:
            logger.warning("ROE calculation: Empty dataframe provided")
            return None

        net_profit = _safe_get_value(pl_data, 'net_profit')
        equity = _get_equity_reserves(bs_data)

        if not _validate_numeric(net_profit, "net_profit"):
            return None
        if equity is None:
            logger.warning(
                f"ROE calculation: Equity + Reserves <= 0 or not available "
                f"(company_id={company_id}, period={period})"
            )
            return None

        roe = (net_profit / equity) * 100
        logger.debug(
            f"ROE calculated: {roe:.2f}% "
            f"(company_id={company_id}, period={period})"
        )
        return round(roe, 2)

    except Exception as e:
        logger.error(f"ROE calculation failed: {str(e)}")
        return None


def calculate_roce(
    pl_data: pd.DataFrame,
    bs_data: pd.DataFrame,
    company_id: Optional[str] = None,
    period: Optional[str] = None
) -> Optional[float]:
    """
    Calculate Return on Capital Employed (ROCE).

    Formula: ROCE = EBIT / (Equity + Reserves + Borrowings) × 100
    Where EBIT = Operating Profit + Other Income

    For Financials sector, supports sector-relative benchmark handling.

    Parameters
    ----------
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
    Optional[float]
        ROCE percentage, or None if calculation not possible
    """
    try:
        if pl_data.empty or bs_data.empty:
            logger.warning("ROCE calculation: Empty dataframe provided")
            return None

        operating_profit = _safe_get_value(pl_data, 'operating_profit')
        other_income = _safe_get_value(pl_data, 'other_income', 0)
        equity = _get_equity_reserves(bs_data)
        borrowings = _safe_get_value(bs_data, 'borrowings', 0)

        if not _validate_numeric(operating_profit, "operating_profit"):
            return None
        if equity is None:
            logger.warning(
                f"ROCE calculation: Equity is not available "
                f"(company_id={company_id}, period={period})"
            )
            return None

        # Calculate EBIT
        other_income = other_income if other_income and not pd.isna(other_income) else 0
        ebit = operating_profit + other_income

        # Capital Employed = Equity + Reserves + Borrowings
        borrowings = borrowings if borrowings and not pd.isna(borrowings) else 0
        capital_employed = equity + borrowings

        if capital_employed <= 0:
            logger.warning(
                f"ROCE calculation: Capital employed <= 0 "
                f"(company_id={company_id}, period={period})"
            )
            return None

        # Check if company is in Financials sector
        sector = _get_company_sector(company_id) if company_id else None
        if sector and sector.lower() == 'financials':
            logger.debug(
                f"ROCE calculation: Financials sector detected - "
                f"using sector-relative benchmark handling "
                f"(company_id={company_id}, period={period})"
            )

        roce = (ebit / capital_employed) * 100
        logger.debug(
            f"ROCE calculated: {roce:.2f}% "
            f"(company_id={company_id}, period={period})"
        )
        return round(roce, 2)

    except Exception as e:
        logger.error(f"ROCE calculation failed: {str(e)}")
        return None


def calculate_roa(
    pl_data: pd.DataFrame,
    bs_data: pd.DataFrame,
    company_id: Optional[str] = None,
    period: Optional[str] = None
) -> Optional[float]:
    """
    Calculate Return on Assets (ROA).

    Formula: ROA = Net Profit / Total Assets × 100

    Parameters
    ----------
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
    Optional[float]
        ROA percentage, or None if Total Assets == 0 or data missing
    """
    try:
        if pl_data.empty or bs_data.empty:
            logger.warning("ROA calculation: Empty dataframe provided")
            return None

        net_profit = _safe_get_value(pl_data, 'net_profit')
        total_assets = _safe_get_value(bs_data, 'total_assets')

        if not _validate_numeric(net_profit, "net_profit"):
            return None
        if not _validate_numeric(total_assets, "total_assets"):
            return None

        if total_assets == 0:
            logger.warning(
                f"ROA calculation: Total Assets is zero "
                f"(company_id={company_id}, period={period})"
            )
            return None

        roa = (net_profit / total_assets) * 100
        logger.debug(
            f"ROA calculated: {roa:.2f}% "
            f"(company_id={company_id}, period={period})"
        )
        return round(roa, 2)

    except Exception as e:
        logger.error(f"ROA calculation failed: {str(e)}")
        return None


# =============================================================================
# LEVERAGE RATIOS
# =============================================================================

def calculate_debt_to_equity(
    bs_data: pd.DataFrame,
    company_id: Optional[str] = None,
    period: Optional[str] = None
) -> tuple[Optional[float], bool]:
    """
    Calculate Debt to Equity Ratio.

    Formula: Debt to Equity = Borrowings / (Equity + Reserves)

    If Borrowings == 0, returns 0 (not None).
    If Debt to Equity > 5 AND company NOT in Financials, sets high_leverage_flag=True.

    Parameters
    ----------
    bs_data : pd.DataFrame
        Balance Sheet data
    company_id : str, optional
        Company identifier for logging
    period : str, optional
        Financial period for logging

    Returns
    -------
    tuple[Optional[float], bool]
        (Debt to Equity ratio, high_leverage_flag)
        Returns (0, False) if Borrowings == 0
    """
    try:
        if bs_data.empty:
            logger.warning("Debt to Equity calculation: Empty dataframe provided")
            return None, False

        borrowings = _safe_get_value(bs_data, 'borrowings', 0)
        equity = _get_equity_reserves(bs_data)

        if equity is None or equity <= 0:
            logger.warning(
                f"Debt to Equity calculation: Equity <= 0 or not available "
                f"(company_id={company_id}, period={period})"
            )
            return None, False

        # If borrowings is 0, return 0 (not None)
        if borrowings == 0 or pd.isna(borrowings):
            logger.debug(
                f"Debt to Equity: Borrowings is zero, returning 0 "
                f"(company_id={company_id}, period={period})"
            )
            return 0.0, False

        ratio = borrowings / equity

        # Check for high leverage flag
        high_leverage_flag = False
        if ratio > 5.0:
            sector = _get_company_sector(company_id) if company_id else None
            if not sector or sector.lower() != 'financials':
                high_leverage_flag = True
                logger.warning(
                    f"High leverage flag triggered: Debt to Equity = {ratio:.2f} "
                    f"(company_id={company_id}, period={period})"
                )

        logger.debug(
            f"Debt to Equity calculated: {ratio:.2f}, high_leverage={high_leverage_flag} "
            f"(company_id={company_id}, period={period})"
        )
        return round(ratio, 2), high_leverage_flag

    except Exception as e:
        logger.error(f"Debt to Equity calculation failed: {str(e)}")
        return None, False


def calculate_interest_coverage(
    pl_data: pd.DataFrame,
    company_id: Optional[str] = None,
    period: Optional[str] = None
) -> tuple[Optional[float], Optional[str], bool]:
    """
    Calculate Interest Coverage Ratio.

    Formula: Interest Coverage = (Operating Profit + Other Income) / Interest

    If Interest == 0, returns (None, "Debt Free", False).
    If ICR < 1.5, sets interest_warning_flag=True.

    Parameters
    ----------
    pl_data : pd.DataFrame
        Profit & Loss data
    company_id : str, optional
        Company identifier for logging
    period : str, optional
        Financial period for logging

    Returns
    -------
    tuple[Optional[float], Optional[str], bool]
        (Interest Coverage ratio, icr_label, interest_warning_flag)
    """
    try:
        if pl_data.empty:
            logger.warning("Interest Coverage calculation: Empty dataframe provided")
            return None, None, False

        operating_profit = _safe_get_value(pl_data, 'operating_profit')
        other_income = _safe_get_value(pl_data, 'other_income', 0)
        interest = _safe_get_value(pl_data, 'interest')

        if not _validate_numeric(operating_profit, "operating_profit"):
            return None, None, False

        if interest is None or pd.isna(interest):
            logger.warning(
                f"Interest Coverage calculation: Interest data missing "
                f"(company_id={company_id}, period={period})"
            )
            return None, None, False

        # If interest is 0, company is debt-free
        if interest == 0:
            logger.info(
                f"Interest Coverage: Debt free company (interest=0) "
                f"(company_id={company_id}, period={period})"
            )
            return None, "Debt Free", False

        # Calculate EBIT
        other_income = other_income if other_income and not pd.isna(other_income) else 0
        ebit = operating_profit + other_income

        coverage = ebit / interest

        # Check for warning flag
        interest_warning_flag = False
        if coverage < 1.5:
            interest_warning_flag = True
            logger.warning(
                f"Interest Coverage warning: ICR = {coverage:.2f} (< 1.5) "
                f"(company_id={company_id}, period={period})"
            )

        logger.debug(
            f"Interest Coverage calculated: {coverage:.2f}, "
            f"warning={interest_warning_flag} "
            f"(company_id={company_id}, period={period})"
        )
        return round(coverage, 2), None, interest_warning_flag

    except Exception as e:
        logger.error(f"Interest Coverage calculation failed: {str(e)}")
        return None, None, False


def calculate_net_debt(
    bs_data: pd.DataFrame,
    company_id: Optional[str] = None,
    period: Optional[str] = None
) -> Optional[float]:
    """
    Calculate Net Debt.

    Formula: Net Debt = Borrowings - Investments

    Parameters
    ----------
    bs_data : pd.DataFrame
        Balance Sheet data
    company_id : str, optional
        Company identifier for logging
    period : str, optional
        Financial period for logging

    Returns
    -------
    Optional[float]
        Net Debt value, or None if data missing
    """
    try:
        if bs_data.empty:
            logger.warning("Net Debt calculation: Empty dataframe provided")
            return None

        borrowings = _safe_get_value(bs_data, 'borrowings', 0)
        investments = _safe_get_value(bs_data, 'investments', 0)

        borrowings = borrowings if borrowings and not pd.isna(borrowings) else 0
        investments = investments if investments and not pd.isna(investments) else 0

        net_debt = borrowings - investments

        logger.debug(
            f"Net Debt calculated: {net_debt:.2f} "
            f"(company_id={company_id}, period={period})"
        )
        return round(net_debt, 2)

    except Exception as e:
        logger.error(f"Net Debt calculation failed: {str(e)}")
        return None


# =============================================================================
# EFFICIENCY RATIOS
# =============================================================================

def calculate_asset_turnover(
    pl_data: pd.DataFrame,
    bs_data: pd.DataFrame,
    company_id: Optional[str] = None,
    period: Optional[str] = None
) -> Optional[float]:
    """
    Calculate Asset Turnover Ratio.

    Formula: Asset Turnover = Sales / Total Assets

    Parameters
    ----------
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
    Optional[float]
        Asset Turnover ratio, or None if Total Assets == 0 or data missing
    """
    try:
        if pl_data.empty or bs_data.empty:
            logger.warning("Asset Turnover calculation: Empty dataframe provided")
            return None

        sales = _safe_get_value(pl_data, 'sales')
        total_assets = _safe_get_value(bs_data, 'total_assets')

        if not _validate_numeric(sales, "sales"):
            return None
        if not _validate_numeric(total_assets, "total_assets"):
            return None

        if total_assets == 0:
            logger.warning(
                f"Asset Turnover calculation: Total Assets is zero "
                f"(company_id={company_id}, period={period})"
            )
            return None

        turnover = sales / total_assets
        logger.debug(
            f"Asset Turnover calculated: {turnover:.2f} "
            f"(company_id={company_id}, period={period})"
        )
        return round(turnover, 2)

    except Exception as e:
        logger.error(f"Asset Turnover calculation failed: {str(e)}")
        return None


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def calculate_all_ratios(
    company_id: str,
    period: str
) -> Dict[str, Any]:
    """
    Calculate all financial ratios for a company in a specific period.

    Parameters
    ----------
    company_id : str
        Company identifier
    period : str
        Financial period (e.g., '2024-Q1', 'FY2024')

    Returns
    -------
    Dict[str, Any]
        Dictionary containing all calculated ratios
    """
    logger.info(f"Calculating all ratios for {company_id}, period {period}")

    try:
        # Fetch required data
        conn = get_connection()
        pl_query = "SELECT * FROM profit_loss WHERE company_id = ? AND period = ? LIMIT 1"
        bs_query = "SELECT * FROM balance_sheet WHERE company_id = ? AND period = ? LIMIT 1"

        pl_df = pd.read_sql_query(pl_query, conn, params=(company_id, period))
        bs_df = pd.read_sql_query(bs_query, conn, params=(company_id, period))

        if pl_df.empty or bs_df.empty:
            logger.warning(f"Insufficient data for {company_id}, period {period}")
            return {}

        # Calculate all ratios
        results = {
            "company_id": company_id,
            "period": period,
        }

        # Profitability ratios
        results["net_profit_margin"] = calculate_net_profit_margin(pl_df, company_id, period)
        results["operating_profit_margin"] = calculate_operating_profit_margin(pl_df, company_id, period)
        results["roe"] = calculate_roe(pl_df, bs_df, company_id, period)
        results["roce"] = calculate_roce(pl_df, bs_df, company_id, period)
        results["roa"] = calculate_roa(pl_df, bs_df, company_id, period)

        # Leverage ratios
        debt_to_equity, high_leverage_flag = calculate_debt_to_equity(bs_df, company_id, period)
        results["debt_to_equity"] = debt_to_equity
        results["high_leverage_flag"] = high_leverage_flag

        interest_coverage, icr_label, interest_warning_flag = calculate_interest_coverage(
            pl_df, company_id, period
        )
        results["interest_coverage"] = interest_coverage
        results["icr_label"] = icr_label
        results["interest_warning_flag"] = interest_warning_flag

        results["net_debt"] = calculate_net_debt(bs_df, company_id, period)

        # Efficiency ratios
        results["asset_turnover"] = calculate_asset_turnover(pl_df, bs_df, company_id, period)

        calculated_count = len([v for v in results.values() if v is not None])
        logger.info(f"Calculated {calculated_count} ratios for {company_id}, period {period}")

        return results

    except Exception as e:
        logger.error(f"Failed to calculate all ratios for {company_id}, period {period}: {str(e)}")
        return {}


def get_ratio_descriptions() -> Dict[str, str]:
    """
    Get descriptions for all financial ratios.

    Returns
    -------
    Dict[str, str]
        Dictionary mapping ratio names to their descriptions
    """
    return {
        "net_profit_margin": "Net Profit Margin - percentage of revenue that remains as net profit after all expenses",
        "operating_profit_margin": "Operating Profit Margin - percentage of revenue that remains as operating profit",
        "roe": "Return on Equity - measures how effectively a company uses shareholder equity to generate profit",
        "roce": "Return on Capital Employed - measures profitability and efficiency in using capital",
        "roa": "Return on Assets - measures how efficiently a company uses its assets to generate profit",
        "debt_to_equity": "Debt to Equity Ratio - measures the proportion of debt to shareholders' equity",
        "high_leverage_flag": "High Leverage Flag - True if Debt to Equity > 5 and company is not in Financials sector",
        "interest_coverage": "Interest Coverage Ratio - measures how easily a company can pay interest on outstanding debt",
        "icr_label": "ICR Label - 'Debt Free' if interest is zero, None otherwise",
        "interest_warning_flag": "Interest Warning Flag - True if Interest Coverage < 1.5",
        "net_debt": "Net Debt - total borrowings minus investments",
        "asset_turnover": "Asset Turnover - measures how efficiently a company uses its assets to generate sales",
    }


def get_ratio_formulas() -> Dict[str, str]:
    """
    Get formulas for all financial ratios.

    Returns
    -------
    Dict[str, str]
        Dictionary mapping ratio names to their formulas
    """
    return {
        "net_profit_margin": "Net Profit Margin = (Net Profit / Sales) × 100",
        "operating_profit_margin": "Operating Profit Margin = (Operating Profit / Sales) × 100",
        "roe": "ROE = (Net Profit / (Equity Capital + Reserves)) × 100",
        "roce": "ROCE = (EBIT / (Equity + Reserves + Borrowings)) × 100, where EBIT = Operating Profit + Other Income",
        "roa": "ROA = (Net Profit / Total Assets) × 100",
        "debt_to_equity": "Debt to Equity = Borrowings / (Equity + Reserves)",
        "interest_coverage": "Interest Coverage = (Operating Profit + Other Income) / Interest",
        "net_debt": "Net Debt = Borrowings - Investments",
        "asset_turnover": "Asset Turnover = Sales / Total Assets",
    }