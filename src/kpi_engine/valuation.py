"""
valuation.py

Valuation KPI calculations for the N100 Financial Intelligence Platform.

This module provides functions to calculate various valuation metrics
that measure a company's market value and investment attractiveness.

KPIs Calculated:
- EPS (Earnings Per Share)
- PE Ratio (Price to Earnings)
- PB Ratio (Price to Book)
- EV/EBITDA
- Dividend Yield
"""

import logging
from typing import Optional, Dict, Any
import pandas as pd

from src.config.logging_config import get_logger
from src.database.connection import get_connection

logger = get_logger(__name__)


class ValuationCalculator:
    """
    Calculates valuation KPIs from financial data.
    
    This class provides methods to calculate various valuation metrics
    based on financial statements and market data to assess company value.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the ValuationCalculator.
        
        Parameters
        ----------
        db_path : str, optional
            Path to SQLite database. If None, uses default connection.
        """
        self.db_path = db_path
        logger.info("ValuationCalculator initialized")

    def calculate_all(self, company_id: str, period: str) -> Dict[str, Any]:
        """
        Calculate all valuation KPIs for a company in a specific period.
        
        Parameters
        ----------
        company_id : str
            Company identifier
        period : str
            Financial period (e.g., '2024-Q1', 'FY2024')
            
        Returns
        -------
        Dict[str, Any]
            Dictionary containing all calculated valuation KPIs
        """
        logger.info(f"Calculating valuation KPIs for {company_id}, period {period}")
        
        # Fetch required data
        pl_data = self._fetch_profit_loss_data(company_id, period)
        bs_data = self._fetch_balance_sheet_data(company_id, period)
        mc_data = self._fetch_market_cap_data(company_id, period)
        
        if pl_data.empty or bs_data.empty:
            logger.warning(f"Insufficient financial data for {company_id}, period {period}")
            return {}
        
        # Calculate all KPIs
        results = {
            "company_id": company_id,
            "period": period,
            "eps": self.calculate_eps(pl_data, bs_data),
            "pe_ratio": self.calculate_pe_ratio(pl_data, mc_data),
            "pb_ratio": self.calculate_pb_ratio(bs_data, mc_data),
            "ev_ebitda": self.calculate_ev_ebitda(bs_data, pl_data, mc_data),
            "dividend_yield": self.calculate_dividend_yield(pl_data, mc_data),
        }
        
        logger.info(f"Calculated {len([v for v in results.values() if v is not None])} valuation KPIs")
        return results

    def calculate_eps(self, pl_data: pd.DataFrame, bs_data: pd.DataFrame) -> Optional[float]:
        """
        Calculate Earnings Per Share (EPS).
        
        Formula: EPS = Net Profit / Number of Shares Outstanding
        Note: Using share_capital as proxy for shares if shares_outstanding not available
        
        Parameters
        ----------
        pl_data : pd.DataFrame
            Profit & Loss data
        bs_data : pd.DataFrame
            Balance Sheet data
            
        Returns
        -------
        Optional[float]
            EPS value, or None if calculation not possible
        """
        try:
            # Check if dataframes are empty
            if pl_data.empty or bs_data.empty:
                logger.warning("EPS calculation: Empty dataframes provided")
                return None
            
            net_profit = pl_data.get('net_profit', pd.Series([None])).iloc[0]
            
            # Try to get shares outstanding, otherwise use share_capital as proxy
            shares = bs_data.get('shares_outstanding', None)
            if shares is None or (hasattr(shares, 'isna') and shares.isna().all()):
                # Use share_capital as rough proxy (assuming face_value of 1)
                shares = bs_data.get('share_capital', pd.Series([None]))
            
            # Safely get the first value
            shares = shares.iloc[0] if shares is not None and len(shares) > 0 else None
            
            if net_profit is None or shares is None or pd.isna(net_profit) or pd.isna(shares):
                logger.warning("EPS calculation: Missing net_profit or shares data")
                return None
            
            if shares == 0:
                logger.warning("EPS calculation: Shares outstanding is zero")
                return None
            
            eps = net_profit / shares
            logger.debug(f"EPS calculated: {eps:.2f}")
            return round(eps, 2)
            
        except IndexError as e:
            logger.error(f"EPS calculation failed - IndexError (empty dataframe): {str(e)}")
            return None
        except Exception as e:
            logger.error(f"EPS calculation failed: {str(e)}")
            return None

    def calculate_pe_ratio(self, pl_data: pd.DataFrame, mc_data: pd.DataFrame) -> Optional[float]:
        """
        Calculate Price to Earnings (PE) Ratio.
        
        Formula: PE Ratio = Market Price per Share / EPS
        Note: Using market_cap and shares to derive price
        
        Parameters
        ----------
        pl_data : pd.DataFrame
            Profit & Loss data
        mc_data : pd.DataFrame
            Market Cap data
            
        Returns
        -------
        Optional[float]
            PE Ratio value, or None if calculation not possible
        """
        try:
            # Check if dataframes are empty
            if pl_data.empty or mc_data.empty:
                logger.warning("PE Ratio calculation: Empty dataframes provided")
                return None
            
            # Get EPS - pass bs_data (we'll use share_capital from balance sheet if needed)
            # For PE ratio, we need shares from market_cap or balance sheet
            eps = self.calculate_eps(pl_data, mc_data)
            if eps is None or eps == 0:
                logger.warning("PE Ratio calculation: EPS is zero or not available")
                return None
            
            # Get market cap and derive price per share
            market_cap = mc_data.get('market_cap', pd.Series([None])).iloc[0]
            shares = mc_data.get('shares_outstanding', None)
            if shares is None or (hasattr(shares, 'isna') and shares.isna().all()):
                shares = mc_data.get('share_capital', pd.Series([None]))
            shares = shares.iloc[0] if shares is not None and len(shares) > 0 else None
            
            if market_cap is None or shares is None or pd.isna(market_cap) or pd.isna(shares):
                logger.warning("PE Ratio calculation: Missing market_cap or shares data")
                return None
            
            if shares == 0:
                logger.warning("PE Ratio calculation: Shares is zero")
                return None
            
            price_per_share = market_cap / shares
            pe_ratio = price_per_share / eps
            
            logger.debug(f"PE Ratio calculated: {pe_ratio:.2f}")
            return round(pe_ratio, 2)
            
        except IndexError as e:
            logger.error(f"PE Ratio calculation failed - IndexError (empty dataframe): {str(e)}")
            return None
        except Exception as e:
            logger.error(f"PE Ratio calculation failed: {str(e)}")
            return None

    def calculate_pb_ratio(self, bs_data: pd.DataFrame, mc_data: pd.DataFrame) -> Optional[float]:
        """
        Calculate Price to Book (PB) Ratio.
        
        Formula: PB Ratio = Market Price per Share / Book Value per Share
        Note: Book value per share = Book Value / Shares Outstanding
        
        Parameters
        ----------
        bs_data : pd.DataFrame
            Balance Sheet data
        mc_data : pd.DataFrame
            Market Cap data
            
        Returns
        -------
        Optional[float]
            PB Ratio value, or None if calculation not possible
        """
        try:
            # Check if dataframes are empty
            if bs_data.empty or mc_data.empty:
                logger.warning("PB Ratio calculation: Empty dataframes provided")
                return None
            
            # Get book value from balance sheet equity_capital or companies table book_value
            # First try equity_capital from balance sheet
            book_value = bs_data.get('equity_capital', pd.Series([None])).iloc[0]
            
            # If equity_capital not available, we'll need to fetch from companies table
            # For now, use share_capital + reserves as proxy for book value
            if book_value is None or pd.isna(book_value):
                share_capital = bs_data.get('share_capital', pd.Series([0])).iloc[0]
                reserves = bs_data.get('reserves', pd.Series([0])).iloc[0]
                book_value = (share_capital if share_capital and not pd.isna(share_capital) else 0) + \
                            (reserves if reserves and not pd.isna(reserves) else 0)
            
            if book_value is None or pd.isna(book_value) or book_value == 0:
                logger.warning("PB Ratio calculation: Book value is zero or not available")
                return None
            
            # Get market cap and derive price per share
            market_cap = mc_data.get('market_cap', pd.Series([None])).iloc[0]
            shares = mc_data.get('shares_outstanding', None)
            if shares is None or (hasattr(shares, 'isna') and shares.isna().all()):
                shares = mc_data.get('share_capital', pd.Series([None]))
            shares = shares.iloc[0] if shares is not None and len(shares) > 0 else None
            
            if market_cap is None or shares is None or pd.isna(market_cap) or pd.isna(shares):
                logger.warning("PB Ratio calculation: Missing market_cap or shares data")
                return None
            
            if shares == 0:
                logger.warning("PB Ratio calculation: Shares is zero")
                return None
            
            price_per_share = market_cap / shares
            book_value_per_share = book_value / shares
            pb_ratio = price_per_share / book_value_per_share
            
            logger.debug(f"PB Ratio calculated: {pb_ratio:.2f}")
            return round(pb_ratio, 2)
            
        except IndexError as e:
            logger.error(f"PB Ratio calculation failed - IndexError (empty dataframe): {str(e)}")
            return None
        except Exception as e:
            logger.error(f"PB Ratio calculation failed: {str(e)}")
            return None

    def calculate_ev_ebitda(self, bs_data: pd.DataFrame, pl_data: pd.DataFrame, mc_data: pd.DataFrame) -> Optional[float]:
        """
        Calculate EV/EBITDA Ratio.
        
        Formula: EV/EBITDA = Enterprise Value / EBITDA
        Where EBITDA = Operating Profit + Depreciation + Interest
        Note: Using enterprise_value from market_cap table if available
        
        Parameters
        ----------
        bs_data : pd.DataFrame
            Balance Sheet data
        pl_data : pd.DataFrame
            Profit & Loss data
        mc_data : pd.DataFrame
            Market Cap data
            
        Returns
        -------
        Optional[float]
            EV/EBITDA value, or None if calculation not possible
        """
        try:
            # Check if dataframes are empty
            if bs_data.empty or pl_data.empty or mc_data.empty:
                logger.warning("EV/EBITDA calculation: Empty dataframes provided")
                return None
            
            # Try to get enterprise_value directly from market_cap table
            ev = mc_data.get('enterprise_value', None)
            if ev is not None and not ev.isna().all():
                ev = ev.iloc[0] if hasattr(ev, 'iloc') and len(ev) > 0 else ev
            else:
                # Calculate EV = Market Cap + Debt - Cash
                market_cap = mc_data.get('market_cap', pd.Series([None])).iloc[0]
                debt = bs_data.get('borrowings', pd.Series([0])).iloc[0]
                ev = market_cap + debt if market_cap and not pd.isna(market_cap) else None
            
            if ev is None or pd.isna(ev):
                logger.warning("EV/EBITDA calculation: Enterprise value not available")
                return None
            
            # Calculate EBITDA
            operating_profit = pl_data.get('operating_profit', pd.Series([None])).iloc[0]
            depreciation = pl_data.get('depreciation', pd.Series([0])).iloc[0]
            interest = pl_data.get('interest', pd.Series([0])).iloc[0]
            
            if operating_profit is None or pd.isna(operating_profit):
                logger.warning("EV/EBITDA calculation: Missing operating_profit data")
                return None
            
            # EBITDA = Operating Profit + Depreciation + Interest
            depreciation = depreciation if depreciation and not pd.isna(depreciation) else 0
            interest = interest if interest and not pd.isna(interest) else 0
            ebitda = operating_profit + depreciation + interest
            
            if ebitda == 0:
                logger.warning("EV/EBITDA calculation: EBITDA is zero")
                return None
            
            ratio = ev / ebitda
            logger.debug(f"EV/EBITDA calculated: {ratio:.2f}")
            return round(ratio, 2)
            
        except IndexError as e:
            logger.error(f"EV/EBITDA calculation failed - IndexError (empty dataframe): {str(e)}")
            return None
        except Exception as e:
            logger.error(f"EV/EBITDA calculation failed: {str(e)}")
            return None

    def calculate_dividend_yield(self, pl_data: pd.DataFrame, mc_data: pd.DataFrame) -> Optional[float]:
        """
        Calculate Dividend Yield.
        
        Formula: Dividend Yield = (Annual Dividend per Share / Market Price per Share) × 100
        Note: Using dividend_payout from P&L and market_cap to derive price
        
        Parameters
        ----------
        pl_data : pd.DataFrame
            Profit & Loss data
        mc_data : pd.DataFrame
            Market Cap data
            
        Returns
        -------
        Optional[float]
            Dividend Yield percentage, or None if calculation not possible
        """
        try:
            # Check if dataframes are empty
            if pl_data.empty or mc_data.empty:
                logger.warning("Dividend Yield calculation: Empty dataframes provided")
                return None
            
            # Get dividend payout
            dividend = pl_data.get('dividend_payout', pd.Series([None])).iloc[0]
            
            if dividend is None or pd.isna(dividend):
                logger.warning("Dividend Yield calculation: Missing dividend_payout data")
                return None
            
            # Get market cap and derive price per share
            market_cap = mc_data.get('market_cap', pd.Series([None])).iloc[0]
            shares = mc_data.get('shares_outstanding', None)
            if shares is None or (hasattr(shares, 'isna') and shares.isna().all()):
                shares = mc_data.get('share_capital', pd.Series([None]))
            shares = shares.iloc[0] if shares is not None and len(shares) > 0 else None
            
            if market_cap is None or shares is None or pd.isna(market_cap) or pd.isna(shares):
                logger.warning("Dividend Yield calculation: Missing market_cap or shares data")
                return None
            
            if shares == 0:
                logger.warning("Dividend Yield calculation: Shares is zero")
                return None
            
            price_per_share = market_cap / shares
            dividend_per_share = dividend / shares if shares > 0 else 0
            
            if price_per_share == 0:
                logger.warning("Dividend Yield calculation: Price per share is zero")
                return None
            
            yield_pct = (dividend_per_share / price_per_share) * 100
            logger.debug(f"Dividend Yield calculated: {yield_pct:.2f}%")
            return round(yield_pct, 2)
            
        except IndexError as e:
            logger.error(f"Dividend Yield calculation failed - IndexError (empty dataframe): {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Dividend Yield calculation failed: {str(e)}")
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

    def _fetch_market_cap_data(self, company_id: str, period: str) -> pd.DataFrame:
        """
        Fetch market cap data from database.
        
        Parameters
        ----------
        company_id : str
            Company identifier
        period : str
            Financial period
            
        Returns
        -------
        pd.DataFrame
            Market Cap data for the company and period
        """
        try:
            conn = get_connection()
            query = """
                SELECT * FROM market_cap 
                WHERE company_id = ? AND period = ?
                LIMIT 1
            """
            df = pd.read_sql_query(query, conn, params=(company_id, period))
            return df
        except Exception as e:
            logger.error(f"Failed to fetch Market Cap data: {str(e)}")
            return pd.DataFrame()

    def get_kpi_descriptions(self) -> Dict[str, str]:
        """
        Get descriptions for all valuation KPIs.
        
        Returns
        -------
        Dict[str, str]
            Dictionary mapping KPI names to their descriptions
        """
        return {
            "eps": "Earnings Per Share - company's profit allocated to each outstanding share",
            "pe_ratio": "Price to Earnings Ratio - measures current share price relative to earnings per share",
            "pb_ratio": "Price to Book Ratio - measures current share price relative to book value per share",
            "ev_ebitda": "EV/EBITDA - measures a company's total value relative to its operating cash flow",
            "dividend_yield": "Dividend Yield - annual dividend payment expressed as percentage of share price",
        }

    def get_kpi_formulas(self) -> Dict[str, str]:
        """
        Get formulas for all valuation KPIs.
        
        Returns
        -------
        Dict[str, str]
            Dictionary mapping KPI names to their formulas
        """
        return {
            "eps": "EPS = Net Profit / Number of Shares Outstanding",
            "pe_ratio": "PE Ratio = Market Price per Share / EPS",
            "pb_ratio": "PB Ratio = Market Price per Share / Book Value per Share",
            "ev_ebitda": "EV/EBITDA = Enterprise Value / EBITDA, where EBITDA = Operating Profit + Depreciation + Interest",
            "dividend_yield": "Dividend Yield = (Annual Dividend per Share / Market Price per Share) × 100",
        }