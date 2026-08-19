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
            raise sqlite3.Error(
                "Database file not found. Please ensure the database exists."
            )

        logger.debug("Opening database connection")
        start_time = time.time()

        conn = sqlite3.connect(
            str(DB_PATH),
            check_same_thread=False,  # Allow multi-threading for Streamlit
            timeout=30,  # 30 second timeout for long queries
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
                    c.company_id as ticker,
                    c.company_name as name,
                    COALESCE(c.sector, pg.peer_group_name, 'Unclassified') as sector,
                    c.industry,
                    c.isin_code as isin,
                    c.listed_date
                FROM companies c
                LEFT JOIN (
                    SELECT company_id, peer_group_name
                    FROM peer_groups
                    WHERE peer_group_name IS NOT NULL
                    GROUP BY company_id
                ) pg ON c.company_id = pg.company_id
                ORDER BY c.company_id
            """

            df = pd.read_sql_query(query, conn)

            elapsed = time.time() - start_time
            logger.info(
                f"Query executed successfully in {elapsed:.3f}s, returned {len(df)} rows"
            )

            return df

    except sqlite3.Error as e:
        logger.error(f"Error in get_companies(): {str(e)}", exc_info=True)
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Unexpected error in get_companies(): {str(e)}", exc_info=True)
        return pd.DataFrame()


@st.cache_data(ttl=600)
def get_ratios(
    ticker: Optional[str] = None, year: Optional[int] = None
) -> pd.DataFrame:
    """
    Retrieve financial ratios for a specific company or all companies.

    Args:
        ticker: Optional company ticker symbol (e.g., 'RELIANCE', 'TCS'). If None, returns ratios for all companies.
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
            - revenue_cagr_5yr: 5-year Revenue CAGR
            - revenue_growth: Revenue growth
            - profit_growth: Profit growth
            - And other financial metrics

    Returns empty DataFrame if:
        - No data found
        - Database is unavailable

    Example:
        df = get_ratios('RELIANCE', year=2024)
        df_all = get_ratios(year=2024)
    """
    logger.info(f"Executing query: get_ratios(ticker={ticker}, year={year})")
    start_time = time.time()

    try:
        with get_connection() as conn:
            # Join financial_ratios with financial_kpis (for period match and TTM CAGR) and market_cap (for fallback valuation metrics)
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
                    COALESCE(k.pe_ratio, m.pe_ratio) as pe_ratio,
                    COALESCE(k.pb_ratio, m.pb_ratio) as pb_ratio,
                    k.net_profit_margin,
                    k.operating_margin,
                    k.gross_margin,
                    k.interest_coverage,
                    k.asset_turnover,
                    k.inventory_turnover,
                    COALESCE(k.revenue_cagr, k_ttm.revenue_cagr) as revenue_cagr_5yr,
                    COALESCE(k.revenue_cagr, k_ttm.revenue_cagr) as revenue_growth,
                    COALESCE(k.profit_cagr, k_ttm.profit_cagr) as profit_growth,
                    k.eps,
                    k.ev_ebitda
                FROM financial_ratios r
                LEFT JOIN financial_kpis k ON r.company_id = k.company_id AND r.period = k.period
                LEFT JOIN financial_kpis k_ttm ON r.company_id = k_ttm.company_id AND k_ttm.period = 'TTM'
                LEFT JOIN market_cap m ON r.company_id = m.company_id
            """
            where_clauses = []
            params = []

            if ticker and isinstance(ticker, str) and ticker.strip():
                where_clauses.append("r.company_id = ?")
                params.append(ticker.strip().upper())

            if year is not None:
                where_clauses.append("r.period LIKE ?")
                params.append(f"%{year}%")

            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)

            query += " ORDER BY r.company_id, r.period DESC"

            df = pd.read_sql_query(query, conn, params=params)

            elapsed = time.time() - start_time

            if df.empty:
                logger.warning(
                    f"No ratio data found for ticker: {ticker}, year: {year}"
                )
            else:
                logger.info(
                    f"Query executed successfully in {elapsed:.3f}s, returned {len(df)} rows"
                )

            return df

    except sqlite3.Error as e:
        logger.error(
            f"Database error in get_ratios() for ticker={ticker}, year={year}: {str(e)}",
            exc_info=True,
        )
        return pd.DataFrame()
    except Exception as e:
        logger.error(
            f"Unexpected error in get_ratios() for ticker={ticker}, year={year}: {str(e)}",
            exc_info=True,
        )
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
                logger.info(
                    f"Query executed successfully in {elapsed:.3f}s, returned {len(df)} rows"
                )

            return df

    except sqlite3.Error as e:
        logger.error(
            f"Database error in get_pl() for {ticker}: {str(e)}", exc_info=True
        )
        return pd.DataFrame()
    except Exception as e:
        logger.error(
            f"Unexpected error in get_pl() for {ticker}: {str(e)}", exc_info=True
        )
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
                logger.info(
                    f"Query executed successfully in {elapsed:.3f}s, returned {len(df)} rows"
                )

            return df

    except sqlite3.Error as e:
        logger.error(
            f"Database error in get_bs() for {ticker}: {str(e)}", exc_info=True
        )
        return pd.DataFrame()
    except Exception as e:
        logger.error(
            f"Unexpected error in get_bs() for {ticker}: {str(e)}", exc_info=True
        )
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
                logger.info(
                    f"Query executed successfully in {elapsed:.3f}s, returned {len(df)} rows"
                )

            return df

    except sqlite3.Error as e:
        logger.error(
            f"Database error in get_cf() for {ticker}: {str(e)}", exc_info=True
        )
        return pd.DataFrame()
    except Exception as e:
        logger.error(
            f"Unexpected error in get_cf() for {ticker}: {str(e)}", exc_info=True
        )
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
                logger.info(
                    f"Query executed successfully in {elapsed:.3f}s, returned {len(df)} rows"
                )

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
                logger.info(
                    f"Query executed successfully in {elapsed:.3f}s, returned {len(df)} rows"
                )

            return df

    except sqlite3.Error as e:
        logger.error(
            f"Database error in get_peers() for {group_name}: {str(e)}", exc_info=True
        )
        return pd.DataFrame()
    except Exception as e:
        logger.error(
            f"Unexpected error in get_peers() for {group_name}: {str(e)}", exc_info=True
        )
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
                logger.info(
                    f"Query executed successfully in {elapsed:.3f}s, returned {len(df)} rows"
                )

            return df

    except sqlite3.Error as e:
        logger.error(
            f"Database error in get_valuation() for {ticker}: {str(e)}", exc_info=True
        )
        return pd.DataFrame()
    except Exception as e:
        logger.error(
            f"Unexpected error in get_valuation() for {ticker}: {str(e)}", exc_info=True
        )
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
    df = _read_df("""
        SELECT company_id, company_name, sector, industry
        FROM companies
        ORDER BY company_name
        """)
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
    df = _read_df("""
        SELECT DISTINCT peer_group_name
        FROM peer_groups
        WHERE peer_group_name IS NOT NULL
        ORDER BY peer_group_name
        """)
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
            "operating_margin",
            "revenue_cagr",
            "profit_cagr",
            "overall_score",
            "operating_activity",
            "investing_activity",
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
        peers = _read_df("""
            SELECT pg.company_id, pg.peer_group_name, pg.is_benchmark
            FROM peer_groups pg
            WHERE pg.peer_group_name IS NOT NULL
            ORDER BY pg.peer_group_name, pg.is_benchmark DESC
            """)
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
        "tables": [],
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


# =============================================================================
# MODULE 5B - COMPANY INTELLIGENCE HELPERS
# =============================================================================


@st.cache_data(ttl=600)
def get_raw_statement(ticker: str, table_name: str) -> pd.DataFrame:
    """
    Retrieve raw statement data (profit_loss, balance_sheet, cash_flow, etc.)
    with original column names for exact business logic consumption.
    """
    if not ticker or not isinstance(ticker, str):
        return pd.DataFrame()
    ticker = ticker.strip().upper()
    valid_tables = {
        "profit_loss",
        "balance_sheet",
        "cash_flow",
        "financial_kpis",
        "financial_ratios",
        "companies",
        "financial_health_scores",
        "peer_percentiles",
        "market_cap",
    }
    if table_name not in valid_tables:
        logger.warning(f"Invalid table name requested: {table_name}")
        return pd.DataFrame()

    try:
        with get_connection() as conn:
            query = (
                f"SELECT * FROM {table_name} WHERE company_id = ? ORDER BY period DESC"
            )
            return pd.read_sql_query(query, conn, params=[ticker])
    except Exception as e:
        logger.error(
            f"Error fetching raw statement {table_name} for {ticker}: {str(e)}"
        )
        return pd.DataFrame()


@st.cache_data(ttl=600)
def get_company_financial_health(ticker: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve financial health score for a company from database or CSV output.
    Does NOT recalculate health scores.
    """
    if not ticker or not isinstance(ticker, str):
        return None
    ticker = ticker.strip().upper()

    try:
        with get_connection() as conn:
            query = """
                SELECT * FROM financial_health_scores
                WHERE company_id = ?
                ORDER BY period DESC LIMIT 1
            """
            df = pd.read_sql_query(query, conn, params=[ticker])
            if not df.empty:
                return df.iloc[0].to_dict()
    except Exception as e:
        logger.warning(f"Database lookup failed for health score of {ticker}: {str(e)}")

    # Fallback to output CSV if DB table is empty/missing
    try:
        csv_path = Path("output/financial_health_scores.csv")
        if csv_path.exists():
            df_csv = pd.read_csv(csv_path)
            if "company_id" in df_csv.columns:
                match = df_csv[df_csv["company_id"].str.upper() == ticker]
                if not match.empty:
                    return match.iloc[0].to_dict()
    except Exception as e:
        logger.error(f"CSV fallback error for health score of {ticker}: {str(e)}")

    return None


@st.cache_data(ttl=600)
def get_company_pros_cons_signals(ticker: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Retrieve Module 2D generated pros and cons for a company.
    Consumes outputs from pros_cons_generated.csv or pros_cons DB table.
    """
    if not ticker or not isinstance(ticker, str):
        return {"pros": [], "cons": []}
    ticker = ticker.strip().upper()

    pros: List[Dict[str, Any]] = []
    cons: List[Dict[str, Any]] = []

    # Check output CSV first (authoritative Module 2D output)
    try:
        csv_path = Path("output/pros_cons_generated.csv")
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            if "company_id" in df.columns:
                match = df[df["company_id"].str.upper() == ticker]
                for _, row in match.iterrows():
                    item = {
                        "rule_id": str(row.get("rule_id", "N/A")),
                        "text": str(row.get("text", "")),
                        "confidence_pct": row.get("confidence_pct", None),
                        "type": str(row.get("type", "")).lower(),
                    }
                    if item["type"] == "pro":
                        pros.append(item)
                    elif item["type"] == "con":
                        cons.append(item)
                return {"pros": pros, "cons": cons}
    except Exception as e:
        logger.error(f"Error reading pros_cons_generated.csv for {ticker}: {str(e)}")

    # Fallback to database pros_cons table if available
    try:
        with get_connection() as conn:
            query = "SELECT * FROM pros_cons WHERE company_id = ?"
            df = pd.read_sql_query(query, conn, params=[ticker])
            if not df.empty:
                row = df.iloc[0]
                p_text = row.get("pros")
                c_text = row.get("cons")
                if p_text and not pd.isna(p_text) and str(p_text).lower() != "nan":
                    pros.append(
                        {
                            "rule_id": "DB_PRO",
                            "text": str(p_text),
                            "confidence_pct": None,
                            "type": "pro",
                        }
                    )
                if c_text and not pd.isna(c_text) and str(c_text).lower() != "nan":
                    cons.append(
                        {
                            "rule_id": "DB_CON",
                            "text": str(c_text),
                            "confidence_pct": None,
                            "type": "con",
                        }
                    )
    except Exception as e:
        logger.error(f"Error querying pros_cons DB table for {ticker}: {str(e)}")

    return {"pros": pros, "cons": cons}


@st.cache_data(ttl=600)
def get_company_capital_allocation_detail(ticker: str) -> Dict[str, Any]:
    """
    Retrieve Module 4 capital allocation classification and pattern history.
    """
    if not ticker or not isinstance(ticker, str):
        return {}
    ticker = ticker.strip().upper()

    res = {
        "rating": None,
        "pattern": None,
        "latest_year": None,
        "previous_pattern": None,
        "changed": False,
    }

    try:
        latest_csv = Path("output/capital_allocation_latest_year.csv")
        if latest_csv.exists():
            df = pd.read_csv(latest_csv)
            if "company_id" in df.columns:
                m = df[df["company_id"].str.upper() == ticker]
                if not m.empty:
                    row = m.iloc[0]
                    res["rating"] = row.get("capital_allocation_rating")
                    res["pattern"] = row.get("capital_allocation_pattern")
                    res["latest_year"] = row.get("latest_year")

        pattern_csv = Path("output/pattern_changes.csv")
        if pattern_csv.exists():
            df_p = pd.read_csv(pattern_csv)
            if "company_id" in df_p.columns:
                m_p = df_p[df_p["company_id"].str.upper() == ticker]
                if not m_p.empty:
                    r_p = m_p.iloc[0]
                    res["previous_pattern"] = r_p.get("previous_pattern")
                    res["changed"] = bool(r_p.get("changed", False))
    except Exception as e:
        logger.error(
            f"Error retrieving capital allocation detail for {ticker}: {str(e)}"
        )

    return res


@st.cache_data(ttl=600)
def get_company_valuation_detail(ticker: str) -> Dict[str, Any]:
    """
    Retrieve Module 4 valuation metrics and flags for a company.
    """
    if not ticker or not isinstance(ticker, str):
        return {}
    ticker = ticker.strip().upper()

    res = {
        "pe": None,
        "pb": None,
        "ps": None,
        "ev_ebitda": None,
        "dividend_yield": None,
        "sector_median_pe": None,
        "pe_vs_sector_median_pct": None,
        "valuation_flag": None,
        "difference_pct": None,
    }

    # Query DB market_cap or financial_ratios table first
    try:
        with get_connection() as conn:
            query = """
                SELECT * FROM market_cap
                WHERE company_id = ?
                ORDER BY period DESC LIMIT 1
            """
            df = pd.read_sql_query(query, conn, params=[ticker])
            if not df.empty:
                row = df.iloc[0]
                res["pe"] = row.get("pe_ratio")
                res["pb"] = row.get("pb_ratio")
                res["ev_ebitda"] = row.get("ev_ebitda")
                res["dividend_yield"] = row.get("dividend_yield")
    except Exception as e:
        logger.error(f"Error querying market_cap for valuation of {ticker}: {str(e)}")

    # Check valuation_flags.csv
    try:
        vf_csv = Path("output/valuation_flags.csv")
        if vf_csv.exists():
            df_vf = pd.read_csv(vf_csv)
            if "Ticker" in df_vf.columns:
                m_vf = df_vf[df_vf["Ticker"].str.upper() == ticker]
                if not m_vf.empty:
                    r_vf = m_vf.iloc[0]
                    res["pe"] = r_vf.get("PE", res["pe"])
                    res["sector_median_pe"] = r_vf.get("Sector Median PE")
                    res["pe_vs_sector_median_pct"] = r_vf.get("PE vs Sector Median %")
                    res["valuation_flag"] = r_vf.get("Valuation Flag")
                    res["difference_pct"] = r_vf.get("Difference %")
    except Exception as e:
        logger.error(f"Error reading valuation_flags.csv for {ticker}: {str(e)}")

    return res


@st.cache_data(ttl=600)
def get_company_peer_percentiles(ticker: str) -> pd.DataFrame:
    """
    Retrieve peer percentile rankings for a company.
    """
    if not ticker or not isinstance(ticker, str):
        return pd.DataFrame()
    ticker = ticker.strip().upper()

    try:
        with get_connection() as conn:
            query = """
                SELECT * FROM peer_percentiles
                WHERE company_id = ?
                ORDER BY period DESC, metric ASC
            """
            df = pd.read_sql_query(query, conn, params=[ticker])
            if not df.empty:
                return df
    except Exception as e:
        logger.error(f"Error querying peer_percentiles for {ticker}: {str(e)}")

    # Fallback to output CSV
    try:
        csv_path = Path("output/peer_percentiles.csv")
        if csv_path.exists():
            df_csv = pd.read_csv(csv_path)
            if "company_id" in df_csv.columns:
                return df_csv[df_csv["company_id"].str.upper() == ticker].copy()
    except Exception as e:
        logger.error(f"CSV fallback error for peer percentiles of {ticker}: {str(e)}")

    return pd.DataFrame()
