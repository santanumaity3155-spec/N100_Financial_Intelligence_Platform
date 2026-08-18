"""
test_pro_rules.py

Sprint 5 - Module 2B: Tests for the 12 Pro rules (PRO_01 - PRO_12).

Covers, per rule, the required cases from the sprint specification plus shared
edge cases (None/NaN/inf, missing metrics, insufficient history, unsorted and
duplicate years) and registry / confidence / output-schema assertions.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.nlp.pros_cons_generator import (  # noqa: E402
    CON_RULES,
    PRO_RULES,
    CompanyContext,
    RuleResult,
    TYPE_CON,
    TYPE_PRO,
    evaluate_rules_for_company,
    get_registered_rules,
    validate_confidence,
    validate_output_schema,
)
from src.nlp.pro_rules import (  # noqa: E402
    PRO_01,
    PRO_02,
    PRO_03,
    PRO_04,
    PRO_05,
    PRO_06,
    PRO_07,
    PRO_08,
    PRO_09,
    PRO_10,
    PRO_11,
    PRO_12,
    get_pro_rule_instances,
)
try:
    from tests.nlp.test_pros_cons_generator import make_context  # noqa: E402
except ImportError:
    from .test_pros_cons_generator import make_context  # noqa: E402

EXPECTED_PRO_IDS = [
    "PRO_01", "PRO_02", "PRO_03", "PRO_04", "PRO_05", "PRO_06",
    "PRO_07", "PRO_08", "PRO_09", "PRO_10", "PRO_11", "PRO_12",
]


def _assert_triggered(result: RuleResult) -> None:
    assert result.triggered is True
    assert result.rule_type == TYPE_PRO
    assert result.text
    assert validate_confidence(result.confidence_pct)
    assert 0.0 <= result.confidence_pct <= 100.0


def _assert_not_triggered(result: RuleResult) -> None:
    assert result.triggered is False
    assert result.confidence_pct == 0.0
    assert result.text == ""


# =============================================================================
# PRO_01 - Sustained High ROE
# =============================================================================


class TestPRO01:
    def test_3_consecutive_years_above_20(self):
        ctx = make_context(
            latest={"roe": 30.0},
            history={"roe": [18.0, 22.0, 25.0, 28.0, 30.0]},
        )
        _assert_triggered(PRO_01().evaluate(ctx))

    def test_only_2_years_above_20(self):
        ctx = make_context(
            latest={"roe": 25.0},
            history={"roe": [18.0, 22.0, 25.0, 12.0, 8.0]},
        )
        _assert_not_triggered(PRO_01().evaluate(ctx))

    def test_missing_year_breaks_streak(self):
        ctx = make_context(
            latest={"roe": 30.0},
            history={"roe": [22.0, 25.0, None, 28.0, 30.0]},
        )
        _assert_not_triggered(PRO_01().evaluate(ctx))

    def test_exactly_20_is_not_above(self):
        ctx = make_context(
            latest={"roe": 20.0},
            history={"roe": [20.0, 20.0, 20.0, 22.0, 25.0]},
        )
        _assert_not_triggered(PRO_01().evaluate(ctx))

    def test_insufficient_history(self):
        ctx = make_context(latest={"roe": 25.0}, history={"roe": [22.0, 25.0]})
        result = PRO_01().evaluate(ctx)
        _assert_not_triggered(result)
        assert "Insufficient" in result.reason

    def test_confidence_rises_with_streak(self):
        base = PRO_01().evaluate(make_context(
            latest={"roe": 21.0},
            history={"roe": [21.0, 22.0, 23.0]}))
        strong = PRO_01().evaluate(make_context(
            latest={"roe": 40.0},
            history={"roe": [35.0, 38.0, 40.0, 41.0, 42.0, 43.0]}))
        assert strong.confidence_pct >= base.confidence_pct

    def test_nan_handling(self):
        ctx = make_context(
            latest={"roe": np.nan},
            history={"roe": [22.0, 25.0, np.nan, 28.0, 30.0]},
        )
        _assert_not_triggered(PRO_01().evaluate(ctx))


# =============================================================================
# PRO_02 - Sustained Positive FCF
# =============================================================================


class TestPRO02:
    def test_5_consecutive_positive_fcf(self):
        ctx = make_context(
            latest={"revenue": 1000.0},
            history={"free_cash_flow": [50.0, 60.0, 70.0, 80.0, 90.0, 100.0]},
        )
        _assert_triggered(PRO_02().evaluate(ctx))

    def test_only_4_years_positive(self):
        ctx = make_context(
            latest={"revenue": 1000.0},
            history={"free_cash_flow": [50.0, 60.0, 70.0, 80.0, -10.0]},
        )
        _assert_not_triggered(PRO_02().evaluate(ctx))

    def test_negative_fcf(self):
        ctx = make_context(
            latest={"revenue": 1000.0},
            history={"free_cash_flow": [-50.0, -60.0, -70.0, -80.0, -90.0, -100.0]},
        )
        _assert_not_triggered(PRO_02().evaluate(ctx))

    def test_missing_year_breaks_streak(self):
        ctx = make_context(
            latest={"revenue": 1000.0},
            history={"free_cash_flow": [50.0, 60.0, None, 80.0, 90.0, 100.0]},
        )
        _assert_not_triggered(PRO_02().evaluate(ctx))

    def test_no_fcf_history(self):
        ctx = make_context(latest={"revenue": 1000.0}, history={"free_cash_flow": []})
        result = PRO_02().evaluate(ctx)
        _assert_not_triggered(result)

    def test_insufficient_history(self):
        ctx = make_context(
            latest={"revenue": 1000.0},
            history={"free_cash_flow": [10.0, 20.0, 30.0, 40.0]},
        )
        _assert_not_triggered(PRO_02().evaluate(ctx))
# =============================================================================
# PRO_03 - Debt Free
# =============================================================================


class TestPRO03:
    def test_de_zero(self):
        _assert_triggered(PRO_03().evaluate(
            make_context(latest={"debt_to_equity": 0})))

    def test_de_zero_float(self):
        _assert_triggered(PRO_03().evaluate(
            make_context(latest={"debt_to_equity": 0.0})))

    def test_de_very_small_treated_as_zero(self):
        _assert_triggered(PRO_03().evaluate(
            make_context(latest={"debt_to_equity": 1e-10})))

    def test_de_positive(self):
        _assert_not_triggered(PRO_03().evaluate(
            make_context(latest={"debt_to_equity": 0.5})))

    def test_de_missing_not_debt_free(self):
        result = PRO_03().evaluate(make_context(latest={}))
        _assert_not_triggered(result)
        assert "unavailable" in result.reason.lower()

    def test_de_nan_not_debt_free(self):
        _assert_not_triggered(PRO_03().evaluate(
            make_context(latest={"debt_to_equity": np.nan})))

    def test_de_inf_not_debt_free(self):
        _assert_not_triggered(PRO_03().evaluate(
            make_context(latest={"debt_to_equity": np.inf})))


# =============================================================================
# PRO_04 - Strong Revenue Growth
# =============================================================================


class TestPRO04:
    def test_cagr_above_15(self):
        _assert_triggered(PRO_04().evaluate(
            make_context(trailing={"revenue_cagr": 20.0})))

    def test_cagr_exactly_15(self):
        _assert_not_triggered(PRO_04().evaluate(
            make_context(trailing={"revenue_cagr": 15.0})))

    def test_cagr_below_15(self):
        _assert_not_triggered(PRO_04().evaluate(
            make_context(trailing={"revenue_cagr": 10.0})))

    def test_fallback_recalc(self):
        ctx = make_context(
            trailing={},
            latest={"revenue_cagr": None},
            history={"revenue": [100.0, 140.0, 190.0, 260.0, 350.0]},
        )
        _assert_triggered(PRO_04().evaluate(ctx))

    def test_missing_cagr(self):
        ctx = make_context(trailing={}, latest={}, history={})
        result = PRO_04().evaluate(ctx)
        _assert_not_triggered(result)
        assert "unavailable" in result.reason.lower()
# =============================================================================
# PRO_05 - Strong Operating Margin
# =============================================================================


class TestPRO05:
    def test_opm_above_25(self):
        _assert_triggered(PRO_05().evaluate(make_context(latest={"opm": 30.0})))

    def test_opm_exactly_25(self):
        _assert_not_triggered(PRO_05().evaluate(make_context(latest={"opm": 25.0})))

    def test_opm_below_25(self):
        _assert_not_triggered(PRO_05().evaluate(make_context(latest={"opm": 20.0})))

    def test_fallback_calculation(self):
        ctx = make_context(latest={"opm": None, "revenue": 1000.0,
                                   "operating_profit": 300.0})
        _assert_triggered(PRO_05().evaluate(ctx))

    def test_uses_opm_not_npm(self):
        # A high NPM alone must NOT trigger OPM rule.
        ctx = make_context(latest={"net_profit": 500.0, "revenue": 1000.0})
        _assert_not_triggered(PRO_05().evaluate(ctx))

    def test_missing_opm(self):
        ctx = make_context(latest={"opm": None, "revenue": None,
                                   "operating_profit": None})
        result = PRO_05().evaluate(ctx)
        _assert_not_triggered(result)
        assert "unavailable" in result.reason.lower()


# =============================================================================
# PRO_06 - Strong PAT Growth
# =============================================================================


class TestPRO06:
    def test_pat_cagr_above_20(self):
        _assert_triggered(PRO_06().evaluate(
            make_context(trailing={"profit_cagr": 25.0})))

    def test_pat_cagr_exactly_20(self):
        _assert_not_triggered(PRO_06().evaluate(
            make_context(trailing={"profit_cagr": 20.0})))

    def test_pat_cagr_below_20(self):
        _assert_not_triggered(PRO_06().evaluate(
            make_context(trailing={"profit_cagr": 10.0})))

    def test_fallback_recalc(self):
        ctx = make_context(
            trailing={},
            latest={"profit_cagr": None},
            history={"net_profit": [40.0, 60.0, 90.0, 135.0, 200.0]},
        )
        _assert_triggered(PRO_06().evaluate(ctx))

    def test_missing_pat_cagr(self):
        result = PRO_06().evaluate(make_context(trailing={}, latest={}, history={}))
        _assert_not_triggered(result)
        assert "unavailable" in result.reason.lower()


# =============================================================================
# PRO_07 - Strong Interest Coverage / Debt Free
# =============================================================================


class TestPRO07:
    def test_icr_above_10(self):
        _assert_triggered(PRO_07().evaluate(
            make_context(latest={"interest_coverage": 15.0})))

    def test_icr_exactly_10(self):
        _assert_not_triggered(PRO_07().evaluate(
            make_context(latest={"interest_coverage": 10.0})))

    def test_icr_below_10(self):
        _assert_not_triggered(PRO_07().evaluate(
            make_context(latest={"interest_coverage": 5.0})))

    def test_debt_free_qualifies(self):
        ctx = make_context(latest={"debt_to_equity": 0.0, "interest_coverage": None})
        _assert_triggered(PRO_07().evaluate(ctx))

    def test_missing_icr_not_infinity(self):
        ctx = make_context(latest={"debt_to_equity": 0.5, "interest_coverage": None})
        result = PRO_07().evaluate(ctx)
        _assert_not_triggered(result)
        assert "unavailable" in result.reason.lower()

    def test_icr_nan_not_infinity(self):
        ctx = make_context(latest={"debt_to_equity": 0.5,
                                   "interest_coverage": np.nan})
        _assert_not_triggered(PRO_07().evaluate(ctx))

    def test_icr_inf_not_infinity(self):
        ctx = make_context(latest={"debt_to_equity": 0.5,
                                   "interest_coverage": np.inf})
        _assert_not_triggered(PRO_07().evaluate(ctx))
# =============================================================================
# PRO_08 - Dividend Quality
# =============================================================================


class TestPRO08:
    def test_yield_high_and_fcf_positive(self):
        ctx = make_context(
            trailing={"dividend_yield": 3.0},
            latest={"free_cash_flow": 100.0},
        )
        _assert_triggered(PRO_08().evaluate(ctx))

    def test_yield_high_but_fcf_negative(self):
        ctx = make_context(
            trailing={"dividend_yield": 3.0},
            latest={"free_cash_flow": -10.0},
        )
        _assert_not_triggered(PRO_08().evaluate(ctx))

    def test_fcf_positive_but_yield_low(self):
        ctx = make_context(
            trailing={"dividend_yield": 1.0},
            latest={"free_cash_flow": 100.0},
        )
        _assert_not_triggered(PRO_08().evaluate(ctx))

    def test_yield_exactly_2(self):
        ctx = make_context(
            trailing={"dividend_yield": 2.0},
            latest={"free_cash_flow": 100.0},
        )
        _assert_not_triggered(PRO_08().evaluate(ctx))

    def test_missing_yield(self):
        ctx = make_context(trailing={"dividend_yield": None},
                           latest={"free_cash_flow": 100.0})
        result = PRO_08().evaluate(ctx)
        _assert_not_triggered(result)
        assert "unavailable" in result.reason.lower()

    def test_missing_fcf(self):
        ctx = make_context(trailing={"dividend_yield": 3.0}, latest={})
        result = PRO_08().evaluate(ctx)
        _assert_not_triggered(result)


# =============================================================================
# PRO_09 - Strong EPS Growth
# =============================================================================


class TestPRO09:
    def test_eps_cagr_above_15(self):
        _assert_triggered(PRO_09().evaluate(
            make_context(trailing={"eps_cagr": 20.0})))

    def test_eps_cagr_exactly_15(self):
        _assert_not_triggered(PRO_09().evaluate(
            make_context(trailing={"eps_cagr": 15.0})))

    def test_eps_cagr_below_15(self):
        _assert_not_triggered(PRO_09().evaluate(
            make_context(trailing={"eps_cagr": 8.0})))

    def test_fallback_recalc(self):
        ctx = make_context(
            trailing={},
            latest={"eps_cagr": None},
            history={"eps": [10.0, 15.0, 22.0, 32.0, 46.0]},
        )
        _assert_triggered(PRO_09().evaluate(ctx))

    def test_missing_eps_cagr(self):
        result = PRO_09().evaluate(make_context(trailing={}, latest={}, history={}))
        _assert_not_triggered(result)
        assert "unavailable" in result.reason.lower()


# =============================================================================
# PRO_10 - Improving ROE
# =============================================================================


class TestPRO10:
    def test_3_consecutive_improvements(self):
        ctx = make_context(latest={"roe": 21.0},
                           history={"roe": [12.0, 15.0, 18.0, 21.0]})
        _assert_triggered(PRO_10().evaluate(ctx))

    def test_only_2_improvements(self):
        ctx = make_context(latest={"roe": 15.0},
                           history={"roe": [12.0, 13.0, 15.0, 12.0]})
        _assert_not_triggered(PRO_10().evaluate(ctx))

    def test_flat_value_breaks(self):
        ctx = make_context(latest={"roe": 14.0},
                           history={"roe": [12.0, 13.0, 14.0, 14.0]})
        _assert_not_triggered(PRO_10().evaluate(ctx))

    def test_declining_value(self):
        ctx = make_context(latest={"roe": 12.0},
                           history={"roe": [21.0, 18.0, 15.0, 12.0]})
        _assert_not_triggered(PRO_10().evaluate(ctx))

    def test_missing_year(self):
        ctx = make_context(latest={"roe": 21.0},
                           history={"roe": [12.0, 20.0, None, 15.0, 18.0, 21.0]})
        result = PRO_10().evaluate(ctx)
        # Missing year produces a compressed series that must not invent
        # 3 uninterrupted improvements.
        _assert_not_triggered(result)

    def test_insufficient_history(self):
        ctx = make_context(latest={"roe": 15.0}, history={"roe": [12.0, 15.0]})
        result = PRO_10().evaluate(ctx)
        _assert_not_triggered(result)
        assert "Insufficient" in result.reason
# =============================================================================
# PRO_11 - Operating Leverage (spec contradiction documented)
# =============================================================================


class TestPRO11:
    def test_rev_cagr_gt_pat_cagr(self):
        ctx = make_context(trailing={"revenue_cagr": 25.0, "profit_cagr": 10.0})
        result = PRO_11().evaluate(ctx)
        _assert_triggered(result)
        assert "slower than profits" in result.text

    def test_rev_cagr_lt_pat_cagr(self):
        ctx = make_context(trailing={"revenue_cagr": 5.0, "profit_cagr": 20.0})
        _assert_not_triggered(PRO_11().evaluate(ctx))

    def test_equal_cagr(self):
        ctx = make_context(trailing={"revenue_cagr": 15.0, "profit_cagr": 15.0})
        _assert_not_triggered(PRO_11().evaluate(ctx))

    def test_missing_cagr(self):
        ctx = make_context(trailing={}, latest={})
        result = PRO_11().evaluate(ctx)
        _assert_not_triggered(result)
        assert "unavailable" in result.reason.lower()

    def test_spec_contradiction_documented(self):
        ctx = make_context(trailing={"revenue_cagr": 25.0, "profit_cagr": 10.0})
        result = PRO_11().evaluate(ctx)
        assert "SPEC CONTRADICTION" in result.reason
        # The supplied text describes the opposite inequality; we implement the
        # explicit condition (Revenue CAGR > PAT CAGR) and flag the conflict.
        assert result.triggered is True


# =============================================================================
# PRO_12 - Asset Growth + Declining Debt
# =============================================================================


class TestPRO12:
    def test_assets_up_debt_down(self):
        ctx = make_context(history={
            "total_assets": [100.0, 110.0, 120.0, 130.0, 140.0],
            "borrowings": [60.0, 50.0, 40.0, 30.0, 20.0],
        })
        _assert_triggered(PRO_12().evaluate(ctx))

    def test_assets_declining(self):
        ctx = make_context(history={
            "total_assets": [100.0, 125.0, 120.0, 105.0],
            "borrowings": [60.0, 50.0, 40.0, 30.0],
        })
        _assert_not_triggered(PRO_12().evaluate(ctx))

    def test_debt_increasing(self):
        ctx = make_context(history={
            "total_assets": [100.0, 110.0, 120.0, 130.0],
            "borrowings": [20.0, 30.0, 40.0, 50.0],
        })
        _assert_not_triggered(PRO_12().evaluate(ctx))

    def test_missing_historical_data(self):
        ctx = make_context(history={"total_assets": [100.0], "borrowings": [50.0]})
        result = PRO_12().evaluate(ctx)
        _assert_not_triggered(result)
        assert "Insufficient" in result.reason

    def test_missing_metric(self):
        ctx = make_context(history={})
        result = PRO_12().evaluate(ctx)
        _assert_not_triggered(result)

# =============================================================================
# Edge cases (must never crash)
# =============================================================================


class TestEdgeCases:
    RULES = [
        PRO_01(), PRO_02(), PRO_03(), PRO_04(), PRO_05(), PRO_06(),
        PRO_07(), PRO_08(), PRO_09(), PRO_10(), PRO_11(), PRO_12(),
    ]

    def test_none_context_never_crashes(self):
        for rule in self.RULES:
            result = rule.evaluate(None)
            assert result.triggered is False
            assert result.rule_type == TYPE_PRO

    def test_minimal_context_never_crashes(self):
        # A bare object exposing only company_id must not raise.
        ns = type("RawCtx", (), {"company_id": "R"})()
        for rule in self.RULES:
            result = rule.evaluate(ns)
            assert isinstance(result, RuleResult)

    def test_duplicate_years_never_crash(self):
        ctx = make_context(
            history_years=[2020, 2020, 2021, 2022],
            history={"roe": [20.0, 24.0, 26.0, 28.0]},
        )
        for rule in self.RULES:
            result = rule.evaluate(ctx)
            assert isinstance(result, RuleResult)
            assert validate_confidence(result.confidence_pct)

    def test_unsorted_years_never_crash(self):
        ctx = make_context(
            history_years=[2022, 2020, 2021, 2019],
            history={"roe": [28.0, 22.0, 25.0, 20.0],
                     "total_assets": [140.0, 100.0, 120.0, 90.0]},
        )
        for rule in self.RULES:
            result = rule.evaluate(ctx)
            assert isinstance(result, RuleResult)
            assert 0.0 <= result.confidence_pct <= 100.0

    def test_all_inf_nan_history_never_crash(self):
        ctx = make_context(history={
            "roe": [np.nan, np.inf],
            "free_cash_flow": [-np.inf, np.nan],
        })
        for rule in self.RULES:
            result = rule.evaluate(ctx)
            assert isinstance(result, RuleResult)
            assert validate_confidence(result.confidence_pct)

    def test_empty_history_never_crash(self):
        ctx = make_context(history={}, latest={}, trailing={})
        for rule in self.RULES:
            result = rule.evaluate(ctx)
            assert isinstance(result, RuleResult)

    def test_confidence_deterministic(self):
        ctx = make_context(
            latest={"roe": 30.0},
            history={"roe": [18.0, 22.0, 25.0, 28.0, 30.0]},
        )
        assert PRO_01().evaluate(ctx).confidence_pct == \
            PRO_01().evaluate(ctx).confidence_pct


# =============================================================================
# Registry + output
# =============================================================================


class TestRegistry:
    def test_pro_registry_has_12_rules(self):
        assert len(PRO_RULES) == 12
        assert [r.rule_id for r in PRO_RULES] == EXPECTED_PRO_IDS
        assert all(r.rule_type == TYPE_PRO for r in PRO_RULES)

    def test_con_registry_has_12_rules(self):
        assert len(CON_RULES) == 12
        assert [r.rule_id for r in CON_RULES] == [f"CON_{i:02d}" for i in range(1, 13)]

    def test_registry_matches_instances(self):
        reg = get_registered_rules()
        assert [r.rule_id for r in reg["pro"]] == EXPECTED_PRO_IDS
        assert len(reg["con"]) == 12

    def test_instances_are_rule_classes(self):
        inst = get_pro_rule_instances()
        assert len(inst) == 12
        for rule in inst:
            assert hasattr(rule, "evaluate")
            assert rule.rule_type == TYPE_PRO

    def test_evaluate_rules_for_company(self):
        results = evaluate_rules_for_company(make_context())
        assert len(results) == 24  # 12 Pro + 12 Con
        pro_results = [r for r in results if r.rule_type == TYPE_PRO]
        con_results = [r for r in results if r.rule_type == TYPE_CON]
        assert len(pro_results) == 12
        assert len(con_results) == 12
        for r in results:
            assert isinstance(r, RuleResult)
            assert validate_confidence(r.confidence_pct)

    def test_triggered_output_schema_valid(self):
        ctx = make_context(
            latest={"roe": 30.0, "opm": 30.0},
            history={"roe": [18.0, 22.0, 25.0, 28.0, 30.0]},
            trailing={"revenue_cagr": 20.0, "profit_cagr": 25.0,
                      "eps_cagr": 20.0},
        )
        rows = [r.to_dict() for r in evaluate_rules_for_company(ctx) if r.triggered]
        df = pd.DataFrame(rows, columns=[
            "company_id", "type", "rule_id", "text", "confidence_pct"])
        assert all(df["type"] == "pro")
        valid, issues = validate_output_schema(df)
        assert valid, issues