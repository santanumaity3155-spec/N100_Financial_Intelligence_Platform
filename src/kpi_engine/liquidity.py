"""
liquidity.py

Liquidity KPI calculations for the N100 Financial Intelligence Platform.

This module provides functions to calculate various liquidity metrics
that measure a company's ability to meet short-term obligations.

KPIs Calculated:
- Current Ratio
- Quick Ratio
- Cash Ratio
"""

import logging
from typing import Optional, Dict, Any
import pandas as pd

from src.config.logging_config import get_logger
from src.database.connection import get_connection

logger = get_logger(__name__)


class LiquidityCalculator:
    """
    Calculates liquidity KPIs from financial data.
    
    This class provides methods to calculate various liquidity metrics
    based on balance sheet data to assess short-term financial health.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the LiquidityCalculator.
        
        Parameters
        ----------
        db_path : str, optional
            Path to SQLite database. If None, uses default connection.
        """
        self.db_path = db_path
        logger.info("LiquidityCalculator initialized")

    def calculate_all(self, company_id: str, period: str) -> Dict[str, Any]:
        """
        Calculate all liquidity KPIs for a company in a specific period.
        
        Parameters
        ----------
        company_id : str
            Company identifier
        period : str
            Financial period (e.g., '2024-Q1', 'FY2024')
            
        Returns
        -------
        Dict[str, Any]
            Dictionary containing all calculated liquidity KPIs
        """
        logger.info(f"Calculating liquidity KPIs for {company_id}, period {period}")
        
        # Fetch required data
        bs_data = self._fetch_balance_sheet_data(company_id, period)
        
        if bs_data.empty:
            logger.warning(f"Insufficient balance sheet data for {company_id}, period {period}")
            return {}
        
        # Calculate all KPIs
        results = {
            "company_id": company_id,
            "period": period,
            "current_ratio": self.calculate_current_ratio(bs_data),
            "quick_ratio": self.calculate_quick_ratio(bs_data),
            "cash_ratio": self.calculate_cash_ratio(bs_data),
        }
        
        logger.info(f"Calculated {len([v for v in results.values() if v is not None])} liquidity KPIs")
        return results

    def calculate_current_ratio(self, bs_data: pd.DataFrame) -> Optional[float]:
        """
        Calculate Current Ratio.
        
        Formula: Current Ratio = Current Assets / Current Liabilities
        
        Parameters
        ----------
        bs_data : pd.DataFrame
            Balance Sheet data
            
        Returns
        -------
        Optional[float]
            Current Ratio value, or None if calculation not possible
        """
        try:
            # Note: current_assets and current_liabilities not available in current schema
            # Using total_assets and total_liabilities as approximation
            current_assets = bs_data.get('total_assets', pd.Series([None])).iloc[0]
            current_liabilities = bs_data.get('total_liabilities', pd.Series([None])).iloc[0]
            
            if current_assets is None or current_liabilities is None or pd.isna(current_assets) or pd.isna(current_liabilities):
                logger.warning("Current Ratio calculation: Missing current_assets or current_liabilities data")
                return None
            
            if current_liabilities == 0:
                logger.warning("Current Ratio calculation: Current liabilities is zero")
                return None
            
            ratio = current_assets / current_liabilities
            logger.debug(f"Current Ratio calculated: {ratio:.2f}")
            return round(ratio, 2)
            
        except Exception as e:
            logger.error(f"Current Ratio calculation failed: {str(e)}")
            return None

    def calculate_quick_ratio(self, bs_data: pd.DataFrame) -> Optional[float]:
        """
        Calculate Quick Ratio (Acid-Test Ratio).
        
        Formula: Quick Ratio = (Current Assets - Inventory) / Current Liabilities
        Note: Using total_assets as proxy since inventory data not available
        
        Parameters
        ----------
        bs_data : pd.DataFrame
            Balance Sheet data
            
        Returns
        -------
        Optional[float]
            Quick Ratio value, or None if calculation not possible
        """
        try:
            # Note: current_assets and current_liabilities not available in current schema
            # Using total_assets and total_liabilities as approximation
            current_assets = bs_data.get('total_assets', pd.Series([None])).iloc[0]
            current_liabilities = bs_data.get('total_liabilities', pd.Series([None])).iloc[0]
            
            if current_assets is None or current_liabilities is None or pd.isna(current_assets) or pd.isna(current_liabilities):
                logger.warning("Quick Ratio calculation: Missing current_assets or current_liabilities data")
                return None
            
            # Quick assets = Current Assets - Inventory (inventory not available, using total_assets)
            quick_assets = current_assets
            
            if current_liabilities == 0:
                logger.warning("Quick Ratio calculation: Current liabilities is zero")
                return None
            
            ratio = quick_assets / current_liabilities
            logger.debug(f"Quick Ratio calculated: {ratio:.2f}")
            return round(ratio, 2)
            
        except Exception as e:
            logger.error(f"Quick Ratio calculation failed: {str(e)}")
            return None

    def calculate_cash_ratio(self, bs_data: pd.DataFrame) -> Optional[float]:
        """
        Calculate Cash Ratio.
        
        Formula: Cash Ratio = Cash and Cash Equivalents / Current Liabilities
        Note: Cash data not available in current schema, returning None
        
        Parameters
        ----------
        bs_data : pd.DataFrame
            Balance Sheet data
            
        Returns
        -------
        Optional[float]
            Cash Ratio value, or None if calculation not possible
        """
        try:
            # Check if dataframe is empty
            if bs_data.empty:
                logger.warning("Cash Ratio calculation: Empty dataframe provided")
                return None
            
            # Try to find cash and cash equivalents
            # Check multiple possible column names
            cash = None
            possible_cash_columns = ['cash', 'cash_equivalents', 'cash_and_equivalents', 
                                     'cash_at_bank', 'cash_on_hand']
            
            for col in possible_cash_columns:
                if col in bs_data.columns:
                    cash = bs_data.get(col, pd.Series([None])).iloc[0]
                    if cash is not None and not pd.isna(cash):
                        break
            
            # If no dedicated cash column found, check if we can use other_assets as proxy
            if cash is None or pd.isna(cash):
                other_assets = bs_data.get('other_assets', pd.Series([None])).iloc[0]
                if other_assets is not None and not pd.isna(other_assets):
                    cash = other_assets
                    logger.debug("Cash Ratio calculation: Using 'other_assets' as proxy for cash")
            
            # Get current liabilities (using total_liabilities as proxy since current_liabilities not available)
            current_liabilities = bs_data.get('total_liabilities', pd.Series([None])).iloc[0]
            
            if cash is None or pd.isna(cash):
                logger.warning("Cash Ratio calculation: Cash and cash equivalents data not available in schema")
                return None
            
            if current_liabilities is None or pd.isna(current_liabilities):
                logger.warning("Cash Ratio calculation: Missing current_liabilities data")
                return None
            
            if current_liabilities == 0:
                logger.warning("Cash Ratio calculation: Current liabilities is zero")
                return None
            
            ratio = cash / current_liabilities
            logger.debug(f"Cash Ratio calculated: {ratio:.2f}")
            return round(ratio, 2)
            
        except IndexError as e:
            logger.error(f"Cash Ratio calculation failed - IndexError (empty dataframe): {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Cash Ratio calculation failed: {str(e)}")
            return None

    def _fetch_balance_sheet_data(self, company_id: str, period: str) -> pd.DataFrame:
        """
        Fetch balance sheet data from database.
        
        Parameters
        ----------
        company_id : str
            Company identifier
        period : str
            Financial period
            
        Returns
        -------
        pd.DataFrame
            Balance Sheet data for the company and period
        """
        try:
            conn = get_connection()
            query = """
                SELECT * FROM balance_sheet 
                WHERE company_id = ? AND period = ?
                LIMIT 1
            """
            df = pd.read_sql_query(query, conn, params=(company_id, period))
            return df
        except Exception as e:
            logger.error(f"Failed to fetch Balance Sheet data: {str(e)}")
            return pd.DataFrame()

    def get_kpi_descriptions(self) -> Dict[str, str]:
        """
        Get descriptions for all liquidity KPIs.
        
        Returns
        -------
        Dict[str, str]
            Dictionary mapping KPI names to their descriptions
        """
        return {
            "current_ratio": "Current Ratio - measures a company's ability to pay short-term obligations with current assets",
            "quick_ratio": "Quick Ratio - measures a company's ability to pay short-term obligations with quick assets (excluding inventory)",
            "cash_ratio": "Cash Ratio - measures a company's ability to pay short-term obligations with cash and cash equivalents only",
        }

    def get_kpi_formulas(self) -> Dict[str, str]:
        """
        Get formulas for all liquidity KPIs.
        
        Returns
        -------
        Dict[str, str]
            Dictionary mapping KPI names to their formulas
        """
        return {
            "current_ratio": "Current Ratio = Current Assets / Current Liabilities",
            "quick_ratio": "Quick Ratio = (Current Assets - Inventory) / Current Liabilities",
            "cash_ratio": "Cash Ratio = Cash and Cash Equivalents / Current Liabilities",
        }