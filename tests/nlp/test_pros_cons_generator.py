"""
test_pros_cons_generator.py

Sprint 5 – Module 2A: Auto Pros/Cons Generator Foundation tests.

Covers:
1.  Data loading
2.  Company context creation
3.  Latest-year extraction
4.  Historical data extraction
5.  Missing-value handling
6.  NaN handling
7.  Infinite-value handling
8.  Zero denominator handling
9.  3-year history detection
10. 5-year history detection
11. Improving trend helper
12. Declining trend helper
13. Consecutive positive helper
14. Consecutive negative helper
15. RuleResult validation
16. Rule registry
17. Confidence range validation
18. Output schema validation
19. Duplicate detection
20. Empty-result company coverage
21. Financial-sector detection
22. Regression test for Module 1 (analysis_parsed.csv / parse_failures.csv)

The 24 actual Pro/Con rules are deliberately NOT tested here (Modules 2B/2C).
"""

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Ensure project root is importable.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.nlp.pros_cons_generator import (  # noqa: E402
    CONFIDENCE_MAX,
    CONFIDENCE_MIN,
    CONFIDENCE_THRESHOLD,
    CON_RULES,
    PRO_RULES,
    CompanyContext,
    FinancialRule,
    OUTPUT_COLUMNS,
    PERIOD_TTM,
    RuleResult,
    TYPE_CON,
    TYPE_PRO,
    calculate_cagr,
    calculate_confidence,
    check_consecutive_condition,
    count_consecutive_negative,
    count_consecutive_positive,
    evaluate_rules_for_company,
    format_confidence,
    get_company_context,
    get_latest_value,
    get_metric_history,
    get_registered_rules,
    get_sub_sector,
    has_consecutive_years,
    has_minimum_history,
    is_declining,
    is_financial_sector,
    is_improving,
    load_analysis_data,
    load_balance_sheet,
    load_cashflow_data,
    load_companies,
    load_financial_data,
    load_profit_loss,
    load_ratio_data,
    load_sectors,
    parse_period,
    prepare_company_history,
    prepare_latest_year_data,
    register_con_rule,
    register_pro_rule,
    safe_divide,
    safe_float,
    validate_company_coverage,
    validate_confidence,
    validate_output_schema,
)


# =============================================================================
# HELPERS / FIXTURES
# =============================================================================


def make_context(
    company_id: str = "TESTCO",
    latest: dict = None,
    history: dict = None,
    history_years: list = None,
    **kwargs,
) -> CompanyContext:
    """Build a synthetic CompanyContext without touching the database."""
    history_years = history_years or [2019, 2020, 2021, 2022, 2023, 2024]
    history = history or {
        metric: [np.nan] * len(history_years)
        for metric in ("roe", "revenue", "net_profit")
    }
    latest = latest or {"roe": 25.0, "revenue": 1200.0, "net_profit": 120.0}
    defaults = dict(
        company_id=company_id,
        company_name="Test Company Ltd",
        sector="Test",
        sub_sector="Unknown",
        broad_sector="Unknown",
        is_financial=kwargs.pop("is_financial", False),
        latest_period="Mar 2024",
        latest_year=history_years[-1],
        history_years=history_years,
        latest=latest,
        history=history,
        trailing={},
        history_df=None,
    )
    defaults.update(kwargs)
    return CompanyContext(**defaults)


@pytest.fixture(scope="module")
def financial_data():
    """Load the real datasets once for DB-backed tests."""
    return load_financial_data()


# =============================================================================
# 1. DATA LOADING
# =============================================================================


class TestDataLoading:
    """Verify the data-access layer against the real database."""

    def test_companies_loaded(self):
        df = load_companies()
        assert not df.empty
        assert {"company_id", "company_name", "sector"}.issubset(df.columns)
        assert len(df) >= 90  # Nifty-100 universe present in live DB

    def test_sectors_loaded(self):
        df = load_sectors()
        assert not df.empty
        assert "sub_sector" in df.columns

    def test_profit_loss_loaded(self):
        df = load_profit_loss()
        assert not df.empty
        assert {"company_id", "period", "sales", "net_profit"}.issubset(df.columns)

    def test_balance_sheet_loaded(self):
        df = load_balance_sheet()
        assert not df.empty
        assert {"company_id", "period", "borrowings"}.issubset(df.columns)

    def test_cashflow_loaded(self):
        df = load_cashflow_data()
        assert not df.empty
        assert "free_cash_flow" in df.columns

    def test_ratio_data_loaded(self):
        df = load_ratio_data()
        assert not df.empty
        assert "company_id" in df.columns

    def test_analysis_data_loaded(self):
        df = load_analysis_data()
        assert "compounded_sales_growth" in df.columns

    def test_load_financial_data_keys(self, financial_data):
        expected = {
            "companies", "sectors", "profit_loss", "balance_sheet",
            "cash_flow", "ratios", "market_cap", "analysis",
        }
        assert set(financial_data.keys()) == expected
        assert not financial_data["companies"].empty

    def test_missing_table_returns_empty(self):
        """A non-existent table must not raise; an empty frame is returned."""
        from src.nlp.pros_cons_generator import _load_table

        df = _load_table("table_that_does_not_exist_xyz", ["company_id"])
        assert isinstance(df, pd.DataFrame)
        assert df.empty


# =============================================================================
# 2. COMPANY CONTEXT CREATION
# =============================================================================


class TestCompanyContext:
    """Verify CompanyContext building against the real database."""

    def test_context_for_tcs(self):
        context = get_company_context("TCS")
        assert context.company_id == "TCS"
        assert isinstance(context.latest_year, int)
        assert len(context.history_years) >= 5
        assert "roe" in context.latest
        assert "revenue" in context.history
        assert isinstance(context.is_financial, bool)

    def test_context_normalizes_company_id(self):
        context = get_company_context("tcs")
        assert context.company_id == "TCS"

    def test_context_for_missing_company_does_not_raise(self):
        context = get_company_context("UNKNOWN_COMPANY_XYZ")
        assert context.company_id == "UNKNOWN_COMPANY_XYZ"
        # Missing company must produce an empty-but-valid context.
        assert context.latest_year is None
        assert context.history_years == []
        assert context.latest == {}

    def test_context_latest_and_history_alignment(self):
        context = get_company_context("RELIANCE")
        assert len(context.history_years) == len(context.history["roe"])
        assert context.latest_year == context.history_years[-1]

    def test_context_to_dict_is_serializable(self):
        context = get_company_context("INFY")
        payload = context.to_dict()
        assert payload["company_id"] == "INFY"
        assert payload["history_df"] is None  # DataFrame stripped


# =============================================================================
# 3. LATEST-YEAR EXTRACTION
# =============================================================================


class TestLatestYearExtraction:
    """Verify latest-year resolution (synthetic + live)."""

    def test_synthetic_latest_year(self):
        df = pd.DataFrame({
            "period": ["Mar 2019", "Mar 2020", "Mar 2021"],
            "company_id": ["X", "X", "X"],
            "revenue": [100.0, 150.0, np.nan],
            "year": [2019, 2020, 2021],
        })
        _, year, metrics = prepare_latest_year_data("X", history_df=df)
        assert year == 2021
        assert metrics["revenue"] is None  # latest year missing revenue

    def test_live_latest_year_is_latest(self):
        context = get_company_context("RELIANCE")
        assert context.latest_year >= 2023

    def test_empty_history_latest(self):
        _, year, metrics = prepare_latest_year_data(
            "X", history_df=pd.DataFrame()
        )
        assert year is None
        assert metrics == {}


# =============================================================================
# 4. HISTORICAL DATA EXTRACTION
# =============================================================================


class TestHistoricalExtraction:
    """Verify per-company history merging and metric extraction."""

    def test_synthetic_history_merge(self):
        data = {
            "profit_loss": pd.DataFrame({
                "company_id": ["SYN"] * 3,
                "period": ["Mar 2020", "Mar 2021", "Mar 2022"],
                "sales": [100.0, 140.0, 200.0],
                "net_profit": [10.0, 15.0, 25.0],
                "operating_profit": [15.0, 20.0, 30.0],
                "depreciation": [5.0, 6.0, 7.0],
            }),
            "balance_sheet": pd.DataFrame({
                "company_id": ["SYN"] * 2,
                "period": ["Mar 2021", "Mar 2022"],
                "borrowings": [50.0, 60.0],
                "investments": [10.0, 12.0],
            }),
            "cash_flow": pd.DataFrame(),
            "ratios": pd.DataFrame(),
            "market_cap": pd.DataFrame(),
        }
        history = prepare_company_history("SYN", data=data)
        assert not history.empty
        assert [int(y) for y in history["year"]] == [2020, 2021, 2022]
        # Derived EBITDA = operating_profit + depreciation for 2022.
        ebitda = history.loc[history["year"] == 2022, "ebitda"].iloc[0]
        assert ebitda == pytest.approx(37.0)
        # Derived net_debt = borrowings - investments for 2021.
        nd = history.loc[history["year"] == 2021, "net_debt"].iloc[0]
        assert nd == pytest.approx(40.0)

    def test_live_history_depth(self):
        history = prepare_company_history("RELIANCE")
        assert len(history) >= 5
        assert int(history["year"].min()) <= 2020
        assert int(history["year"].max()) >= 2023

    def test_metric_history_from_context(self):
        context = get_company_context("ITC")
        roe_series = get_metric_history(context, "roe")
        assert isinstance(roe_series, list)
        assert len(roe_series) > 0

    def test_metric_history_filtered_by_years(self):
        context = make_context()
        context.history = {"roe": [10.0, 11.0, 12.0, 13.0, 14.0]}
        context.history_years = [2020, 2021, 2022, 2023, 2024]
        last3 = get_metric_history(context, "roe", years=[2022, 2023, 2024])
        assert last3 == [12.0, 13.0, 14.0]


# =============================================================================
# 5–8. SAFE DATA HANDLING (missing / NaN / inf / zero denominator)
# =============================================================================


class TestSafeDataHandling:
    """Verify safe_float, get_latest_value, safe_divide, period parsing."""

    def test_safe_float_missing(self):
        assert safe_float(None) is None

    def test_safe_float_nan(self):
        assert safe_float(float("nan")) is None
        assert safe_float(np.nan) is None

    def test_safe_float_inf(self):
        assert safe_float(float("inf")) is None
        assert safe_float(float("-inf")) is None

    def test_safe_float_strings(self):
        assert safe_float("12.5") == 12.5
        assert safe_float("") is None
        assert safe_float("abc") is None

    def test_safe_float_does_not_fabricate_zero(self):
        """Missing financial data must never silently become 0."""
        assert safe_float(None) != 0

    def test_zero_denominator(self):
        assert safe_divide(10.0, 0.0) is None
        assert safe_divide(10.0, np.nan) is None

    def test_normal_division(self):
        assert safe_divide(10.0, 4.0) == 2.5

    def test_get_latest_value_skips_gaps(self):
        series = [np.nan, None, 5.0, np.nan, 9.0]
        assert get_latest_value(series) == 9.0

    def test_get_latest_value_all_missing(self):
        assert get_latest_value([None, np.nan, None]) is None

    def test_get_latest_value_empty(self):
        assert get_latest_value([]) is None

    def test_parse_period(self):
        assert parse_period("Mar 2024") == 2024
        assert parse_period("Sep 2019") == 2019
        assert parse_period(2021) == 2021
        assert parse_period("Mar 2023 15") == 2023  # artifact tolerated

    def test_parse_period_trailing_and_missing(self):
        assert parse_period(PERIOD_TTM) is None
        assert parse_period(None) is None
        assert parse_period(float("nan")) is None


# =============================================================================
# 9–10. HISTORY DETECTION (3yr / 5yr)
# =============================================================================


class TestHistoryDetection:
    """Verify has_consecutive_years and has_minimum_history."""

    def test_three_consecutive_years(self):
        assert has_consecutive_years([2019, 2020, 2021], 3) is True
        assert has_consecutive_years([2019, 2021, 2022], 3) is False

    def test_five_consecutive_years(self):
        years = [2016, 2017, 2018, 2019, 2020, 2022]
        assert has_consecutive_years(years, 5) is True
        assert has_consecutive_years([2016, 2018, 2020, 2022, 2024], 5) is False

    def test_unsorted_years(self):
        assert has_consecutive_years([2021, 2019, 2020], 3) is True

    def test_minimum_history(self):
        assert has_minimum_history([1.0, 2.0, 3.0], min_years=3) is True
        assert has_minimum_history([1.0, np.nan, 2.0], min_years=3) is False

    def test_zero_required_is_true(self):
        assert has_consecutive_years([], 0) is True


# =============================================================================
# 11–14. TREND HELPERS
# =============================================================================


class TestTrendHelpers:
    """Verify is_improving / is_declining / consecutive +/- helpers."""

    def test_improving(self):
        assert is_improving([10.0, 12.0, 15.0, 18.0], periods=3) is True
        assert is_improving([10.0, 12.0, 15.0, 14.0], periods=3) is False

    def test_improving_insufficient_history(self):
        assert is_improving([10.0, 12.0], periods=3) is False

    def test_declining(self):
        assert is_declining([18.0, 15.0, 12.0, 10.0], periods=3) is True
        assert is_declining([18.0, 15.0, 12.0, 14.0], periods=3) is False

    def test_improving_skips_invalid(self):
        assert is_improving([10.0, np.nan, 12.0, 14.0, 16.0], periods=3) is True

    def test_consecutive_positive(self):
        values = [-5.0, 2.0, 4.0, 6.0, 8.0]
        assert count_consecutive_positive(values) == 4

    def test_consecutive_positive_none(self):
        assert count_consecutive_positive([-5.0, -2.0, -1.0]) == 0

    def test_consecutive_negative(self):
        values = [5.0, -2.0, -4.0, -6.0]
        assert count_consecutive_negative(values) == 3

    def test_consecutive_condition_with_predicate(self):
        values = [10.0, 25.0, 35.0, 40.0, 12.0]
        above_20 = check_consecutive_condition(
            values, lambda v: v > 20.0, required=3
        )
        assert above_20 is True
        not_above = check_consecutive_condition(
            values, lambda v: v > 20.0, required=4
        )
        assert not_above is False

    def test_cagr_calculation(self):
        assert calculate_cagr(100.0, 121.0, 2) == pytest.approx(10.0)

    def test_cagr_zero_base_returns_none(self):
        assert calculate_cagr(0.0, 100.0, 3) is None

    def test_cagr_invalid_returns_none(self):
        assert calculate_cagr(np.nan, 100.0, 3) is None
        assert calculate_cagr(100.0, -50.0, 3) is None


# =============================================================================
# 15. RULERESULT VALIDATION
# =============================================================================


class TestRuleResult:
    """Verify RuleResult fields, validation, and output serialization."""

    def test_valid_result(self):
        result = RuleResult(
            company_id="TCS",
            rule_id="PRO_00",
            rule_type=TYPE_PRO,
            triggered=True,
            text="Some text",
            confidence_pct=75.0,
            reason="test",
        )
        assert result.validate() == []

    def test_invalid_rule_type(self):
        result = RuleResult(
            company_id="TCS", rule_id="X", rule_type="info",
            triggered=False, confidence_pct=50.0,
        )
        assert any("rule_type" in m for m in result.validate())

    def test_invalid_confidence(self):
        result = RuleResult(
            company_id="TCS", rule_id="X", rule_type=TYPE_PRO,
            triggered=False, confidence_pct=150.0,
        )
        assert any("confidence_pct" in m for m in result.validate())

    def test_null_ids(self):
        result = RuleResult(
            company_id="", rule_id="", rule_type=TYPE_CON,
            triggered=False, confidence_pct=50.0,
        )
        issues = result.validate()
        assert any("company_id" in m for m in issues)
        assert any("rule_id" in m for m in issues)

    def test_to_dict_matches_output_schema(self):
        result = RuleResult(
            company_id="TCS", rule_id="PRO_00", rule_type=TYPE_PRO,
            triggered=True, text="x", confidence_pct=80.123,
        )
        d = result.to_dict()
        assert set(d.keys()) == set(OUTPUT_COLUMNS)
        assert d["confidence_pct"] == 80.12  # rounded


# =============================================================================
# 16. RULE REGISTRY
# =============================================================================


class _DummyProRule(FinancialRule):
    rule_id = "PRO_TEST_DUMMY"
    rule_type = TYPE_PRO
    name = "Dummy Pro"

    def evaluate(self, context, conn=None):
        return RuleResult(
            company_id=context.company_id,
            rule_id=self.rule_id,
            rule_type=self.rule_type,
            triggered=True,
            confidence_pct=80.0,
        )


class _DummyConRule(FinancialRule):
    rule_id = "CON_TEST_DUMMY"
    rule_type = TYPE_CON
    name = "Dummy Con"

    def evaluate(self, context, conn=None):
        return RuleResult(
            company_id=context.company_id,
            rule_id=self.rule_id,
            rule_type=self.rule_type,
            triggered=False,
            confidence_pct=0.0,
        )


class TestRuleRegistry:
    """Verify registries are populated by default and accept registrations."""

    def test_registries_by_default(self):
        # After Module 2C, both registries must be populated with 12 rules each.
        assert len(PRO_RULES) == 12
        assert [r.rule_id for r in PRO_RULES] == [
            f"PRO_{i:02d}" for i in range(1, 13)
        ]
        assert len(CON_RULES) == 12
        assert [r.rule_id for r in CON_RULES] == [
            f"CON_{i:02d}" for i in range(1, 13)
        ]

        reg = get_registered_rules()
        assert len(reg["pro"]) == 12
        assert len(reg["con"]) == 12
        assert [r.rule_id for r in reg["pro"]] == [r.rule_id for r in PRO_RULES]
        assert [r.rule_id for r in reg["con"]] == [r.rule_id for r in CON_RULES]

    def test_register_rule(self, monkeypatch):
        # Temporarily clear the registries for this test
        monkeypatch.setattr("src.nlp.pros_cons_generator.PRO_RULES", [])
        monkeypatch.setattr("src.nlp.pros_cons_generator.CON_RULES", [])

        pro_rule = _DummyProRule()
        register_pro_rule(pro_rule)
        assert len(get_registered_rules()["pro"]) == 1
        assert get_registered_rules()["pro"][0].rule_id == "PRO_TEST_DUMMY"

        con_rule = _DummyConRule()
        register_con_rule(con_rule)
        assert len(get_registered_rules()["con"]) == 1
        assert get_registered_rules()["con"][0].rule_id == "CON_TEST_DUMMY"

    def test_register_wrong_type(self, monkeypatch):
        monkeypatch.setattr("src.nlp.pros_cons_generator.CON_RULES", [])
        with pytest.raises(ValueError):
            register_con_rule(_DummyProRule())  # pro rule into con registry

    def test_evaluate_rules_returns_registered_results(self):
        # After Module 2C, evaluating a company returns 24 results.
        context = make_context()
        results = evaluate_rules_for_company(context)
        assert len(results) == 24
        assert all(isinstance(r, RuleResult) for r in results)

        pro_results = [r for r in results if r.rule_type == TYPE_PRO]
        con_results = [r for r in results if r.rule_type == TYPE_CON]

        assert len(pro_results) == 12
        assert len(con_results) == 12

    def test_concrete_rule_placeholder(self):
        context = make_context(company_id="X")
        rule = _DummyConRule()
        result = rule.evaluate(context)
        assert result.company_id == "X"
        assert isinstance(result, RuleResult)


# =============================================================================
# 17. CONFIDENCE FRAMEWORK
# =============================================================================


class TestConfidence:
    """Verify confidence validation, formatting, and generic aggregation."""

    def test_validate_bounds(self):
        assert validate_confidence(0.0) is True
        assert validate_confidence(100.0) is True
        assert validate_confidence(60.0) is True

    def test_validate_out_of_range(self):
        assert validate_confidence(-1.0) is False
        assert validate_confidence(101.0) is False
        assert validate_confidence(np.nan) is False
        assert validate_confidence(None) is False

    def test_threshold_default(self):
        assert CONFIDENCE_THRESHOLD == 60.0

    def test_format_clamps_and_rounds(self):
        assert format_confidence(101.0) == 100.0
        assert format_confidence(-5.0) == 0.0
        assert format_confidence(None) == 0.0
        assert format_confidence(80.456) == 80.46

    def test_calculate_equal_weights(self):
        assert calculate_confidence([50.0, 100.0]) == 75.0

    def test_calculate_weighted(self):
        value = calculate_confidence([0.0, 100.0], weights=[1.0, 3.0])
        assert value == 75.0

    def test_calculate_invalid_inputs(self):
        assert calculate_confidence([]) is None
        assert calculate_confidence([None, 50.0]) is None
        assert calculate_confidence([50.0, 150.0]) is None
        assert calculate_confidence([50.0, 50.0], weights=[1.0]) is None

    def test_min_max_constants(self):
        assert CONFIDENCE_MIN == 0.0
        assert CONFIDENCE_MAX == 100.0


# =============================================================================
# 18–19. OUTPUT SCHEMA VALIDATION + DUPLICATE DETECTION
# =============================================================================


def _valid_results_df():
    return pd.DataFrame([
        {"company_id": "TCS", "type": TYPE_PRO, "rule_id": "PRO_01",
         "text": "a", "confidence_pct": 80.0},
        {"company_id": "TCS", "type": TYPE_CON, "rule_id": "CON_01",
         "text": "b", "confidence_pct": 70.0},
        {"company_id": "INFY", "type": TYPE_PRO, "rule_id": "PRO_01",
         "text": "c", "confidence_pct": 90.0},
    ])


class TestOutputSchema:
    """Verify validate_output_schema against the required schema."""

    def test_valid_df_passes(self):
        ok, issues = validate_output_schema(_valid_results_df())
        assert ok is True
        assert issues == []

    def test_empty_valid_df_passes(self):
        df = pd.DataFrame(columns=OUTPUT_COLUMNS)
        ok, _ = validate_output_schema(df)
        assert ok is True

    def test_missing_columns(self):
        df = _valid_results_df().drop(columns=["text"])
        ok, issues = validate_output_schema(df)
        assert ok is False
        assert any("missing required columns" in m for m in issues)

    def test_invalid_type(self):
        df = _valid_results_df()
        df.loc[0, "type"] = "info"
        ok, issues = validate_output_schema(df)
        assert ok is False
        assert any("invalid type" in m for m in issues)

    def test_confidence_out_of_range(self):
        df = _valid_results_df()
        df.loc[0, "confidence_pct"] = 150.0
        ok, issues = validate_output_schema(df)
        assert ok is False
        assert any("confidence_pct" in m for m in issues)

    def test_null_company_id(self):
        df = _valid_results_df()
        df.loc[0, "company_id"] = None
        ok, issues = validate_output_schema(df)
        assert ok is False
        assert any("company_id" in m for m in issues)

    def test_null_rule_id(self):
        df = _valid_results_df()
        df.loc[0, "rule_id"] = ""
        ok, issues = validate_output_schema(df)
        assert ok is False
        assert any("rule_id" in m for m in issues)

    def test_duplicate_detection(self):
        df = _valid_results_df()
        df = pd.concat([df, df.iloc[[0]]], ignore_index=True)  # duplicate row 0
        ok, issues = validate_output_schema(df)
        assert ok is False
        assert any("duplicate" in m.lower() for m in issues)

    def test_no_duplicates_in_valid(self):
        ok, _ = validate_output_schema(_valid_results_df())
        assert ok is True


# =============================================================================
# 20. EMPTY-RESULT COMPANY COVERAGE
# =============================================================================


class TestCompanyCoverage:
    """Verify coverage validation handles empty results in Module 2A."""

    def test_empty_results_all_missing(self):
        stats = validate_company_coverage(["A", "B", "C"], None)
        assert stats["companies_total"] == 3
        assert stats["missing_pro"] == 3
        assert stats["missing_con"] == 3
        assert stats["companies_fully_covered"] == 0
        assert stats["expected_incomplete_module_2a"] is True

    def test_empty_dataframe_results(self):
        stats = validate_company_coverage(["A", "B"], pd.DataFrame())
        assert stats["missing_pro"] == 2
        assert stats["missing_con"] == 2

    def test_partial_coverage(self):
        df = pd.DataFrame([
            {"company_id": "A", "type": TYPE_PRO, "rule_id": "PRO_01",
             "text": "x", "confidence_pct": 50.0},
            {"company_id": "A", "type": TYPE_CON, "rule_id": "CON_01",
             "text": "y", "confidence_pct": 50.0},
        ])
        stats = validate_company_coverage(["A", "B"], df)
        assert stats["companies_fully_covered"] == 1
        assert stats["missing_pro"] == 1  # B missing
        assert stats["missing_con"] == 1  # B missing

    def test_no_fabrication(self):
        """Module 2A must not claim coverage that does not exist."""
        stats = validate_company_coverage(list("ABCDEF"))
        assert stats["missing_pro"] == 6
        assert stats["missing_con"] == 6


# =============================================================================
# 21. FINANCIAL-SECTOR DETECTION
# =============================================================================


class TestFinancialSector:
    """Verify is_financial_sector and get_sub_sector."""

    def test_financial_sub_sectors(self):
        for sub in ["Private Banks", "Public Sector Banks", "Consumer Finance",
                    "Life Insurance", "General Insurance", "Diversified Financials",
                    "Speciality Finance"]:
            assert is_financial_sector(sub) is True

    def test_non_financial_sub_sector(self):
        assert is_financial_sector("IT Services") is False
        assert is_financial_sector("Cement") is False

    def test_missing_sub_sector(self):
        assert is_financial_sector(None) is False
        assert is_financial_sector("") is False

    def test_case_insensitive(self):
        assert is_financial_sector("private banks") is True

    def test_live_financial_company(self):
        assert is_financial_sector(get_sub_sector("AXISBANK")) is True

    def test_live_non_financial_company(self):
        assert is_financial_sector(get_sub_sector("TCS")) is False


# =============================================================================
# 22. MODULE 1 REGRESSION
# =============================================================================


class TestModule1Regression:
    """Verify Sprint 5 Module 1 outputs remain intact."""

    def test_analysis_parsed_csv_exists(self):
        path = PROJECT_ROOT / "output" / "analysis_parsed.csv"
        assert path.exists()
        df = pd.read_csv(path)
        assert {"company_id", "metric_type", "value_pct"}.issubset(df.columns)
        assert len(df) > 0

    def test_parse_failures_csv_exists(self):
        path = PROJECT_ROOT / "output" / "parse_failures.csv"
        assert path.exists()
        df = pd.read_csv(path)
        assert {"company_id", "metric_type", "failure_reason"}.issubset(df.columns)

    def test_module1_outputs_not_modified(self):
        """Module 2A must not overwrite Module 1 CSV outputs."""
        parsed = PROJECT_ROOT / "output" / "analysis_parsed.csv"
        failures = PROJECT_ROOT / "output" / "parse_failures.csv"
        assert parsed.stat().st_size > 0
        assert failures.stat().st_size > 0