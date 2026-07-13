"""
schema.py

Database schema definitions for the N100 Financial Intelligence Platform.
Defines table structures, constraints, and indexes for all 12 datasets.
"""

import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

# =============================================================================
# TABLE SCHEMAS
# =============================================================================

# Companies table - Master table for company information
COMPANIES_SCHEMA = """
CREATE TABLE IF NOT EXISTS companies (
    company_id TEXT PRIMARY KEY,
    company_name TEXT NOT NULL,
    sector TEXT,
    industry TEXT,
    listed_date TEXT,
    isin_code TEXT UNIQUE,
    company_logo TEXT,
    chart_link TEXT,
    about_company TEXT,
    website TEXT,
    nse_profile TEXT,
    bse_profile TEXT,
    face_value REAL,
    book_value REAL,
    roce_percentage REAL,
    roe_percentage REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# Profit & Loss table
PROFIT_LOSS_SCHEMA = """
CREATE TABLE IF NOT EXISTS profit_loss (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    period TEXT,
    sales REAL,
    expenses REAL,
    operating_profit REAL,
    opm_percentage REAL,
    other_income REAL,
    interest REAL,
    depreciation REAL,
    profit_before_tax REAL,
    tax_percentage REAL,
    net_profit REAL,
    eps REAL,
    dividend_payout REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(company_id) ON DELETE CASCADE
);
"""

# Balance Sheet table
BALANCE_SHEET_SCHEMA = """
CREATE TABLE IF NOT EXISTS balance_sheet (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    period TEXT,
    share_capital REAL,
    reserves REAL,
    borrowings REAL,
    other_liabilities REAL,
    total_liabilities REAL,
    fixed_assets REAL,
    cwip REAL,
    investments REAL,
    other_assets REAL,
    total_assets REAL,
    equity_capital REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(company_id) ON DELETE CASCADE
);
"""

# Cash Flow table
CASH_FLOW_SCHEMA = """
CREATE TABLE IF NOT EXISTS cash_flow (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    period TEXT,
    cash_from_operating_activity REAL,
    cash_from_investing_activity REAL,
    cash_from_financing_activity REAL,
    free_cash_flow REAL,
    net_cash_flow REAL,
    operating_activity REAL,
    investing_activity REAL,
    financing_activity REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(company_id) ON DELETE CASCADE
);
"""

# Analysis table
ANALYSIS_SCHEMA = """
CREATE TABLE IF NOT EXISTS analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    period TEXT,
    compounded_sales_growth REAL,
    compounded_profit_growth REAL,
    roe REAL,
    stock_price_cagr REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(company_id) ON DELETE CASCADE
);
"""

# Documents table
DOCUMENTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    document_type TEXT,
    document_url TEXT,
    upload_date TEXT,
    year TEXT,
    annual_report TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(company_id) ON DELETE CASCADE
);
"""

# Pros and Cons table
PROS_CONS_SCHEMA = """
CREATE TABLE IF NOT EXISTS pros_cons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    pros TEXT,
    cons TEXT,
    analysis_period TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(company_id) ON DELETE CASCADE,
    UNIQUE(company_id, analysis_period)
);
"""

# Sectors table (actually a company-sector mapping)
SECTORS_SCHEMA = """
CREATE TABLE IF NOT EXISTS sectors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    broad_sector TEXT,
    sub_sector TEXT,
    index_weight_pct REAL,
    market_cap_category TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(company_id) ON DELETE CASCADE
);
"""

# Stock Prices table
STOCK_PRICES_SCHEMA = """
CREATE TABLE IF NOT EXISTS stock_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    date TEXT NOT NULL,
    open_price REAL,
    high_price REAL,
    low_price REAL,
    close_price REAL,
    volume INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(company_id) ON DELETE CASCADE,
    UNIQUE(company_id, date)
);
"""

# Market Cap table
MARKET_CAP_SCHEMA = """
CREATE TABLE IF NOT EXISTS market_cap (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    period TEXT,
    market_cap REAL,
    enterprise_value REAL,
    pe_ratio REAL,
    pb_ratio REAL,
    ev_ebitda REAL,
    dividend_yield REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(company_id) ON DELETE CASCADE
);
"""

# Financial Ratios table
FINANCIAL_RATIOS_SCHEMA = """
CREATE TABLE IF NOT EXISTS financial_ratios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    period TEXT,
    pe_ratio REAL,
    pb_ratio REAL,
    ps_ratio REAL,
    roe REAL,
    roa REAL,
    debt_to_equity REAL,
    current_ratio REAL,
    quick_ratio REAL,
    dividend_yield REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(company_id) ON DELETE CASCADE
);
"""

# Peer Groups table
PEER_GROUPS_SCHEMA = """
CREATE TABLE IF NOT EXISTS peer_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    peer_group_name TEXT,
    is_benchmark INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(company_id) ON DELETE CASCADE
);
"""

# =============================================================================
# INDEXES
# =============================================================================

INDEXES = {
    "companies": [
        "CREATE INDEX IF NOT EXISTS idx_companies_sector ON companies(sector);",
        "CREATE INDEX IF NOT EXISTS idx_companies_industry ON companies(industry);",
    ],
    "profit_loss": [
        "CREATE INDEX IF NOT EXISTS idx_profit_loss_company ON profit_loss(company_id);",
        "CREATE INDEX IF NOT EXISTS idx_profit_loss_period ON profit_loss(period);",
    ],
    "balance_sheet": [
        "CREATE INDEX IF NOT EXISTS idx_balance_sheet_company ON balance_sheet(company_id);",
        "CREATE INDEX IF NOT EXISTS idx_balance_sheet_period ON balance_sheet(period);",
    ],
    "cash_flow": [
        "CREATE INDEX IF NOT EXISTS idx_cash_flow_company ON cash_flow(company_id);",
        "CREATE INDEX IF NOT EXISTS idx_cash_flow_period ON cash_flow(period);",
    ],
    "analysis": [
        "CREATE INDEX IF NOT EXISTS idx_analysis_company ON analysis(company_id);",
        "CREATE INDEX IF NOT EXISTS idx_analysis_period ON analysis(period);",
    ],
    "documents": [
        "CREATE INDEX IF NOT EXISTS idx_documents_company ON documents(company_id);",
    ],
    "pros_cons": [
        "CREATE INDEX IF NOT EXISTS idx_pros_cons_company ON pros_cons(company_id);",
    ],
    "stock_prices": [
        "CREATE INDEX IF NOT EXISTS idx_stock_prices_company ON stock_prices(company_id);",
        "CREATE INDEX IF NOT EXISTS idx_stock_prices_date ON stock_prices(date);",
    ],
    "market_cap": [
        "CREATE INDEX IF NOT EXISTS idx_market_cap_company ON market_cap(company_id);",
        "CREATE INDEX IF NOT EXISTS idx_market_cap_period ON market_cap(period);",
    ],
    "financial_ratios": [
        "CREATE INDEX IF NOT EXISTS idx_financial_ratios_company ON financial_ratios(company_id);",
        "CREATE INDEX IF NOT EXISTS idx_financial_ratios_period ON financial_ratios(period);",
    ],
    "peer_groups": [
        "CREATE INDEX IF NOT EXISTS idx_peer_groups_company ON peer_groups(company_id);",
        "CREATE INDEX IF NOT EXISTS idx_peer_groups_name ON peer_groups(peer_group_name);",
    ],
}

# =============================================================================
# SCHEMA MAPPING
# =============================================================================

TABLE_SCHEMAS: Dict[str, str] = {
    "companies": COMPANIES_SCHEMA,
    "profit_loss": PROFIT_LOSS_SCHEMA,
    "balance_sheet": BALANCE_SHEET_SCHEMA,
    "cash_flow": CASH_FLOW_SCHEMA,
    "analysis": ANALYSIS_SCHEMA,
    "documents": DOCUMENTS_SCHEMA,
    "pros_cons": PROS_CONS_SCHEMA,
    "sectors": SECTORS_SCHEMA,
    "stock_prices": STOCK_PRICES_SCHEMA,
    "market_cap": MARKET_CAP_SCHEMA,
    "financial_ratios": FINANCIAL_RATIOS_SCHEMA,
    "peer_groups": PEER_GROUPS_SCHEMA,
}

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def get_table_schema(table_name: str) -> str:
    """
    Get CREATE TABLE statement for a specific table.

    Parameters
    ----------
    table_name : str
        Name of the table

    Returns
    -------
    str
        CREATE TABLE SQL statement

    Raises
    ------
    ValueError
        If table_name is not found in TABLE_SCHEMAS
    """
    if table_name not in TABLE_SCHEMAS:
        raise ValueError(f"Unknown table: {table_name}")

    return TABLE_SCHEMAS[table_name]


def get_all_schemas() -> List[str]:
    """
    Get all CREATE TABLE statements.

    Returns
    -------
    List[str]
        List of all CREATE TABLE SQL statements
    """
    return list(TABLE_SCHEMAS.values())


def get_indexes(table_name: str) -> List[str]:
    """
    Get CREATE INDEX statements for a specific table.

    Parameters
    ----------
    table_name : str
        Name of the table

    Returns
    -------
    List[str]
        List of CREATE INDEX SQL statements for the table
    """
    return INDEXES.get(table_name, [])


def get_all_indexes() -> List[str]:
    """
    Get all CREATE INDEX statements.

    Returns
    -------
    List[str]
        List of all CREATE INDEX SQL statements
    """
    all_indexes = []
    for indexes in INDEXES.values():
        all_indexes.extend(indexes)
    return all_indexes


def get_safe_indexes(table_name: str, existing_columns: List[str]) -> List[str]:
    """
    Get CREATE INDEX statements for columns that actually exist in the table.
    
    This prevents errors when trying to create indexes on non-existent columns,
    which can happen when tables are created dynamically from DataFrames.

    Parameters
    ----------
    table_name : str
        Name of the table
    existing_columns : List[str]
        List of column names that actually exist in the table

    Returns
    -------
    List[str]
        List of safe CREATE INDEX SQL statements
    """
    safe_indexes = []
    index_statements = INDEXES.get(table_name, [])
    
    for index_sql in index_statements:
        # Extract column name from index statement
        # Format: "CREATE INDEX IF NOT EXISTS idx_name ON table(column);"
        try:
            # Parse the column name from the SQL
            column_part = index_sql.split('(')[1].split(')')[0]
            column_name = column_part.split('.')[-1]  # Handle table.column format
            
            # Only add index if column exists
            if column_name in existing_columns:
                safe_indexes.append(index_sql)
            else:
                logger.warning(
                    f"Skipping index on '{column_name}' for table '{table_name}' "
                    f"- column does not exist"
                )
        except (IndexError, AttributeError) as e:
            logger.warning(f"Could not parse index SQL: {index_sql}. Error: {e}")
    
    return safe_indexes
