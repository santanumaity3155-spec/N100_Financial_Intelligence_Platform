"""
test_parser.py

Unit and integration tests for the NLP Analysis Text Parser
(Sprint 5 – Module 1).

Verifies:
- analysis.xlsx loads
- Regex parses valid formats
- Invalid formats go to parse_failures.csv
- analysis_parsed.csv generated
- parse_failures.csv generated
- Validation against Ratio Engine works
- Difference > 5% flagged
- No runtime errors
- No SQL errors
"""

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.nlp.parser import (  # noqa: E402
    ANALYSIS_DATASET_NAME,
    FAILURES_CSV_PATH,
    MANUAL_REVIEW_THRESHOLD,
    METRIC_ROE,
    METRIC_SALES_GROWTH,
    PARSED_CSV_PATH,
    PERIOD_REGEX,
    load_analysis_data,
    parse_dataframe,
    parse_metric,
    save_analysis_csv,
    save_failures_csv,
    validate_against_ratio_engine,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture(scope="module")
def parsed_outputs(tmp_path_factory):
    """Run the full pipeline and return (parsed_df, failures_df)."""
    tmp = tmp_path_factory.mktemp("nlp_outputs")
    parsed_csv = tmp / "analysis_parsed.csv"
    failures_csv = tmp / "parse_failures.csv"

    df = load_analysis_data()
    parsed_df, failures_df = parse_dataframe(df)
    validated_df = validate_against_ratio_engine(parsed_df)

    save_analysis_csv(validated_df, parsed_csv)
    save_failures_csv(failures_df, failures_csv)

    return validated_df, failures_df, parsed_csv, failures_csv


# =============================================================================
# REGEX TESTS
# =============================================================================


class TestRegex:
    """Verify the official Sprint regex behaviour."""

    def test_ten_years_21_percent(self):
        m = PERIOD_REGEX.search("10 Years: 21%")
        assert m is not None
        assert int(m.group(1)) == 10
        assert float(m.group(2)) == 21.0

    def test_five_year_17_6_percent(self):
        m = PERIOD_REGEX.search("5 Year : 17.6%")
        assert m is not None
        assert int(m.group(1)) == 5
        assert float(m.group(2)) == 17.6

    def test_mixed_capitalization(self):
        m = PERIOD_REGEX.search("10 yEaRs: 21%")
        assert m is not None
        assert int(m.group(1)) == 10
        assert float(m.group(2)) == 21.0

    def test_extra_spaces(self):
        m = PERIOD_REGEX.search("10  Years   :   21  %")
        assert m is not None
        assert int(m.group(1)) == 10
        assert float(m.group(2)) == 21.0

    def test_trailing_spaces(self):
        m = PERIOD_REGEX.search("10 Years: 21%   ")
        assert m is not None
        assert float(m.group(2)) == 21.0

    def test_negative_value(self):
        m = PERIOD_REGEX.search("3 Years: -1%")
        assert m is not None
        assert int(m.group(1)) == 3
        assert float(m.group(2)) == -1.0

    def test_one_year(self):
        m = PERIOD_REGEX.search("1 Year: -2%")
        assert m is not None
        assert int(m.group(1)) == 1
        assert float(m.group(2)) == -2.0

    def test_no_match_ttm(self):
        assert PERIOD_REGEX.search("TTM: 43%") is None

    def test_no_match_last_year(self):
        assert PERIOD_REGEX.search("Last Year: 12%") is None


# =============================================================================
# PARSE_METRIC TESTS
# =============================================================================


class TestParseMetric:
    """Verify parse_metric handles valid and invalid inputs."""

    def test_valid_parse(self):
        result = parse_metric("10 Years: 21%", METRIC_SALES_GROWTH)
        assert result.parsed_success is True
        assert result.period_years == 10
        assert result.value_pct == 21.0
        assert result.failure_reason is None

    def test_valid_parse_5_year(self):
        result = parse_metric("5 Year : 17.6%", METRIC_SALES_GROWTH)
        assert result.parsed_success is True
        assert result.period_years == 5
        assert result.value_pct == 17.6

    def test_negative_cagr(self):
        result = parse_metric("3 Years: -1%", METRIC_SALES_GROWTH)
        assert result.parsed_success is True
        assert result.period_years == 3
        assert result.value_pct == -1.0

    def test_none_input(self):
        result = parse_metric(None, METRIC_SALES_GROWTH)
        assert result.parsed_success is False
        assert result.failure_reason is not None

    def test_nan_input(self):
        result = parse_metric(np.nan, METRIC_SALES_GROWTH)
        assert result.parsed_success is False

    def test_ttm_failure(self):
        result = parse_metric("TTM: 43%", METRIC_SALES_GROWTH)
        assert result.parsed_success is False
        assert "TTM" in result.failure_reason

    def test_last_year_failure(self):
        result = parse_metric("Last Year: 12%", METRIC_ROE)
        assert result.parsed_success is False

    def test_garbage_failure(self):
        result = parse_metric("gibberish", METRIC_SALES_GROWTH)
        assert result.parsed_success is False

    def test_empty_string_failure(self):
        result = parse_metric("   ", METRIC_SALES_GROWTH)
        assert result.parsed_success is False

    def test_mixed_case(self):
        result = parse_metric("10 YeArS: 21%", METRIC_SALES_GROWTH)
        assert result.parsed_success is True
        assert result.period_years == 10
        assert result.value_pct == 21.0


# =============================================================================
# LOAD DATA TESTS
# =============================================================================


class TestLoadData:
    """Verify analysis.xlsx loads correctly."""

    def test_loads_analysis_data(self):
        df = load_analysis_data()
        assert not df.empty
        assert "company_id" in df.columns
        # At least one target column must exist
        target_cols = [
            "compounded_sales_growth",
            "compounded_profit_growth",
            "stock_price_cagr",
            "roe",
        ]
        assert any(c in df.columns for c in target_cols)

    def test_company_ids_present(self):
        df = load_analysis_data()
        assert df["company_id"].nunique() >= 5


# =============================================================================
# PARSE_DATAFRAME TESTS
# =============================================================================


class TestParseDataFrame:
    """Verify parse_dataframe returns parsed + failures DataFrames."""

    def test_returns_both_dataframes(self):
        df = pd.DataFrame({
            "company_id": ["TEST"],
            "compounded_sales_growth": ["10 Years: 21%"],
            "compounded_profit_growth": ["TTM: 5%"],
        })
        parsed_df, failures_df = parse_dataframe(df)
        assert len(parsed_df) == 1
        assert len(failures_df) == 1

    def test_parsed_columns(self):
        df = pd.DataFrame({
            "company_id": ["TEST"],
            "compounded_sales_growth": ["10 Years: 21%"],
        })
        parsed_df, _ = parse_dataframe(df)
        expected_cols = {
            "company_id", "metric_type", "period_years",
            "value_pct", "source_text", "parsed_success", "failure_reason",
        }
        assert expected_cols.issubset(set(parsed_df.columns))
        assert parsed_df.iloc[0]["period_years"] == 10
        assert parsed_df.iloc[0]["value_pct"] == 21.0

    def test_empty_dataframe(self):
        parsed_df, failures_df = parse_dataframe(pd.DataFrame())
        assert parsed_df.empty
        assert failures_df.empty


# =============================================================================
# VALIDATION TESTS
# =============================================================================


class TestValidation:
    """Verify validation against Ratio Engine works."""

    def test_adds_validation_columns(self, parsed_outputs):
        validated_df, _, _, _ = parsed_outputs
        if not validated_df.empty:
            assert "manual_review" in validated_df.columns
            assert "difference_pct" in validated_df.columns

    def test_manual_review_is_bool(self, parsed_outputs):
        validated_df, _, _, _ = parsed_outputs
        if not validated_df.empty:
            assert validated_df["manual_review"].isin([True, False]).all()

    def test_difference_calculation(self):
        # Simulate a parsed row and validate against a known reference
        parsed_df = pd.DataFrame([
            {
                "company_id": "HDFCBANK",
                "metric_type": "compounded_sales_growth",
                "period_years": 10,
                "value_pct": 20.29,  # matches financial_kpis revenue_cagr exactly
                "source_text": "10 Years: 20.29%",
                "parsed_success": True,
            }
        ])
        validated_df = validate_against_ratio_engine(parsed_df)
        row = validated_df.iloc[0]
        assert abs(row["difference_pct"]) <= 0.01
        assert row["manual_review"] is False

    def test_large_difference_flagged(self):
        # Parsed value deliberately differs > 5% from reference
        parsed_df = pd.DataFrame([
            {
                "company_id": "HDFCBANK",
                "metric_type": "compounded_sales_growth",
                "period_years": 10,
                "value_pct": 99.0,  # reference ~20.29, diff ~78.7
                "source_text": "10 Years: 99%",
                "parsed_success": True,
            }
        ])
        validated_df = validate_against_ratio_engine(parsed_df)
        row = validated_df.iloc[0]
        assert row["manual_review"] is True
        assert abs(row["difference_pct"]) > MANUAL_REVIEW_THRESHOLD

    def test_no_reference_no_flag(self):
        # stock_price_cagr has no reference → manual_review False, diff None
        parsed_df = pd.DataFrame([
            {
                "company_id": "HDFCBANK",
                "metric_type": "stock_price_cagr",
                "period_years": 10,
                "value_pct": 15.0,
                "source_text": "10 Years: 15%",
                "parsed_success": True,
            }
        ])
        validated_df = validate_against_ratio_engine(parsed_df)
        row = validated_df.iloc[0]
        assert row["manual_review"] is False
        assert pd.isna(row["difference_pct"])


# =============================================================================
# CSV OUTPUT TESTS
# =============================================================================


class TestCsvOutput:
    """Verify CSV generation."""

    def test_analysis_csv_generated(self, parsed_outputs):
        _, _, parsed_csv, _ = parsed_outputs
        assert parsed_csv.exists()
        df = pd.read_csv(parsed_csv)
        assert {"company_id", "metric_type", "period_years", "value_pct"}.issubset(set(df.columns))

    def test_failures_csv_generated(self, parsed_outputs):
        _, _, _, failures_csv = parsed_outputs
        assert failures_csv.exists()
        df = pd.read_csv(failures_csv)
        assert {"company_id", "metric_type", "source_text", "failure_reason"}.issubset(set(df.columns))

    def test_failures_csv_contains_ttm(self, parsed_outputs):
        _, failures_df, _, failures_csv = parsed_outputs
        # TTM rows must be present in failures
        if not failures_df.empty:
            ttm_failures = failures_df[failures_df["source_text"].str.contains("TTM", na=False)]
            assert len(ttm_failures) > 0

    def test_save_empty_failures(self, tmp_path):
        empty_df = pd.DataFrame(columns=[
            "company_id", "metric_type", "source_text", "failure_reason",
        ])
        path = tmp_path / "empty_failures.csv"
        save_failures_csv(empty_df, path)
        assert path.exists()
        assert os.path.getsize(path) > 0

    def test_save_empty_parsed(self, tmp_path):
        empty_df = pd.DataFrame(columns=[
            "company_id", "metric_type", "period_years", "value_pct",
            "source_text", "parsed_success", "manual_review", "difference_pct",
        ])
        path = tmp_path / "empty_parsed.csv"
        save_analysis_csv(empty_df, path)
        assert path.exists()
        assert os.path.getsize(path) > 0


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestIntegration:
    """End-to-end pipeline tests."""

    def test_full_pipeline_parses_real_data(self, parsed_outputs):
        validated_df, failures_df, _, _ = parsed_outputs
        # Real analysis.xlsx has 20 rows × 4 metrics = 80 cells
        # TTM and Last Year rows will fail, others succeed
        assert len(validated_df) + len(failures_df) >= 60

    def test_parsed_rows_are_success(self, parsed_outputs):
        validated_df, _, _, _ = parsed_outputs
        if not validated_df.empty:
            assert (validated_df["parsed_success"] == True).all()  # noqa: E712

    def test_sorted_output(self, parsed_outputs):
        validated_df, _, _, _ = parsed_outputs
        if len(validated_df) > 1:
            keys = list(zip(
                validated_df["company_id"],
                validated_df["metric_type"],
                validated_df["period_years"].fillna(0),
            ))
            assert keys == sorted(keys, key=lambda k: (k[0], k[1], k[2]))

