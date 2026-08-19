"""
test_cashflow_intelligence.py

Unit and integration tests for Sprint 5 Module 3 - Cash Flow Intelligence.

Covers:
- CFO Quality Score
- CapEx Intensity
- Free Cash Flow (FCF)
- FCF CAGR (5 year)
- FCF Conversion
- Distress Signal
- Deleveraging Flag
- Capital Allocation
- Output generation
- Output schema
"""

import numpy as np
import pandas as pd
import pytest
from pathlib import Path

from src.analytics.cashflow_intelligence import (
    parse_period,
    is_valid_annual_period,
    compute_cfo_quality,
    compute_capex_intensity,
    compute_fcf_cagr_5yr,
    compute_fcf_conversion,
    compute_distress_flag,
    compute_deleveraging_flag,
    compute_capital_allocation_label,
)
from src.analytics.cashflow_kpis import calculate_free_cash_flow
from src.analytics.cagr import (
    FLAG_NORMAL,
    FLAG_ZERO_BASE,
    FLAG_DECLINE_TO_LOSS,
    FLAG_TURNAROUND,
    FLAG_BOTH_NEGATIVE,
    FLAG_INSUFFICIENT,
)
from src.module3_cashflow_intelligence import (
    OUTPUT_COLUMNS,
    DISTRESS_CSV_COLUMNS,
    build_output_dataframe,
    build_distress_dataframe,
    write_outputs,
    validate_output_files,
    process_all_companies,
)

# =============================================================================
# TEST DATA HELPERS
# =============================================================================


def make_cf(rows):
    """Build a cash-flow DataFrame with the populated *_activity columns."""
    return pd.DataFrame(
        rows,
        columns=[
            "period",
            "operating_activity",
            "investing_activity",
            "financing_activity",
        ],
    )


def make_pl(rows):
    """Build a profit & loss DataFrame."""
    return pd.DataFrame(rows, columns=["period", "sales", "net_profit"])


def make_bs(rows):
    """Build a balance-sheet DataFrame."""
    return pd.DataFrame(rows, columns=["period", "borrowings"])


# =============================================================================
# PERIOD PARSING
# =============================================================================


class TestParsePeriod:
    """Period parsing and annual-period validation."""

    def test_canonical_period(self):
        assert parse_period("Mar 2024") == (2024, 3)

    def test_legacy_period(self):
        assert parse_period("Mar-24") == (2024, 3)

    def test_year_only_period(self):
        assert parse_period("2023") == (2023, 12)

    def test_ttm_rejected(self):
        assert parse_period("TTM") is None

    def test_non_annual_rejected(self):
        assert parse_period("Mar 2016 9m") is None
        assert parse_period("Mar 2023 15") is None
        assert parse_period("2024.5") is None

    def test_garbage_rejected(self):
        assert parse_period("not a period") is None
        assert parse_period(None) is None

    def test_is_valid_annual_period(self):
        assert is_valid_annual_period("Mar 2024") is True
        assert is_valid_annual_period("TTM") is False


# =============================================================================
# CFO QUALITY
# =============================================================================


class TestCFOQuality:
    """CFO Quality = average(CFO / PAT) over the latest 5 valid years."""

    def test_normal_average(self):
        cf = make_cf(
            [
                ("Mar 2020", 200, -50, 0),
                ("Mar 2021", 300, -50, 0),
                ("Mar 2022", 400, -50, 0),
            ]
        )
        pl = make_pl(
            [
                ("Mar 2020", 1000, 200),
                ("Mar 2021", 1000, 300),
                ("Mar 2022", 1000, 400),
            ]
        )
        result = compute_cfo_quality(cf, pl)
        # ratios: 1.0, 1.0, 1.0 -> average 1.0 -> Moderate (0.5 <= 1.0 <= 1.0)
        assert result["score"] == 1.0
        assert result["label"] == "Moderate"
        assert result["years_used"] == 3

    def test_high_quality(self):
        cf = make_cf([("Mar 2024", 200, -50, 0)])
        pl = make_pl([("Mar 2024", 1000, 100)])
        result = compute_cfo_quality(cf, pl)
        assert result["score"] == 2.0
        assert result["label"] == "High Quality"

    def test_accrual_risk(self):
        cf = make_cf([("Mar 2024", 40, -50, 0)])
        pl = make_pl([("Mar 2024", 1000, 100)])
        result = compute_cfo_quality(cf, pl)
        assert result["score"] == 0.4
        assert result["label"] == "Accrual Risk"

    def test_pat_zero_skipped(self):
        cf = make_cf(
            [
                ("Mar 2023", 100, -50, 0),
                ("Mar 2024", 200, -50, 0),
            ]
        )
        pl = make_pl(
            [
                ("Mar 2023", 1000, 0),  # PAT == 0 -> skipped, never fabricated
                ("Mar 2024", 1000, 100),
            ]
        )
        result = compute_cfo_quality(cf, pl)
        assert result["score"] == 2.0
        assert result["years_used"] == 1

    def test_insufficient_data(self):
        cf = make_cf([])
        pl = make_pl([])
        result = compute_cfo_quality(cf, pl)
        assert result["score"] is None
        assert result["label"] == "Insufficient Data"

    def test_legacy_and_canonical_periods_merged(self):
        # TCS-style mix of "Mar 2021" and legacy "Mar-22" must sort correctly.
        cf = make_cf(
            [
                ("Mar 2021", 100, -50, 0),
                ("Mar-22", 150, -50, 0),
                ("Mar 2023", 200, -50, 0),
            ]
        )
        pl = make_pl(
            [
                ("Mar 2021", 1000, 100),
                ("Mar-22", 1000, 150),
                ("Mar 2023", 1000, 200),
            ]
        )
        result = compute_cfo_quality(cf, pl)
        assert result["score"] == 1.0
        assert result["years_used"] == 3


# =============================================================================
# CAPEX INTENSITY
# =============================================================================


class TestCapexIntensity:
    """CapEx Intensity = abs(investing_activity) / sales * 100 (latest year)."""

    def test_asset_light(self):
        cf = make_cf([("Mar 2024", 500, -20, 0)])
        pl = make_pl([("Mar 2024", 1000, 100)])
        result = compute_capex_intensity(cf, pl)
        assert result["value"] == 2.0
        assert result["label"] == "Asset Light"

    def test_moderate(self):
        cf = make_cf([("Mar 2024", 500, -50, 0)])
        pl = make_pl([("Mar 2024", 1000, 100)])
        result = compute_capex_intensity(cf, pl)
        assert result["value"] == 5.0
        assert result["label"] == "Moderate"

    def test_capital_intensive(self):
        cf = make_cf([("Mar 2024", 500, -200, 0)])
        pl = make_pl([("Mar 2024", 1000, 100)])
        result = compute_capex_intensity(cf, pl)
        assert result["value"] == 20.0
        assert result["label"] == "Capital Intensive"

    def test_boundary_values(self):
        # 3.0 and 8.0 are inclusive of Moderate.
        cf = make_cf([("Mar 2024", 500, -30, 0)])
        pl = make_pl([("Mar 2024", 1000, 100)])
        assert compute_capex_intensity(cf, pl)["label"] == "Moderate"

        cf = make_cf([("Mar 2024", 500, -80, 0)])
        pl = make_pl([("Mar 2024", 1000, 100)])
        assert compute_capex_intensity(cf, pl)["label"] == "Moderate"

    def test_zero_sales_insufficient(self):
        cf = make_cf([("Mar 2024", 500, -50, 0)])
        pl = make_pl([("Mar 2024", 0, 100)])
        result = compute_capex_intensity(cf, pl)
        assert result["value"] is None
        assert result["label"] == "Insufficient Data"

    def test_missing_investing_insufficient(self):
        cf = make_cf([("Mar 2024", 500, np.nan, 0)])
        pl = make_pl([("Mar 2024", 1000, 100)])
        result = compute_capex_intensity(cf, pl)
        assert result["value"] is None
        assert result["label"] == "Insufficient Data"

    def test_uses_sales_not_ocf(self):
        # Sprint 5 formula is abs(investing)/sales*100, NOT investing/OCF*100.
        cf = make_cf([("Mar 2024", 10, -40, 0)])
        pl = make_pl([("Mar 2024", 1000, 100)])
        result = compute_capex_intensity(cf, pl)
        assert result["value"] == 4.0  # 40/1000*100 ; OCF-based would be 400%


# =============================================================================
# FREE CASH FLOW
# =============================================================================


class TestFreeCashFlow:
    """FCF = CFO - CapEx (CapEx = |investing_activity|)."""

    def test_fcf_canonical_columns(self):
        cf = pd.DataFrame(
            {
                "cash_from_operating_activity": [1000.0],
                "cash_from_investing_activity": [-300.0],
            }
        )
        assert calculate_free_cash_flow(cf) == 700.0

    def test_fcf_computed_from_populated_activity_columns(self):
        # The engine computes FCF = OCF - |investing| even when the database
        # only populates the operating_activity / investing_activity columns.
        cf = make_cf(
            [
                ("Mar 2023", 1000.0, -300.0, 0.0),
                ("Mar 2024", 1200.0, -300.0, 0.0),
            ]
        )
        # FCF 2023 = 700, FCF 2024 = 900 -> 1-year CAGR = 900/700 - 1
        result = compute_fcf_cagr_5yr(cf)
        assert result["value"] is not None
        assert abs(result["value"] - ((900.0 / 700.0) - 1.0) * 100.0) < 0.05

    def test_fcf_positive_investing(self):
        cf = pd.DataFrame(
            {
                "cash_from_operating_activity": [1000.0],
                "cash_from_investing_activity": [300.0],
            }
        )
        assert calculate_free_cash_flow(cf) == 700.0

    def test_fcf_missing_ocf_none(self):
        cf = pd.DataFrame({"cash_from_investing_activity": [-300.0]})
        assert calculate_free_cash_flow(cf) is None


# =============================================================================
# FCF CAGR (5 YEAR)
# =============================================================================


def _fcf_series(fcf_values):
    """Build 6 annual cash-flow rows that produce the given FCF values (OCF=FCF+100, investing=-100)."""
    rows = []
    for i, fcf in enumerate(fcf_values):
        year = 2019 + i
        rows.append((f"Mar {year}", fcf + 100, -100, 0))
    return make_cf(rows)


class TestFCFCagr:
    """5-year FCF CAGR using the existing cagr.calculate_cagr conventions."""

    def test_normal_positive_cagr(self):
        cf = _fcf_series([100.0, 120.0, 130.0, 140.0, 150.0, 161.05])
        result = compute_fcf_cagr_5yr(cf)
        assert result["flag"] is FLAG_NORMAL
        assert result["value"] is not None
        assert abs(result["value"] - 10.0) < 0.05  # (161.05/100)^(1/5)-1 ~ 10%

    def test_insufficient_history(self):
        cf = _fcf_series([100.0])
        result = compute_fcf_cagr_5yr(cf)
        assert result["value"] is None
        assert result["flag"] == FLAG_INSUFFICIENT

    def test_empty_dataframe(self):
        result = compute_fcf_cagr_5yr(make_cf([]))
        assert result["value"] is None
        assert result["flag"] == FLAG_INSUFFICIENT

    def test_zero_starting_fcf(self):
        cf = _fcf_series([0.0, 100.0, 110.0, 120.0, 130.0, 140.0])
        result = compute_fcf_cagr_5yr(cf)
        assert result["value"] is None
        assert result["flag"] == FLAG_ZERO_BASE

    def test_negative_to_positive_turnaround(self):
        cf = _fcf_series([-100.0, -50.0, 0.0, 50.0, 100.0, 200.0])
        result = compute_fcf_cagr_5yr(cf)
        assert result["value"] is None
        assert result["flag"] == FLAG_TURNAROUND

    def test_positive_to_negative_decline_to_loss(self):
        cf = _fcf_series([100.0, 80.0, 60.0, 40.0, 20.0, -10.0])
        result = compute_fcf_cagr_5yr(cf)
        assert result["value"] is None
        assert result["flag"] == FLAG_DECLINE_TO_LOSS

    def test_both_negative(self):
        cf = _fcf_series([-200.0, -180.0, -160.0, -140.0, -120.0, -100.0])
        result = compute_fcf_cagr_5yr(cf)
        assert result["value"] is None
        assert result["flag"] == FLAG_BOTH_NEGATIVE

    def test_missing_inputs_skipped(self):
        # One year with a missing OCF is skipped rather than treated as zero.
        cf = make_cf(
            [
                ("Mar 2019", 200, -100, 0),
                ("Mar 2020", np.nan, -100, 0),
                ("Mar 2021", 220, -100, 0),
                ("Mar 2022", 230, -100, 0),
                ("Mar 2023", 240, -100, 0),
                ("Mar 2024", 250, -100, 0),
            ]
        )
        result = compute_fcf_cagr_5yr(cf)
        assert result["value"] is not None
        assert result["flag"] is FLAG_NORMAL
        assert result["years_used"] == 5


# =============================================================================
# FCF CONVERSION
# =============================================================================


class TestFCFConversion:
    """FCF Conversion = FCF / PAT * 100 for the latest year."""

    def test_normal(self):
        cf = make_cf([("Mar 2024", 1000.0, -300.0, 0)])
        pl = make_pl([("Mar 2024", 5000, 200)])
        result = compute_fcf_conversion(cf, pl)
        # FCF = 700, PAT = 200 -> 350%
        assert result["value"] == 350.0
        assert result["flag"] is None

    def test_positive_fcf_negative_pat(self):
        cf = make_cf([("Mar 2024", 1000.0, -300.0, 0)])
        pl = make_pl([("Mar 2024", 5000, -200)])
        result = compute_fcf_conversion(cf, pl)
        assert result["value"] == -350.0

    def test_zero_pat_returns_none(self):
        cf = make_cf([("Mar 2024", 1000.0, -300.0, 0)])
        pl = make_pl([("Mar 2024", 5000, 0)])
        result = compute_fcf_conversion(cf, pl)
        assert result["value"] is None
        assert result["flag"] == "ZERO_PAT"

    def test_missing_pat_returns_none(self):
        cf = make_cf([("Mar 2024", 1000.0, -300.0, 0)])
        pl = make_pl([("Mar 2024", 5000, np.nan)])
        result = compute_fcf_conversion(cf, pl)
        assert result["value"] is None
        assert result["flag"] == "INSUFFICIENT_PAT"

    def test_not_fcf_over_sales(self):
        # Must be FCF/PAT, not FCF/Sales and not OCF/PAT.
        cf = make_cf([("Mar 2024", 1000.0, -300.0, 0)])  # FCF = 700
        pl = make_pl([("Mar 2024", 5000, 200)])  # FCF/PAT = 350%; FCF/Sales = 14%
        result = compute_fcf_conversion(cf, pl)
        assert result["value"] == 350.0


# =============================================================================
# DISTRESS SIGNAL
# =============================================================================


class TestDistressSignal:
    """Distress = latest-year CFO < 0 AND CFF > 0."""

    def test_distress_true(self):
        cf = make_cf(
            [
                ("Mar 2023", 500, -100, -200),
                ("Mar 2024", -100, -50, 300),
            ]
        )
        result = compute_distress_flag(cf)
        assert result["flag"] is True
        assert result["cfo"] == -100.0
        assert result["cff"] == 300.0

    def test_cfo_positive_not_distress(self):
        cf = make_cf([("Mar 2024", 500, -100, 300)])
        result = compute_distress_flag(cf)
        assert result["flag"] is False

    def test_cff_negative_not_distress(self):
        cf = make_cf([("Mar 2024", -100, -50, -300)])
        result = compute_distress_flag(cf)
        assert result["flag"] is False

    def test_missing_cfo_not_distress(self):
        cf = make_cf([("Mar 2024", np.nan, -50, 300)])
        result = compute_distress_flag(cf)
        assert result["flag"] is False

    def test_empty_not_distress(self):
        result = compute_distress_flag(make_cf([]))
        assert result["flag"] is False


# =============================================================================
# DELEVERAGING
# =============================================================================


class TestDeleveraging:
    """Deleveraging = latest CFF < 0 AND borrowings declining year-over-year."""

    def test_deleveraging_true(self):
        cf = make_cf(
            [
                ("Mar 2023", 500, -100, -100),
                ("Mar 2024", 400, -100, -300),
            ]
        )
        bs = make_bs(
            [
                ("Mar 2023", 1000),
                ("Mar 2024", 800),
            ]
        )
        result = compute_deleveraging_flag(cf, bs)
        assert result["flag"] is True
        assert result["borrowings_change"] == -200.0

    def test_borrowings_rising_not_deleveraging(self):
        cf = make_cf(
            [
                ("Mar 2023", 500, -100, -100),
                ("Mar 2024", 400, -100, -300),
            ]
        )
        bs = make_bs(
            [
                ("Mar 2023", 800),
                ("Mar 2024", 1000),
            ]
        )
        result = compute_deleveraging_flag(cf, bs)
        assert result["flag"] is False

    def test_positive_cff_not_deleveraging(self):
        cf = make_cf(
            [
                ("Mar 2023", 500, -100, -100),
                ("Mar 2024", 400, -100, 300),
            ]
        )
        bs = make_bs(
            [
                ("Mar 2023", 1000),
                ("Mar 2024", 800),
            ]
        )
        result = compute_deleveraging_flag(cf, bs)
        assert result["flag"] is False

    def test_missing_borrowings_not_treated_as_zero(self):
        cf = make_cf(
            [
                ("Mar 2023", 500, -100, -100),
                ("Mar 2024", 400, -100, -300),
            ]
        )
        bs = make_bs(
            [
                ("Mar 2023", np.nan),
                ("Mar 2024", np.nan),
            ]
        )
        result = compute_deleveraging_flag(cf, bs)
        assert result["flag"] is False

    def test_insufficient_balance_sheet_history(self):
        cf = make_cf([("Mar 2024", 400, -100, -300)])
        bs = make_bs([("Mar 2024", 800)])
        result = compute_deleveraging_flag(cf, bs)
        assert result["flag"] is False


# =============================================================================
# CAPITAL ALLOCATION
# =============================================================================


class TestCapitalAllocation:
    """Capital allocation label reuses the existing classification engine."""

    VALID = {"EXCELLENT", "GOOD", "MODERATE", "WEAK", "DISTRESSED", "Insufficient Data"}

    def test_excellent_case(self):
        cf = make_cf([("Mar 2024", 1000.0, -100.0, 0)])
        pl = make_pl([("Mar 2024", 5000, 200)])
        label = compute_capital_allocation_label(cf, pl)
        assert label in self.VALID

    def test_negative_fcf_is_distressed(self):
        cf = make_cf([("Mar 2024", -100.0, -100.0, 300)])
        pl = make_pl([("Mar 2024", 5000, 200)])
        label = compute_capital_allocation_label(cf, pl)
        assert label == "DISTRESSED"

    def test_missing_data_insufficient(self):
        label = compute_capital_allocation_label(make_cf([]), make_pl([]))
        assert label == "Insufficient Data"


# =============================================================================
# OUTPUT GENERATION & SCHEMA
# =============================================================================


def sample_results_df():
    """A small synthetic results DataFrame with the module3 result schema."""
    return pd.DataFrame(
        [
            {
                "company_id": "COMP1",
                "company_name": "Company One",
                "sector": "IT Services",
                "cfo_quality_score": 1.5,
                "cfo_quality_label": "High Quality",
                "capex_intensity_pct": 4.0,
                "capex_label": "Moderate",
                "fcf_cagr_5yr": 12.5,
                "fcf_conversion_pct": 80.0,
                "distress_flag": True,
                "deleveraging_flag": False,
                "capital_allocation_label": "GOOD",
                "_cfo_value": -100.0,
                "_cff_value": 500.0,
                "_net_profit_latest": 200.0,
            },
            {
                "company_id": "COMP2",
                "company_name": "Company Two",
                "sector": "Banks",
                "cfo_quality_score": 0.8,
                "cfo_quality_label": "Moderate",
                "capex_intensity_pct": 10.0,
                "capex_label": "Capital Intensive",
                "fcf_cagr_5yr": None,
                "fcf_conversion_pct": None,
                "distress_flag": False,
                "deleveraging_flag": True,
                "capital_allocation_label": "WEAK",
                "_cfo_value": 100.0,
                "_cff_value": -200.0,
                "_net_profit_latest": 150.0,
            },
            {
                "company_id": "COMP3",
                "company_name": "Company Three",
                "sector": None,
                "cfo_quality_score": None,
                "cfo_quality_label": "Insufficient Data",
                "capex_intensity_pct": None,
                "capex_label": "Insufficient Data",
                "fcf_cagr_5yr": None,
                "fcf_conversion_pct": None,
                "distress_flag": False,
                "deleveraging_flag": False,
                "capital_allocation_label": "Insufficient Data",
                "_cfo_value": None,
                "_cff_value": None,
                "_net_profit_latest": None,
            },
        ]
    )


class TestOutputSchema:
    """Excel/CSV output column schema."""

    def test_output_columns_match_spec(self):
        assert OUTPUT_COLUMNS == [
            "company_id",
            "sector",
            "cfo_quality_score",
            "cfo_quality_label",
            "capex_intensity_pct",
            "capex_label",
            "fcf_cagr_5yr",
            "fcf_conversion_pct",
            "distress_flag",
            "deleveraging_flag",
            "capital_allocation_label",
        ]

    def test_distress_csv_columns_match_spec(self):
        assert DISTRESS_CSV_COLUMNS == [
            "company_id",
            "sector",
            "CFO",
            "CFF",
            "latest_net_profit",
        ]

    def test_build_output_dataframe(self):
        out = build_output_dataframe(sample_results_df())
        assert out.columns.tolist() == OUTPUT_COLUMNS
        assert len(out) == 3

    def test_build_distress_dataframe(self):
        distress = build_distress_dataframe(sample_results_df())
        assert distress.columns.tolist() == DISTRESS_CSV_COLUMNS
        assert len(distress) == 1
        assert distress.iloc[0]["company_id"] == "COMP1"
        assert distress.iloc[0]["CFO"] == -100.0
        assert distress.iloc[0]["CFF"] == 500.0


class TestOutputGeneration:
    """End-to-end output generation into a pytest tmp directory."""

    def test_write_outputs_creates_directory_and_files(self, tmp_path):
        out_dir = tmp_path / "nested" / "output"
        paths = write_outputs(sample_results_df(), output_dir=out_dir)

        assert paths["excel"].exists()
        assert paths["csv"].exists()
        assert paths["excel"].stat().st_size > 0

    def test_written_excel_readable_with_expected_schema(self, tmp_path):
        paths = write_outputs(sample_results_df(), output_dir=tmp_path)

        df = pd.read_excel(paths["excel"])
        assert df.columns.tolist() == OUTPUT_COLUMNS
        assert len(df) == 3
        assert df["company_id"].is_unique

    def test_written_csv_contains_only_distress(self, tmp_path):
        paths = write_outputs(sample_results_df(), output_dir=tmp_path)

        df = pd.read_csv(paths["csv"])
        assert df.columns.tolist() == DISTRESS_CSV_COLUMNS
        assert len(df) == 1
        assert bool((df["CFO"] < 0).all())
        assert bool((df["CFF"] > 0).all())

    def test_validate_output_files(self, tmp_path):
        paths = write_outputs(sample_results_df(), output_dir=tmp_path)
        report = validate_output_files(paths["excel"], paths["csv"])

        assert report["excel_exists"] is True
        assert report["excel_readable"] is True
        assert report["excel_rows"] == 3
        assert report["duplicate_rows"] == 0
        assert report["missing_columns"] == []
        assert report["csv_readable"] is True
        assert report["csv_rows"] == 1
        assert report["csv_missing_columns"] == []


class TestModule3Pipeline:
    """Integration tests against the canonical project database."""

    @pytest.mark.skipif(
        not Path("data/database/n100.db").exists(),
        reason="Canonical database not present",
    )
    def test_process_all_companies_covers_every_company(self):
        import sqlite3

        conn = sqlite3.connect("data/database/n100.db")
        try:
            expected = pd.read_sql_query(
                "SELECT company_id FROM companies ORDER BY company_id", conn
            )["company_id"].tolist()
        finally:
            conn.close()

        results = process_all_companies()
        assert len(results) == len(expected)
        assert set(results["company_id"]) == set(expected)
        assert results["company_id"].is_unique
