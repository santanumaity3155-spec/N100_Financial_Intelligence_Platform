"""
Database utility module for N100 Financial Intelligence Platform.

This module provides database connection management and query functions
for accessing financial data from the SQLite database.

All query functions are cached using Streamlit's cache_data decorator
with a TTL of 600 seconds (10 minutes) for optimal performance.
"""

import logging
import sqlite3
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

import pandas as pd
import streamlit as st

# Configure module logger
logger = logging.getLogger(__name__)

# Database path configuration
# Try multiple possible locations for the database
DB_PATHS = [
    Path("data/database/n100.db"),
    Path("data/database/nifty100.db"),
    Path("data/nifty100.db"),
    Path("nifty100.db"),
    Path("data/database/financial_data.db"),
]


def find_database() -> Optional[Path]:
    """
    Find the database file by checking multiple possible locations.

    Returns:
        Path object to the database file, or None if not found.
    """
    for db_path in DB_PATHS:
        if db_path.exists() and db_path.is_file():
            logger.info(f"Database found at: {db_path.absolute()}")
            return db_path
    
    logger.warning("Database file not found in any of the expected locations")
    return None


# Global database path
DB_PATH = find_database()


@contextmanager
def get_connection():
    """
    Context manager for database connections.
    
    Provides safe connection creation and automatic closing.
    Uses singleton pattern for connection reuse within the same session.
    
    Yields:
        sqlite3.Connection: Database connection object
        
    Raises:
        sqlite3.Error: If database connection fails
        
    Example:
        with get_connection() as conn:
            df = pd.read_sql_query("SELECT * FROM companies", conn)
    """
    conn = None
    try:
        if DB_PATH is None:
            raise sqlite3.Error("Database file not found. Please ensure the database exists.")
        
        logger.debug("Opening database connection")
        start_time = time.time()
        
        conn = sqlite3.connect(
            str(DB_PATH),
            check_same_thread=False,  # Allow multi-threading for Streamlit
            timeout=30  # 30 second timeout for long queries
        )
        
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        
        # Set row factory for dict-like access
        conn.row_factory = sqlite3.Row
        
        elapsed = time.time() - start_time
        logger.info(f"Database connection opened successfully in {elapsed:.3f}s")
        
        yield conn
        
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {str(e)}", exc_info=True)
        raise
    finally:
        if conn:
            try:
                conn.close()
                logger.debug("Database connection closed")
            except Exception as e:
                logger.error(f"Error closing database connection: {str(e)}")


@st.cache_data(ttl=600)
def get_companies() -> pd.DataFrame:
    """
    Retrieve company master data from the database.
    
    Returns:
        pd.DataFrame: DataFrame containing company information with columns:
            - ticker: Company ticker symbol (company_id)
            - name: Company name (company_name)
            - sector: Sector classification
            - industry: Industry classification
            - isin: ISIN number (isin_code)
            - listed_date: Date of listing
             
    Returns empty DataFrame if:
        - Database is unavailable
        - Table doesn't exist
        - No data found
         
    Example:
        df = get_companies()
        print(df.head())
    """
    logger.info("Executing query: get_companies()")
    start_time = time.time()
    
    try:
        with get_connection() as conn:
            query = """
                SELECT 
                    company_id as ticker,
                    company_name as name,
                    sector,
                    industry,
                    isin_code as isin,
                    listed_date
                FROM companies
                ORDER BY company_id
            """
            
            df = pd.read_sql_query(query, conn)
            
            elapsed = time.time() - start_time
            logger.info(f"Query executed successfully in {elapsed:.3f}s, returned {len(df)} rows")
            
            return df
            
    except sqlite3.Error as e:
        logger.error(f"Error in get_companies(): {str(e)}", exc_info=True)
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Unexpected error in get_companies(): {str(e)}", exc_info=True)
        return pd.DataFrame()


@st.cache_data(ttl=600)
def get_ratios(ticker: str, year: Optional[int] = None) -> pd.DataFrame:
    """
    Retrieve financial ratios for a specific company.
    
    Args:
        ticker: Company ticker symbol (e.g., 'RELIANCE', 'TCS')
        year: Optional year filter (e.g., 2024). If None, returns all years.
    
    Returns:
        pd.DataFrame: DataFrame containing financial ratios with columns:
            - ticker: Company ticker
            - year: Financial year
            - pe_ratio: Price to Earnings ratio (from financial_kpis)
            - pb_ratio: Price to Book ratio (from financial_kpis)
            - roe: Return on Equity
            - roa: Return on Assets
            - debt_equity: Debt to Equity ratio
            - current_ratio: Current ratio
            - And other financial metrics
             
    Returns empty DataFrame if:
        - Ticker is missing or empty
        - No data found for the ticker
        - Database is unavailable
         
    Example:
        df = get_ratios('RELIANCE', year=2024)
    """
    logger.info(f"Executing query: get_ratios(ticker={ticker}, year={year})")
    start_time = time.time()
    
    # Validate input
    if not ticker or not isinstance(ticker, str):
        logger.warning(f"Invalid ticker provided: {ticker}")
        return pd.DataFrame()
    
    ticker = ticker.strip().upper()
    
    try:
        with get_connection() as conn:
            # Base query - pe_ratio and pb_ratio are in financial_kpis, not financial_ratios
            # Note: financial_ratios uses 'period' column (e.g., 'Mar 2024'), not 'year'
            query = """
                SELECT 
                    r.company_id as ticker,
                    r.period as year,
                    r.roe,
                    r.roa,
                    r.debt_to_equity as debt_equity,
                    r.current_ratio,
                    r.quick_ratio,
                    r.dividend_yield,
                    k.pe_ratio,
                    k.pb_ratio,
                    k.net_profit_margin,
                    k.operating_margin,
                    k.gross_margin,
                    k.interest_coverage,
                    k.asset_turnover,
                    k.inventory_turnover,
                    k.revenue_cagr as revenue_growth,
                    k.profit_cagr as profit_growth,
                    k.eps,
                    k.ev_ebitda
                FROM financial_ratios r
                LEFT JOIN financial_kpis k ON r.company_id = k.company_id AND r.period = k.period
                WHERE r.company_id = ?
            """
            params = [ticker]
            
            # Add year filter if provided (convert int year to period format)
            if year is not None:
                # Try to match year to period format (e.g., 2024 -> 'Mar 2024')
                # This is a best-effort match since period format varies
                query += " AND r.period LIKE ?"
                params.append(f"%{year}%")
            
            query += " ORDER BY r.period DESC"
            
            df = pd.read_sql_query(query, conn, params=params)
            
            elapsed = time.time() - start_time
            
            if df.empty:
                logger.warning(f"No ratio data found for ticker: {ticker}, year: {year}")
            else:
                logger.info(f"Query executed successfully in {elapsed:.3f}s, returned {len(df)} rows")
            
            return df
            
    except sqlite3.Error as e:
        logger.error(f"Database error in get_ratios() for {ticker}: {str(e)}", exc_info=True)
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Unexpected error in get_ratios() for {ticker}: {str(e)}", exc_info=True)
        return pd.DataFrame()


@st.cache_data(ttl=600)
def get_pl(ticker: str) -> pd.DataFrame:
    """
    Retrieve Profit and Loss statement for a specific company.
    
    Args:
        ticker: Company ticker symbol (e.g., 'RELIANCE', 'TCS')
    
    Returns:
        pd.DataFrame: DataFrame containing Profit & Loss data with columns:
            - ticker: Company ticker (company_id)
            - year: Financial year (period)
            - sales: Total sales
            - operating_profit: Operating profit
            - net_profit: Net profit
            - And other P&L line items
            
    Returns empty DataFrame if:
        - Ticker is missing or empty
        - No data found for the ticker
        - Database is unavailable
        
    Example:
        df = get_pl('RELIANCE')
    """
    logger.info(f"Executing query: get_pl(ticker={ticker})")
    start_time = time.time()
    
    # Validate input
    if not ticker or not isinstance(ticker, str):
        logger.warning(f"Invalid ticker provided: {ticker}")
        return pd.DataFrame()
    
    ticker = ticker.strip().upper()
    
    try:
        with get_connection() as conn:
            # Note: profit_loss table uses 'company_id' and 'period' columns
            query = """
                SELECT 
                    company_id as ticker,
                    period as year,
                    sales,
                    expenses,
                    operating_profit,
                    opm_percentage,
                    other_income,
                    interest,
                    depreciation,
                    profit_before_tax,
                    tax_percentage,
                    net_profit,
                    eps,
                    dividend_payout
                FROM profit_loss
                WHERE company_id = ?
                ORDER BY period DESC
            """
            
            df = pd.read_sql_query(query, conn, params=[ticker])
            
            elapsed = time.time() - start_time
            
            if df.empty:
                logger.warning(f"No P&L data found for ticker: {ticker}")
            else:
                logger.info(f"Query executed successfully in {elapsed:.3f}s, returned {len(df)} rows")
            
            return df
            
    except sqlite3.Error as e:
        logger.error(f"Database error in get_pl() for {ticker}: {str(e)}", exc_info=True)
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Unexpected error in get_pl() for {ticker}: {str(e)}", exc_info=True)
        return pd.DataFrame()


@st.cache_data(ttl=600)
def get_bs(ticker: str) -> pd.DataFrame:
    """
    Retrieve Balance Sheet data for a specific company.
    
    Args:
        ticker: Company ticker symbol (e.g., 'RELIANCE', 'TCS')
    
    Returns:
        pd.DataFrame: DataFrame containing Balance Sheet data with columns:
            - ticker: Company ticker (company_id)
            - year: Financial year (period)
            - total_assets: Total assets
            - total_liabilities: Total liabilities
            - And other balance sheet items
            
    Returns empty DataFrame if:
        - Ticker is missing or empty
        - No data found for the ticker
        - Database is unavailable
        
    Example:
        df = get_bs('RELIANCE')
    """
    logger.info(f"Executing query: get_bs(ticker={ticker})")
    start_time = time.time()
    
    # Validate input
    if not ticker or not isinstance(ticker, str):
        logger.warning(f"Invalid ticker provided: {ticker}")
        return pd.DataFrame()
    
    ticker = ticker.strip().upper()
    
    try:
        with get_connection() as conn:
            # Note: balance_sheet table uses 'company_id' and 'period' columns
            query = """
                SELECT 
                    company_id as ticker,
                    period as year,
                    share_capital,
                    reserves,
                    borrowings,
                    other_liabilities,
                    total_liabilities,
                    fixed_assets,
                    cwip,
                    investments,
                    other_assets,
                    total_assets,
                    equity_capital
                FROM balance_sheet
                WHERE company_id = ?
                ORDER BY period DESC
            """
            
            df = pd.read_sql_query(query, conn, params=[ticker])
            
            elapsed = time.time() - start_time
            
            if df.empty:
                logger.warning(f"No balance sheet data found for ticker: {ticker}")
            else:
                logger.info(f"Query executed successfully in {elapsed:.3f}s, returned {len(df)} rows")
            
            return df
            
    except sqlite3.Error as e:
        logger.error(f"Database error in get_bs() for {ticker}: {str(e)}", exc_info=True)
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Unexpected error in get_bs() for {ticker}: {str(e)}", exc_info=True)
        return pd.DataFrame()


@st.cache_data(ttl=600)
def get_cf(ticker: str) -> pd.DataFrame:
    """
    Retrieve Cash Flow statement for a specific company.
    
    Args:
        ticker: Company ticker symbol (e.g., 'RELIANCE', 'TCS')
    
    Returns:
        pd.DataFrame: DataFrame containing Cash Flow data with columns:
            - ticker: Company ticker (company_id)
            - year: Financial year (period)
            - operating_activity: Cash from operating activities
            - investing_activity: Cash from investing activities
            - financing_activity: Cash from financing activities
            - free_cash_flow: Free cash flow
            - net_cash_flow: Net change in cash
            - And other cash flow items
            
    Returns empty DataFrame if:
        - Ticker is missing or empty
        - No data found for the ticker
        - Database is unavailable
        
    Example:
        df = get_cf('RELIANCE')
    """
    logger.info(f"Executing query: get_cf(ticker={ticker})")
    start_time = time.time()
    
    # Validate input
    if not ticker or not isinstance(ticker, str):
        logger.warning(f"Invalid ticker provided: {ticker}")
        return pd.DataFrame()
    
    ticker = ticker.strip().upper()
    
    try:
        with get_connection() as conn:
            # Note: cash_flow table uses 'company_id' and 'period' columns
            query = """
                SELECT 
                    company_id as ticker,
                    period as year,
                    cash_from_operating_activity,
                    cash_from_investing_activity,
                    cash_from_financing_activity,
                    free_cash_flow,
                    net_cash_flow,
                    operating_activity,
                    investing_activity,
                    financing_activity
                FROM cash_flow
                WHERE company_id = ?
                ORDER BY period DESC
            """
            
            df = pd.read_sql_query(query, conn, params=[ticker])
            
            elapsed = time.time() - start_time
            
            if df.empty:
                logger.warning(f"No cash flow data found for ticker: {ticker}")
            else:
                logger.info(f"Query executed successfully in {elapsed:.3f}s, returned {len(df)} rows")
            
            return df
            
    except sqlite3.Error as e:
        logger.error(f"Database error in get_cf() for {ticker}: {str(e)}", exc_info=True)
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Unexpected error in get_cf() for {ticker}: {str(e)}", exc_info=True)
        return pd.DataFrame()


@st.cache_data(ttl=600)
def get_sectors() -> pd.DataFrame:
    """
    Retrieve sector information from the database.
    
    Returns:
        pd.DataFrame: DataFrame containing sector information with columns:
            - sector_id: Unique sector identifier
            - sector_name: Name of the sector
            - sector_code: Sector code
            - company_count: Number of companies in sector
            - market_cap_total: Total market cap of sector
            
    Returns empty DataFrame if:
        - Table doesn't exist
        - No data found
        - Database is unavailable
        
    Example:
        df = get_sectors()
    """
    logger.info("Executing query: get_sectors()")
    start_time = time.time()
    
    try:
        with get_connection() as conn:
            query = """
                SELECT 
                    sector_id,
                    sector_name,
                    sector_code,
                    company_count,
                    market_cap_total
                FROM sectors
                ORDER BY sector_name
            """
            
            df = pd.read_sql_query(query, conn)
            
            elapsed = time.time() - start_time
            
            if df.empty:
                logger.warning("No sector data found")
            else:
                logger.info(f"Query executed successfully in {elapsed:.3f}s, returned {len(df)} rows")
            
            return df
            
    except sqlite3.Error as e:
        logger.error(f"Database error in get_sectors(): {str(e)}", exc_info=True)
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Unexpected error in get_sectors(): {str(e)}", exc_info=True)
        return pd.DataFrame()


@st.cache_data(ttl=600)
def get_peers(group_name: str) -> pd.DataFrame:
    """
    Retrieve peer group information.
    
    Args:
        group_name: Name of the peer group (e.g., 'IT Services', 'Banking')
    
    Returns:
        pd.DataFrame: DataFrame containing peer group data with columns:
            - group_name: Peer group name
            - ticker: Company ticker
            - company_name: Company name
            - sector: Company sector
            - market_cap: Market capitalization
            - rank: Rank within peer group
            
    Returns empty DataFrame if:
        - group_name is missing or empty
        - No data found for the group
        - Database is unavailable
        
    Example:
        df = get_peers('IT Services')
    """
    logger.info(f"Executing query: get_peers(group_name={group_name})")
    start_time = time.time()
    
    # Validate input
    if not group_name or not isinstance(group_name, str):
        logger.warning(f"Invalid group_name provided: {group_name}")
        return pd.DataFrame()
    
    group_name = group_name.strip()
    
    try:
        with get_connection() as conn:
            query = """
                SELECT 
                    group_name,
                    ticker,
                    company_name,
                    sector,
                    market_cap,
                    rank
                FROM peer_groups
                WHERE group_name = ?
                ORDER BY rank ASC
            """
            
            df = pd.read_sql_query(query, conn, params=[group_name])
            
            elapsed = time.time() - start_time
            
            if df.empty:
                logger.warning(f"No peer data found for group: {group_name}")
            else:
                logger.info(f"Query executed successfully in {elapsed:.3f}s, returned {len(df)} rows")
            
            return df
            
    except sqlite3.Error as e:
        logger.error(f"Database error in get_peers() for {group_name}: {str(e)}", exc_info=True)
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Unexpected error in get_peers() for {group_name}: {str(e)}", exc_info=True)
        return pd.DataFrame()


@st.cache_data(ttl=600)
def get_valuation(ticker: str) -> pd.DataFrame:
    """
    Retrieve valuation data for a specific company.
    
    Args:
        ticker: Company ticker symbol (e.g., 'RELIANCE', 'TCS')
    
    Returns:
        pd.DataFrame: DataFrame containing valuation metrics with columns:
            - ticker: Company ticker
            - year: Financial year
            - market_cap: Market capitalization
            - enterprise_value: Enterprise value
            - ev_ebitda: EV/EBITDA ratio
            - ev_revenue: EV/Revenue ratio
            - price_to_sales: Price to Sales ratio
            - price_to_book: Price to Book ratio
            - price_to_earnings: Price to Earnings ratio
            - And other valuation metrics
            
    Returns empty DataFrame if:
        - Ticker is missing or empty
        - No data found for the ticker
        - Database is unavailable
        
    Example:
        df = get_valuation('RELIANCE')
    """
    logger.info(f"Executing query: get_valuation(ticker={ticker})")
    start_time = time.time()
    
    # Validate input
    if not ticker or not isinstance(ticker, str):
        logger.warning(f"Invalid ticker provided: {ticker}")
        return pd.DataFrame()
    
    ticker = ticker.strip().upper()
    
    try:
        with get_connection() as conn:
            query = """
                SELECT 
                    ticker,
                    year,
                    market_cap,
                    enterprise_value,
                    ev_ebitda,
                    ev_revenue,
                    price_to_sales,
                    price_to_book,
                    price_to_earnings,
                    peg_ratio,
                    market_cap_to_sales,
                    market_cap_to_profit,
                    equity_value,
                    net_debt,
                    shares_outstanding
                FROM valuation
                WHERE ticker = ?
                ORDER BY year DESC
            """
            
            df = pd.read_sql_query(query, conn, params=[ticker])
            
            elapsed = time.time() - start_time
            
            if df.empty:
                logger.warning(f"No valuation data found for ticker: {ticker}")
            else:
                logger.info(f"Query executed successfully in {elapsed:.3f}s, returned {len(df)} rows")
            
            return df
            
    except sqlite3.Error as e:
        logger.error(f"Database error in get_valuation() for {ticker}: {str(e)}", exc_info=True)
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Unexpected error in get_valuation() for {ticker}: {str(e)}", exc_info=True)
        return pd.DataFrame()


# =============================================================================
# MODULE 3 - SCREENER & PEER COMPARISON HELPERS
# =============================================================================


def _read_df(query: str, params: Optional[List[Any]] = None) -> pd.DataFrame:
    """
    Execute a read-only SQL query and return a DataFrame.

    Parameters
    ----------
    query : str
        SQL SELECT statement.
    params : Optional[List[Any]], optional
        Query parameters for safe binding, by default None.

    Returns
    -------
    pd.DataFrame
        Query result. Empty DataFrame on any error.
    """
    try:
        with get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params or [])
    except Exception as e:  # pragma: no cover - defensive
        logger.error(f"Database query failed: {str(e)}", exc_info=True)
        return pd.DataFrame()


@st.cache_data(ttl=600)
def get_company_master() -> pd.DataFrame:
    """
    Retrieve company master data using the canonical n100.db schema.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns: company_id, company_name, sector, industry.
    """
    logger.info("Executing query: get_company_master()")
    df = _read_df(
        """
        SELECT company_id, company_name, sector, industry
        FROM companies
        ORDER BY company_name
        """
    )
    logger.info(f"get_company_master() returned {len(df)} rows")
    return df


@st.cache_data(ttl=600)
def get_peer_groups_list() -> List[str]:
    """
    Retrieve the list of all available peer group names.

    Returns
    -------
    List[str]
        Sorted list of distinct peer group names.
    """
    logger.info("Executing query: get_peer_groups_list()")
    df = _read_df(
        """
        SELECT DISTINCT peer_group_name
        FROM peer_groups
        WHERE peer_group_name IS NOT NULL
        ORDER BY peer_group_name
        """
    )
    groups = df["peer_group_name"].dropna().astype(str).tolist() if not df.empty else []
    logger.info(f"get_peer_groups_list() returned {len(groups)} groups")
    return groups


@st.cache_data(ttl=600)
def get_peer_group_companies(group_name: str) -> pd.DataFrame:
    """
    Retrieve companies belonging to a specific peer group.

    Parameters
    ----------
    group_name : str
        Peer group name (e.g., 'IT Services').

    Returns
    -------
    pd.DataFrame
        DataFrame with columns: company_id, is_benchmark, company_name, sector.
    """
    logger.info(f"Executing query: get_peer_group_companies(group_name={group_name})")
    if not group_name or not isinstance(group_name, str):
        return pd.DataFrame()
    df = _read_df(
        """
        SELECT pg.company_id, pg.is_benchmark, c.company_name, c.sector
        FROM peer_groups pg
        LEFT JOIN companies c ON pg.company_id = c.company_id
        WHERE pg.peer_group_name = ?
        ORDER BY pg.is_benchmark DESC, c.company_name
        """,
        params=[group_name],
    )
    logger.info(f"get_peer_group_companies() returned {len(df)} rows")
    return df


@st.cache_data(ttl=600)
def get_all_screener_data(period: str = "Mar 2024") -> pd.DataFrame:
    """
    Build a consolidated screener dataset joining all relevant tables.

    The dataset is assembled from:
    - companies (company_id, company_name, sector, industry)
    - financial_ratios (roe, debt_to_equity)
    - financial_kpis (roce, net_profit_margin, operating_margin, interest_coverage)
    - financial_kpis TTM (revenue_cagr, profit_cagr)
    - financial_health_scores (overall_score as composite quality score, rating)
    - cash_flow (operating_activity + investing_activity = free_cash_flow)
    - market_cap (pe_ratio, pb_ratio, dividend_yield - latest available)

    Parameters
    ----------
    period : str, optional
        Reporting period for annual metrics, by default "Mar 2024".

    Returns
    -------
    pd.DataFrame
        One row per company with all screener metrics.
    """
    logger.info(f"Building consolidated screener dataset for period {period}")
    try:
        with get_connection() as conn:
            companies = pd.read_sql_query(
                "SELECT company_id, company_name, sector, industry FROM companies",
                conn,
            )
            ratios = pd.read_sql_query(
                """
                SELECT company_id, roe, debt_to_equity
                FROM financial_ratios
                WHERE period = ?
                """,
                conn,
                params=[period],
            )
            kpis = pd.read_sql_query(
                """
                SELECT company_id, roce, net_profit_margin, operating_margin,
                       interest_coverage
                FROM financial_kpis
                WHERE period = ?
                """,
                conn,
                params=[period],
            )
            health = pd.read_sql_query(
                """
                SELECT company_id, overall_score, rating
                FROM financial_health_scores
                WHERE period = ?
                """,
                conn,
                params=[period],
            )
            cagr = pd.read_sql_query(
                """
                SELECT company_id, revenue_cagr, profit_cagr
                FROM financial_kpis
                WHERE period = 'TTM'
                """,
                conn,
            )
            cf = pd.read_sql_query(
                """
                SELECT company_id, operating_activity, investing_activity
                FROM cash_flow
                WHERE period IN (?, ?)
                ORDER BY CASE WHEN period = ? THEN 1 ELSE 0 END, company_id
                """,
                conn,
                params=[period, "Mar-24", "Mar-24"],
            )
            cf = cf.drop_duplicates(subset=["company_id"], keep="first").copy()
            cf["free_cash_flow"] = cf["operating_activity"] + cf["investing_activity"]
            valuation = pd.read_sql_query(
                """
                SELECT company_id, pe_ratio, pb_ratio, dividend_yield
                FROM market_cap
                WHERE period = (SELECT MAX(period) FROM market_cap)
                """,
                conn,
            )

        df = companies.merge(ratios, on="company_id", how="left")
        df = df.merge(kpis, on="company_id", how="left")
        df = df.merge(health, on="company_id", how="left")
        df = df.merge(cagr, on="company_id", how="left")
        df = df.merge(cf, on="company_id", how="left")
        df = df.merge(valuation, on="company_id", how="left")

        # Standardized output columns used by the screener/peer pages
        df["composite_quality_score"] = df["overall_score"]
        df["operating_profit_margin"] = df["operating_margin"]
        df["revenue_cagr_5yr"] = df["revenue_cagr"]
        df["pat_cagr_5yr"] = df["profit_cagr"]
        df["ticker"] = df["company_id"]
        df["company"] = df["company_name"]

        drop_cols = [
            "operating_margin", "revenue_cagr", "profit_cagr",
            "overall_score", "operating_activity", "investing_activity",
        ]
        df = df.drop(columns=[c for c in drop_cols if c in df.columns], errors="ignore")

        logger.info(f"Consolidated screener dataset built: {len(df)} rows")
        return df
    except Exception as e:
        logger.error(f"Failed to build screener dataset: {str(e)}", exc_info=True)
        return pd.DataFrame()


@st.cache_data(ttl=600)
def get_peer_group_metrics(period: str = "Mar 2024") -> pd.DataFrame:
    """
    Build a consolidated dataset of peer-group company metrics.

    Combines peer group assignments with the consolidated screener dataset.

    Parameters
    ----------
    period : str, optional
        Reporting period for annual metrics, by default "Mar 2024".

    Returns
    -------
    pd.DataFrame
        One row per company per peer group with all metrics.
    """
    logger.info(f"Building peer group metrics for period {period}")
    try:
        peers = _read_df(
            """
            SELECT pg.company_id, pg.peer_group_name, pg.is_benchmark
            FROM peer_groups pg
            WHERE pg.peer_group_name IS NOT NULL
            ORDER BY pg.peer_group_name, pg.is_benchmark DESC
            """
        )
        screener_df = get_all_screener_data(period)
        if peers.empty or screener_df.empty:
            logger.warning("No peer group or screener data available")
            return pd.DataFrame()
        merged = peers.merge(screener_df, on="company_id", how="left")
        logger.info(f"Peer group metrics built: {len(merged)} rows")
        return merged
    except Exception as e:
        logger.error(f"Failed to build peer group metrics: {str(e)}", exc_info=True)
        return pd.DataFrame()


def get_database_info() -> Dict[str, Any]:
    """
    Get information about the database.
    
    Returns:
        Dict containing database information:
            - path: Database file path
            - exists: Whether database exists
            - size_mb: Database file size in MB
            - tables: List of tables in database
            
    Example:
        info = get_database_info()
        print(f"Database size: {info['size_mb']} MB")
    """
    logger.info("Retrieving database information")
    
    info = {
        "path": str(DB_PATH) if DB_PATH else None,
        "exists": DB_PATH.exists() if DB_PATH else False,
        "size_mb": 0.0,
        "tables": []
    }
    
    if DB_PATH and DB_PATH.exists():
        # Get file size
        size_bytes = DB_PATH.stat().st_size
        info["size_mb"] = round(size_bytes / (1024 * 1024), 2)
        
        # Get table names
        try:
            with get_connection() as conn:
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                )
                info["tables"] = [row[0] for row in cursor.fetchall()]
                logger.info(f"Database contains {len(info['tables'])} tables")
        except Exception as e:
            logger.error(f"Error retrieving table list: {str(e)}")
    
    return info


def clear_cache():
    """
    Clear all Streamlit cache for database query functions.
    
    This forces fresh data retrieval on next query.
    Useful for debugging or when data is updated.
    """
    logger.info("Clearing database query cache")
    
    # Clear cache for all query functions
    st.cache_data.clear()
    
    logger.info("Cache cleared successfully")