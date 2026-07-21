"""
engine.py

Financial Health Score Engine (Module 5) for the N100 Financial Intelligence Platform.

This module calculates an overall Financial Health Score (0–100) for every company
using the KPIs generated in Module 4 (financial_ratios table). It does NOT recalculate
any KPIs — it solely consumes the existing data.

Responsibilities:
1. Load data from the financial_ratios table
2. Calculate category scores: profitability, growth, cash flow, leverage, efficiency
3. Calculate weighted overall score
4. Generate qualitative ratings and remarks
5. Save results to financial_health_scores table (UPSERT, transactions, rollback)
6. Export results to CSV
7. Comprehensive logging and validation
"""

import csv
import logging
import math
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import numpy as np
import sqlite3

from src.config.logging_config import get_logger
from src.config.constants import LOG_DIR, OUTPUT_DIR
from src.database.connection import get_connection, commit, rollback
from src.database.schema import get_table_schema
from src.health_score.constants import (
    CATEGORY_WEIGHTS,
    SCORE_MIN,
    SCORE_MAX,
    PROFITABILITY_RANGES,
    PROFITABILITY_METRICS,
    GROWTH_CAGR_FIELDS,
    CAGR_MIN,
    CAGR_MAX,
    CAPITAL_ALLOCATION_MAP,
    CAPITAL_ALLOCATION_MAP_NORMALIZED,
    FCF_MARGIN_MIN,
    FCF_MARGIN_MAX,
    CASH_CONVERSION_MIN,
    CASH_CONVERSION_MAX,
    CASH_ROA_MIN,
    CASH_ROA_MAX,
    DE_TO_EQUITY_IDEAL_MAX,
    DE_TO_EQUITY_HIGH,
    DE_TO_EQUITY_VERY_HIGH,
    INTEREST_COVERAGE_SAFE,
    INTEREST_COVERAGE_MINIMAL,
    HIGH_LEVERAGE_PENALTY,
    NEGATIVE_EQUITY_PENALTY,
    LOW_INTEREST_COVERAGE_PENALTY,
    ASSET_TURNOVER_MIN,
    ASSET_TURNOVER_MAX,
    RATING_BANDS,
    REMARK_TEMPLATES,
    HEALTH_SCORE_LOG_NAME,
    HEALTH_SCORE_CSV_NAME,
    HEALTH_SCORE_TABLE,
)

logger = get_logger(__name__)

# =============================================================================
# OUTPUT PATHS
# =============================================================================

HEALTH_SCORE_LOG_PATH = LOG_DIR / HEALTH_SCORE_LOG_NAME
HEALTH_SCORE_CSV_PATH = OUTPUT_DIR / HEALTH_SCORE_CSV_NAME


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _is_valid_numeric(value: Any) -> bool:
    """Check if a value is a valid finite numeric value."""
    if value is None:
        return False
    if isinstance(value, (int, float)):
        if np.isnan(value) or np.isinf(value):
            return False
        return True
    if isinstance(value, np.generic):
        try:
            val = float(value)
            if np.isnan(val) or np.isinf(val):
                return False
            return True
        except (ValueError, TypeError):
            return False
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False


def _safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    """Safely convert a value to float, returning default on failure."""
    try:
        val = float(value)
        if np.isnan(val) or np.isinf(val):
            return default
        return val
    except (ValueError, TypeError, OverflowError):
        return default


def _normalize_score(
    value: Optional[float],
    min_val: float,
    max_val: float,
    invert: bool = False,
) -> Optional[float]:
    """
    Normalize a value to a 0–100 score based on expected min/max range.

    Parameters
    ----------
    value : Optional[float]
        The raw metric value
    min_val : float
        Minimum expected value (maps to 0)
    max_val : float
        Maximum expected value (maps to 100)
    invert : bool, optional
        If True, higher raw values give lower scores (e.g. for leverage), by default False

    Returns
    -------
    Optional[float]
        Normalized score between 0 and 100, or None if input is invalid
    """
    if value is None:
        return None

    # Clamp value to expected range
    clamped = max(min_val, min(max_val, value))

    # Normalize
    if max_val == min_val:
        return 50.0  # Default middle score

    if invert:
        score = ((max_val - clamped) / (max_val - min_val)) * 100.0
    else:
        score = ((clamped - min_val) / (max_val - min_val)) * 100.0

    return max(SCORE_MIN, min(SCORE_MAX, score))


def _get_cagr_value(row: pd.Series, field: str) -> Optional[float]:
    """
    Safely extract CAGR value from a row, trying both direct field and nested dict.

    CAGR data may be stored as:
    - Direct float: row["revenue_cagr_3yr"] = 15.0
    - Dict string: row["revenue_cagr_3yr"] = '{"value": 15.0, "flag": null}'

    Parameters
    ----------
    row : pd.Series
        Row from financial_ratios DataFrame
    field : str
        CAGR field name

    Returns
    -------
    Optional[float]
        CAGR value, or None if not available
    """
    value = row.get(field)
    if value is None:
        return None

    # If it's already numeric
    if isinstance(value, (int, float)):
        if np.isnan(value) or np.isinf(value):
            return None
        return float(value)

    # If it's a string dict representation (from JSON)
    if isinstance(value, str):
        try:
            import json
            parsed = json.loads(value)
            if isinstance(parsed, dict):
                return _safe_float(parsed.get("value"))
        except (json.JSONDecodeError, ValueError, TypeError):
            pass

    return _safe_float(value)


# =============================================================================
# HEALTH SCORE ENGINE
# =============================================================================

class HealthScoreEngine:
    """
    Financial Health Score Engine.

    Calculates an overall Financial Health Score (0–100) for every company
    using KPIs from the financial_ratios table.
    """

    def __init__(self, output_dir: Path = OUTPUT_DIR):
        """
        Initialize the Health Score Engine.

        Parameters
        ----------
        output_dir : Path, optional
            Output directory for CSV exports and logs, by default OUTPUT_DIR
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        LOG_DIR.mkdir(parents=True, exist_ok=True)

        # File handler for dedicated health score log
        self._setup_dedicated_logger()

        self.data: Optional[pd.DataFrame] = None
        self.results: List[Dict[str, Any]] = []

        self.pipeline_stats: Dict[str, Any] = {
            "start_time": None,
            "end_time": None,
            "status": "not_started",
            "total_companies": 0,
            "companies_processed": 0,
            "companies_skipped": 0,
            "companies_failed": 0,
            "rows_inserted": 0,
            "rows_skipped": 0,
            "errors": [],
            "warnings": [],
            "duplicates_found": 0,
            "missing_metrics_summary": {
                "profitability": 0,
                "growth": 0,
                "cashflow": 0,
                "leverage": 0,
                "efficiency": 0,
            },
        }

    def _setup_dedicated_logger(self) -> None:
        """Set up a dedicated file handler for the health score log."""
        try:
            self._file_handler = logging.FileHandler(
                HEALTH_SCORE_LOG_PATH, encoding="utf-8", mode="a"
            )
            formatter = logging.Formatter(
                "%(asctime)s | %(levelname)s | %(message)s"
            )
            self._file_handler.setFormatter(formatter)
            self._file_handler.setLevel(logging.INFO)

            # Add handler to the module logger
            logger.addHandler(self._file_handler)
        except Exception as e:
            logger.warning(f"Could not set up dedicated log file: {e}")
            self._file_handler = None

    # ------------------------------------------------------------------
    # DATA LOADING
    # ------------------------------------------------------------------

    def load_data(self) -> pd.DataFrame:
        """
        Load financial ratios data from the database.

        Returns
        -------
        pd.DataFrame
            DataFrame containing all financial ratios records
        """
        logger.info("Loading financial ratios data...")

        try:
            conn = get_connection()

            query = "SELECT * FROM financial_ratios ORDER BY company_id, period"
            self.data = pd.read_sql_query(query, conn)

            logger.info(
                f"Loaded {len(self.data)} records from financial_ratios table"
            )

            if self.data.empty:
                logger.warning("No data found in financial_ratios table")
                return self.data

            # Log available columns
            available_cols = list(self.data.columns)
            logger.info(f"Available columns: {available_cols}")
            
            # Log which optional columns are missing (INFO level, not warning)
            optional_cols = {
                'growth': ['revenue_cagr_3yr', 'pat_cagr_3yr', 'eps_cagr_3yr'],
                'cashflow': ['free_cash_flow', 'fcf_margin', 'cash_conversion', 
                            'cash_return_on_assets', 'capital_allocation_rating'],
                'efficiency': ['asset_turnover'],
                'leverage': ['interest_coverage', 'high_leverage_flag'],
                'profitability': ['roce', 'net_profit_margin', 'operating_profit_margin']
            }
            
            missing_optional = {}
            for category, cols in optional_cols.items():
                missing = [c for c in cols if c not in available_cols]
                if missing:
                    missing_optional[category] = missing
            
            if missing_optional:
                logger.info(
                    f"Optional columns not available in database schema: {missing_optional}. "
                    f"Engine will calculate scores using only available metrics."
                )

            return self.data

        except Exception as e:
            logger.error(f"Failed to load financial ratios data: {str(e)}")
            self.pipeline_stats["errors"].append(f"Data loading failed: {str(e)}")
            raise

    # ------------------------------------------------------------------
    # SCORE CALCULATION METHODS
    # ------------------------------------------------------------------

    def calculate_profitability_score(self, row: pd.Series) -> Optional[float]:
        """
        Calculate profitability score (0–100) using ROE, ROCE, ROA, NPM, OPM.

        Parameters
        ----------
        row : pd.Series
            Row from financial_ratios DataFrame

        Returns
        -------
        Optional[float]
            Profitability score between 0 and 100, or None if no valid metrics
        """
        scores = []

        for metric in PROFITABILITY_METRICS:
            value = _safe_float(row.get(metric))
            if value is not None:
                min_val, max_val = PROFITABILITY_RANGES.get(metric, (-50, 50))
                score = _normalize_score(value, min_val, max_val)
                if score is not None:
                    scores.append(score)

        if not scores:
            logger.debug(f"No profitability metrics available")
            return None

        avg_score = sum(scores) / len(scores)
        logger.debug(f"Profitability score: {avg_score:.2f} (from {len(scores)} metrics)")
        return round(max(SCORE_MIN, min(SCORE_MAX, avg_score)), 2)

    def calculate_growth_score(self, row: pd.Series) -> Optional[float]:
        """
        Calculate growth score (0–100) using Revenue CAGR, PAT CAGR, EPS CAGR.

        Handles negative CAGR, turnaround companies, loss-making companies,
        and missing values gracefully.

        Parameters
        ----------
        row : pd.Series
            Row from financial_ratios DataFrame

        Returns
        -------
        Optional[float]
            Growth score between 0 and 100, or None if no valid CAGR data
        """
        scores = []

        for field in GROWTH_CAGR_FIELDS:
            cagr_value = _get_cagr_value(row, field)

            if cagr_value is not None:
                # Check for negative CAGR (loss-making, turnaround)
                score = _normalize_score(cagr_value, CAGR_MIN, CAGR_MAX)
                if score is not None:
                    scores.append(score)
                    logger.debug(
                        f"Growth metric {field}: value={cagr_value:.2f}%, score={score:.2f}"
                    )

        if not scores:
            # No CAGR data available - try flag fields for context
            logger.debug("No CAGR data available for growth score")
            return None

        avg_score = sum(scores) / len(scores)
        logger.debug(f"Growth score: {avg_score:.2f} (from {len(scores)} metrics)")
        return round(max(SCORE_MIN, min(SCORE_MAX, avg_score)), 2)

    def calculate_cashflow_score(self, row: pd.Series) -> Optional[float]:
        """
        Calculate cash flow score (0–100) using FCF, FCF Margin,
        Cash Conversion, Cash ROA, and Capital Allocation Rating.

        Parameters
        ----------
        row : pd.Series
            Row from financial_ratios DataFrame

        Returns
        -------
        Optional[float]
            Cash flow score between 0 and 100, or None if no valid metrics
        """
        scores = []

        # 1. Free Cash Flow (raw FCF normalized)
        fcf = _safe_float(row.get("free_cash_flow"))
        if fcf is not None:
            # Normalize FCF: positive is good, negative is bad
            # Scale: FCF in millions, range -5000 to +5000 (adjustable)
            fcf_score = _normalize_score(fcf, -5000, 5000)
            scores.append(fcf_score)

        # 2. FCF Margin
        fcf_margin = _safe_float(row.get("fcf_margin"))
        if fcf_margin is not None:
            score = _normalize_score(fcf_margin, FCF_MARGIN_MIN, FCF_MARGIN_MAX)
            if score is not None:
                scores.append(score)

        # 3. Cash Conversion
        cash_conv = _safe_float(row.get("cash_conversion"))
        if cash_conv is not None:
            score = _normalize_score(cash_conv, CASH_CONVERSION_MIN, CASH_CONVERSION_MAX)
            if score is not None:
                scores.append(score)

        # 4. Cash Return on Assets
        cash_roa = _safe_float(row.get("cash_return_on_assets"))
        if cash_roa is not None:
            score = _normalize_score(cash_roa, CASH_ROA_MIN, CASH_ROA_MAX)
            if score is not None:
                scores.append(score)

        # 5. Capital Allocation Rating
        cap_alloc = row.get("capital_allocation_rating")
        if cap_alloc is not None and isinstance(cap_alloc, str):
            cap_score = CAPITAL_ALLOCATION_MAP_NORMALIZED.get(cap_alloc.upper())
            if cap_score is not None:
                scores.append(cap_score)

        if not scores:
            logger.debug("No cash flow metrics available")
            return None

        avg_score = sum(scores) / len(scores)
        logger.debug(f"Cash flow score: {avg_score:.2f} (from {len(scores)} metrics)")
        return round(max(SCORE_MIN, min(SCORE_MAX, avg_score)), 2)

    def calculate_leverage_score(self, row: pd.Series) -> Optional[float]:
        """
        Calculate leverage score (0–100) using Debt to Equity,
        Interest Coverage, and High Leverage Flag.

        Applies penalties for:
        - High leverage (D/E > 2.0)
        - Very high leverage (D/E > 5.0)
        - Negative equity
        - Low interest coverage (< 1.5)

        Parameters
        ----------
        row : pd.Series
            Row from financial_ratios DataFrame

        Returns
        -------
        Optional[float]
            Leverage score between 0 and 100, or None if no valid metrics
        """
        # Start with a neutral score
        score = 80.0
        metrics_available = False

        # 1. Debt to Equity assessment
        de = _safe_float(row.get("debt_to_equity"))
        if de is not None:
            metrics_available = True
            if de < 0:
                # Negative equity
                score -= NEGATIVE_EQUITY_PENALTY
                logger.warning(f"Negative equity detected (D/E={de}), applying penalty")
            elif de == 0:
                # Debt-free company - excellent
                score = min(score + 10, 100)
            elif de <= DE_TO_EQUITY_IDEAL_MAX:
                # Ideal range - no penalty
                score = min(score + 5, 100)
            elif de <= DE_TO_EQUITY_HIGH:
                # Moderate leverage - small penalty
                score -= 10
            elif de <= DE_TO_EQUITY_VERY_HIGH:
                # High leverage
                score -= HIGH_LEVERAGE_PENALTY
            else:
                # Very high leverage
                score -= HIGH_LEVERAGE_PENALTY * 1.5

        # 2. Interest Coverage assessment
        icr = _safe_float(row.get("interest_coverage"))
        if icr is not None:
            metrics_available = True
            if icr >= INTEREST_COVERAGE_SAFE:
                score = min(score + 5, 100)
            elif icr >= INTEREST_COVERAGE_MINIMAL:
                # Minimal coverage - small penalty
                score -= 10
            elif icr > 0:
                # Low coverage
                score -= LOW_INTEREST_COVERAGE_PENALTY
            elif icr == 0:
                # No interest (debt-free) - positive
                score = min(score + 10, 100)
            else:
                # Negative ICR (loss-making)
                score -= LOW_INTEREST_COVERAGE_PENALTY * 1.5

        # 3. High Leverage Flag
        high_leverage = row.get("high_leverage_flag")
        if high_leverage is not None:
            try:
                if int(high_leverage) == 1:
                    metrics_available = True
                    score -= HIGH_LEVERAGE_PENALTY * 0.5
                    logger.debug("High leverage flag triggered, applying additional penalty")
            except (ValueError, TypeError):
                pass

        if not metrics_available:
            logger.debug("No leverage metrics available")
            return None

        final_score = max(SCORE_MIN, min(SCORE_MAX, score))
        logger.debug(f"Leverage score: {final_score:.2f}")
        return round(final_score, 2)

    def calculate_efficiency_score(self, row: pd.Series) -> Optional[float]:
        """
        Calculate efficiency score (0–100) using Asset Turnover.

        Parameters
        ----------
        row : pd.Series
            Row from financial_ratios DataFrame

        Returns
        -------
        Optional[float]
            Efficiency score between 0 and 100, or None if no valid metrics
        """
        asset_turn = _safe_float(row.get("asset_turnover"))

        if asset_turn is None:
            logger.debug("No asset turnover data available")
            return None

        score = _normalize_score(asset_turn, ASSET_TURNOVER_MIN, ASSET_TURNOVER_MAX)
        logger.debug(f"Efficiency score: {score:.2f} (asset_turnover={asset_turn:.2f})")
        return score

    def calculate_overall_score(self, scores: Dict[str, Optional[float]]) -> Optional[float]:
        """
        Calculate overall weighted Financial Health Score.

        Weights:
        - Profitability: 30%
        - Growth: 20%
        - Cash Flow: 20%
        - Leverage: 15%
        - Efficiency: 15%

        Parameters
        ----------
        scores : Dict[str, Optional[float]]
            Dictionary of category scores

        Returns
        -------
        Optional[float]
            Overall score between 0 and 100, or None if no categories available
        """
        weighted_sum = 0.0
        total_weight = 0.0

        for category, weight in CATEGORY_WEIGHTS.items():
            cat_score = scores.get(category)
            if cat_score is not None and _is_valid_numeric(cat_score):
                weighted_sum += cat_score * weight
                total_weight += weight
                logger.debug(
                    f"Category '{category}': score={cat_score:.2f}, "
                    f"weight={weight:.2f}, contribution={cat_score * weight:.2f}"
                )

        if total_weight == 0:
            logger.warning("No valid category scores available for overall calculation")
            return None

        # Normalize by actual weight used
        # Scores are already 0-100, so weighted_sum gives max 100 when total_weight=1.0
        if total_weight > 0:
            overall = weighted_sum / total_weight
        else:
            overall = weighted_sum

        overall = max(SCORE_MIN, min(SCORE_MAX, overall))

        logger.debug(
            f"Overall score: {overall:.2f} (weighted_sum={weighted_sum:.2f}, "
            f"total_weight={total_weight:.2f})"
        )
        return round(overall, 2)

    # ------------------------------------------------------------------
    # RATING & REMARKS
    # ------------------------------------------------------------------

    def generate_rating(self, overall_score: Optional[float]) -> str:
        """
        Generate qualitative rating based on overall score.

        Rating bands:
        90–100 → Excellent
        75–89  → Strong
        60–74  → Healthy
        45–59  → Moderate
        30–44  → Weak
        0–29   → Distressed

        Parameters
        ----------
        overall_score : Optional[float]
            Overall Financial Health Score

        Returns
        -------
        str
            Qualitative rating
        """
        if overall_score is None:
            return "Insufficient Data"

        for band_min, band_max, rating in RATING_BANDS:
            if band_min <= overall_score <= band_max:
                return rating

        # Fallback
        if overall_score > 100:
            return "Excellent"
        return "Distressed"

    def generate_remarks(self, scores: Dict[str, Optional[float]]) -> str:
        """
        Automatically generate meaningful remarks based on category scores.

        Parameters
        ----------
        scores : Dict[str, Optional[float]]
            Dictionary of category scores

        Returns
        -------
        str
            Combined remarks string
        """
        remarks_parts = []

        # Profitability remarks
        prof_score = scores.get("profitability")
        if prof_score is not None:
            if prof_score >= 80:
                remarks_parts.append(REMARK_TEMPLATES["profitability"]["excellent"])
            elif prof_score >= 60:
                remarks_parts.append(REMARK_TEMPLATES["profitability"]["good"])
            elif prof_score >= 40:
                remarks_parts.append(REMARK_TEMPLATES["profitability"]["moderate"])
            elif prof_score >= 20:
                remarks_parts.append(REMARK_TEMPLATES["profitability"]["weak"])
            else:
                remarks_parts.append(REMARK_TEMPLATES["profitability"]["poor"])

        # Growth remarks
        growth_score = scores.get("growth")
        if growth_score is not None:
            if growth_score >= 80:
                remarks_parts.append(REMARK_TEMPLATES["growth"]["excellent"])
            elif growth_score >= 60:
                remarks_parts.append(REMARK_TEMPLATES["growth"]["good"])
            elif growth_score >= 40:
                remarks_parts.append(REMARK_TEMPLATES["growth"]["moderate"])
            elif growth_score >= 20:
                remarks_parts.append(REMARK_TEMPLATES["growth"]["weak"])
            else:
                remarks_parts.append(REMARK_TEMPLATES["growth"]["negative"])

        # Cash flow remarks
        cf_score = scores.get("cashflow")
        if cf_score is not None:
            if cf_score >= 80:
                remarks_parts.append(REMARK_TEMPLATES["cashflow"]["excellent"])
            elif cf_score >= 60:
                remarks_parts.append(REMARK_TEMPLATES["cashflow"]["good"])
            elif cf_score >= 40:
                remarks_parts.append(REMARK_TEMPLATES["cashflow"]["moderate"])
            elif cf_score >= 20:
                remarks_parts.append(REMARK_TEMPLATES["cashflow"]["weak"])
            else:
                remarks_parts.append(REMARK_TEMPLATES["cashflow"]["poor"])

        # Leverage remarks
        lev_score = scores.get("leverage")
        if lev_score is not None:
            if lev_score >= 80:
                remarks_parts.append(REMARK_TEMPLATES["leverage"]["low"])
            elif lev_score >= 60:
                remarks_parts.append(REMARK_TEMPLATES["leverage"]["moderate"])
            elif lev_score >= 40:
                remarks_parts.append(REMARK_TEMPLATES["leverage"]["high"])
            elif lev_score >= 20:
                remarks_parts.append(REMARK_TEMPLATES["leverage"]["very_high"])
            else:
                remarks_parts.append(REMARK_TEMPLATES["leverage"]["critical"])

        # Efficiency remarks
        eff_score = scores.get("efficiency")
        if eff_score is not None:
            if eff_score >= 80:
                remarks_parts.append(REMARK_TEMPLATES["efficiency"]["excellent"])
            elif eff_score >= 60:
                remarks_parts.append(REMARK_TEMPLATES["efficiency"]["good"])
            elif eff_score >= 40:
                remarks_parts.append(REMARK_TEMPLATES["efficiency"]["moderate"])
            elif eff_score >= 20:
                remarks_parts.append(REMARK_TEMPLATES["efficiency"]["weak"])
            else:
                remarks_parts.append(REMARK_TEMPLATES["efficiency"]["poor"])

        if not remarks_parts:
            return "Insufficient data for remarks generation"

        # Combine remarks with semicolons
        combined = "; ".join(remarks_parts)
        return combined

    # ------------------------------------------------------------------
    # COMPANY PROCESSING
    # ------------------------------------------------------------------

    def _process_company_row(
        self, row: pd.Series
    ) -> Tuple[Optional[Dict[str, Any]], List[str]]:
        """
        Process a single company-period row and calculate health scores.

        Parameters
        ----------
        row : pd.Series
            A row from the financial_ratios DataFrame

        Returns
        -------
        Tuple[Optional[Dict[str, Any]], List[str]]
            (Result dictionary or None if invalid, list of warnings)
        """
        warnings = []

        # Extract identifiers
        company_id = row.get("company_id")
        period = row.get("period")

        # Validate identifiers
        if pd.isna(company_id) or not str(company_id).strip():
            warnings.append("Missing or invalid company_id")
            return None, warnings

        if pd.isna(period) or not str(period).strip():
            warnings.append("Missing or invalid period")
            return None, warnings

        company_id = str(company_id)
        period = str(period)

        # Calculate category scores
        profitability_score = self.calculate_profitability_score(row)
        growth_score = self.calculate_growth_score(row)
        cashflow_score = self.calculate_cashflow_score(row)
        leverage_score = self.calculate_leverage_score(row)
        efficiency_score = self.calculate_efficiency_score(row)

        category_scores = {
            "profitability": profitability_score,
            "growth": growth_score,
            "cashflow": cashflow_score,
            "leverage": leverage_score,
            "efficiency": efficiency_score,
        }

        # Track warnings for missing categories
        missing_categories = []
        for cat, score in category_scores.items():
            if score is None:
                missing_categories.append(cat)
                # Track missing metrics for summary statistics
                if cat in self.pipeline_stats["missing_metrics_summary"]:
                    self.pipeline_stats["missing_metrics_summary"][cat] += 1
        
        # Only add to warnings list if ALL categories are missing (truly insufficient data)
        # Missing individual categories is expected and not a warning-worthy event
        if len(missing_categories) == len(category_scores):
            warning_msg = (
                f"All category metrics missing for {company_id}, period {period} - "
                f"cannot calculate health score"
            )
            warnings.append(warning_msg)
            logger.warning(warning_msg)
        elif missing_categories:
            # Log at DEBUG level only - don't add to warnings list
            logger.debug(
                f"Missing metrics for {company_id}, period {period}: "
                f"{', '.join(missing_categories)} "
                f"(expected for early periods with limited historical data)"
            )

        # Calculate overall score
        overall_score = self.calculate_overall_score(category_scores)

        if overall_score is None:
            warnings.append(f"No valid scores for {company_id}, period {period}")
            return None, warnings

        # Generate rating and remarks
        rating = self.generate_rating(overall_score)
        remarks = self.generate_remarks(category_scores)

        # Build result
        company_name = row.get("company_name")
        if pd.isna(company_name):
            company_name = None

        result = {
            "company_id": company_id,
            "company_name": company_name,
            "period": period,
            "profitability_score": profitability_score,
            "growth_score": growth_score,
            "cashflow_score": cashflow_score,
            "leverage_score": leverage_score,
            "efficiency_score": efficiency_score,
            "overall_score": overall_score,
            "rating": rating,
            "remarks": remarks,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        return result, warnings

    # ------------------------------------------------------------------
    # DATABASE OPERATIONS
    # ------------------------------------------------------------------

    def _ensure_table_exists(self) -> None:
        """Ensure the financial_health_scores table exists."""
        try:
            conn = get_connection()
            schema = get_table_schema(HEALTH_SCORE_TABLE)
            conn.execute(schema)
            conn.commit()
            logger.info("Ensured financial_health_scores table exists")
        except Exception as e:
            logger.error(f"Failed to ensure table exists: {str(e)}")
            raise

    def save_to_database(self, records: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Save health score records to the database using UPSERT.

        Supports:
        - Transaction management
        - Rollback on failure
        - Duplicate prevention (INSERT OR REPLACE)
        - Foreign key validation
        - Proper connection handling

        Parameters
        ----------
        records : List[Dict[str, Any]]
            List of health score records to save

        Returns
        -------
        Dict[str, int]
            Statistics: inserted, skipped, duplicates
        """
        stats = {"inserted": 0, "skipped": 0, "duplicates": 0}

        if not records:
            logger.warning("No records to save to database")
            return stats

        self._ensure_table_exists()

        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Begin transaction
            conn.execute("BEGIN TRANSACTION")

            for record in records:
                try:
                    # Check for existing record (duplicate detection)
                    cursor.execute(
                        f"SELECT id FROM {HEALTH_SCORE_TABLE} "
                        "WHERE company_id = ? AND period = ?",
                        (record["company_id"], record["period"]),
                    )
                    existing = cursor.fetchone()

                    if existing:
                        stats["duplicates"] += 1
                        logger.debug(
                            f"Updating existing record: {record['company_id']}, "
                            f"{record['period']}"
                        )

                    # Prepare column names and placeholders
                    columns = list(record.keys())
                    placeholders = ", ".join(["?"] * len(columns))
                    column_names = ", ".join(columns)
                    values = tuple(record.values())

                    # UPSERT: INSERT OR REPLACE
                    # This automatically handles duplicates by replacing the existing row
                    sql = f"""
                        INSERT OR REPLACE INTO {HEALTH_SCORE_TABLE}
                        ({column_names})
                        VALUES ({placeholders})
                    """
                    cursor.execute(sql, values)
                    stats["inserted"] += 1

                except sqlite3.IntegrityError as e:
                    # Foreign key violation - company_id doesn't exist in companies table
                    error_msg = str(e)
                    logger.warning(
                        f"Foreign key violation for {record.get('company_id')}: {error_msg}"
                    )
                    stats["skipped"] += 1
                    self.pipeline_stats["warnings"].append(
                        f"FK violation: {record.get('company_id')} ({record.get('period')}) - "
                        f"company not found in companies table"
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to insert record for {record.get('company_id')}, "
                        f"{record.get('period')}: {e}"
                    )
                    stats["skipped"] += 1

            # Commit transaction
            conn.commit()
            logger.info(
                f"Database save complete: {stats['inserted']} inserted/updated, "
                f"{stats['skipped']} skipped (FK violations), "
                f"{stats['duplicates']} existing records updated"
            )

        except Exception as e:
            # Rollback on failure
            if conn:
                try:
                    conn.rollback()
                    logger.error(f"Transaction rolled back due to error: {str(e)}")
                except Exception as rb_error:
                    logger.error(f"Rollback also failed: {str(rb_error)}")

            self.pipeline_stats["errors"].append(f"Database save failed: {str(e)}")
            raise

        finally:
            # Note: We don't close the connection here because get_connection() returns
            # a singleton connection that should remain open for the application lifetime.
            # The connection will be closed when the application exits.
            pass

        return stats

    # ------------------------------------------------------------------
    # CSV EXPORT
    # ------------------------------------------------------------------

    def export_csv(self, records: List[Dict[str, Any]]) -> Optional[Path]:
        """
        Export health score records to CSV.

        Parameters
        ----------
        records : List[Dict[str, Any]]
            List of health score records to export

        Returns
        -------
        Optional[Path]
            Path to the generated CSV file, or None if export failed
        """
        if not records:
            logger.warning("No records to export to CSV")
            return None

        csv_path = self.output_dir / HEALTH_SCORE_CSV_NAME

        try:
            fieldnames = [
                "company_id",
                "company_name",
                "period",
                "profitability_score",
                "growth_score",
                "cashflow_score",
                "leverage_score",
                "efficiency_score",
                "overall_score",
                "rating",
                "remarks",
            ]

            with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction="ignore")
                writer.writeheader()

                for record in records:
                    row = {k: record.get(k, "") for k in fieldnames}
                    writer.writerow(row)

            logger.info(f"CSV exported successfully: {csv_path} ({len(records)} records)")
            return csv_path

        except Exception as e:
            logger.error(f"Failed to export CSV: {str(e)}")
            self.pipeline_stats["errors"].append(f"CSV export failed: {str(e)}")
            return None

    # ------------------------------------------------------------------
    # MAIN PIPELINE
    # ------------------------------------------------------------------

    def run(self) -> Dict[str, Any]:
        """
        Run the complete Financial Health Score pipeline.

        Steps:
        1. Load financial ratios data
        2. Calculate scores for each company-period
        3. Save results to database
        4. Export results to CSV
        5. Log summary

        Returns
        -------
        Dict[str, Any]
            Pipeline statistics and results
        """
        start_time = time.time()
        self.pipeline_stats["start_time"] = datetime.now().isoformat()
        self.pipeline_stats["status"] = "running"

        logger.info("=" * 80)
        logger.info("FINANCIAL HEALTH SCORE ENGINE - STARTING")
        logger.info("=" * 80)

        try:
            # Step 1: Load data
            data = self.load_data()

            if data.empty:
                logger.warning("No data loaded, pipeline aborted")
                self.pipeline_stats["status"] = "completed_no_data"
                return self.pipeline_stats

            total_records = len(data)
            self.pipeline_stats["total_companies"] = total_records
            logger.info(f"Processing {total_records} company-period records")

            # Step 2: Calculate scores for each row
            valid_records = []

            for idx, row in data.iterrows():
                try:
                    result, warnings = self._process_company_row(row)

                    if result is not None:
                        valid_records.append(result)
                        self.pipeline_stats["companies_processed"] += 1
                    else:
                        self.pipeline_stats["companies_skipped"] += 1

                    self.pipeline_stats["warnings"].extend(warnings)

                except Exception as e:
                    self.pipeline_stats["companies_failed"] += 1
                    error_msg = (
                        f"Failed to process row {idx}: {str(e)}"
                    )
                    logger.error(error_msg)
                    self.pipeline_stats["errors"].append(error_msg)

            self.results = valid_records
            logger.info(
                f"Processed {self.pipeline_stats['companies_processed']} records, "
                f"{self.pipeline_stats['companies_skipped']} skipped, "
                f"{self.pipeline_stats['companies_failed']} failed"
            )

            # Step 3: Save to database
            if valid_records:
                db_stats = self.save_to_database(valid_records)
                self.pipeline_stats["rows_inserted"] = db_stats["inserted"]
                self.pipeline_stats["rows_skipped"] = db_stats["skipped"]
                self.pipeline_stats["duplicates_found"] = db_stats["duplicates"]

            # Step 4: Export to CSV
            if valid_records:
                csv_path = self.export_csv(valid_records)
                if csv_path:
                    logger.info(f"Results exported to {csv_path}")

            self.pipeline_stats["status"] = "completed"

        except Exception as e:
            self.pipeline_stats["status"] = "failed"
            error_msg = f"Pipeline execution failed: {str(e)}"
            logger.error(error_msg)
            self.pipeline_stats["errors"].append(error_msg)

        finally:
            self.pipeline_stats["end_time"] = datetime.now().isoformat()
            execution_time = time.time() - start_time

            # Log summary
            self._log_summary(execution_time)

        return self.pipeline_stats

    def _log_summary(self, execution_time: float) -> None:
        """Log pipeline execution summary."""
        stats = self.pipeline_stats

        # Build missing metrics summary
        missing_summary = stats.get("missing_metrics_summary", {})
        missing_lines = []
        for category, count in missing_summary.items():
            if count > 0:
                missing_lines.append(f"  {category.capitalize()} Metrics Missing: {count} records")
        
        missing_text = "\n".join(missing_lines) if missing_lines else "  None"

        summary = f"""
{'=' * 60}
FINANCIAL HEALTH SCORE ENGINE - SUMMARY
{'=' * 60}
Status: {stats['status']}
Total Records Processed: {stats['companies_processed']}
Records Skipped: {stats['companies_skipped']}
Records Failed: {stats['companies_failed']}
Rows Inserted in DB: {stats['rows_inserted']}
Rows Skipped in DB: {stats['rows_skipped']}
Duplicates Found: {stats['duplicates_found']}
Warnings: {len(stats['warnings'])}
Errors: {len(stats['errors'])}
Execution Time: {execution_time:.2f}s
{'-' * 60}
Missing Metrics Summary:
{missing_text}
{'=' * 60}
"""

        logger.info(summary)

        # Write to dedicated log file
        try:
            with open(HEALTH_SCORE_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(f"\n{summary}\n")
        except Exception as e:
            logger.warning(f"Could not write to log file: {e}")


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def run_health_score_pipeline() -> Dict[str, Any]:
    """
    Convenience function to run the Health Score Engine pipeline.

    Returns
    -------
    Dict[str, Any]
        Pipeline statistics
    """
    engine = HealthScoreEngine()
    return engine.run()


def get_health_score_statistics() -> Dict[str, Any]:
    """
    Get statistics from the financial_health_scores table.

    Returns
    -------
    Dict[str, Any]
        Database statistics
    """
    try:
        conn = get_connection()

        stats = {}

        # Total records
        cursor = conn.execute(f"SELECT COUNT(*) FROM {HEALTH_SCORE_TABLE}")
        stats["total_records"] = cursor.fetchone()[0]

        # Rating distribution
        cursor = conn.execute(f"""
            SELECT rating, COUNT(*) as count
            FROM {HEALTH_SCORE_TABLE}
            WHERE rating IS NOT NULL
            GROUP BY rating
            ORDER BY count DESC
        """)
        stats["rating_distribution"] = {
            row[0]: row[1] for row in cursor.fetchall()
        }

        # Average scores
        cursor = conn.execute(f"""
            SELECT
                AVG(profitability_score) as avg_profitability,
                AVG(growth_score) as avg_growth,
                AVG(cashflow_score) as avg_cashflow,
                AVG(leverage_score) as avg_leverage,
                AVG(efficiency_score) as avg_efficiency,
                AVG(overall_score) as avg_overall
            FROM {HEALTH_SCORE_TABLE}
        """)
        row = cursor.fetchone()
        if row:
            stats["averages"] = {
                "profitability": round(row[0], 2) if row[0] else None,
                "growth": round(row[1], 2) if row[1] else None,
                "cashflow": round(row[2], 2) if row[2] else None,
                "leverage": round(row[3], 2) if row[3] else None,
                "efficiency": round(row[4], 2) if row[4] else None,
                "overall": round(row[5], 2) if row[5] else None,
            }

        # Top performers
        cursor = conn.execute(f"""
            SELECT company_id, company_name, overall_score, rating
            FROM {HEALTH_SCORE_TABLE}
            ORDER BY overall_score DESC
            LIMIT 10
        """)
        stats["top_performers"] = [
            {
                "company_id": row[0],
                "company_name": row[1],
                "overall_score": row[2],
                "rating": row[3],
            }
            for row in cursor.fetchall()
        ]

        return stats

    except Exception as e:
        logger.error(f"Failed to get health score statistics: {str(e)}")
        return {}


# =============================================================================
# SCRIPT ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    import logging

    # Ensure the log handler is set up when run as script
    logger.info("Running Health Score Engine as script")
    stats = run_health_score_pipeline()
    print(f"Pipeline status: {stats['status']}")
    print(f"Records processed: {stats['companies_processed']}")
    print(f"Errors: {len(stats['errors'])}")

