"""
column_mappings.py

Column mapping configurations for the N100 Financial Intelligence Platform.
Maps source Excel columns to target database columns for each dataset.
"""

from typing import Dict, List

# =============================================================================
# COLUMN MAPPINGS
# =============================================================================

# Companies dataset column mapping
COMPANIES_COLUMN_MAPPING = {
    "id": "company_id",  # Map 'id' to 'company_id' - this is the primary key
    "company_name": "company_name",
    "sector": "sector",
    "industry": "industry",
    "listed_date": "listed_date",
    "isin_code": "isin_code",
    # Additional columns that exist in source but not in target schema
    "company_logo": "company_logo",
    "chart_link": "chart_link",
    "about_company": "about_company",
    "website": "website",
    "nse_profile": "nse_profile",
    "bse_profile": "bse_profile",
    "face_value": "face_value",
    "book_value": "book_value",
    "roce_percentage": "roce_percentage",
    "roe_percentage": "roe_percentage",
}

# Profit & Loss dataset column mapping
PROFIT_LOSS_COLUMN_MAPPING = {
    "company_id": "company_id",
    "year": "period",  # Map 'year' to 'period'
    "sales": "sales",
    "expenses": "expenses",
    "operating_profit": "operating_profit",
    "opm_percentage": "opm_percentage",
    "other_income": "other_income",
    "interest": "interest",
    "depreciation": "depreciation",
    "profit_before_tax": "profit_before_tax",
    "tax_percentage": "tax_percentage",
    "net_profit": "net_profit",
    "eps": "eps",
    "dividend_payout": "dividend_payout",
    # Note: 'id' column from Excel is dropped (DB has auto-increment)
}

# Balance Sheet dataset column mapping
BALANCE_SHEET_COLUMN_MAPPING = {
    "company_id": "company_id",
    "year": "period",
    "equity_capital": "share_capital",  # Map equity_capital to share_capital
    "reserves": "reserves",
    "borrowings": "borrowings",
    "other_liabilities": "other_liabilities",
    "total_liabilities": "total_liabilities",
    "fixed_assets": "fixed_assets",
    "cwip": "cwip",
    "investments": "investments",
    "other_asset": "other_assets",  # Map other_asset to other_assets
    "total_assets": "total_assets",
    # Note: 'id' column from Excel is dropped (DB has auto-increment)
    # Missing: total_equity, current_assets, current_liabilities (not in source)
}

# Cash Flow dataset column mapping
CASH_FLOW_COLUMN_MAPPING = {
    "company_id": "company_id",
    "year": "period",
    "cash_from_operating_activity": "cash_from_operating_activity",
    "cash_from_investing_activity": "cash_from_investing_activity",
    "cash_from_financing_activity": "cash_from_financing_activity",
    "free_cash_flow": "free_cash_flow",
    "net_cash_flow": "net_cash_flow",
    "operating_activity": "operating_activity",
    "investing_activity": "investing_activity",
    "financing_activity": "financing_activity",
    # Note: 'id' column from Excel is dropped (DB has auto-increment)
}

# Analysis dataset column mapping
ANALYSIS_COLUMN_MAPPING = {
    "company_id": "company_id",
    "compounded_sales_growth": "compounded_sales_growth",
    "compounded_profit_growth": "compounded_profit_growth",
    "roe": "roe",
    "stock_price_cagr": "stock_price_cagr",
}

# Documents dataset column mapping
DOCUMENTS_COLUMN_MAPPING = {
    "company_id": "company_id",
    "document_type": "document_type",
    "document_url": "document_url",
    "year": "year",
    "annual_report": "annual_report",
}

# Pros and Cons dataset column mapping
PROS_CONS_COLUMN_MAPPING = {
    "company_id": "company_id",
    "pros": "pros",
    "cons": "cons",
}

# Sectors dataset column mapping - this is actually a company-sector mapping
SECTORS_COLUMN_MAPPING = {
    "id": "id",  # Keep id column
    "company_id": "company_id",
    "broad_sector": "sector_name",  # Map broad_sector to sector_name
    "sub_sector": "sub_sector",
    "index_weight_pct": "index_weight_pct",
    "market_cap_category": "market_cap_category",
}

# Stock Prices dataset column mapping
STOCK_PRICES_COLUMN_MAPPING = {
    "company_id": "company_id",
    "date": "date",
    "open_price": "open_price",
    "high_price": "high_price",
    "low_price": "low_price",
    "close_price": "close_price",
    "volume": "volume",
}

# Market Cap dataset column mapping
MARKET_CAP_COLUMN_MAPPING = {
    "company_id": "company_id",
    "year": "period",  # Map 'year' to 'period'
    "market_cap_crore": "market_cap",  # Map market_cap_crore to market_cap
    "enterprise_value_crore": "enterprise_value",  # Map enterprise_value_crore to enterprise_value
    "pe_ratio": "pe_ratio",
    "pb_ratio": "pb_ratio",
    "ev_ebitda": "ev_ebitda",
    "dividend_yield_pct": "dividend_yield",  # Map dividend_yield_pct to dividend_yield
    # Note: 'id' column from Excel is dropped (DB has auto-increment)
    # Note: shares_outstanding not in source data
}

# Financial Ratios dataset column mapping
FINANCIAL_RATIOS_COLUMN_MAPPING = {
    "company_id": "company_id",
    "year": "period",
    "return_on_equity_pct": "roe",  # Map return_on_equity_pct to roe
    "debt_to_equity": "debt_to_equity",
    "interest_coverage": "interest_coverage",
    "asset_turnover": "asset_turnover",
    "earnings_per_share": "eps",  # Map earnings_per_share to eps
    # Note: 'id' column from Excel is dropped (DB has auto-increment)
    # Note: Many columns in source don't have direct mapping to DB schema
}

# Peer Groups dataset column mapping
PEER_GROUPS_COLUMN_MAPPING = {
    "company_id": "company_id",
    "peer_group_name": "peer_group_name",
    "is_benchmark": "is_benchmark",
    # Note: 'id' column from Excel is dropped (DB has auto-increment)
    # Note: peer_company_id not in source - using peer_group_name instead
}

# =============================================================================
# MAPPING REGISTRY
# =============================================================================

COLUMN_MAPPINGS: Dict[str, Dict[str, str]] = {
    "companies": COMPANIES_COLUMN_MAPPING,
    "profit_loss": PROFIT_LOSS_COLUMN_MAPPING,
    "balance_sheet": BALANCE_SHEET_COLUMN_MAPPING,
    "cash_flow": CASH_FLOW_COLUMN_MAPPING,
    "analysis": ANALYSIS_COLUMN_MAPPING,
    "documents": DOCUMENTS_COLUMN_MAPPING,
    "pros_cons": PROS_CONS_COLUMN_MAPPING,
    "sectors": SECTORS_COLUMN_MAPPING,
    "stock_prices": STOCK_PRICES_COLUMN_MAPPING,
    "market_cap": MARKET_CAP_COLUMN_MAPPING,
    "financial_ratios": FINANCIAL_RATIOS_COLUMN_MAPPING,
    "peer_groups": PEER_GROUPS_COLUMN_MAPPING,
}

# =============================================================================
# REQUIRED COLUMNS (AFTER MAPPING)
# =============================================================================

REQUIRED_COLUMNS: Dict[str, List[str]] = {
    "companies": ["company_id", "company_name"],
    "profit_loss": ["company_id", "period"],
    "balance_sheet": ["company_id", "period"],
    "cash_flow": ["company_id", "period"],
    "analysis": ["company_id"],  # period is optional in analysis
    "documents": ["company_id"],
    "pros_cons": ["company_id"],
    "sectors": ["company_id"],  # sectors uses company_id as primary key
    "stock_prices": ["company_id", "date"],
    "market_cap": ["company_id", "period"],
    "financial_ratios": ["company_id", "period"],
    "peer_groups": ["company_id"],  # peer_group_name is optional
}

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def get_column_mapping(dataset_name: str) -> Dict[str, str]:
    """
    Get column mapping for a dataset.
    
    Parameters
    ----------
    dataset_name : str
        Name of the dataset
        
    Returns
    -------
    Dict[str, str]
        Column mapping dictionary
        
    Raises
    ------
    ValueError
        If dataset_name is not found
    """
    if dataset_name not in COLUMN_MAPPINGS:
        raise ValueError(f"Unknown dataset: {dataset_name}")
    
    return COLUMN_MAPPINGS[dataset_name]


def get_required_columns(dataset_name: str) -> List[str]:
    """
    Get required columns for a dataset (after mapping).
    
    Parameters
    ----------
    dataset_name : str
        Name of the dataset
        
    Returns
    -------
    List[str]
        List of required column names
        
    Raises
    ------
    ValueError
        If dataset_name is not found
    """
    if dataset_name not in REQUIRED_COLUMNS:
        raise ValueError(f"Unknown dataset: {dataset_name}")
    
    return REQUIRED_COLUMNS[dataset_name]


def apply_column_mapping(df: pd.DataFrame, dataset_name: str) -> pd.DataFrame:
    """
    Apply column mapping to a DataFrame.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with source columns
    dataset_name : str
        Name of the dataset
        
    Returns
    -------
    pd.DataFrame
        DataFrame with mapped column names
    """
    import pandas as pd
    
    mapping = get_column_mapping(dataset_name)
    
    # Create a mapping from normalized column names to original column names
    # Normalize by stripping whitespace and converting to lowercase
    column_name_map = {}
    for col in df.columns:
        normalized = str(col).strip().lower()
        column_name_map[normalized] = col
    
    # Create rename dictionary by matching normalized names
    rename_dict = {}
    for source_col, target_col in mapping.items():
        normalized_source = source_col.strip().lower()
        if normalized_source in column_name_map:
            original_col = column_name_map[normalized_source]
            rename_dict[original_col] = target_col
    
    # Rename columns - only columns in the mapping are renamed
    # All other columns are kept as-is
    df = df.rename(columns=rename_dict)
    
    return df
