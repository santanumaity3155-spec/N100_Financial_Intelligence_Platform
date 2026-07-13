"""
cashflow.py

Cash Flow KPI calculations for the N100 Financial Intelligence Platform.

This module provides functions to calculate various cash flow metrics
that measure a company's cash generation and management.

KPIs Calculated:
- Operating Cash Flow
- Free Cash Flow
- Cash Conversion Ratio
"""

import logging
from typing import Optional, Dict, Any
import pandas as pd

from src.config.logging_config import get_logger
from src.database.connection import get_connection

logger = get_logger(__name__)


class CashFlowCalculator:
    """
    Calculates cash flow KPIs from financial data.
    
    This class provides methods to calculate various cash flow metrics
    based on cash flow statements to assess cash generation and management.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the CashFlowCalculator.
        
        Parameters
        ----------
        db_path : str, optional
            Path to SQLite database. If None, uses default connection.
        """
        self.db_path = db_path
        logger.info("CashFlowCalculator initialized")

    def calculate_all(self, company_id: str, period: str) -> Dict[str, Any]:
        """
        Calculate all cash flow KPIs for a company in a specific period.
        
        Parameters
        ----------
        company_id : str
            Company identifier
        period : str
            Financial period (e.g., '2024-Q1', 'FY2024')
            
        Returns
        -------
        Dict[str, Any]
            Dictionary containing all calculated cash flow KPIs
        """
        logger.info(f"Calculating cash flow KPIs for {company_id}, period {period}")
        
        # Fetch required data
        cf_data = self._fetch_cash_flow_data(company_id, period)
        pl_data = self._fetch_profit_loss_data(company_id, period)
        
        if cf_data.empty or pl_data.empty:
            logger.warning(f"Insufficient data for {company_id}, period {period}")
            return {}
        
        # Calculate all KPIs
        results = {
            "company_id": company_id,
            "period": period,
            "operating_cash_flow": self.calculate_operating_cash_flow(cf_data),
            "free_cash_flow": self.calculate_free_cash_flow(cf_data),
            "cash_conversion_ratio": self.calculate_cash_conversion_ratio(cf_data, pl_data),
        }
        
        logger.info(f"Calculated {len([v for v in results.values() if v is not None])} cash flow KPIs")
        return results

    def calculate_operating_cash_flow(self, cf_data: pd.DataFrame) -> Optional[float]:
        """
        Calculate Operating Cash Flow.
        
        Formula: Operating Cash Flow = Cash from Operating Activities
        
        Parameters
        ----------
        cf_data : pd.DataFrame
            Cash Flow data
            
        Returns
        -------
        Optional[float]
            Operating Cash Flow value, or None if calculation not possible
        """
        try:
            ocf = cf_data.get('cash_from_operating_activity', pd.Series([None])).iloc[0]
            
            if ocf is None or pd.isna(ocf):
                logger.warning("Operating Cash Flow calculation: Missing cash_from_operating_activity data")
                return None
            
            logger.debug(f"Operating Cash Flow calculated: {ocf:.2f}")
            return round(ocf, 2)
            
        except Exception as e:
            logger.error(f"Operating Cash Flow calculation failed: {str(e)}")
            return None

    def calculate_free_cash_flow(self, cf_data: pd.DataFrame) -> Optional[float]:
        """
        Calculate Free Cash Flow.
        
        Formula: Free Cash Flow = Operating Cash Flow - Capital Expenditures
        Note: Using free_cash_flow column if available, otherwise calculating from components
        
        Parameters
        ----------
        cf_data : pd.DataFrame
            Cash Flow data
            
        Returns
        -------
        Optional[float]
            Free Cash Flow value, or None if calculation not possible
        """
        try:
            # Try to get free_cash_flow directly if available
            fcf = cf_data.get('free_cash_flow', None)
            if fcf is not None and not fcf.isna().all():
                fcf = fcf.iloc[0]
                if not pd.isna(fcf):
                    logger.debug(f"Free Cash Flow calculated from direct value: {fcf:.2f}")
                    return round(fcf, 2)
            
            # Otherwise calculate: Operating CF - Capital Expenditures
            ocf = cf_data.get('cash_from_operating_activity', pd.Series([None])).iloc[0]
            capex = cf_data.get('cash_from_investing_activity', pd.Series([0])).iloc[0]
            
            if ocf is None or pd.isna(ocf):
                logger.warning("Free Cash Flow calculation: Missing operating cash flow data")
                return None
            
            # Capex is typically negative (cash outflow), so we add it
            capex = capex if capex and not pd.isna(capex) else 0
            fcf = ocf + abs(capex) if capex < 0 else ocf - capex
            
            logger.debug(f"Free Cash Flow calculated: {fcf:.2f}")
            return round(fcf, 2)
            
        except Exception as e:
            logger.error(f"Free Cash Flow calculation failed: {str(e)}")
            return None

    def calculate_cash_conversion_ratio(self, cf_data: pd.DataFrame, pl_data: pd.DataFrame) -> Optional[float]:
        """
        Calculate Cash Conversion Ratio.
        
        Formula: Cash Conversion Ratio = Operating Cash Flow / Net Profit
        Measures how efficiently a company converts net profit into cash
        
        Parameters
        ----------
        cf_data : pd.DataFrame
            Cash Flow data
        pl_data : pd.DataFrame
            Profit & Loss data
            
        Returns
        -------
        Optional[float]
            Cash Conversion Ratio value, or None if calculation not possible
        """
        try:
            ocf = cf_data.get('cash_from_operating_activity', pd.Series([None])).iloc[0]
            net_profit = pl_data.get('net_profit', pd.Series([None])).iloc[0]
            
            if ocf is None or net_profit is None or pd.isna(ocf) or pd.isna(net_profit):
                logger.warning("Cash Conversion Ratio calculation: Missing OCF or net profit data")
                return None
            
            if net_profit == 0:
                logger.warning("Cash Conversion Ratio calculation: Net profit is zero")
                return None
            
            ratio = ocf / net_profit
            logger.debug(f"Cash Conversion Ratio calculated: {ratio:.2f}")
            return round(ratio, 2)
            
        except Exception as e:
            logger.error(f"Cash Conversion Ratio calculation failed: {str(e)}")
            return None

    def _fetch_cash_flow_data(self, company_id: str, period: str) -> pd.DataFrame:
        """
        Fetch cash flow data from database.
        
        Parameters
        ----------
        company_id : str
            Company identifier
        period : str
            Financial period
            
        Returns
        -------
        pd.DataFrame
            Cash Flow data for the company and period
        """
        try:
            conn = get_connection()
            query = """
                SELECT * FROM cash_flow 
                WHERE company_id = ? AND period = ?
                LIMIT 1
            """
            df = pd.read_sql_query(query, conn, params=(company_id, period))
            return df
        except Exception as e:
            logger.error(f"Failed to fetch Cash Flow data: {str(e)}")
            return pd.DataFrame()

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

    def get_kpi_descriptions(self) -> Dict[str, str]:
        """
        Get descriptions for all cash flow KPIs.
        
        Returns
        -------
        Dict[str, str]
            Dictionary mapping KPI names to their descriptions
        """
        return {
            "operating_cash_flow": "Operating Cash Flow - cash generated from core business operations",
            "free_cash_flow": "Free Cash Flow - cash available after capital expenditures",
            "cash_conversion_ratio": "Cash Conversion Ratio - measures how efficiently net profit is converted to cash",
        }

    def get_kpi_formulas(self) -> Dict[str, str]:
        """
        Get formulas for all cash flow KPIs.
        
        Returns
        -------
        Dict[str, str]
            Dictionary mapping KPI names to their formulas
        """
        return {
            "operating_cash_flow": "Operating Cash Flow = Cash from Operating Activities",
            "free_cash_flow": "Free Cash Flow = Operating Cash Flow - Capital Expenditures",
            "cash_conversion_ratio": "Cash Conversion Ratio = Operating Cash Flow / Net Profit",
        }