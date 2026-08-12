"""
test_pro_rules.py

Sprint 5 - Module 2B: Tests for PRO_01 - PRO_12.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.nlp.pros_cons_generator import (
    CompanyContext,
    RuleResult,
    TYPE_PRO,
    validate_confidence,
)
from src.nlp.pro_rules import (
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
from tests.nlp.test_pros_cons_generator import make_context


class TestPRO01:
    def test_3_consecutive_years_above_20(self):
        rule = PRO_01()
        ctx = make_context(latest={"roe": 25.0}, history={"roe": [18.0, 22.0, 25.0, 28.0, 30.0]})
        result = rule.evaluate(ctx)
        assert result.triggered is True
        assert "capital efficiency" in result.text
        assert validate_confidence(result.confidence_pct)
        assert result.confidence_pct >= 60.0

    def test_only_2_years_above_20(self):
        rule = PRO_01()
        ctx = make_context(latest={"roe": 25.0}, history={"roe": [18.0, 22.0, 25.0, 12.0, 8.0]})
        result = rule.evaluate(ctx)
        assert result.triggered is False
        assert result.confidence_pct == 0.0

    def test_missing_year_breaks_streak(self):
        rule = PRO_01()
        ctx = make_context(latest={"roe": 25.0}, history={"roe": [22.0, 25.0, None, 28.0, 30.0]})
        result = rule.evaluate(ctx)
        assert result.triggered is False

    def test_exactly_20_is_not_above(self):
        rule = PRO_01()
        ctx = make_context(latest={"roe": 20.0}, history={"roe": [20.0, 20.0, 20.0, 22.0, 25.0]})
        result = rule.evaluate(ctx)
        assert result.triggered is False

    def test_insufficient_history(self):
        rule = PRO_01()
        ctx = make_context(latest={"roe": 25.0}, history={"roe": [22.0, 25.0]})
        result = rule.evaluate(ctx)
        assert result.triggered is False
        assert "Insufficient" in result.reason

    def test_nan_handling(self):
        rule = PRO_01()
        ctx = make_context(latest={"roe": np.nan}, history={"roe": [22.0, 25.0, np.nan, 28.0, 30.0]})
        result = rule.evaluate(ctx)
        assert result.triggered is False


class TestPRO02:
    def test_5_consecutive_positive_fcf(self):
        rule = PRO_02()
        ctx = make_context(latest={"revenue": 1000.0}, history={"free_cash_flow": [50.0, 60.0, 70.0, 80.0, 90.0, 100.0]})
        result = rule.evaluate(ctx)
        assert result.triggered is True
        assert result.confidence_pct >= 60.0
class TestPRO03:
    def test_de_zero(self):
        rule = PRO_03()
        ctx = make_context(latest={"debt_to_equity": 0.0})
        result = rule.evaluate(ctx)
        assert result.triggered is True
        assert result.confidence_pct == 95.0

    def test_de_zero_point_zero(self):
        rule = PRO_03()
        ctx = make_context(latest={"debt_to_equity": 0.0})
        result = rule.evaluate(ctx)
        assert result.triggered is True

    def test_de_very_small_treated_as_zero(self):
        rule = PRO_03()
        ctx = make_context(latest={"debt_to_equity": 1e-10})
        result = rule.evaluate(ctx)
        assert result.triggered is True

    def test_de_positive(self):
        rule = PRO_03()
        ctx = make_context(latest={"debt_to_equity": 0.5})
        result = rule.evaluate(ctx)
        assert result.triggered is False

    def test_missing_de(self):
        rule = PRO_03()
        ctx = make_context(latest={"debt_to_equity": None})
        result = rule.evaluate(ctx)
        assert result.triggered is False
        assert "unavailable" in result.reason.lower()


class TestPRO04:
    def test_cagr_above_15(self):
        rule = PRO_04()
        ctx = make_context(latest={"revenue_cagr": 20.0})
        result = rule.evaluate(ctx)
        assert result.triggered is True
        assert result.confidence_pct > 60.0

    def test_cagr_exactly_15(self):
        rule = PRO_04()
        ctx = make_context(latest={"revenue_cagr": 15.0})
        result = rule.evaluate(ctx)
        assert result.triggered is False

    def test_cagr_below_15(self):
        rule = PRO_04()
        ctx = make_context(latest={"revenue_cagr": 10.0})
        result = rule.evaluate(ctx)
        assert result.triggered is False

    def test_missing_cagr(self):
        rule = PRO_04()
        ctx = make_context(latest={"revenue_cagr": None})
        result = rule.evaluate(ctx)
        assert result.triggered is False
        assert "unavailable" in result.reason.lower()


class TestPRO05:
    def test_opm_above_25(self):
        rule = PRO_05()
class TestPRO06:
    def test_pat_cagr_above_20(self):
        rule = PRO_06()
        ctx = make_context(latest={"profit_cagr": 25.0})
        result = rule.evaluate(ctx)
        assert result.triggered is True

    def test_pat_cagr_exactly_20(self):
        rule = PRO_06()
        ctx = make_context(latest={"profit_cagr": 20.0})
        result = rule.evaluate(ctx)
        assert result.triggered is False

    def test_pat_cagr_below_20(self):
        rule = PRO_06()
        ctx = make_context(latest={"profit_cagr": 15.0})
        result = rule.evaluate(ctx)
        assert result.triggered is False

    def test_missing_pat_cagr(self):
        rule = PRO_06()
        ctx = make_context(latest={"profit_cagr": None})
        result = rule.evaluate(ctx)
        assert result.triggered is False
        assert "unavailable" in result.reason.lower()


class TestPRO07:
    def test_icr_above_10(self):
        rule = PRO_07()
        ctx = make_context(latest={"interest_coverage": 15.0, "debt_to_equity": 0.5})
        result = rule.evaluate(ctx)
        assert result.triggered is True

    def test_icr_exactly_10(self):
        rule = PRO_07()
        ctx = make_context(latest={"interest_coverage": 10.0, "debt_to_equity": 0.5})
        result = rule.evaluate(ctx)
        assert result.triggered is False

    def test_icr_below_10(self):
        rule = PRO_07()
        ctx = make_context(latest={"interest_coverage": 5.0, "debt_to_equity": 0.5})
        result = rule.evaluate(ctx)
        assert result.triggered is False

    def test_debt_free_qualifies(self):
        rule = PRO_07()
        ctx = make_context(latest={"debt_to_equity": 0.0, "interest_coverage": None})
        result = rule.evaluate(ctx)
        assert result.triggered is True
        assert result.confidence_pct == 95.0

    def test_missing_icr_and_not_debt_free(self):
        rule = PRO_07()
        ctx = make_context(latest={"interest_coverage": None, "debt_to_equity": 0.5})
        result = rule.evaluate(ctx)
        assert result.triggered is False


class TestPRO08:
    def test_yield_and_fcf_positive(self):
        rule = PRO_08()
        ctx = make_context(latest={"dividend_yield": 3.0, "free_cash_flow": 100.0})
        result = rule.evaluate(ctx)
        assert result.triggered is True

    def test_yield_above_2_but_fcf_negative(self):
        rule = PRO_08()
        ctx = make_context(latest={"dividend_yield": 3.0, "free_cash_flow": -50.0})
        result = rule.evaluate(ctx)
        assert result.triggered is False

class TestPRO09:
    def test_eps_cagr_above_15(self):
        rule = PRO_09()
        ctx = make_context(latest={"eps_cagr": 18.0})
        result = rule.evaluate(ctx)
        assert result.triggered is True

    def test_eps_cagr_exactly_15(self):
        rule = PRO_09()
        ctx = make_context(latest={"eps_cagr": 15.0})
        result = rule.evaluate(ctx)
        assert result.triggered is False

    def test_eps_cagr_below_15(self):
        rule = PRO_09()
        ctx = make_context(latest={"eps_cagr": 10.0})
        result = rule.evaluate(ctx)
        assert result.triggered is False

    def test_missing_eps_cagr(self):
        rule = PRO_09()
        ctx = make_context(latest={"eps_cagr": None})
        result = rule.evaluate(ctx)
        assert result.triggered is False
        assert "unavailable" in result.reason.lower()


class TestPRO10:
    def test_3_consecutive_improvements(self):
        rule = PRO_10()
        ctx = make_context(latest={"roe": 21.0}, history={"roe": [12.0, 15.0, 18.0, 21.0]})
        result = rule.evaluate(ctx)
        assert result.triggered is True
        assert "12.0" in result.reason
        assert "21.0" in result.reason

    def test_2_improvements(self):
        rule = PRO_10()
        ctx = make_context(latest={"roe": 18.0}, history={"roe": [12.0, 15.0, 18.0, 18.0]})
        result = rule.evaluate(ctx)
        assert result.triggered is False

    def test_flat_value(self):
        rule = PRO_10()
        ctx = make_context(latest={"roe": 15.0}, history={"roe": [15.0, 15.0, 15.0, 15.0]})
        result = rule.evaluate(ctx)
        assert result.triggered is False

    def test_declining_value(self):
        rule = PRO_10()
        ctx = make_context(latest={"roe": 10.0}, history={"roe": [20.0, 18.0, 15.0, 10.0]})
        result = rule.evaluate(ctx)
        assert result.triggered is False

    def test_missing_year(self):
        rule = PRO_10()
        ctx = make_context(latest={"roe": 21.0}, history={"roe": [12.0, 15.0, None, 21.0]})
        result = rule.evaluate(ctx)
        assert result.triggered is False

    def test_insufficient_history(self):
        rule = PRO_10()
        ctx = make_context(latest={"roe": 21.0}, history={"roe": [15.0, 18.0, 21.0]})
        result = rule.evaluate(ctx)
        assert result.triggered is False
        assert "Insufficient" in result.reason

class TestPRO11:
    def test_revenue_cagr_greater_than_pat_cagr(self):
        rule = PRO_11()
        ctx = make_context(latest={"revenue_cagr": 20.0, "profit_cagr": 15.0})
        result = rule.evaluate(ctx)
        assert result.triggered is True

    def test_revenue_cagr_less_than_pat_cagr(self):
        rule = PRO_11()
        ctx = make_context(latest={"revenue_cagr": 10.0, "profit_cagr": 20.0})
        result = rule.evaluate(ctx)
        assert result.triggered is False

    def test_equal_cagr(self):
        rule = PRO_11()
        ctx = make_context(latest={"revenue_cagr": 15.0, "profit_cagr": 15.0})
        result = rule.evaluate(ctx)
        assert result.triggered is False

    def test_contradiction_documented(self):
        rule = PRO_11()
        ctx = make_context(latest={"revenue_cagr": 20.0, "profit_cagr": 15.0})
        result = rule.evaluate(ctx)
        assert "CONTRADICTION" in result.reason

    def test_missing_cagrs(self):
        rule = PRO_11()
        ctx = make_context(latest={"revenue_cagr": None, "profit_cagr": None})
        result = rule.evaluate(ctx)
        assert result.triggered is False
        assert "unavailable" in result.reason.lower()


class TestPRO12:
    def test_assets_increasing_debt_declining(self):
        rule = PRO_12()
        ctx = make_context(
            latest={},
            history={"total_assets": [100.0, 120.0, 140.0, 160.0], "borrowings": [50.0, 40.0, 30.0, 20.0]},
            history_years=[2020, 2021, 2022, 2023],
        )
        result = rule.evaluate(ctx)
        assert result.triggered is True
        assert "growing" in result.reason.lower()
        assert "declining" in result.reason.lower()

    def test_assets_declining(self):
        rule = PRO_12()
        ctx = make_context(
            latest={},
            history={"total_assets": [160.0, 140.0, 120.0, 100.0], "borrowings": [50.0, 40.0, 30.0, 20.0]},
            history_years=[2020, 2021, 2022, 2023],
        )
class TestEdgeCases:
    def test_none_values_dont_crash(self):
        for rule_cls in get_pro_rule_instances():
            rule = rule_cls()
            ctx = make_context(latest={}, history={"roe": [None, None], "free_cash_flow": [None], "total_assets": [None], "borrowings": [None]})
            result = rule.evaluate(ctx)
            assert isinstance(result, RuleResult)
            assert result.rule_id == rule.rule_id

    def test_nan_values_dont_crash(self):
        for rule_cls in get_pro_rule_instances():
            rule = rule_cls()
            ctx = make_context(latest={"roe": np.nan, "debt_to_equity": np.nan, "interest_coverage": np.nan}, history={"roe": [np.nan, np.nan]})
            result = rule.evaluate(ctx)
            assert isinstance(result, RuleResult)

    def test_infinity_handling(self):
        rule = PRO_04()
        ctx = make_context(latest={"revenue_cagr": float("inf")})
        result = rule.evaluate(ctx)
        assert result.triggered is False

    def test_negative_infinity_handling(self):
        rule = PRO_04()
        ctx = make_context(latest={"revenue_cagr": float("-inf")})
        result = rule.evaluate(ctx)
        assert result.triggered is False

    def test_missing_company(self):
        rule = PRO_01()
        ctx = make_context(company_id="UNKNOWN_XYZ", latest={}, history={"roe": []})
        result = rule.evaluate(ctx)
        assert result.company_id == "UNKNOWN_XYZ"
        assert result.triggered is False

    def test_confidence_in_valid_range(self):
        for rule_cls in get_pro_rule_instances():
            rule = rule_cls()
            ctx = make_context(
                latest={
                    "roe": 100.0,
                    "debt_to_equity": 0.0,
class TestRegistry:
    def test_all_12_rules_registered(self):
        from src.nlp.pros_cons_generator import get_registered_rules
        reg = get_registered_rules()
        assert len(reg["pro"]) == 12

    def test_no_con_rules_registered(self):
        from src.nlp.pros_cons_generator import get_registered_rules
        reg = get_registered_rules()
        assert len(reg["con"]) == 0

    def test_rule_ids_are_unique(self):
        from src.nlp.pros_cons_generator import get_registered_rules
        reg = get_registered_rules()
        ids = [r.rule_id for r in reg["pro"]]
        assert len(ids) == len(set(ids))

    def test_all_pro_rule_types_are_pro(self):
        from src.nlp.pros_cons_generator import get_registered_rules
        reg = get_registered_rules()
        for rule in reg["pro"]:
            assert rule.rule_type == "pro"

    def test_evaluate_runs_all_rules(self):
        from src.nlp.pros_cons_generator import evaluate_rules_for_company
        ctx = make_context()
        results = evaluate_rules_for_company(ctx)
        assert len(results) == 12
        for r in results:
            assert isinstance(r, RuleResult)

                    "interest_coverage": 100.0,
                    "dividend_yield": 5.0,
                    "free_cash_flow": 500.0,
                    "opm": 40.0,
                    "revenue_cagr": 30.0,
                    "profit_cagr": 25.0,
                    "eps_cagr": 25.0,
                },
                history={
                    "roe": [10.0, 15.0, 20.0, 25.0, 30.0, 35.0],
                    "free_cash_flow": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0],
                    "total_assets": [100.0, 120.0, 140.0, 160.0, 180.0, 200.0],
                    "borrowings": [50.0, 45.0, 40.0, 35.0, 30.0, 25.0],
                },
            )
            result = rule.evaluate(ctx)
            assert validate_confidence(result.confidence_pct), f"{rule.rule_id} confidence out of range: {result.confidence_pct}"

        result = rule.evaluate(ctx)
        assert result.triggered is False

    def test_debt_increasing(self):
        rule = PRO_12()
        ctx = make_context(
            latest={},
            history={"total_assets": [100.0, 120.0, 140.0, 160.0], "borrowings": [20.0, 30.0, 40.0, 50.0]},
            history_years=[2020, 2021, 2022, 2023],
        )
        result = rule.evaluate(ctx)
        assert result.triggered is False

    def test_missing_historical_data(self):
        rule = PRO_12()
        ctx = make_context(latest={}, history={"total_assets": [100.0], "borrowings": [50.0]})
        result = rule.evaluate(ctx)
        assert result.triggered is False
        assert "Insufficient" in result.reason

    def test_fcf_positive_but_yield_below_2(self):
        rule = PRO_08()
        ctx = make_context(latest={"dividend_yield": 1.0, "free_cash_flow": 100.0})
        result = rule.evaluate(ctx)
        assert result.triggered is False

    def test_missing_yield(self):
        rule = PRO_08()
        ctx = make_context(latest={"dividend_yield": None, "free_cash_flow": 100.0})
        result = rule.evaluate(ctx)
        assert result.triggered is False
        assert "unavailable" in result.reason.lower()

    def test_missing_fcf(self):
        rule = PRO_08()
        ctx = make_context(latest={"dividend_yield": 3.0, "free_cash_flow": None})
        result = rule.evaluate(ctx)
        assert result.triggered is False

        ctx = make_context(latest={"opm": 30.0})
        result = rule.evaluate(ctx)
        assert result.triggered is True

    def test_opm_exactly_25(self):
        rule = PRO_05()
        ctx = make_context(latest={"opm": 25.0})
        result = rule.evaluate(ctx)
        assert result.triggered is False

    def test_opm_below_25(self):
        rule = PRO_05()
        ctx = make_context(latest={"opm": 20.0})
        result = rule.evaluate(ctx)
        assert result.triggered is False

    def test_opm_fallback_calculation(self):
        rule = PRO_05()
        ctx = make_context(latest={"opm": None, "revenue": 1000.0, "operating_profit": 300.0})
        result = rule.evaluate(ctx)
        assert result.triggered is True
        assert result.confidence_pct > 60.0

    def test_missing_opm(self):
        rule = PRO_05()
        ctx = make_context(latest={"opm": None, "revenue": None, "operating_profit": None})
        result = rule.evaluate(ctx)
        assert result.triggered is False
        assert "unavailable" in result.reason.lower()


    def test_only_4_years_positive(self):
        rule = PRO_02()
        ctx = make_context(latest={"revenue": 1000.0}, history={"free_cash_flow": [50.0, 60.0, 70.0, 80.0, -10.0]})
        result = rule.evaluate(ctx)
        assert result.triggered is False

    def test_negative_fcf(self):
        rule = PRO_02()
        ctx = make_context(latest={"revenue": 1000.0}, history={"free_cash_flow": [-50.0, -60.0, -70.0, -80.0, -90.0]})
        result = rule.evaluate(ctx)
        assert result.triggered is False

    def test_missing_year(self):
        rule = PRO_02()
        ctx = make_context(latest={"revenue": 1000.0}, history={"free_cash_flow": [50.0, 60.0, None, 80.0, 90.0, 100.0]})
        result = rule.evaluate(ctx)
        assert result.triggered is False

    def test_no_fcf_history(self):
        rule = PRO_02()
        ctx = make_context(latest={"revenue": 1000.0}, history={"free_cash_flow": []})
        result = rule.evaluate(ctx)
        assert result.triggered is False
        assert "No FCF history" in result.reason

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
from tests.nlp.test_pros_cons_generator import make_context
