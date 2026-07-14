"""
profitability.py

Profitability KPI calculations for the N100 Financial Intelligence Platform.

This module provides functions to calculate various profitability metrics
including ROE, ROCE, ROA, and profit margins.

KPIs Calculated:
- ROE (Return on Equity)
- ROCE (Return on Capital Employed)
- ROA (Return on Assets)
- Net Profit Margin
- Operating Margin
- EBIT Margin
- Gross Margin
"""

import logging
from typing import Optional, Dict, Any
import pandas as pd
import numpy as np

from src.config.logging_config import get_logger
from src.database.connection import get_connection

logger = get_logger(__name__)


class ProfitabilityCalculator:
    """
    Calculates profitability KPIs from financial data.
    
    This class provides methods to calculate various profitability metrics
    based on profit & loss and balance sheet data.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the ProfitabilityCalculator.
        
        Parameters
        ----------
        db_path : str, optional
            Path to SQLite database. If None, uses default connection.
        """
        self.db_path = db_path
        logger.info("ProfitabilityCalculator initialized")

    def calculate_all(self, company_id: str, period: str) -> Dict[str, Any]:
        """
        Calculate all profitability KPIs for a company in a specific period.
        
        Parameters
        ----------
        company_id : str
            Company identifier
        period : str
            Financial period (e.g., '2024-Q1', 'FY2024')
            
        Returns
        -------
        Dict[str, Any]
            Dictionary containing all calculated profitability KPIs
        """
        logger.info(f"Calculating profitability KPIs for {company_id}, period {period}")
        
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
            "roe": self.calculate_roe(pl_data, bs_data),
            "roce": self.calculate_roce(pl_data, bs_data),
            "roa": self.calculate_roa(pl_data, bs_data),
            "net_profit_margin": self.calculate_net_profit_margin(pl_data),
            "operating_margin": self.calculate_operating_margin(pl_data),
            "ebit_margin": self.calculate_ebit_margin(pl_data),
            "gross_margin": self.calculate_gross_margin(pl_data),
        }
        
        logger.info(f"Calculated {len([v for v in results.values() if v is not None])} profitability KPIs")
        return results

    def calculate_roe(
        self,
        pl_data: pd.DataFrame,
        bs_data: pd.DataFrame
    ) -> Optional[float]:
        """
        Calculate Return on Equity (ROE).
        
        Formula: ROE = Net Profit / Shareholders' Equity * 100
        
        Parameters
        ----------
        pl_data : pd.DataFrame
            Profit & Loss data
        bs_data : pd.DataFrame
            Balance Sheet data
            
        Returns
        -------
        Optional[float]
            ROE percentage, or None if calculation not possible
        """
        try:
            net_profit = pl_data.get('net_profit', pd.Series([None])).iloc[0]
            equity = bs_data.get('share_capital', pd.Series([None])).iloc[0]
            
            if net_profit is None or equity is None or pd.isna(net_profit) or pd.isna(equity):
                logger.warning("ROE calculation: Missing net_profit or equity data")
                return None
            
            if equity == 0:
                logger.warning("ROE calculation: Equity is zero, cannot calculate")
                return None
            
            roe = (net_profit / equity) * 100
            logger.debug(f"ROE calculated: {roe:.2f}%")
            return round(roe, 2)
            
        except Exception as e:
            logger.error(f"ROE calculation failed: {str(e)}")
            return None

    def calculate_roce(
        self,
        pl_data: pd.DataFrame,
        bs_data: pd.DataFrame
    ) -> Optional[float]:
        """
        Calculate Return on Capital Employed (ROCE).
        
        Formula: ROCE = EBIT / (Total Assets - Current Liabilities) * 100
        Where EBIT = Operating Profit + Interest
        
        Parameters
        ----------
        pl_data : pd.DataFrame
            Profit & Loss data
        bs_data : pd.DataFrame
            Balance Sheet data
            
        Returns
        -------
        Optional[float]
            ROCE percentage, or None if calculation not possible
        """
        try:
            operating_profit = pl_data.get('operating_profit', pd.Series([None])).iloc[0]
            interest = pl_data.get('interest', pd.Series([0])).iloc[0]
            total_assets = bs_data.get('total_assets', pd.Series([None])).iloc[0]
            
            if operating_profit is None or total_assets is None or pd.isna(operating_profit) or pd.isna(total_assets):
                logger.warning("ROCE calculation: Missing operating_profit or total_assets data")
                return None
            
            # Calculate EBIT
            ebit = operating_profit + (interest if interest and not pd.isna(interest) else 0)
            
            # Capital Employed = Total Assets (simplified, as current_liabilities not available)
            capital_employed = total_assets
            
            if capital_employed == 0:
                logger.warning("ROCE calculation: Capital employed is zero")
                return None
            
            roce = (ebit / capital_employed) * 100
            logger.debug(f"ROCE calculated: {roce:.2f}%")
            return round(roce, 2)
            
        except Exception as e:
            logger.error(f"ROCE calculation failed: {str(e)}")
            return None

    def calculate_roa(
        self,
        pl_data: pd.DataFrame,
        bs_data: pd.DataFrame
    ) -> Optional[float]:
        """
        Calculate Return on Assets (ROA).
        
        Formula: ROA = Net Profit / Total Assets * 100
        
        Parameters
        ----------
        pl_data : pd.DataFrame
            Profit & Loss data
        bs_data : pd.DataFrame
            Balance Sheet data
            
        Returns
        -------
        Optional[float]
            ROA percentage, or None if calculation not possible
        """
        try:
            # Check if dataframes are empty
            if pl_data.empty or bs_data.empty:
                logger.warning("ROA calculation: Empty dataframes provided")
                return None
            
            net_profit = pl_data.get('net_profit', pd.Series([None])).iloc[0]
            total_assets = bs_data.get('total_assets', pd.Series([None])).iloc[0]
            
            if net_profit is None or pd.isna(net_profit):
                logger.warning("ROA calculation: Missing net_profit data")
                return None
            
            if total_assets is None or pd.isna(total_assets):
                logger.warning("ROA calculation: Missing total_assets data")
                return None
            
            if total_assets == 0:
                logger.warning("ROA calculation: Total assets is zero")
                return None
            
            roa = (net_profit / total_assets) * 100
            logger.debug(f"ROA calculated: {roa:.2f}%")
            return round(roa, 2)
            
        except IndexError as e:
            logger.error(f"ROA calculation failed - IndexError (empty dataframe): {str(e)}")
            return None
        except Exception as e:
            logger.error(f"ROA calculation failed: {str(e)}")
            return None

    def calculate_net_profit_margin(self, pl_data: pd.DataFrame) -> Optional[float]:
        """
        Calculate Net Profit Margin.
        
        Formula: Net Profit Margin = Net Profit / Sales * 100
        
        Parameters
        ----------
        pl_data : pd.DataFrame
            Profit & Loss data
            
        Returns
        -------
        Optional[float]
            Net Profit Margin percentage, or None if calculation not possible
        """
        try:
            # Check if dataframe is empty
            if pl_data.empty:
                logger.warning("Net Profit Margin calculation: Empty dataframe provided")
                return None
            
            net_profit = pl_data.get('net_profit', pd.Series([None])).iloc[0]
            sales = pl_data.get('sales', pd.Series([None])).iloc[0]
            
            if net_profit is None or sales is None or pd.isna(net_profit) or pd.isna(sales):
                logger.warning("Net Profit Margin calculation: Missing net_profit or sales data")
                return None
            
            if sales == 0:
                logger.warning("Net Profit Margin calculation: Sales is zero")
                return None
            
            margin = (net_profit / sales) * 100
            logger.debug(f"Net Profit Margin calculated: {margin:.2f}%")
            return round(margin, 2)
            
        except IndexError as e:
            logger.error(f"Net Profit Margin calculation failed - IndexError (empty dataframe): {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Net Profit Margin calculation failed: {str(e)}")
            return None

    def calculate_operating_margin(self, pl_data: pd.DataFrame) -> Optional[float]:
        """
        Calculate Operating Margin.
        
        Formula: Operating Margin = Operating Profit / Sales * 100
        
        Parameters
        ----------
        pl_data : pd.DataFrame
            Profit & Loss data
            
        Returns
        -------
        Optional[float]
            Operating Margin percentage, or None if calculation not possible
        """
        try:
            # Check if dataframe is empty
            if pl_data.empty:
                logger.warning("Operating Margin calculation: Empty dataframe provided")
                return None
            
            operating_profit = pl_data.get('operating_profit', pd.Series([None])).iloc[0]
            sales = pl_data.get('sales', pd.Series([None])).iloc[0]
            
            if operating_profit is None or sales is None or pd.isna(operating_profit) or pd.isna(sales):
                logger.warning("Operating Margin calculation: Missing operating_profit or sales data")
                return None
            
            if sales == 0:
                logger.warning("Operating Margin calculation: Sales is zero")
                return None
            
            margin = (operating_profit / sales) * 100
            logger.debug(f"Operating Margin calculated: {margin:.2f}%")
            return round(margin, 2)
            
        except IndexError as e:
            logger.error(f"Operating Margin calculation failed - IndexError (empty dataframe): {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Operating Margin calculation failed: {str(e)}")
            return None

    def calculate_ebit_margin(self, pl_data: pd.DataFrame) -> Optional[float]:
        """
        Calculate EBIT Margin.
        
        Formula: EBIT Margin = EBIT / Sales * 100
        Where EBIT = Operating Profit + Interest
        
        Parameters
        ----------
        pl_data : pd.DataFrame
            Profit & Loss data
            
        Returns
        -------
        Optional[float]
            EBIT Margin percentage, or None if calculation not possible
        """
        try:
            # Check if dataframe is empty
            if pl_data.empty:
                logger.warning("EBIT Margin calculation: Empty dataframe provided")
                return None
            
            operating_profit = pl_data.get('operating_profit', pd.Series([None])).iloc[0]
            interest = pl_data.get('interest', pd.Series([0])).iloc[0]
            sales = pl_data.get('sales', pd.Series([None])).iloc[0]
            
            if operating_profit is None or pd.isna(operating_profit):
                logger.warning("EBIT Margin calculation: Missing operating_profit data")
                return None
            
            if sales is None or pd.isna(sales):
                logger.warning("EBIT Margin calculation: Missing sales data")
                return None
            
            # Calculate EBIT
            interest = interest if interest and not pd.isna(interest) else 0
            ebit = operating_profit + interest
            
            if sales == 0:
                logger.warning("EBIT Margin calculation: Sales is zero")
                return None
            
            margin = (ebit / sales) * 100
            logger.debug(f"EBIT Margin calculated: {margin:.2f}%")
            return round(margin, 2)
            
        except IndexError as e:
            logger.error(f"EBIT Margin calculation failed - IndexError (empty dataframe): {str(e)}")
            return None
        except Exception as e:
            logger.error(f"EBIT Margin calculation failed: {str(e)}")
            return None

    def calculate_gross_margin(self, pl_data: pd.DataFrame) -> Optional[float]:
        """
        Calculate Gross Margin.
        
        Formula: Gross Margin = (Sales - Expenses) / Sales * 100
        Note: Using operating_profit as proxy for gross profit if gross_profit not available
        
        Parameters
        ----------
        pl_data : pd.DataFrame
            Profit & Loss data
            
        Returns
        -------
        Optional[float]
            Gross Margin percentage, or None if calculation not possible
        """
        try:
            # Check if dataframe is empty
            if pl_data.empty:
                logger.warning("Gross Margin calculation: Empty dataframe provided")
                return None
            
            # Try to get gross profit, if not available use operating profit
            gross_profit = pl_data.get('gross_profit', None)
            if gross_profit is None or (hasattr(gross_profit, 'isna') and gross_profit.isna().all()):
                gross_profit = pl_data.get('operating_profit', pd.Series([None]))
            
            # Safely get the value
            if gross_profit is not None and hasattr(gross_profit, 'iloc') and len(gross_profit) > 0:
                gross_profit = gross_profit.iloc[0]
            elif gross_profit is not None and not hasattr(gross_profit, 'iloc'):
                gross_profit = gross_profit
            else:
                gross_profit = None
            
            sales = pl_data.get('sales', pd.Series([None])).iloc[0]
            
            if gross_profit is None or sales is None or pd.isna(gross_profit) or pd.isna(sales):
                logger.warning("Gross Margin calculation: Missing gross_profit or sales data")
                return None
            
            if sales == 0:
                logger.warning("Gross Margin calculation: Sales is zero")
                return None
            
            margin = (gross_profit / sales) * 100
            logger.debug(f"Gross Margin calculated: {margin:.2f}%")
            return round(margin, 2)
            
        except IndexError as e:
            logger.error(f"Gross Margin calculation failed - IndexError (empty dataframe): {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Gross Margin calculation failed: {str(e)}")
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
        Get descriptions for all profitability KPIs.
        
        Returns
        -------
        Dict[str, str]
            Dictionary mapping KPI names to their descriptions
        """
        return {
            "roe": "Return on Equity - measures how effectively a company is using shareholder equity to generate profit",
            "roce": "Return on Capital Employed - measures a company's profitability and efficiency in using capital",
            "roa": "Return on Assets - measures how efficiently a company is using its assets to generate profit",
            "net_profit_margin": "Net Profit Margin - percentage of revenue that remains as net profit after all expenses",
            "operating_margin": "Operating Margin - percentage of revenue that remains as operating profit",
            "ebit_margin": "EBIT Margin - percentage of revenue that remains as earnings before interest and taxes",
            "gross_margin": "Gross Margin - percentage of revenue that remains as gross profit after cost of goods sold",
        }

    def get_kpi_formulas(self) -> Dict[str, str]:
        """
        Get formulas for all profitability KPIs.
        
        Returns
        -------
        Dict[str, str]
            Dictionary mapping KPI names to their formulas
        """
        return {
            "roe": "ROE = (Net Profit / Shareholders' Equity) × 100",
            "roce": "ROCE = (EBIT / Capital Employed) × 100, where EBIT = Operating Profit + Interest",
            "roa": "ROA = (Net Profit / Total Assets) × 100",
            "net_profit_margin": "Net Profit Margin = (Net Profit / Sales) × 100",
            "operating_margin": "Operating Margin = (Operating Profit / Sales) × 100",
            "ebit_margin": "EBIT Margin = (EBIT / Sales) × 100, where EBIT = Operating Profit + Interest",
            "gross_margin": "Gross Margin = (Gross Profit / Sales) × 100",
        }