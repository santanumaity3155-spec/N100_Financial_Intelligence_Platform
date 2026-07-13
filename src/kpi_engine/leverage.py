"""
leverage.py

Leverage KPI calculations for the N100 Financial Intelligence Platform.

This module provides functions to calculate various leverage metrics
that measure a company's use of debt and financial risk.

KPIs Calculated:
- Debt to Equity
- Debt Ratio
- Interest Coverage
- Financial Leverage
"""

import logging
from typing import Optional, Dict, Any
import pandas as pd

from src.config.logging_config import get_logger
from src.database.connection import get_connection

logger = get_logger(__name__)


class LeverageCalculator:
    """
    Calculates leverage KPIs from financial data.
    
    This class provides methods to calculate various leverage metrics
    based on balance sheet and profit & loss data to assess financial risk.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the LeverageCalculator.
        
        Parameters
        ----------
        db_path : str, optional
            Path to SQLite database. If None, uses default connection.
        """
        self.db_path = db_path
        logger.info("LeverageCalculator initialized")

    def calculate_all(self, company_id: str, period: str) -> Dict[str, Any]:
        """
        Calculate all leverage KPIs for a company in a specific period.
        
        Parameters
        ----------
        company_id : str
            Company identifier
        period : str
            Financial period (e.g., '2024-Q1', 'FY2024')
            
        Returns
        -------
        Dict[str, Any]
            Dictionary containing all calculated leverage KPIs
        """
        logger.info(f"Calculating leverage KPIs for {company_id}, period {period}")
        
        # Fetch required data
        pl_data = self._fetch_profit_loss_data(company_id, period)
        bs_data = self._fetch_balance_sheet_data(company_id, period)
        
        if pl_data.empty or bs_data.empty:
            logger.warning(f"Insufficient data for {company_id}, period {period}")
            return {}
        
        # Calculate all KPIs
        results = {
            "company_id": company_id,
            "period": period,
            "debt_to_equity": self.calculate_debt_to_equity(bs_data),
            "debt_ratio": self.calculate_debt_ratio(bs_data),
            "interest_coverage": self.calculate_interest_coverage(pl_data),
            "financial_leverage": self.calculate_financial_leverage(bs_data),
        }
        
        logger.info(f"Calculated {len([v for v in results.values() if v is not None])} leverage KPIs")
        return results

    def calculate_debt_to_equity(self, bs_data: pd.DataFrame) -> Optional[float]:
        """
        Calculate Debt to Equity Ratio.
        
        Formula: Debt to Equity = Total Debt / Shareholders' Equity
        
        Parameters
        ----------
        bs_data : pd.DataFrame
            Balance Sheet data
            
        Returns
        -------
        Optional[float]
            Debt to Equity ratio, or None if calculation not possible
        """
        try:
            # Using borrowings as proxy for total debt
            total_debt = bs_data.get('borrowings', pd.Series([None])).iloc[0]
            equity = bs_data.get('share_capital', pd.Series([None])).iloc[0]
            
            if total_debt is None or equity is None or pd.isna(total_debt) or pd.isna(equity):
                logger.warning("Debt to Equity calculation: Missing debt or equity data")
                return None
            
            if equity == 0:
                logger.warning("Debt to Equity calculation: Equity is zero")
                return None
            
            ratio = total_debt / equity
            logger.debug(f"Debt to Equity calculated: {ratio:.2f}")
            return round(ratio, 2)
            
        except Exception as e:
            logger.error(f"Debt to Equity calculation failed: {str(e)}")
            return None

    def calculate_debt_ratio(self, bs_data: pd.DataFrame) -> Optional[float]:
        """
        Calculate Debt Ratio.
        
        Formula: Debt Ratio = Total Debt / Total Assets
        
        Parameters
        ----------
        bs_data : pd.DataFrame
            Balance Sheet data
            
        Returns
        -------
        Optional[float]
            Debt Ratio value, or None if calculation not possible
        """
        try:
            # Using borrowings as proxy for total debt
            total_debt = bs_data.get('borrowings', pd.Series([None])).iloc[0]
            total_assets = bs_data.get('total_assets', pd.Series([None])).iloc[0]
            
            if total_debt is None or total_assets is None or pd.isna(total_debt) or pd.isna(total_assets):
                logger.warning("Debt Ratio calculation: Missing debt or total_assets data")
                return None
            
            if total_assets == 0:
                logger.warning("Debt Ratio calculation: Total assets is zero")
                return None
            
            ratio = total_debt / total_assets
            logger.debug(f"Debt Ratio calculated: {ratio:.2f}")
            return round(ratio, 2)
            
        except Exception as e:
            logger.error(f"Debt Ratio calculation failed: {str(e)}")
            return None

    def calculate_interest_coverage(self, pl_data: pd.DataFrame) -> Optional[float]:
        """
        Calculate Interest Coverage Ratio.
        
        Formula: Interest Coverage = EBIT / Interest Expense
        Where EBIT = Operating Profit + Interest
        
        Parameters
        ----------
        pl_data : pd.DataFrame
            Profit & Loss data
            
        Returns
        -------
        Optional[float]
            Interest Coverage ratio, or None if calculation not possible
        """
        try:
            operating_profit = pl_data.get('operating_profit', pd.Series([None])).iloc[0]
            interest = pl_data.get('interest', pd.Series([None])).iloc[0]
            
            if operating_profit is None or interest is None or pd.isna(operating_profit) or pd.isna(interest):
                logger.warning("Interest Coverage calculation: Missing operating_profit or interest data")
                return None
            
            if interest == 0:
                logger.warning("Interest Coverage calculation: Interest expense is zero")
                return None
            
            # EBIT = Operating Profit + Interest (adding back interest)
            ebit = operating_profit + interest
            
            coverage = ebit / interest
            logger.debug(f"Interest Coverage calculated: {coverage:.2f}")
            return round(coverage, 2)
            
        except Exception as e:
            logger.error(f"Interest Coverage calculation failed: {str(e)}")
            return None

    def calculate_financial_leverage(self, bs_data: pd.DataFrame) -> Optional[float]:
        """
        Calculate Financial Leverage Ratio.
        
        Formula: Financial Leverage = Total Assets / Shareholders' Equity
        
        Parameters
        ----------
        bs_data : pd.DataFrame
            Balance Sheet data
            
        Returns
        -------
        Optional[float]
            Financial Leverage ratio, or None if calculation not possible
        """
        try:
            total_assets = bs_data.get('total_assets', pd.Series([None])).iloc[0]
            equity = bs_data.get('share_capital', pd.Series([None])).iloc[0]
            
            if total_assets is None or equity is None or pd.isna(total_assets) or pd.isna(equity):
                logger.warning("Financial Leverage calculation: Missing total_assets or equity data")
                return None
            
            if equity == 0:
                logger.warning("Financial Leverage calculation: Equity is zero")
                return None
            
            leverage = total_assets / equity
            logger.debug(f"Financial Leverage calculated: {leverage:.2f}")
            return round(leverage, 2)
            
        except Exception as e:
            logger.error(f"Financial Leverage calculation failed: {str(e)}")
            return None

    def _fetch_profit_loss_data(self, company_id: str, period: str) -> pd.DataFrame:
        """
        Fetch profit & loss data from database.
        
        Parameters
        ----------
        company_id : str
            Company identifier
        period : str
            Financial period
            
        Returns
        -------
        pd.DataFrame
            Profit & Loss data for the company and period
        """
        try:
            conn = get_connection()
            query = """
                SELECT * FROM profit_loss 
                WHERE company_id = ? AND period = ?
                LIMIT 1
            """
            df = pd.read_sql_query(query, conn, params=(company_id, period))
            return df
        except Exception as e:
            logger.error(f"Failed to fetch P&L data: {str(e)}")
            return pd.DataFrame()

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
        Get descriptions for all leverage KPIs.
        
        Returns
        -------
        Dict[str, str]
            Dictionary mapping KPI names to their descriptions
        """
        return {
            "debt_to_equity": "Debt to Equity Ratio - measures the proportion of debt to shareholders' equity",
            "debt_ratio": "Debt Ratio - measures the proportion of total assets financed by debt",
            "interest_coverage": "Interest Coverage Ratio - measures how easily a company can pay interest on outstanding debt",
            "financial_leverage": "Financial Leverage Ratio - measures the extent to which a company uses debt to finance assets",
        }

    def get_kpi_formulas(self) -> Dict[str, str]:
        """
        Get formulas for all leverage KPIs.
        
        Returns
        -------
        Dict[str, str]
            Dictionary mapping KPI names to their formulas
        """
        return {
            "debt_to_equity": "Debt to Equity = Total Debt / Shareholders' Equity",
            "debt_ratio": "Debt Ratio = Total Debt / Total Assets",
            "interest_coverage": "Interest Coverage = EBIT / Interest Expense, where EBIT = Operating Profit + Interest",
            "financial_leverage": "Financial Leverage = Total Assets / Shareholders' Equity",
        }