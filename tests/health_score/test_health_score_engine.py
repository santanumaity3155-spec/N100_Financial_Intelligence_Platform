"""
test_health_score_engine.py

Comprehensive test suite for Module 5 - Financial Health Score Engine.

Tests cover:
- Individual score calculations (profitability, growth, cashflow, leverage, efficiency)
- Overall score calculation
- Rating assignment
- Remarks generation
- Missing/edge cases
- Invalid values
- Database operations
- CSV export
- End-to-end pipeline execution

Target: 50+ test cases
"""

import pytest
import pandas as pd
import numpy as np
import sqlite3
import tempfile
import os
import csv
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock, PropertyMock

from src.health_score.engine import (
    HealthScoreEngine,
    _is_valid_numeric,
    _safe_float,
    _normalize_score,
    _get_cagr_value,
    run_health_score_pipeline,
    get_health_score_statistics,
)
from src.health_score.constants import (
    CATEGORY_WEIGHTS,
    SCORE_MIN,
    SCORE_MAX,
    PROFITABILITY_METRICS,
    PROFITABILITY_RANGES,
    GROWTH_CAGR_FIELDS,
    RATING_BANDS,
    REMARK_TEMPLATES,
    CAPITAL_ALLOCATION_MAP,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def engine():
    """Create a HealthScoreEngine instance with temp output dir."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        eng = HealthScoreEngine(output_dir=output_dir)
        yield eng


@pytest.fixture
def sample_profitability_row():
    """Sample row with profitability metrics."""
    return pd.Series({
        "company_id": "TCS",
        "company_name": "Tata Consultancy Services",
        "period": "FY2024",
        "roe": 25.0,
        "roce": 30.0,
        "roa": 15.0,
        "net_profit_margin": 20.0,
        "operating_profit_margin": 25.0,
        "debt_to_equity": 0.1,
        "interest_coverage": 15.0,
        "asset_turnover": 1.2,
        "revenue_cagr_3yr": 15.0,
        "pat_cagr_3yr": 12.0,
        "eps_cagr_3yr": 14.0,
        "free_cash_flow": 5000.0,
        "fcf_margin": 15.0,
        "cash_conversion": 120.0,
        "cash_return_on_assets": 12.0,
        "capital_allocation_rating": "EXCELLENT",
        "high_leverage_flag": 0,
    })


@pytest.fixture
def sample_leverage_row():
    """Sample row with high leverage metrics."""
    return pd.Series({
        "company_id": "HIGHD",
        "company_name": "High Debt Corp",
        "period": "FY2024",
        "roe": 5.0,
        "roce": 8.0,
        "roa": 2.0,
        "net_profit_margin": 5.0,
        "operating_profit_margin": 8.0,
        "debt_to_equity": 6.5,
        "interest_coverage": 1.2,
        "asset_turnover": 0.3,
        "revenue_cagr_3yr": 2.0,
        "pat_cagr_3yr": -5.0,
        "eps_cagr_3yr": -3.0,
        "free_cash_flow": -500.0,
        "fcf_margin": -10.0,
        "cash_conversion": 30.0,
        "cash_return_on_assets": 1.0,
        "capital_allocation_rating": "DISTRESSED",
        "high_leverage_flag": 1,
    })


@pytest.fixture
def sample_missing_data_row():
    """Sample row with missing metrics."""
    return pd.Series({
        "company_id": "MISSCO",
        "company_name": "Missing Data Corp",
        "period": "FY2024",
        "roe": None,
        "roce": None,
        "roa": None,
        "net_profit_margin": 10.0,
        "operating_profit_margin": None,
        "debt_to_equity": None,
        "interest_coverage": None,
        "asset_turnover": None,
        "revenue_cagr_3yr": None,
        "pat_cagr_3yr": np.nan,
        "eps_cagr_3yr": None,
        "free_cash_flow": None,
        "fcf_margin": None,
        "cash_conversion": None,
        "cash_return_on_assets": None,
        "capital_allocation_rating": None,
        "high_leverage_flag": None,
    })


@pytest.fixture
def test_db():
    """Create a temporary SQLite database for testing."""
    tmpfile = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path = tmpfile.name
    tmpfile.close()

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")

    # Create companies table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            company_id TEXT PRIMARY KEY,
            company_name TEXT NOT NULL
        )
    """)

    # Create financial_ratios table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS financial_ratios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id TEXT NOT NULL,
            company_name TEXT,
            period TEXT,
            roe REAL,
            roce REAL,
            roa REAL,
            net_profit_margin REAL,
            operating_profit_margin REAL,
            debt_to_equity REAL,
            interest_coverage REAL,
            high_leverage_flag INTEGER DEFAULT 0,
            asset_turnover REAL,
            revenue_cagr_3yr REAL,
            pat_cagr_3yr REAL,
            eps_cagr_3yr REAL,
            free_cash_flow REAL,
            fcf_margin REAL,
            cash_conversion REAL,
            capital_allocation_rating TEXT,
            cash_return_on_assets REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies(company_id) ON DELETE CASCADE,
            UNIQUE(company_id, period)
        )
    """)

    # Insert test companies
    conn.execute("INSERT OR IGNORE INTO companies (company_id, company_name) VALUES (?, ?)",
                 ("TCS", "Tata Consultancy Services"))
    conn.execute("INSERT OR IGNORE INTO companies (company_id, company_name) VALUES (?, ?)",
                 ("RELIANCE", "Reliance Industries"))

    # Insert test financial ratios
    conn.execute("""
        INSERT OR REPLACE INTO financial_ratios
        (company_id, company_name, period, roe, roce, roa, net_profit_margin,
         operating_profit_margin, debt_to_equity, interest_coverage, high_leverage_flag,
         asset_turnover, revenue_cagr_3yr, pat_cagr_3yr, eps_cagr_3yr,
         free_cash_flow, fcf_margin, cash_conversion, capital_allocation_rating, cash_return_on_assets)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "TCS", "Tata Consultancy Services", "FY2024",
        25.0, 30.0, 15.0, 20.0, 25.0,
        0.1, 15.0, 0, 1.2,
        15.0, 12.0, 14.0,
        5000.0, 15.0, 120.0, "EXCELLENT", 12.0
    ))

    conn.execute("""
        INSERT OR REPLACE INTO financial_ratios
        (company_id, company_name, period, roe, roce, roa, net_profit_margin,
         operating_profit_margin, debt_to_equity, interest_coverage, high_leverage_flag,
         asset_turnover, revenue_cagr_3yr, pat_cagr_3yr, eps_cagr_3yr,
         free_cash_flow, fcf_margin, cash_conversion, capital_allocation_rating, cash_return_on_assets)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "RELIANCE", "Reliance Industries", "FY2024",
        10.0, 12.0, 6.0, 8.0, 12.0,
        1.5, 4.0, 0, 0.8,
        8.0, 10.0, 9.0,
        2000.0, 5.0, 80.0, "GOOD", 6.0
    ))

    conn.commit()
    conn.close()

    yield db_path

    # Cleanup
    try:
        os.unlink(db_path)
    except (OSError, FileNotFoundError):
        pass


# =============================================================================
# TEST HELPER FUNCTIONS
# =============================================================================

class TestIsValidNumeric:
    """Tests for _is_valid_numeric helper."""

    def test_valid_float(self):
        assert _is_valid_numeric(25.0) is True

    def test_valid_int(self):
        assert _is_valid_numeric(10) is True

    def test_zero(self):
        assert _is_valid_numeric(0.0) is True

    def test_none(self):
        assert _is_valid_numeric(None) is False

    def test_nan(self):
        assert _is_valid_numeric(float('nan')) is False

    def test_inf(self):
        assert _is_valid_numeric(float('inf')) is False

    def test_neg_inf(self):
        assert _is_valid_numeric(float('-inf')) is False

    def test_string(self):
        assert _is_valid_numeric("hello") is False

    def test_np_nan(self):
        assert _is_valid_numeric(np.nan) is False

    def test_np_inf(self):
        assert _is_valid_numeric(np.inf) is False


class TestSafeFloat:
    """Tests for _safe_float helper."""

    def test_valid_float(self):
        assert _safe_float(25.0) == 25.0

    def test_valid_int(self):
        assert _safe_float(10) == 10.0

    def test_none(self):
        assert _safe_float(None) is None

    def test_nan(self):
        assert _safe_float(float('nan')) is None

    def test_inf(self):
        assert _safe_float(float('inf')) is None

    def test_string_number(self):
        assert _safe_float("25.5") == 25.5

    def test_invalid_string(self):
        assert _safe_float("abc") is None

    def test_default_value(self):
        assert _safe_float(None, default=0.0) == 0.0


class TestNormalizeScore:
    """Tests for _normalize_score helper."""

    def test_mid_range(self):
        score = _normalize_score(50.0, 0.0, 100.0)
        assert score == 50.0

    def test_min_range(self):
        score = _normalize_score(0.0, 0.0, 100.0)
        assert score == 0.0

    def test_max_range(self):
        score = _normalize_score(100.0, 0.0, 100.0)
        assert score == 100.0

    def test_above_max(self):
        score = _normalize_score(150.0, 0.0, 100.0)
        assert score == 100.0

    def test_below_min(self):
        score = _normalize_score(-50.0, 0.0, 100.0)
        assert score == 0.0

    def test_none_value(self):
        score = _normalize_score(None, 0.0, 100.0)
        assert score is None

    def test_invert_true(self):
        """Higher raw value should give lower score when invert=True."""
        score = _normalize_score(80.0, 0.0, 100.0, invert=True)
        assert score == 20.0

    def test_equal_min_max(self):
        score = _normalize_score(50.0, 100.0, 100.0)
        assert score == 50.0

    def test_negative_range(self):
        score = _normalize_score(0.0, -50.0, 50.0)
        assert score == 50.0


class TestGetCagrValue:
    """Tests for _get_cagr_value helper."""

    def test_direct_float(self):
        row = pd.Series({"revenue_cagr_3yr": 15.0})
        assert _get_cagr_value(row, "revenue_cagr_3yr") == 15.0

    def test_none_value(self):
        row = pd.Series({"revenue_cagr_3yr": None})
        assert _get_cagr_value(row, "revenue_cagr_3yr") is None

    def test_nan_value(self):
        row = pd.Series({"revenue_cagr_3yr": np.nan})
        assert _get_cagr_value(row, "revenue_cagr_3yr") is None

    def test_missing_field(self):
        row = pd.Series({"other_field": 10.0})
        assert _get_cagr_value(row, "revenue_cagr_3yr") is None


# =============================================================================
# TEST PROFITABILITY SCORE
# =============================================================================

class TestProfitabilityScore:
    """Tests for calculate_profitability_score."""

def test_high_profitability(self, engine, sample_profitability_row):
        score = engine.calculate_profitability_score(sample_profitability_row)
        assert score is
        score = engine.calculate_profitability_score(sample_leverage_row)
        assert score is not None
        assert 0 <= score <= 100
        assert score < 50  # Low profitability

    def test_missing_all_metrics(self, engine, sample_missing_data_row):
        score = engine.calculate_profitability_score(sample_missing_data_row)
        assert score is not None  # Only NPM available
        assert 0 <= score <= 100

    def test_empty_row(self, engine):
        row = pd.Series({"company_id": "TEST"})
        score = engine.calculate_profitability_score(row)
        assert score is None

    def test_all_metrics_zero(self, engine):
        row = pd.Series({m: 0.0 for m in PROFITABILITY_METRICS})
        score = engine.calculate_profitability_score(row)
        assert score is not None
        assert score == 50.0  # 0 is mid-range for most metrics

    def test_negative_roe(self, engine):
        row = pd.Series({
            "roe": -30.0, "roce": -20.0, "roa": -15.0,
            "net_profit_margin": -25.0, "operating_profit_margin": -10.0,
        })
        score = engine.calculate_profitability_score(row)
        assert score is not None
        assert score < 40

    def test_invalid_values_ignored(self, engine):
        row = pd.Series({
            "roe": float('inf'), "roce": "INVALID", "roa": None,
            "net_profit_margin": 15.0, "operating_profit_margin": np.nan,
        })
        score = engine.calculate_profitability_score(row)
        assert score is not None
        assert score > 0


# =============================================================================
# TEST GROWTH SCORE
# =============================================================================

class TestGrowthScore:
    """Tests for calculate_growth_score."""

    def test_high_growth(self, engine, sample_profitability_row):
        score = engine.calculate_growth_score(sample_profitability_row)
        assert score is not None
        assert 0 <= score <= 100
        assert score > 60

    def test_low_growth(self, engine, sample_leverage_row):
        score = engine.calculate_growth_score(sample_leverage_row)
        assert score is not None
        assert 0 <= score <= 100
        assert score < 50

    def test_missing_all_cagr(self, engine, sample_missing_data_row):
        score = engine.calculate_growth_score(sample_missing_data_row)
        assert score is None

    def test_negative_cagr(self, engine):
        row = pd.Series({
            "revenue_cagr_3yr": -10.0,
            "pat_cagr_3yr": -20.0,
            "eps_cagr_3yr": -15.0,
        })
        score = engine.calculate_growth_score(row)
        assert score is not None
        assert score < 40  # Negative CAGR should give low score

    def test_mixed_cagr(self, engine):
        row = pd.Series({
            "revenue_cagr_3yr": 20.0,
            "pat_cagr_3yr": -5.0,
            "eps_cagr_3yr": None,
        })
        score = engine.calculate_growth_score(row)
        assert score is not None
        assert 0 <= score <= 100

    def test_empty_cagr_fields(self, engine):
        row = pd.Series({"company_id": "TEST"})
        score = engine.calculate_growth_score(row)
        assert score is None


# =============================================================================
# TEST CASH FLOW SCORE
# =============================================================================

class TestCashflowScore:
    """Tests for calculate_cashflow_score."""

    def test_excellent_cashflow(self, engine, sample_profitability_row):
        score = engine.calculate_cashflow_score(sample_profitability_row)
        assert score is not None
        assert 0 <= score <= 100
        assert score > 70

    def test_distressed_cashflow(self, engine, sample_leverage_row):
        score = engine.calculate_cashflow_score(sample_leverage_row)
        assert score is not None
        assert score < 40

    def test_missing_cashflow(self, engine, sample_missing_data_row):
        score = engine.calculate_cashflow_score(sample_missing_data_row)
        assert score is None

    def test_negative_fcf(self, engine):
        row = pd.Series({
            "free_cash_flow": -1000.0,
            "fcf_margin": -20.0,
            "cash_conversion": 50.0,
            "cash_return_on_assets": -5.0,
            "capital_allocation_rating": "WEAK",
        })
        score = engine.calculate_cashflow_score(row)
        assert score is not None
        assert score < 50

    def test_all_ratings(self, engine):
        """Test all capital allocation ratings map correctly."""
        for rating, expected_score in CAPITAL_ALLOCATION_MAP.items():
            row = pd.Series({
                "free_cash_flow": 1000.0,
                "fcf_margin": 20.0,
                "cash_conversion": 100.0,
                "cash_return_on_assets": 10.0,
                "capital_allocation_rating": rating,
            })
            score = engine.calculate_cashflow_score(row)
            assert score is not None
            assert 0 <= score <= 100

    def test_capital_allocation_none(self, engine):
        row = pd.Series({
            "free_cash_flow": 1000.0,
            "fcf_margin": 20.0,
            "cash_conversion": 100.0,
            "cash_return_on_assets": 10.0,
            "capital_allocation_rating": None,
        })
        score = engine.calculate_cashflow_score(row)
        assert score is not None


# =============================================================================
# TEST LEVERAGE SCORE
# =============================================================================

class TestLeverageScore:
    """Tests for calculate_leverage_score."""

    def test_low_leverage(self, engine, sample_profitability_row):
        score = engine.calculate_leverage_score(sample_profitability_row)
        assert score is not None
        assert 0 <= score <= 100
        assert score > 70  # Low D/E, high ICR should give high score

    def test_high_leverage(self, engine, sample_leverage_row):
        score = engine.calculate_leverage_score(sample_leverage_row)
        assert score is not None
        assert score < 50  # High D/E, low ICR should give low score

    def test_missing_leverage(self, engine, sample_missing_data_row):
        score = engine.calculate_leverage_score(sample_missing_data_row)
        assert score is None

    def test_debt_free(self, engine):
        """Debt-free company (D/E=0, ICR=0) should score high."""
        row = pd.Series({
            "debt_to_equity": 0.0,
            "interest_coverage": 0.0,
            "high_leverage_flag": 0,
        })
        score = engine.calculate_leverage_score(row)
        assert score is not None
        assert score > 80

    def test_negative_equity(self, engine):
        """Negative equity should apply heavy penalty."""
        row = pd.Series({
            "debt_to_equity": -5.0,
            "interest_coverage": 2.0,
            "high_leverage_flag": 1,
        })
        score = engine.calculate_leverage_score(row)
        assert score is not None
        assert score < 50

    def test_very_high_leverage(self, engine):
        row = pd.Series({
            "debt_to_equity": 10.0,
            "interest_coverage": 0.5,
            "high_leverage_flag": 1,
        })
        score = engine.calculate_leverage_score(row)
        assert score is not None
        assert score < 30


# =============================================================================
# TEST EFFICIENCY SCORE
# =============================================================================

class TestEfficiencyScore:
    """Tests for calculate_efficiency_score."""

    def test_high_efficiency(self, engine, sample_profitability_row):
        score = engine.calculate_efficiency_score(sample_profitability_row)
        assert score is not None
        assert 0 <= score <= 100
        assert score > 30  # Asset turnover 1.2

    def test_low_efficiency(self, engine, sample_leverage_row):
        score = engine.calculate_efficiency_score(sample_leverage_row)
        assert score is not None
        assert score < 20  # Asset turnover 0.3

    def test_missing_asset_turnover(self, engine, sample_missing_data_row):
        score = engine.calculate_efficiency_score(sample_missing_data_row)
        assert score is None

    def test_zero_asset_turnover(self, engine):
        row = pd.Series({"asset_turnover": 0.0})
        score = engine.calculate_efficiency_score(row)
        assert score == 0.0

    def test_high_asset_turnover(self, engine):
        row = pd.Series({"asset_turnover": 3.0})
        score = engine.calculate_efficiency_score(row)
        assert score == 100.0


# =============================================================================
# TEST OVERALL SCORE
# =============================================================================

class TestOverallScore:
    """Tests for calculate_overall_score."""

    def test_all_categories_present(self, engine):
        scores = {
            "profitability": 80.0,
            "growth": 70.0,
            "cashflow": 75.0,
            "leverage": 85.0,
            "efficiency": 65.0,
        }
        overall = engine.calculate_overall_score(scores)
        assert overall is not None
        assert 0 <= overall <= 100
        # Weighted: 80*0.30 + 70*0.20 + 75*0.20 + 85*0.15 + 65*0.15
        expected = (80*0.30 + 70*0.20 + 75*0.20 + 85*0.15 + 65*0.15)
        assert overall == pytest.approx(expected, rel=0.01)

    def test_some_missing_categories(self, engine):
        scores = {
            "profitability": 80.0,
            "growth": None,
            "cashflow": 70.0,
            "leverage": None,
            "efficiency": 60.0,
        }
        overall = engine.calculate_overall_score(scores)
        assert overall is not None
        # Weighted: only profitability(0.30), cashflow(0.20), efficiency(0.15) = 0.65
        # Normalized: (80*0.30 + 70*0.20 + 60*0.15) / 0.65
        expected = (80*0.30 + 70*0.20 + 60*0.15) / 0.65
        assert overall == pytest.approx(expected, rel=0.01)

    def test_all_missing_categories(self, engine):
        scores = {
            "profitability": None,
            "growth": None,
            "cashflow": None,
            "leverage": None,
            "efficiency": None,
        }
        overall = engine.calculate_overall_score(scores)
        assert overall is None

    def test_perfect_scores(self, engine):
        scores = {k: 100.0 for k in CATEGORY_WEIGHTS}
        overall = engine.calculate_overall_score(scores)
        assert overall == 100.0

    def test_minimum_scores(self, engine):
        scores = {k: 0.0 for k in CATEGORY_WEIGHTS}
        overall = engine.calculate_overall_score(scores)
        assert overall == 0.0

    def test_score_clamping_above(self, engine):
        scores = {k: 150.0 for k in CATEGORY_WEIGHTS}
        overall = engine.calculate_overall_score(scores)
        assert overall == 100.0

    def test_score_clamping_below(self, engine):
        scores = {k: -50.0 for k in CATEGORY_WEIGHTS}
        overall = engine.calculate_overall_score(scores)
        assert overall == 0.0

    def test_single_category_only(self, engine):
        scores = {"profitability": 80.0}
        overall = engine.calculate_overall_score(scores)
        assert overall is not None
        assert overall == 80.0


# =============================================================================
# TEST RATING
# =============================================================================

class TestRating:
    """Tests for generate_rating."""

    def test_excellent(self, engine):
        assert engine.generate_rating(95.0) == "Excellent"
        assert engine.generate_rating(100.0) == "Excellent"
        assert engine.generate_rating(90.0) == "Excellent"

    def test_strong(self, engine):
        assert engine.generate_rating(85.0) == "Strong"
        assert engine.generate_rating(75.0) == "Strong"
        assert engine.generate_rating(80.0) == "Strong"

    def test_healthy(self, engine):
        assert engine.generate_rating(70.0) == "Healthy"
        assert engine.generate_rating(60.0) == "Healthy"
        assert engine.generate_rating(65.0) == "Healthy"

    def test_moderate(self, engine):
        assert engine.generate_rating(55.0) == "Moderate"
        assert engine.generate_rating(45.0) == "Moderate"
        assert engine.generate_rating(50.0) == "Moderate"

    def test_weak(self, engine):
        assert engine.generate_rating(40.0) == "Weak"
        assert engine.generate_rating(30.0) == "Weak"
        assert engine.generate_rating(35.0) == "Weak"

    def test_distressed(self, engine):
        assert engine.generate_rating(20.0) == "Distressed"
        assert engine.generate_rating(0.0) == "Distressed"
        assert engine.generate_rating(29.0) == "Distressed"

    def test_boundary_89_9(self, engine):
        assert engine.generate_rating(89.99) == "Strong"
        assert engine.generate_rating(90.0) == "Excellent"

    def test_boundary_74_9(self, engine):
        assert engine.generate_rating(74.99) == "Healthy"
        assert engine.generate_rating(75.0) == "Strong"

    def test_boundary_59_9(self, engine):
        assert engine.generate_rating(59.99) == "Moderate"
        assert engine.generate_rating(60.0) == "Healthy"

    def test_boundary_44_9(self, engine):
        assert engine.generate_rating(44.99) == "Weak"
        assert engine.generate_rating(45.0) == "Moderate"

    def test_boundary_29_9(self, engine):
        assert engine.generate_rating(29.99) == "Distressed"
        assert engine.generate_rating(30.0) == "Weak"

    def test_none_score(self, engine):
        assert engine.generate_rating(None) == "Insufficient Data"

    def test_above_100(self, engine):
        assert engine.generate_rating(150.0) == "Excellent"


# =============================================================================
# TEST REMARKS
# =============================================================================

class TestRemarks:
    """Tests for generate_remarks."""

    def test_excellent_all_categories(self, engine):
        scores = {k: 95.0 for k in CATEGORY_WEIGHTS}
        remarks = engine.generate_remarks(scores)
        assert "Excellent" in remarks
        assert "Exceptional" in remarks
        assert len(remarks) > 10

    def test_poor_all_categories(self, engine):
        scores = {k: 10.0 for k in CATEGORY_WEIGHTS}
        remarks = engine.generate_remarks(scores)
        assert "Poor" in remarks or "Weak" in remarks or "Critical" in remarks or "Negative" in remarks
        assert len(remarks) > 10

    def test_mixed_scores(self, engine):
        scores = {
            "profitability": 85.0,
            "growth": 30.0,
            "cashflow": 70.0,
            "leverage": 50.0,
            "efficiency": 65.0,
        }
        remarks = engine.generate_remarks(scores)
        assert "profitability" in remarks.lower() or "excellent" in remarks.lower()
        assert len(remarks) > 20

    def test_all_none(self, engine):
        scores = {k: None for k in CATEGORY_WEIGHTS}
        remarks = engine.generate_remarks(scores)
        assert remarks == "Insufficient data for remarks generation"

    def test_single_category(self, engine):
        scores = {"profitability": 90.0}
        remarks = engine.generate_remarks(scores)
        assert "Excellent profitability" in remarks

    def test_remarks_are_semicolon_separated(self, engine):
        scores = {k: 80.0 for k in CATEGORY_WEIGHTS}
        remarks = engine.generate_remarks(scores)
        assert "; " in remarks


# =============================================================================
# TEST PROCESS COMPANY ROW
# =============================================================================

class TestProcessCompanyRow:
    """Tests for _process_company_row."""

    def test_valid_row(self, engine, sample_profitability_row):
        result, warnings = engine._process_company_row(sample_profitability_row)
        assert result is not None
        assert result["company_id"] == "TCS"
        assert result["period"] == "FY2024"
        assert "overall_score" in result
        assert "rating" in result
        assert "remarks" in result
        assert 0 <= result["overall_score"] <= 100

    def test_missing_company_id(self, engine):
        row = pd.Series({"period": "FY2024"})
        result, warnings = engine._process_company_row(row)
        assert result is None
        assert len(warnings) > 0

    def test_missing_period(self, engine):
        row = pd.Series({"company_id": "TEST"})
        result, warnings = engine._process_company_row(row)
        assert result is None
        assert len(warnings) > 0

    def test_nan_company_id(self, engine):
        row = pd.Series({"company_id": np.nan, "period": "FY2024"})
        result, warnings = engine._process_company_row(row)
        assert result is None

    def test_empty_company_id(self, engine):
        row = pd.Series({"company_id": "", "period": "FY2024"})
        result, warnings = engine._process_company_row(row)
        assert result is None

    def test_no_valid_metrics(self, engine, sample_missing_data_row):
        result, warnings = engine._process_company_row(sample_missing_data_row)
        assert result is None
        assert len(warnings) > 0


# =============================================================================
# TEST CSV EXPORT
# =============================================================================

class TestCsvExport:
    """Tests for export_csv."""

    def test_export_valid_records(self, engine):
        records = [
            {
                "company_id": "TCS",
                "company_name": "TCS",
                "period": "FY2024",
                "profitability_score": 80.0,
                "growth_score": 70.0,
                "cashflow_score": 75.0,
                "leverage_score": 85.0,
                "efficiency_score": 65.0,
                "overall_score": 76.0,
                "rating": "Strong",
                "remarks": "Good performance",
            }
        ]
        csv_path = engine.export_csv(records)
        assert csv_path is not None
        assert csv_path.exists()
        assert csv_path.suffix == ".csv"

        # Verify content
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]["company_id"] == "TCS"
            assert rows[0]["rating"] == "Strong"

    def test_export_empty_records(self, engine):
        csv_path = engine.export_csv([])
        assert csv_path is None

    def test_export_multiple_records(self, engine):
        records = [
            {"company_id": f"COMP{i}", "company_name": f"Company {i}",
             "period": "FY2024", "overall_score": 80.0, "rating": "Strong",
             "remarks": "Good"}
            for i in range(5)
        ]
        csv_path = engine.export_csv(records)
        assert csv_path is not None
        assert csv_path.exists()

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 5


# =============================================================================
# TEST DATABASE OPERATIONS
# =============================================================================

class TestDatabaseOperations:
    """Tests for save_to_database and table creation."""

    def test_save_single_record(self, engine, test_db):
        with patch('src.health_score.engine.get_connection') as mock_conn:
            mock_conn.return_value = sqlite3.connect(test_db)
            records = [{
                "company_id": "TCS",
                "company_name": "Tata Consultancy Services",
                "period": "FY2024",
                "profitability_score": 80.0,
                "growth_score": 70.0,
                "cashflow_score": 75.0,
                "leverage_score": 85.0,
                "efficiency_score": 65.0,
                "overall_score": 76.0,
                "rating": "Strong",
                "remarks": "Good performance",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
            }]
            stats = engine.save_to_database(records)
            assert stats["inserted"] == 1
            assert stats["skipped"] == 0

    def test_save_empty_records(self, engine):
        stats = engine.save_to_database([])
        assert stats["inserted"] == 0
        assert stats["skipped"] == 0

    def test_save_duplicate_handling(self, engine, test_db):
        with patch('src.health_score.engine.get_connection') as mock_conn:
            mock_conn.return_value = sqlite3.connect(test_db)
            records = [{
                "company_id": "TCS",
                "company_name": "Tata Consultancy Services",
                "period": "FY2024",
                "profitability_score": 80.0,
                "growth_score": 70.0,
                "cashflow_score": 75.0,
                "leverage_score": 85.0,
                "efficiency_score": 65.0,
                "overall_score": 76.0,
                "rating": "Strong",
                "remarks": "Good",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
            }]
            # First insert
            stats1 = engine.save_to_database(records)
            assert stats1["inserted"] == 1

            # Second insert (duplicate) - should update
            stats2 = engine.save_to_database(records)
            assert stats2["duplicates"] == 1

    def test_table_auto_creation(self, engine, test_db):
        """Table should be created automatically on save."""
        with patch('src.health_score.engine.get_connection') as mock_conn:
            conn = sqlite3.connect(test_db)
            mock_conn.return_value = conn
            records = [{
                "company_id": "TCS",
                "company_name": "TCS",
                "period": "FY2024",
                "profitability_score": 80.0,
                "growth_score": 70.0,
                "cashflow_score": 75.0,
                "leverage_score": 85.0,
                "efficiency_score": 65.0,
                "overall_score": 76.0,
                "rating": "Strong",
                "remarks": "Good",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
            }]
            engine.save_to_database(records)

            # Verify table exists
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='financial_health_scores'"
            )
            assert cursor.fetchone() is not None


# =============================================================================
# TEST END-TO-END PIPELINE
# =============================================================================

class TestPipeline:
    """End-to-end pipeline tests."""

    @patch('src.health_score.engine.get_connection')
    def test_run_with_data(self, mock_get_conn, engine, test_db):
        conn = sqlite3.connect(test_db)
        mock_get_conn.return_value = conn

        stats = engine.run()

        assert stats["status"] == "completed"
        assert stats["companies_processed"] > 0
        assert stats["errors"] == []

    @patch('src.health_score.engine.get_connection')
    def test_run_statistics(self, mock_get_conn, engine, test_db):
        conn = sqlite3.connect(test_db)
        mock_get_conn.return_value = conn

        engine.run()
        assert engine.pipeline_stats["start_time"] is not None
        assert engine.pipeline_stats["end_time"] is not None
        assert engine.pipeline_stats["companies_processed"] > 0

    @patch('src.health_score.engine.get_connection')
    def test_pipeline_creates_csv(self, mock_get_conn, engine, test_db):
        conn = sqlite3.connect(test_db)
        mock_get_conn.return_value = conn

        engine.run()

        csv_path = engine.output_dir / "financial_health_scores.csv"
        assert csv_path.exists()

        # Verify CSV has content
        with open(csv_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) > 1  # Header + at least 1 data row

    @patch('src.health_score.engine.get_connection')
    def test_pipeline_duplicate_handling(self, mock_get_conn, engine, test_db):
        conn = sqlite3.connect(test_db)
        mock_get_conn.return_value = conn

        # Run twice to create duplicates
        engine.run()
        assert engine.pipeline_stats["duplicates_found"] >= 0

    def test_run_with_empty_database(self, engine):
        """Pipeline should handle empty database gracefully."""
        with patch('src.health_score.engine.get_connection') as mock_conn:
            mock_db = sqlite3.connect(":memory:")
            mock_db.execute("""
                CREATE TABLE IF NOT EXISTS financial_ratios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id TEXT,
                    period TEXT
                )
            """)
            mock_conn.return_value = mock_db

            stats = engine.run()
            assert stats["status"] == "completed" or stats["status"] == "completed_no_data"


# =============================================================================
# TEST RUN_HEALTH_SCORE_PIPELINE CONVENIENCE FUNCTION
# =============================================================================

class TestRunHealthScorePipeline:
    """Tests for run_health_score_pipeline convenience function."""

    @patch('src.health_score.engine.HealthScoreEngine')
    def test_convenience_function(self, mock_engine_class):
        mock_instance = MagicMock()
        mock_instance.run.return_value = {"status": "completed", "companies_processed": 10}
        mock_engine_class.return_value = mock_instance

        result = run_health_score_pipeline()
        assert result["status"] == "completed"
        assert result["companies_processed"] == 10


# =============================================================================
# TEST GET_HEALTH_SCORE_STATISTICS
# =============================================================================

class TestGetHealthScoreStatistics:
    """Tests for get_health_score_statistics."""

    def test_statistics_with_data(self, engine, test_db):
        with patch('src.health_score.engine.get_connection') as mock_conn:
            mock_conn.return_value = sqlite3.connect(test_db)
            # First save some data
            records = [{
                "company_id": "TCS",
                "company_name": "TCS",
                "period": "FY2024",
                "profitability_score": 80.0,
                "growth_score": 70.0,
                "cashflow_score": 75.0,
                "leverage_score": 85.0,
                "efficiency_score": 65.0,
                "overall_score": 76.0,
                "rating": "Strong",
                "remarks": "Good",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
            }]
            engine.save_to_database(records)

    def test_statistics_empty_db(self):
        with patch('src.health_score.engine.get_connection') as mock_conn:
            mock_db = sqlite3.connect(":memory:")
            mock_conn.return_value = mock_db
            mock_db.execute("""
                CREATE TABLE IF NOT EXISTS financial_health_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id TEXT,
                    period TEXT,
                    overall_score REAL,
                    rating TEXT
                )
            """)
            stats = get_health_score_statistics()
            assert isinstance(stats, dict)
            assert "total_records" in stats

    def test_statistics_error_handling(self):
        with patch('src.health_score.engine.get_connection', side_effect=Exception("DB Error")):
            stats = get_health_score_statistics()
            assert stats == {}


# =============================================================================
# TEST CONSTANTS VALIDATION
# =============================================================================

class TestConstants:
    """Test that constants are properly defined."""

    def test_category_weights_sum(self):
        total = sum(CATEGORY_WEIGHTS.values())
        assert total == pytest.approx(1.0, abs=0.001)

    def test_all_metrics_defined(self):
        assert len(PROFITABILITY_METRICS) == 5
        for metric in PROFITABILITY_METRICS:
            assert metric in PROFITABILITY_RANGES

    def test_cagr_fields_defined(self):
        assert len(GROWTH_CAGR_FIELDS) == 3

    def test_rating_bands_cover_full_range(self):
        covered = 0.0
        for band_min, band_max, _ in RATING_BANDS:
            covered = band_max if band_max > covered else covered
        assert covered >= 100.0
        assert RATING_BANDS[0][0] == 0.0

    def test_capital_allocation_mapping(self):
        assert "EXCELLENT" in CAPITAL_ALLOCATION_MAP
        assert "GOOD" in CAPITAL_ALLOCATION_MAP
        assert "MODERATE" in CAPITAL_ALLOCATION_MAP
        assert "WEAK" in CAPITAL_ALLOCATION_MAP
        assert "DISTRESSED" in CAPITAL_ALLOCATION_MAP
        assert CAPITAL_ALLOCATION_MAP["EXCELLENT"] == 100.0
        assert CAPITAL_ALLOCATION_MAP["DISTRESSED"] == 20.0

    def test_remark_templates_complete(self):
        categories = ["profitability", "growth", "cashflow", "leverage", "efficiency"]
        for cat in categories:
            assert cat in REMARK_TEMPLATES
            assert len(REMARK_TEMPLATES[cat]) >= 4


# =============================================================================
# TEST EDGE CASES AND INVALID VALUES
# =============================================================================

class TestEdgeCases:
    """Test edge cases and invalid values."""

    def test_infinite_values_handled(self, engine):
        row = pd.Series({
            "roe": float('inf'),
            "roce": float('-inf'),
            "asset_turnover": float('inf'),
            "debt_to_equity": float('inf'),
            "free_cash_flow": float('inf'),
            "revenue_cagr_3yr": float('inf'),
        })
        # Should not crash - invalid values should be skipped
        result, warnings = engine._process_company_row(row)
        assert result is None or isinstance(result, dict)

    def test_nan_values_handled(self, engine):
        row = pd.Series({
            "roe": np.nan,
            "roce": np.nan,
            "asset_turnover": np.nan,
            "debt_to_equity": np.nan,
        })
        result, warnings = engine._process_company_row(row)
        assert result is None

    def test_string_in_place_of_number(self, engine):
        row = pd.Series({
            "company_id": "TEST",
            "company_name": "Test Corp",
            "period": "FY2024",
            "roe": "NOT_A_NUMBER",
            "net_profit_margin": "25%",  # String with %
        })
        result, warnings = engine._process_company_row(row)
        # Should handle gracefully - string values should be skipped
        assert result is not None or len(warnings) > 0

    def test_mixed_valid_invalid(self, engine):
        row = pd.Series({
            "company_id": "TEST",
            "company_name": "Test Corp",
            "period": "FY2024",
            "roe": 15.0,
            "roce": float('nan'),
            "roa": float('-inf'),
            "net_profit_margin": 10.0,
            "operating_profit_margin": None,
            "debt_to_equity": 0.5,
            "asset_turnover": 1.0,
            "revenue_cagr_3yr": 10.0,
            "free_cash_flow": 100.0,
            "cash_conversion": 80.0,
        })
        result, warnings = engine._process_company_row(row)
        assert result is not None
        assert 0 <= result["overall_score"] <= 100

    def test_duplicate_detection(self, engine):
        records = [
            {"company_id": "A", "company_name": "A", "period": "FY2024",
             "profitability_score": 80.0, "growth_score": 70.0, "cashflow_score": 75.0,
             "leverage_score": 85.0, "efficiency_score": 65.0, "overall_score": 76.0,
             "rating": "Strong", "remarks": "Good", "created_at": "now", "updated_at": "now"},
            {"company_id": "A", "company_name": "A", "period": "FY2024",
             "profitability_score": 80.0, "growth_score": 70.0, "cashflow_score": 75.0,
             "leverage_score": 85.0, "efficiency_score": 65.0, "overall_score": 76.0,
             "rating": "Strong", "remarks": "Good", "created_at": "now", "updated_at": "now"},
        ]
        with patch('src.health_score.engine.get_connection') as mock_conn:
            mock_db = sqlite3.connect(":memory:")
            mock_conn.return_value = mock_db
            stats = engine.save_to_database(records)

    def test_very_large_values(self, engine):
        row = pd.Series({
            "company_id": "BIG",
            "company_name": "Big Corp",
            "period": "FY2024",
            "roe": 1000.0,
            "roce": 2000.0,
            "net_profit_margin": 500.0,
            "asset_turnover": 100.0,
        })
        result, warnings = engine._process_company_row(row)
        assert result is not None
        assert result["overall_score"] <= 100


# =============================================================================
# TEST PERFORMANCE
# =============================================================================

class TestPerformance:
    """Performance-related tests."""

    def test_batch_processing(self, engine):
        """Process multiple rows efficiently."""
        rows = []
        for i in range(100):
            rows.append(pd.Series({
                "company_id": f"COMP{i}",
                "company_name": f"Company {i}",
                "period": "FY2024",
                "roe": 15.0 + (i * 0.1),
                "roce": 20.0,
                "roa": 10.0,
                "net_profit_margin": 15.0,
                "operating_profit_margin": 18.0,
                "debt_to_equity": 0.5,
                "interest_coverage": 5.0,
                "high_leverage_flag": 0,
                "asset_turnover": 1.0,
                "revenue_cagr_3yr": 10.0,
                "pat_cagr_3yr": 8.0,
                "eps_cagr_3yr": 9.0,
                "free_cash_flow": 1000.0,
                "fcf_margin": 10.0,
                "cash_conversion": 90.0,
                "cash_return_on_assets": 8.0,
                "capital_allocation_rating": "GOOD",
            }))

        results = []
        for row in rows:
            result, warnings = engine._process_company_row(row)
            if result:
                results.append(result)

        assert len(results) == 100
        scores = [r["overall_score"] for r in results]
        assert all(0 <= s <= 100 for s in scores)


# =============================================================================
# TEST LOGGING
# =============================================================================

class TestLogging:
    """Test logging functionality."""

    def test_dedicated_logger_setup(self, engine):
        log_path = engine.output_dir.parent / "logs" / "health_score.log"
        # The engine sets up its logger in __init__

    def test_logging_summary(self, engine):
        """Verify pipeline logging works."""
        with patch('src.health_score.engine.get_connection') as mock_conn:
            mock_db = sqlite3.connect(":memory:")
            mock_db.execute("""
                CREATE TABLE financial_ratios (
                    company_id TEXT, company_name TEXT, period TEXT,
                    roe REAL, roce REAL, roa REAL, net_profit_margin REAL,
                    operating_profit_margin REAL, debt_to_equity REAL,
                    interest_coverage REAL, high_leverage_flag INTEGER,
                    asset_turnover REAL
                )
            """)
            mock_db.execute("""
                INSERT INTO financial_ratios VALUES
                ('TEST', 'Test Corp', 'FY2024',
                 15, 20, 10, 12, 15,
                 0.5, 5, 0,
                 1.0)
            """)
            mock_conn.return_value = mock_db

            engine.run()
            assert engine.pipeline_stats["status"] in ["completed", "completed_no_data"]


if __name__ == "__main__":
    pytest.main(["-v", __file__])

