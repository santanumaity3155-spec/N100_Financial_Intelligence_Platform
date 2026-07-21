"""
constants.py

Constants for the Financial Health Score Engine (Module 5).

Defines score weights, normalization thresholds, rating bands,
and remark templates used throughout the engine.
"""

from typing import Dict, List, Tuple

# =============================================================================
# CATEGORY WEIGHTS
# =============================================================================

CATEGORY_WEIGHTS: Dict[str, float] = {
    "profitability": 0.30,
    "growth": 0.20,
    "cashflow": 0.20,
    "leverage": 0.15,
    "efficiency": 0.15,
}

# =============================================================================
# SCORE BOUNDARIES
# =============================================================================

SCORE_MIN: float = 0.0
SCORE_MAX: float = 100.0

# =============================================================================
# PROFITABILITY SCORE SETTINGS
# =============================================================================

# Expected ranges for normalization (typical values)
PROFITABILITY_RANGES: Dict[str, Tuple[float, float]] = {
    "roe": (-50.0, 50.0),        # Return on Equity (%)
    "roce": (-30.0, 60.0),       # Return on Capital Employed (%)
    "roa": (-20.0, 30.0),        # Return on Assets (%)
    "net_profit_margin": (-30.0, 60.0),   # Net Profit Margin (%)
    "operating_profit_margin": (-20.0, 50.0),  # Operating Profit Margin (%)
}

PROFITABILITY_METRICS: List[str] = [
    "roe", "roce", "roa", "net_profit_margin", "operating_profit_margin",
]

# =============================================================================
# GROWTH SCORE SETTINGS
# =============================================================================

GROWTH_CAGR_FIELDS: List[str] = [
    "revenue_cagr_3yr",
    "pat_cagr_3yr",
    "eps_cagr_3yr",
]

# CAGR normalization: typical range -50% to +100%
CAGR_MIN: float = -50.0
CAGR_MAX: float = 100.0

# =============================================================================
# CASH FLOW SCORE SETTINGS
# =============================================================================

# Capital Allocation Rating → numeric score mapping
CAPITAL_ALLOCATION_MAP: Dict[str, float] = {
    "EXCELLENT": 100.0,
    "GOOD": 80.0,
    "MODERATE": 60.0,
    "WEAK": 40.0,
    "DISTRESSED": 20.0,
}

# Also handle title case / mixed case variants
CAPITAL_ALLOCATION_MAP_NORMALIZED: Dict[str, float] = {
    k.upper(): v for k, v in CAPITAL_ALLOCATION_MAP.items()
}
for k, v in list(CAPITAL_ALLOCATION_MAP.items()):
    CAPITAL_ALLOCATION_MAP_NORMALIZED[k.title()] = v
    CAPITAL_ALLOCATION_MAP_NORMALIZED[k.capitalize()] = v

# FCF Margin normalization range (%)
FCF_MARGIN_MIN: float = -50.0
FCF_MARGIN_MAX: float = 50.0

# Cash Conversion normalization range (%)
CASH_CONVERSION_MIN: float = 0.0
CASH_CONVERSION_MAX: float = 200.0

# Cash ROA normalization range (%)
CASH_ROA_MIN: float = -20.0
CASH_ROA_MAX: float = 40.0

# =============================================================================
# LEVERAGE SCORE SETTINGS
# =============================================================================

# Ideal D/E ratio range
DE_TO_EQUITY_IDEAL_MAX: float = 1.0
DE_TO_EQUITY_HIGH: float = 2.0
DE_TO_EQUITY_VERY_HIGH: float = 5.0

# Interest Coverage thresholds
INTEREST_COVERAGE_SAFE: float = 3.0
INTEREST_COVERAGE_MINIMAL: float = 1.5

# Penalties
HIGH_LEVERAGE_PENALTY: float = 20.0
NEGATIVE_EQUITY_PENALTY: float = 30.0
LOW_INTEREST_COVERAGE_PENALTY: float = 15.0

# =============================================================================
# EFFICIENCY SCORE SETTINGS
# =============================================================================

# Asset Turnover normalization
ASSET_TURNOVER_MIN: float = 0.0
ASSET_TURNOVER_MAX: float = 3.0

# =============================================================================
# RATING SYSTEM
# =============================================================================

RATING_BANDS: List[Tuple[float, float, str]] = [
    (90.0, 100.0, "Excellent"),
    (75.0, 89.99, "Strong"),
    (60.0, 74.99, "Healthy"),
    (45.0, 59.99, "Moderate"),
    (30.0, 44.99, "Weak"),
    (0.0, 29.99, "Distressed"),
]

# =============================================================================
# REMARK TEMPLATES
# =============================================================================

REMARK_TEMPLATES: Dict[str, Dict[str, str]] = {
    "profitability": {
        "excellent": "Excellent profitability with strong margins and returns",
        "good": "Good profitability with healthy margins",
        "moderate": "Moderate profitability with average margins",
        "weak": "Weak profitability with low or negative margins",
        "poor": "Poor profitability with significant losses",
    },
    "growth": {
        "excellent": "Exceptional revenue and earnings growth trajectory",
        "good": "Strong growth across revenue and earnings",
        "moderate": "Moderate growth performance",
        "weak": "Weak or flat growth trends",
        "negative": "Negative growth trend, declining operations",
    },
    "cashflow": {
        "excellent": "Excellent cash generation with strong capital allocation",
        "good": "Strong cash flow generation and healthy conversion",
        "moderate": "Adequate cash flow generation",
        "weak": "Weak cash generation ability",
        "poor": "Poor cash generation, potential liquidity concerns",
    },
    "leverage": {
        "low": "Low leverage with strong debt servicing capacity",
        "moderate": "Manageable debt levels",
        "high": "High leverage risk, elevated debt burden",
        "very_high": "Very high leverage with significant financial risk",
        "critical": "Critical leverage levels, negative equity concern",
    },
    "efficiency": {
        "excellent": "Excellent asset utilization and operational efficiency",
        "good": "Strong asset turnover and operational efficiency",
        "moderate": "Adequate asset utilization",
        "weak": "Weak asset utilization, low operational efficiency",
        "poor": "Poor asset utilization, significant efficiency concerns",
    },
}

# =============================================================================
# OUTPUT PATHS
# =============================================================================

HEALTH_SCORE_LOG_NAME: str = "health_score.log"
HEALTH_SCORE_CSV_NAME: str = "financial_health_scores.csv"

# =============================================================================
# DATABASE TABLE NAME
# =============================================================================

HEALTH_SCORE_TABLE: str = "financial_health_scores"

