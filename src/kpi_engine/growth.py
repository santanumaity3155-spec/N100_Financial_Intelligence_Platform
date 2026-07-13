"""
growth.py

Growth KPI calculations for the N100 Financial Intelligence Platform.

This module provides functions to calculate various growth metrics
that measure a company's performance over time.

KPIs Calculated:
- Revenue CAGR
- Profit CAGR
- EPS CAGR
- Margin Expansion
"""

import logging
from typing import Optional, Dict, Any, List
import pandas as pd
import numpy as np

from src.config.logging_config import get_logger
from src.database.connection import get_connection

logger = get_logger(__name__)


class GrowthCalculator:
    """
    Calculates growth KPIs from financial data.
    
    This class provides methods to calculate various growth metrics
    based on historical financial data to assess company performance trends.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the GrowthCalculator.
        
        Parameters
        ----------
        db_path : str, optional
            Path to SQLite database. If None, uses default connection.
        """
        self.db_path = db_path
        logger.info("GrowthCalculator initialized")

    def calculate_all(self, company_id: str, periods: List[str]) -> Dict[str, Any]:
        """
        Calculate all growth KPIs for a company across multiple periods.
        
        Parameters
        ----------
        company_id : str
            Company identifier
        periods : List[str]
            List of financial periods (e.g., ['2022-Q1', '2023-Q1', '2024-Q1'])
            
        Returns
        -------
        Dict[str, Any]
            Dictionary containing all calculated growth KPIs
        """
        logger.info(f"Calculating growth KPIs for {company_id} across {len(periods)} periods")
        
        if len(periods) < 2:
            logger.warning(f"Insufficient periods for growth calculation: {len(periods)}")
            return {}
        
        # Fetch required data for all periods
        pl_data = self._fetch_profit_loss_data(company_id, periods)
        
        if pl_data.empty or len(pl_data) < 2:
            logger.warning(f"Insufficient P&L data for {company_id}")
            return {}
        
        # Calculate all KPIs
        results = {
            "company_id": company_id,
            "periods": periods,
            "revenue_cagr": self.calculate_revenue_cagr(pl_data),
            "profit_cagr": self.calculate_profit_cagr(pl_data),
            "eps_cagr": self.calculate_eps_cagr(pl_data),
            "margin_expansion": self.calculate_margin_expansion(pl_data),
        }
        
        logger.info(f"Calculated {len([v for v in results.values() if v is not None])} growth KPIs")
        return results

    def calculate_revenue_cagr(self, pl_data: pd.DataFrame) -> Optional[float]:
        """
        Calculate Revenue CAGR (Compound Annual Growth Rate).
        
        Formula: CAGR = (Ending Value / Beginning Value)^(1/n) - 1
        Where n = number of years
        
        Parameters
        ----------
        pl_data : pd.DataFrame
            Profit & Loss data with multiple periods
            
        Returns
        -------
        Optional[float]
            Revenue CAGR percentage, or None if calculation not possible
        """
        try:
            if 'sales' not in pl_data.columns or pl_data['sales'].isna().all():
                logger.warning("Revenue CAGR calculation: Missing sales data")
                return None
            
            sales_values = pl_data['sales'].dropna()
            
            if len(sales_values) < 2:
                logger.warning("Revenue CAGR calculation: Insufficient data points")
                return None
            
            beginning_value = sales_values.iloc[0]
            ending_value = sales_values.iloc[-1]
            
            if beginning_value <= 0 or ending_value <= 0:
                logger.warning("Revenue CAGR calculation: Invalid sales values")
                return None
            
            # Calculate number of years
            n = len(sales_values) - 1
            
            # CAGR formula
            cagr = ((ending_value / beginning_value) ** (1 / n)) - 1
            cagr_pct = cagr * 100
            
            logger.debug(f"Revenue CAGR calculated: {cagr_pct:.2f}%")
            return round(cagr_pct, 2)
            
        except Exception as e:
            logger.error(f"Revenue CAGR calculation failed: {str(e)}")
            return None

    def calculate_profit_cagr(self, pl_data: pd.DataFrame) -> Optional[float]:
        """
        Calculate Profit CAGR (Compound Annual Growth Rate).
        
        Formula: CAGR = (Ending Value / Beginning Value)^(1/n) - 1
        Where n = number of years
        
        Parameters
        ----------
        pl_data : pd.DataFrame
            Profit & Loss data with multiple periods
            
        Returns
        -------
        Optional[float]
            Profit CAGR percentage, or None if calculation not possible
        """
        try:
            if 'net_profit' not in pl_data.columns or pl_data['net_profit'].isna().all():
                logger.warning("Profit CAGR calculation: Missing net_profit data")
                return None
            
            profit_values = pl_data['net_profit'].dropna()
            
            if len(profit_values) < 2:
                logger.warning("Profit CAGR calculation: Insufficient data points")
                return None
            
            beginning_value = profit_values.iloc[0]
            ending_value = profit_values.iloc[-1]
            
            # Handle negative profits
            if beginning_value <= 0 or ending_value <= 0:
                logger.warning("Profit CAGR calculation: Invalid profit values (negative or zero)")
                return None
            
            # Calculate number of years
            n = len(profit_values) - 1
            
            # CAGR formula
            cagr = ((ending_value / beginning_value) ** (1 / n)) - 1
            cagr_pct = cagr * 100
            
            logger.debug(f"Profit CAGR calculated: {cagr_pct:.2f}%")
            return round(cagr_pct, 2)
            
        except Exception as e:
            logger.error(f"Profit CAGR calculation failed: {str(e)}")
            return None

    def calculate_eps_cagr(self, pl_data: pd.DataFrame) -> Optional[float]:
        """
        Calculate EPS CAGR (Compound Annual Growth Rate).
        
        Formula: CAGR = (Ending Value / Beginning Value)^(1/n) - 1
        Where n = number of years
        
        Parameters
        ----------
        pl_data : pd.DataFrame
            Profit & Loss data with multiple periods
            
        Returns
        -------
        Optional[float]
            EPS CAGR percentage, or None if calculation not possible
        """
        try:
            if 'eps' not in pl_data.columns or pl_data['eps'].isna().all():
                logger.warning("EPS CAGR calculation: Missing EPS data")
                return None
            
            eps_values = pl_data['eps'].dropna()
            
            if len(eps_values) < 2:
                logger.warning("EPS CAGR calculation: Insufficient data points")
                return None
            
            beginning_value = eps_values.iloc[0]
            ending_value = eps_values.iloc[-1]
            
            if beginning_value <= 0 or ending_value <= 0:
                logger.warning("EPS CAGR calculation: Invalid EPS values")
                return None
            
            # Calculate number of years
            n = len(eps_values) - 1
            
            # CAGR formula
            cagr = ((ending_value / beginning_value) ** (1 / n)) - 1
            cagr_pct = cagr * 100
            
            logger.debug(f"EPS CAGR calculated: {cagr_pct:.2f}%")
            return round(cagr_pct, 2)
            
        except Exception as e:
            logger.error(f"EPS CAGR calculation failed: {str(e)}")
            return None

    def calculate_margin_expansion(self, pl_data: pd.DataFrame) -> Optional[float]:
        """
        Calculate Margin Expansion (change in net profit margin over time).
        
        Formula: Margin Expansion = Latest Margin - Earliest Margin
        
        Parameters
        ----------
        pl_data : pd.DataFrame
            Profit & Loss data with multiple periods
            
        Returns
        -------
        Optional[float]
            Margin Expansion in percentage points, or None if calculation not possible
        """
        try:
            if 'net_profit' not in pl_data.columns or 'sales' not in pl_data.columns:
                logger.warning("Margin Expansion calculation: Missing net_profit or sales data")
                return None
            
            # Calculate margins for each period
            margins = []
            for _, row in pl_data.iterrows():
                net_profit = row.get('net_profit')
                sales = row.get('sales')
                
                if net_profit is not None and sales is not None and not pd.isna(net_profit) and not pd.isna(sales):
                    if sales != 0:
                        margin = (net_profit / sales) * 100
                        margins.append(margin)
            
            if len(margins) < 2:
                logger.warning("Margin Expansion calculation: Insufficient valid margin data points")
                return None
            
            # Calculate expansion
            earliest_margin = margins[0]
            latest_margin = margins[-1]
            expansion = latest_margin - earliest_margin
            
            logger.debug(f"Margin Expansion calculated: {expansion:.2f} percentage points")
            return round(expansion, 2)
            
        except Exception as e:
            logger.error(f"Margin Expansion calculation failed: {str(e)}")
            return None

    def _fetch_profit_loss_data(self, company_id: str, periods: List[str]) -> pd.DataFrame:
        """
        Fetch profit & loss data for multiple periods from database.
        
        Parameters
        ----------
        company_id : str
            Company identifier
        periods : List[str]
            List of financial periods
            
        Returns
        -------
        pd.DataFrame
            Profit & Loss data for the company across multiple periods
        """
        try:
            conn = get_connection()
            
            # Build query with IN clause for multiple periods
            placeholders = ','.join(['?' for _ in periods])
            query = f"""
                SELECT * FROM profit_loss 
                WHERE company_id = ? AND period IN ({placeholders})
                ORDER BY period
            """
            
            params = [company_id] + periods
            df = pd.read_sql_query(query, conn, params=params)
            
            return df
        except Exception as e:
            logger.error(f"Failed to fetch P&L data: {str(e)}")
            return pd.DataFrame()

    def get_kpi_descriptions(self) -> Dict[str, str]:
        """
        Get descriptions for all growth KPIs.
        
        Returns
        -------
        Dict[str, str]
            Dictionary mapping KPI names to their descriptions
        """
        return {
            "revenue_cagr": "Revenue CAGR - compound annual growth rate of revenue over time",
            "profit_cagr": "Profit CAGR - compound annual growth rate of net profit over time",
            "eps_cagr": "EPS CAGR - compound annual growth rate of earnings per share over time",
            "margin_expansion": "Margin Expansion - change in net profit margin percentage over time",
        }

    def get_kpi_formulas(self) -> Dict[str, str]:
        """
        Get formulas for all growth KPIs.
        
        Returns
        -------
        Dict[str, str]
            Dictionary mapping KPI names to their formulas
        """
        return {
            "revenue_cagr": "Revenue CAGR = (Ending Revenue / Beginning Revenue)^(1/n) - 1, where n = number of years",
            "profit_cagr": "Profit CAGR = (Ending Profit / Beginning Profit)^(1/n) - 1, where n = number of years",
            "eps_cagr": "EPS CAGR = (Ending EPS / Beginning EPS)^(1/n) - 1, where n = number of years",
            "margin_expansion": "Margin Expansion = Latest Net Profit Margin - Earliest Net Profit Margin",
        }