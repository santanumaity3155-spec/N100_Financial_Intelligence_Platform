"""
health_score package

Financial Health Score Engine (Module 5) for the N100 Financial Intelligence Platform.

Exports:
- HealthScoreEngine: Main engine class
- run_health_score_pipeline: Convenience function
- get_health_score_statistics: Statistics function
- Constants for health score configuration
"""

from src.health_score.engine import (
    HealthScoreEngine,
    run_health_score_pipeline,
    get_health_score_statistics,
)

from src.health_score.constants import (
    CATEGORY_WEIGHTS,
    SCORE_MIN,
    SCORE_MAX,
    RATING_BANDS,
    REMARK_TEMPLATES,
    PROFITABILITY_METRICS,
    GROWTH_CAGR_FIELDS,
    CAPITAL_ALLOCATION_MAP,
    HEALTH_SCORE_TABLE,
)

__all__ = [
    "HealthScoreEngine",
    "run_health_score_pipeline",
    "get_health_score_statistics",
    "CATEGORY_WEIGHTS",
    "SCORE_MIN",
    "SCORE_MAX",
    "RATING_BANDS",
    "REMARK_TEMPLATES",
    "PROFITABILITY_METRICS",
    "GROWTH_CAGR_FIELDS",
    "CAPITAL_ALLOCATION_MAP",
    "HEALTH_SCORE_TABLE",
]

