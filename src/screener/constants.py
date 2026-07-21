"""
constants.py

Constants and configuration for the Investment Screener Engine (Module 6).
"""

from pathlib import Path

from src.config.constants import LOG_DIR, OUTPUT_DIR

# =============================================================================
# TABLE NAMES
# =============================================================================

SCREEN_TEMPLATES_TABLE = "screen_templates"

# =============================================================================
# FILE PATHS
# =============================================================================

SCREENER_LOG_NAME = "screener.log"
SCREENER_CSV_NAME = "screener_results.csv"

SCREENER_LOG_PATH = LOG_DIR / SCREENER_LOG_NAME
SCREENER_CSV_PATH = OUTPUT_DIR / SCREENER_CSV_NAME

# =============================================================================
# FILTER CONFIGURATION
# =============================================================================

# Supported filter operators
SUPPORTED_OPERATORS = [
    ">",
    ">=",
    "<",
    "<=",
    "=",
    "!=",
    "BETWEEN",
    "IN",
    "NOT IN",
    "IS NULL",
    "IS NOT NULL",
]

# Valid KPI fields for screening
VALID_SCREEN_FIELDS = {
    # Company Info
    "company_id": {"table": "companies", "type": "string", "category": "Info"},
    "company_name": {"table": "companies", "type": "string", "category": "Info"},
    "sector": {"table": "companies", "type": "string", "category": "Info"},
    "industry": {"table": "companies", "type": "string", "category": "Info"},
    "period": {"table": "financial_ratios", "type": "string", "category": "Info"},
    # Valuation
    "pe_ratio": {"table": "market_cap", "type": "float", "category": "Valuation"},
    "pb_ratio": {"table": "market_cap", "type": "float", "category": "Valuation"},
    "ps_ratio": {"table": "market_cap", "type": "float", "category": "Valuation"},
    # Profitability
    "roe": {"table": "financial_ratios", "type": "float", "category": "Profitability"},
    "roa": {"table": "financial_ratios", "type": "float", "category": "Profitability"},
    "net_profit_margin": {"table": "financial_ratios", "type": "float", "category": "Profitability"},
    "operating_profit_margin": {"table": "financial_ratios", "type": "float", "category": "Profitability"},
    "roce": {"table": "financial_ratios", "type": "float", "category": "Profitability"},
    # Growth
    "revenue_cagr_3yr": {"table": "financial_ratios", "type": "float", "category": "Growth"},
    "revenue_cagr_5yr": {"table": "financial_ratios", "type": "float", "category": "Growth"},
    "pat_cagr_3yr": {"table": "financial_ratios", "type": "float", "category": "Growth"},
    "pat_cagr_5yr": {"table": "financial_ratios", "type": "float", "category": "Growth"},
    "eps_cagr_3yr": {"table": "financial_ratios", "type": "float", "category": "Growth"},
    "eps_cagr_5yr": {"table": "financial_ratios", "type": "float", "category": "Growth"},
    # Cash Flow
    "free_cash_flow": {"table": "financial_ratios", "type": "float", "category": "Cash Flow"},
    "fcf_margin": {"table": "financial_ratios", "type": "float", "category": "Cash Flow"},
    "cash_conversion": {"table": "financial_ratios", "type": "float", "category": "Cash Flow"},
    "cash_return_on_assets": {"table": "financial_ratios", "type": "float", "category": "Cash Flow"},
    # Leverage
    "debt_to_equity": {"table": "financial_ratios", "type": "float", "category": "Leverage"},
    "current_ratio": {"table": "balance_sheet", "type": "float", "category": "Leverage"},
    "quick_ratio": {"table": "balance_sheet", "type": "float", "category": "Leverage"},
    "interest_coverage": {"table": "financial_ratios", "type": "float", "category": "Leverage"},
    # Health
    "overall_score": {"table": "financial_health_scores", "type": "float", "category": "Health"},
    "rating": {"table": "financial_health_scores", "type": "string", "category": "Health"},
    "profitability_score": {"table": "financial_health_scores", "type": "float", "category": "Health"},
    "growth_score": {"table": "financial_health_scores", "type": "float", "category": "Health"},
    "cashflow_score": {"table": "financial_health_scores", "type": "float", "category": "Health"},
    "leverage_score": {"table": "financial_health_scores", "type": "float", "category": "Health"},
    "efficiency_score": {"table": "financial_health_scores", "type": "float", "category": "Health"},
    # Dividend
    "dividend_yield": {"table": "market_cap", "type": "float", "category": "Dividend"},
}

# =============================================================================
# RANKING CONFIGURATION
# =============================================================================

SUPPORTED_RANK_FIELDS = [
    "overall_score",
    "roe",
    "revenue_cagr_3yr",
    "dividend_yield",
    "pe_ratio",
    "pb_ratio",
    "roa",
    "free_cash_flow",
    "debt_to_equity",
    "custom_score",
]

# =============================================================================
# PRESET SCREENER DEFINITIONS
# =============================================================================

PRESET_SCREENERS = {
    "value_investing": {
        "name": "Value Investing",
        "description": "Low PE, low PB, high dividend yield, strong balance sheet",
        "filters": [
            {"field": "pe_ratio", "operator": "<=", "value": 20},
            {"field": "pb_ratio", "operator": "<=", "value": 3},
            {"field": "dividend_yield", "operator": ">=", "value": 1.5},
            {"field": "debt_to_equity", "operator": "<=", "value": 0.5},
        ],
        "sort_by": "pe_ratio",
        "sort_order": "asc",
    },
    "growth_investing": {
        "name": "Growth Investing",
        "description": "High revenue and profit growth, strong ROE",
        "filters": [
            {"field": "revenue_cagr_3yr", "operator": ">=", "value": 15},
            {"field": "pat_cagr_3yr", "operator": ">=", "value": 15},
            {"field": "roe", "operator": ">=", "value": 15},
        ],
        "sort_by": "revenue_cagr_3yr",
        "sort_order": "desc",
    },
    "dividend_investing": {
        "name": "Dividend Investing",
        "description": "High dividend yield, stable companies",
        "filters": [
            {"field": "dividend_yield", "operator": ">=", "value": 3},
            {"field": "overall_score", "operator": ">=", "value": 60},
        ],
        "sort_by": "dividend_yield",
        "sort_order": "desc",
    },
    "high_roe": {
        "name": "High ROE",
        "description": "Companies with superior return on equity",
        "filters": [
            {"field": "roe", "operator": ">=", "value": 20},
        ],
        "sort_by": "roe",
        "sort_order": "desc",
    },
    "low_debt": {
        "name": "Low Debt",
        "description": "Debt-free or low debt companies",
        "filters": [
            {"field": "debt_to_equity", "operator": "<=", "value": 0.3},
        ],
        "sort_by": "debt_to_equity",
        "sort_order": "asc",
    },
    "blue_chip": {
        "name": "Blue Chip",
        "description": "Large, stable, profitable companies with strong health scores",
        "filters": [
            {"field": "overall_score", "operator": ">=", "value": 75},
            {"field": "roe", "operator": ">=", "value": 15},
            {"field": "revenue_cagr_3yr", "operator": ">=", "value": 8},
        ],
        "sort_by": "overall_score",
        "sort_order": "desc",
    },
    "momentum": {
        "name": "Momentum",
        "description": "High growth momentum across revenue and profit",
        "filters": [
            {"field": "revenue_cagr_3yr", "operator": ">=", "value": 20},
            {"field": "pat_cagr_3yr", "operator": ">=", "value": 20},
            {"field": "eps_cagr_3yr", "operator": ">=", "value": 15},
        ],
        "sort_by": "revenue_cagr_3yr",
        "sort_order": "desc",
    },
    "quality": {
        "name": "Quality",
        "description": "High quality companies with strong profitability and low debt",
        "filters": [
            {"field": "roe", "operator": ">=", "value": 18},
            {"field": "roa", "operator": ">=", "value": 12},
            {"field": "debt_to_equity", "operator": "<=", "value": 0.5},
            {"field": "interest_coverage", "operator": ">=", "value": 3},
        ],
        "sort_by": "roe",
        "sort_order": "desc",
    },
    "undervalued": {
        "name": "Undervalued",
        "description": "Low valuation multiples with decent fundamentals",
        "filters": [
            {"field": "pe_ratio", "operator": "<=", "value": 15},
            {"field": "pb_ratio", "operator": "<=", "value": 2},
            {"field": "roe", "operator": ">=", "value": 12},
        ],
        "sort_by": "pe_ratio",
        "sort_order": "asc",
    },
    "healthy_companies": {
        "name": "Healthy Companies",
        "description": "Companies with excellent overall health scores",
        "filters": [
            {"field": "overall_score", "operator": ">=", "value": 80},
        ],
        "sort_by": "overall_score",
        "sort_order": "desc",
    },
}

# =============================================================================
# OUTPUT COLUMNS
# =============================================================================

DEFAULT_OUTPUT_COLUMNS = [
    "company_id",
    "company_name",
    "period",
    "sector",
    "industry",
    # Valuation
    "pe_ratio",
    "pb_ratio",
    "ps_ratio",
    # Profitability
    "roe",
    "roa",
    "net_profit_margin",
    "operating_profit_margin",
    "roce",
    # Growth
    "revenue_cagr_3yr",
    "pat_cagr_3yr",
    "eps_cagr_3yr",
    # Cash Flow
    "free_cash_flow",
    "fcf_margin",
    "cash_conversion",
    # Leverage
    "debt_to_equity",
    "current_ratio",
    "quick_ratio",
    "interest_coverage",
    # Health
    "overall_score",
    "rating",
    "profitability_score",
    "growth_score",
    "cashflow_score",
    "leverage_score",
    "efficiency_score",
    # Dividend
    "dividend_yield",
]

# =============================================================================
# PERFORMANCE
# =============================================================================

MAX_RECORDS_LIMIT = 10000  # Maximum records to return in a single query

# =============================================================================
# LOGGING
# =============================================================================

SCREENER_LOG_NAME = "screener.log"