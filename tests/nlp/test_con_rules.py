"""
test_con_rules.py

Sprint 5 - Module 2C: Tests for the 12 Con rules (CON_01 - CON_12).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.nlp.pros_cons_generator import RuleResult, TYPE_CON, validate_confidence
from src.nlp.con_rules import (
    CON_01, CON_02, CON_03, CON_04, CON_05, CON_06,
    CON_07, CON_08, CON_09, CON_10, CON_11, CON_12,
)
from tests.nlp.test_pros_cons_generator import make_context

def _assert_triggered(result: RuleResult) -> None:
    assert result.triggered is True
    assert result.rule_type == TYPE_CON
    assert result.text
    assert validate_confidence(result.confidence_pct)
    assert 0.0 <= result.confidence_pct <= 100.0

def _assert_not_triggered(result: RuleResult) -> None:
    assert result.triggered is False
    assert result.confidence_pct == 0.0
    assert result.text == ""

# =============================================================================
# BATCH 1: CON_01 - CON_03
# =============================================================================

class TestCON01:
    def test_de_high_non_financial(self):
        ctx = make_context(latest={"debt_to_equity": 2.5}, is_financial=False)
        _assert_triggered(CON_01().evaluate(ctx))

    def test_de_equal_2_non_financial(self):
        ctx = make_context(latest={"debt_to_equity": 2.0}, is_financial=False)
        _assert_not_triggered(CON_01().evaluate(ctx))

    def test_financial_company_excluded(self):
        ctx = make_context(latest={"debt_to_equity": 5.0}, is_financial=True)
        _assert_not_triggered(CON_01().evaluate(ctx))

    def test_missing_de(self):
        ctx = make_context(latest={}, is_financial=False)
        _assert_not_triggered(CON_01().evaluate(ctx))

class TestCON02:
    def test_3_negative_fcf_years(self):
        ctx = make_context(history={"free_cash_flow": [10, -5, -10, -15]})
        _assert_triggered(CON_02().evaluate(ctx))

    def test_4_negative_fcf_years(self):
        ctx = make_context(history={"free_cash_flow": [-5, -10, -15, -20]})
        _assert_triggered(CON_02().evaluate(ctx))

    def test_2_negative_fcf_years(self):
        ctx = make_context(history={"free_cash_flow": [10, 5, -10, -15]})
        _assert_not_triggered(CON_02().evaluate(ctx))

    def test_fcf_zero_not_negative(self):
        ctx = make_context(history={"free_cash_flow": [10, 0, -10, -15]})
        _assert_not_triggered(CON_02().evaluate(ctx))

    def test_missing_year_breaks_streak(self):
        ctx = make_context(history={"free_cash_flow": [-5, -10, np.nan, -15, -20]})
        _assert_not_triggered(CON_02().evaluate(ctx))

class TestCON03:
    def test_3_opm_declines(self):
        ctx = make_context(history={"opm": [30, 28, 25, 22]})
        _assert_triggered(CON_03().evaluate(ctx))

    def test_2_opm_declines(self):
        ctx = make_context(history={"opm": [30, 28, 25, 26]})
        _assert_not_triggered(CON_03().evaluate(ctx))

    def test_flat_opm_breaks_streak(self):
        ctx = make_context(history={"opm": [30, 28, 28, 25]})
        _assert_not_triggered(CON_03().evaluate(ctx))

    def test_increasing_opm(self):
        ctx = make_context(history={"opm": [22, 25, 28, 30]})
        _assert_not_triggered(CON_03().evaluate(ctx))

    def test_missing_year_breaks_streak_opm(self):
        ctx = make_context(history={"opm": [30, 28, np.nan, 25, 22]})
        _assert_not_triggered(CON_03().evaluate(ctx))

# =============================================================================
# BATCH 2: CON_04 - CON_06
# =============================================================================

class TestCON04:
    def test_negative_net_profit(self):
        ctx = make_context(latest={"net_profit": -100})
        _assert_triggered(CON_04().evaluate(ctx))

    def test_zero_net_profit(self):
        ctx = make_context(latest={"net_profit": 0})
        _assert_not_triggered(CON_04().evaluate(ctx))

    def test_positive_net_profit(self):
        ctx = make_context(latest={"net_profit": 100})
        _assert_not_triggered(CON_04().evaluate(ctx))

    def test_missing_net_profit(self):
        ctx = make_context(latest={})
        _assert_not_triggered(CON_04().evaluate(ctx))

class TestCON05:
    def test_2_revenue_declines(self):
        ctx = make_context(history={"revenue": [100, 95, 90]})
        _assert_triggered(CON_05().evaluate(ctx))

    def test_1_revenue_decline(self):
        ctx = make_context(history={"revenue": [100, 95, 98]})
        _assert_not_triggered(CON_05().evaluate(ctx))

    def test_flat_revenue(self):
        ctx = make_context(history={"revenue": [100, 95, 95]})
        _assert_not_triggered(CON_05().evaluate(ctx))

    def test_increasing_revenue(self):
        ctx = make_context(history={"revenue": [90, 95, 100]})
        _assert_not_triggered(CON_05().evaluate(ctx))

class TestCON06:
    def test_icr_low(self):
        ctx = make_context(latest={"interest_coverage": 1.2})
        _assert_triggered(CON_06().evaluate(ctx))

    def test_icr_equal(self):
        ctx = make_context(latest={"interest_coverage": 1.5})
        _assert_not_triggered(CON_06().evaluate(ctx))

    def test_icr_high(self):
        ctx = make_context(latest={"interest_coverage": 5.0})
        _assert_not_triggered(CON_06().evaluate(ctx))

    def test_missing_icr(self):
        ctx = make_context(latest={})
        _assert_not_triggered(CON_06().evaluate(ctx))

# =============================================================================
# BATCH 3: CON_07 - CON_09
# =============================================================================

class TestCON07:
    def test_payout_high(self):
        ctx = make_context(latest={"dividend_payout": 110.0})
        _assert_triggered(CON_07().evaluate(ctx))

    def test_payout_equal(self):
        ctx = make_context(latest={"dividend_payout": 100.0})
        _assert_not_triggered(CON_07().evaluate(ctx))

    def test_payout_low(self):
        ctx = make_context(latest={"dividend_payout": 80.0})
        _assert_not_triggered(CON_07().evaluate(ctx))

class TestCON08:
    def test_3_de_increases(self):
        ctx = make_context(history={"debt_to_equity": [0.5, 0.8, 1.1, 1.5]})
        _assert_triggered(CON_08().evaluate(ctx))

    def test_2_de_increases(self):
        ctx = make_context(history={"debt_to_equity": [0.5, 0.8, 1.1, 1.0]})
        _assert_not_triggered(CON_08().evaluate(ctx))

    def test_flat_de(self):
        ctx = make_context(history={"debt_to_equity": [0.5, 0.8, 0.8, 1.1]})
        _assert_not_triggered(CON_08().evaluate(ctx))

    def test_decreasing_de(self):
        ctx = make_context(history={"debt_to_equity": [1.5, 1.1, 0.8, 0.5]})
        _assert_not_triggered(CON_08().evaluate(ctx))

class TestCON09:
    def test_3_eps_declines(self):
        ctx = make_context(history={"eps": [20, 18, 15, 12]})
        _assert_triggered(CON_09().evaluate(ctx))

    def test_2_eps_declines(self):
        ctx = make_context(history={"eps": [20, 18, 15, 16]})
        _assert_not_triggered(CON_09().evaluate(ctx))

    def test_flat_eps(self):
        ctx = make_context(history={"eps": [20, 18, 18, 15]})
        _assert_not_triggered(CON_09().evaluate(ctx))

    def test_increasing_eps(self):
        ctx = make_context(history={"eps": [12, 15, 18, 20]})
        _assert_not_triggered(CON_09().evaluate(ctx))

    def test_negative_eps_handled(self):
        ctx = make_context(history={"eps": [5, 2, -1, -5]})
        _assert_triggered(CON_09().evaluate(ctx))

# =============================================================================
# BATCH 4: CON_10 - CON_12
# =============================================================================

class TestCON10:
    def test_roce_low(self):
        ctx = make_context(latest={"roce": 8.0})
        _assert_triggered(CON_10().evaluate(ctx))

    def test_roce_equal(self):
        ctx = make_context(latest={"roce": 10.0})
        _assert_not_triggered(CON_10().evaluate(ctx))

    def test_roce_high(self):
        ctx = make_context(latest={"roce": 12.0})
        _assert_not_triggered(CON_10().evaluate(ctx))

class TestCON11:
    def test_net_debt_high(self):
        ctx = make_context(latest={"net_debt": 350, "ebitda": 100})
        _assert_triggered(CON_11().evaluate(ctx))

    def test_net_debt_equal(self):
        ctx = make_context(latest={"net_debt": 300, "ebitda": 100})
        _assert_not_triggered(CON_11().evaluate(ctx))

    def test_net_debt_low(self):
        ctx = make_context(latest={"net_debt": 250, "ebitda": 100})
        _assert_not_triggered(CON_11().evaluate(ctx))

    def test_ebitda_zero(self):
        ctx = make_context(latest={"net_debt": 350, "ebitda": 0})
        _assert_not_triggered(CON_11().evaluate(ctx))

    def test_ebitda_negative(self):
        ctx = make_context(latest={"net_debt": 350, "ebitda": -50})
        _assert_not_triggered(CON_11().evaluate(ctx))

    def test_ebitda_missing(self):
        ctx = make_context(latest={"net_debt": 350})
        _assert_not_triggered(CON_11().evaluate(ctx))

class TestCON12:
    def test_rev_cagr_low(self):
        ctx = make_context(trailing={"revenue_cagr": 4.0})
        _assert_triggered(CON_12().evaluate(ctx))

    def test_rev_cagr_equal(self):
        ctx = make_context(trailing={"revenue_cagr": 5.0})
        _assert_not_triggered(CON_12().evaluate(ctx))

    def test_rev_cagr_high(self):
        ctx = make_context(trailing={"revenue_cagr": 8.0})
        _assert_not_triggered(CON_12().evaluate(ctx))

    def test_rev_cagr_missing(self):
        ctx = make_context(trailing={})
        _assert_not_triggered(CON_12().evaluate(ctx))

# =============================================================================
# Edge cases
# =============================================================================

class TestConEdgeCases:
    RULES = [
        CON_01(), CON_02(), CON_03(), CON_04(), CON_05(), CON_06(),
        CON_07(), CON_08(), CON_09(), CON_10(), CON_11(), CON_12(),
    ]

    def test_none_context_never_crashes(self):
        for rule in self.RULES:
            result = rule.evaluate(None)
            assert result.triggered is False
            assert result.rule_type == TYPE_CON

    def test_empty_context_never_crashes(self):
        ctx = make_context(latest={}, history={}, trailing={})
        for rule in self.RULES:
            result = rule.evaluate(ctx)
            assert isinstance(result, RuleResult)
            assert result.triggered is False

    def test_all_nan_history_never_crashes(self):
        ctx = make_context(history={
            "free_cash_flow": [np.nan, np.nan],
            "opm": [np.nan, np.nan],
            "revenue": [np.nan, np.nan],
            "debt_to_equity": [np.nan, np.nan],
            "eps": [np.nan, np.nan],
        })
        for rule in self.RULES:
            result = rule.evaluate(ctx)
            assert isinstance(result, RuleResult)
            assert result.triggered is False