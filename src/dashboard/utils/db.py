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
            - ticker: Company ticker symbol
            - name: Company name
            - sector: Sector classification
            - industry: Industry classification
            - isin: ISIN number
            - listed_date: Date of listing
            - market_cap: Market capitalization
            
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
                    ticker,
                    name,
                    sector,
                    industry,
                    isin,
                    listed_date,
                    market_cap
                FROM companies
                ORDER BY ticker
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
            - pe_ratio: Price to Earnings ratio
            - pb_ratio: Price to Book ratio
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
            # Base query
            query = """
                SELECT 
                    ticker,
                    year,
                    pe_ratio,
                    pb_ratio,
                    roe,
                    roa,
                    debt_equity,
                    current_ratio,
                    quick_ratio,
                    gross_margin,
                    operating_margin,
                    net_margin,
                    asset_turnover,
                    inventory_turnover,
                    revenue_growth,
                    profit_growth,
                    eps,
                    book_value_per_share,
                    dividend_yield
                FROM financial_ratios
                WHERE ticker = ?
            """
            params = [ticker]
            
            # Add year filter if provided
            if year is not None:
                query += " AND year = ?"
                params.append(year)
            
            query += " ORDER BY year DESC"
            
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
            - ticker: Company ticker
            - year: Financial year
            - revenue: Total revenue
            - gross_profit: Gross profit
            - operating_profit: Operating profit
            - net_profit: Net profit
            - ebitda: EBITDA
            - interest_expense: Interest expense
            - tax_expense: Tax expense
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
            query = """
                SELECT 
                    ticker,
                    year,
                    revenue,
                    gross_profit,
                    operating_profit,
                    net_profit,
                    ebitda,
                    interest_expense,
                    tax_expense,
                    depreciation,
                    amortization,
                    other_income,
                    exceptional_items,
                    net_sales,
                    cost_of_materials,
                    employee_benefits,
                    other_expenses
                FROM profit_loss
                WHERE ticker = ?
                ORDER BY year DESC
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
            - ticker: Company ticker
            - year: Financial year
            - total_assets: Total assets
            - total_liabilities: Total liabilities
            - total_equity: Total equity
            - current_assets: Current assets
            - non_current_assets: Non-current assets
            - current_liabilities: Current liabilities
            - non_current_liabilities: Non-current liabilities
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
            query = """
                SELECT 
                    ticker,
                    year,
                    total_assets,
                    total_liabilities,
                    total_equity,
                    current_assets,
                    non_current_assets,
                    current_liabilities,
                    non_current_liabilities,
                    cash_and_equivalents,
                    inventory,
                    accounts_receivable,
                    property_plant_equipment,
                    goodwill,
                    intangible_assets,
                    long_term_debt,
                    short_term_debt,
                    accounts_payable,
                    retained_earnings,
                    share_capital
                FROM balance_sheet
                WHERE ticker = ?
                ORDER BY year DESC
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
            - ticker: Company ticker
            - year: Financial year
            - operating_cash_flow: Cash flow from operations
            - investing_cash_flow: Cash flow from investing
            - financing_cash_flow: Cash flow from financing
            - net_cash_flow: Net change in cash
            - capex: Capital expenditure
            - free_cash_flow: Free cash flow
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
            query = """
                SELECT 
                    ticker,
                    year,
                    operating_cash_flow,
                    investing_cash_flow,
                    financing_cash_flow,
                    net_cash_flow,
                    capex,
                    free_cash_flow,
                    depreciation,
                    working_capital_change,
                    tax_paid,
                    interest_paid,
                    dividends_paid,
                    debt_repayment,
                    equity_issuance
                FROM cash_flow
                WHERE ticker = ?
                ORDER BY year DESC
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