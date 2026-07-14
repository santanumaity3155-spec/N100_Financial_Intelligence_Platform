"""
efficiency.py

Efficiency KPI calculations for the N100 Financial Intelligence Platform.

This module provides functions to calculate various efficiency metrics
that measure how effectively a company uses its assets and manages operations.

KPIs Calculated:
- Asset Turnover
- Inventory Turnover
- Receivable Turnover
- Working Capital Turnover
"""

import logging
from typing import Optional, Dict, Any
import pandas as pd

from src.config.logging_config import get_logger
from src.database.connection import get_connection

logger = get_logger(__name__)


class EfficiencyCalculator:
    """
    Calculates efficiency KPIs from financial data.
    
    This class provides methods to calculate various efficiency metrics
    based on financial statements to assess operational effectiveness.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the EfficiencyCalculator.
        
        Parameters
        ----------
        db_path : str, optional
            Path to SQLite database. If None, uses default connection.
        """
        self.db_path = db_path
        logger.info("EfficiencyCalculator initialized")

    def calculate_all(self, company_id: str, period: str) -> Dict[str, Any]:
        """
        Calculate all efficiency KPIs for a company in a specific period.
        
        Parameters
        ----------
        company_id : str
            Company identifier
        period : str
            Financial period (e.g., '2024-Q1', 'FY2024')
            
        Returns
        -------
        Dict[str, Any]
            Dictionary containing all calculated efficiency KPIs
        """
        logger.info(f"Calculating efficiency KPIs for {company_id}, period {period}")
        
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
            "asset_turnover": self.calculate_asset_turnover(pl_data, bs_data),
            "inventory_turnover": self.calculate_inventory_turnover(pl_data, bs_data),
            "receivable_turnover": self.calculate_receivable_turnover(pl_data, bs_data),
            "working_capital_turnover": self.calculate_working_capital_turnover(pl_data, bs_data),
        }
        
        logger.info(f"Calculated {len([v for v in results.values() if v is not None])} efficiency KPIs")
        return results

    def calculate_asset_turnover(self, pl_data: pd.DataFrame, bs_data: pd.DataFrame) -> Optional[float]:
        """
        Calculate Asset Turnover Ratio.
        
        Formula: Asset Turnover = Sales / Total Assets
        
        Parameters
        ----------
        pl_data : pd.DataFrame
            Profit & Loss data
        bs_data : pd.DataFrame
            Balance Sheet data
            
        Returns
        -------
        Optional[float]
            Asset Turnover ratio, or None if calculation not possible
        """
        try:
            sales = pl_data.get('sales', pd.Series([None])).iloc[0]
            total_assets = bs_data.get('total_assets', pd.Series([None])).iloc[0]
            
            if sales is None or total_assets is None or pd.isna(sales) or pd.isna(total_assets):
                logger.warning("Asset Turnover calculation: Missing sales or total_assets data")
                return None
            
            if total_assets == 0:
                logger.warning("Asset Turnover calculation: Total assets is zero")
                return None
            
            turnover = sales / total_assets
            logger.debug(f"Asset Turnover calculated: {turnover:.2f}")
            return round(turnover, 2)
            
        except Exception as e:
            logger.error(f"Asset Turnover calculation failed: {str(e)}")
            return None

    def calculate_inventory_turnover(self, pl_data: pd.DataFrame, bs_data: pd.DataFrame) -> Optional[float]:
        """
        Calculate Inventory Turnover Ratio.
        
        Formula: Inventory Turnover = Cost of Goods Sold / Average Inventory
        Note: Using expenses as proxy for COGS, and total_assets as inventory proxy
        
        Parameters
        ----------
        pl_data : pd.DataFrame
            Profit & Loss data
        bs_data : pd.DataFrame
            Balance Sheet data
            
        Returns
        -------
        Optional[float]
            Inventory Turnover ratio, or None if calculation not possible
        """
        try:
            # Using expenses as proxy for COGS
            cogs = pl_data.get('expenses', pd.Series([None])).iloc[0]
            inventory = bs_data.get('total_assets', pd.Series([None])).iloc[0]  # Proxy
            
            if cogs is None or inventory is None or pd.isna(cogs) or pd.isna(inventory):
                logger.warning("Inventory Turnover calculation: Missing expenses or inventory data")
                return None
            
            if inventory == 0:
                logger.warning("Inventory Turnover calculation: Inventory is zero")
                return None
            
            turnover = cogs / inventory
            logger.debug(f"Inventory Turnover calculated: {turnover:.2f}")
            return round(turnover, 2)
            
        except Exception as e:
            logger.error(f"Inventory Turnover calculation failed: {str(e)}")
            return None

    def calculate_receivable_turnover(self, pl_data: pd.DataFrame, bs_data: pd.DataFrame) -> Optional[float]:
        """
        Calculate Receivable Turnover Ratio.
        
        Formula: Receivable Turnover = Net Credit Sales / Average Accounts Receivable
        Note: Using sales as proxy for net credit sales, total_assets as AR proxy
        
        Parameters
        ----------
        pl_data : pd.DataFrame
            Profit & Loss data
        bs_data : pd.DataFrame
            Balance Sheet data
            
        Returns
        -------
        Optional[float]
            Receivable Turnover ratio, or None if calculation not possible
        """
        try:
            # Using sales as proxy for net credit sales
            sales = pl_data.get('sales', pd.Series([None])).iloc[0]
            receivables = bs_data.get('total_assets', pd.Series([None])).iloc[0]  # Proxy
            
            if sales is None or receivables is None or pd.isna(sales) or pd.isna(receivables):
                logger.warning("Receivable Turnover calculation: Missing sales or receivables data")
                return None
            
            if receivables == 0:
                logger.warning("Receivable Turnover calculation: Receivables is zero")
                return None
            
            turnover = sales / receivables
            logger.debug(f"Receivable Turnover calculated: {turnover:.2f}")
            return round(turnover, 2)
            
        except Exception as e:
            logger.error(f"Receivable Turnover calculation failed: {str(e)}")
            return None

    def calculate_working_capital_turnover(self, pl_data: pd.DataFrame, bs_data: pd.DataFrame) -> Optional[float]:
        """
        Calculate Working Capital Turnover Ratio.
        
        Formula: Working Capital Turnover = Sales / Working Capital
        Where Working Capital = Current Assets - Current Liabilities
        Note: Using total_assets and total_liabilities as proxies
        
        Parameters
        ----------
        pl_data : pd.DataFrame
            Profit & Loss data
        bs_data : pd.DataFrame
            Balance Sheet data
            
        Returns
        -------
        Optional[float]
            Working Capital Turnover ratio, or None if calculation not possible
        """
        try:
            # Check if dataframes are empty
            if pl_data.empty or bs_data.empty:
                logger.warning("Working Capital Turnover calculation: Empty dataframes provided")
                return None
            
            sales = pl_data.get('sales', pd.Series([None])).iloc[0]
            current_assets = bs_data.get('total_assets', pd.Series([None])).iloc[0]
            current_liabilities = bs_data.get('total_liabilities', pd.Series([None])).iloc[0]
            
            if sales is None or current_assets is None or current_liabilities is None:
                logger.warning("Working Capital Turnover calculation: Missing data")
                return None
            
            if pd.isna(sales) or pd.isna(current_assets) or pd.isna(current_liabilities):
                logger.warning("Working Capital Turnover calculation: NaN values found")
                return None
            
            # Calculate working capital
            working_capital = current_assets - current_liabilities
            
            # Log the calculated working capital for debugging
            logger.debug(f"Working Capital Turnover: Current Assets={current_assets}, "
                        f"Current Liabilities={current_liabilities}, "
                        f"Working Capital={working_capital}")
            
            # Check if working capital is zero or negative
            if working_capital == 0:
                logger.warning("Working Capital Turnover calculation: Working capital is zero "
                              "(Current Assets equals Current Liabilities)")
                return None
            
            if working_capital < 0:
                logger.warning(f"Working Capital Turnover calculation: Working capital is negative ({working_capital:.2f}). "
                              "This indicates current liabilities exceed current assets.")
                return None
            
            if sales == 0:
                logger.warning("Working Capital Turnover calculation: Sales is zero")
                return None
            
            turnover = sales / working_capital
            logger.debug(f"Working Capital Turnover calculated: {turnover:.2f}")
            return round(turnover, 2)
            
        except IndexError as e:
            logger.error(f"Working Capital Turnover calculation failed - IndexError (empty dataframe): {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Working Capital Turnover calculation failed: {str(e)}")
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
        Get descriptions for all efficiency KPIs.
        
        Returns
        -------
        Dict[str, str]
            Dictionary mapping KPI names to their descriptions
        """
        return {
            "asset_turnover": "Asset Turnover - measures how efficiently a company uses its assets to generate sales",
            "inventory_turnover": "Inventory Turnover - measures how many times inventory is sold and replaced over a period",
            "receivable_turnover": "Receivable Turnover - measures how efficiently a company collects revenue from credit sales",
            "working_capital_turnover": "Working Capital Turnover - measures how efficiently a company uses working capital to generate sales",
        }

    def get_kpi_formulas(self) -> Dict[str, str]:
        """
        Get formulas for all efficiency KPIs.
        
        Returns
        -------
        Dict[str, str]
            Dictionary mapping KPI names to their formulas
        """
        return {
            "asset_turnover": "Asset Turnover = Sales / Total Assets",
            "inventory_turnover": "Inventory Turnover = Cost of Goods Sold / Average Inventory",
            "receivable_turnover": "Receivable Turnover = Net Credit Sales / Average Accounts Receivable",
            "working_capital_turnover": "Working Capital Turnover = Sales / Working Capital, where Working Capital = Current Assets - Current Liabilities",
        }