"""
test_module4b_distribution.py

Unit Test Suite for Module 4B — Latest-Year Capital Allocation Pattern Distribution
N100 Financial Intelligence Platform (Sprint 5)
"""

import tempfile
from pathlib import Path
import pandas as pd
import numpy as np
import pytest

from src.analytics.capital_allocation_distribution import (
    SUPPORTED_PATTERNS,
    RATING_TO_PATTERN_MAP,
    parse_year_from_period,
    determine_latest_year,
    map_rating_to_pattern,
    generate_distribution_summary,
    run_module4b_pipeline,
)


@pytest.fixture
def mock_financial_periods():
    cf_df = pd.DataFrame(
        {
            "company_id": ["C1", "C2", "C3"],
            "period": ["Mar 2022", "Mar 2023", "Mar 2024"],
        }
    )
    pl_df = pd.DataFrame(
        {
            "company_id": ["C1", "C2", "C3"],
            "period": ["Mar 2022", "Mar 2023", "Mar 2024"],
        }
    )
    return cf_df, pl_df


@pytest.fixture
def mock_classifications():
    return pd.DataFrame(
        {
            "company_id": ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "C10"],
            "company_name": [f"Company {i}" for i in range(1, 11)],
            "sector": ["Tech"] * 10,
            "latest_year": [2024] * 10,
            "capital_allocation_rating": [
                "EXCELLENT",
                "EXCELLENT",
                "GOOD",
                "GOOD",
                "GOOD",
                "MODERATE",
                "WEAK",
                "WEAK",
                "DISTRESSED",
                "DISTRESSED",
            ],
            "capital_allocation_pattern": [
                "Reinvestor",
                "Reinvestor",
                "Shareholder Returns",
                "Shareholder Returns",
                "Shareholder Returns",
                "Mixed",
                "Cash Accumulator",
                "Cash Accumulator",
                "Distress Signal",
                "Distress Signal",
            ],
        }
    )


def test_1_latest_year_detection(mock_financial_periods):
    """1. Test latest-year detection from period strings."""
    cf_df, pl_df = mock_financial_periods
    latest = determine_latest_year(cf_df, pl_df)
    assert latest == 2024, f"Expected 2024, got {latest}"

    assert parse_year_from_period("Mar 2025") == 2025
    assert parse_year_from_period("Dec-23") == 2023
    assert parse_year_from_period(None) is None


def test_2_distribution_calculation(mock_classifications):
    """2. Test distribution calculation company counts."""
    dist_df = generate_distribution_summary(2024, mock_classifications)
    assert not dist_df.empty

    counts = dict(zip(dist_df["pattern"], dist_df["company_count"]))
    assert counts["Reinvestor"] == 2
    assert counts["Shareholder Returns"] == 3
    assert counts["Mixed"] == 1
    assert counts["Cash Accumulator"] == 2
    assert counts["Distress Signal"] == 2


def test_3_percentage_calculation(mock_classifications):
    """3. Test percentage calculation logic."""
    dist_df = generate_distribution_summary(2024, mock_classifications)
    pcts = dict(zip(dist_df["pattern"], dist_df["percentage"]))

    assert pcts["Reinvestor"] == 20.0
    assert pcts["Shareholder Returns"] == 30.0
    assert pcts["Mixed"] == 10.0
    assert pcts["Cash Accumulator"] == 20.0
    assert pcts["Distress Signal"] == 20.0


def test_4_all_supported_patterns_appear(mock_classifications):
    """4. Test all 8 supported patterns appear in output."""
    dist_df = generate_distribution_summary(2024, mock_classifications)
    patterns = dist_df["pattern"].tolist()

    assert len(patterns) == 8
    for p in SUPPORTED_PATTERNS:
        assert p in patterns, f"Pattern {p} missing from distribution output"


def test_5_zero_count_patterns_appear(mock_classifications):
    """5. Test zero-count patterns appear with count=0 and percentage=0.0."""
    dist_df = generate_distribution_summary(2024, mock_classifications)

    zero_patterns = ["Liquidating Assets", "Growth Funded by Debt", "Pre-Revenue"]
    for p in zero_patterns:
        row = dist_df[dist_df["pattern"] == p]
        assert not row.empty
        assert row["company_count"].iloc[0] == 0
        assert row["percentage"].iloc[0] == 0.00


def test_6_distribution_count_total(mock_classifications):
    """6. Test distribution company count total equals input total."""
    dist_df = generate_distribution_summary(2024, mock_classifications)
    total_count = dist_df["company_count"].sum()

    assert total_count == len(mock_classifications)


def test_7_distribution_percentage_total(mock_classifications):
    """7. Test distribution percentage total equals ~100%."""
    dist_df = generate_distribution_summary(2024, mock_classifications)
    total_pct = dist_df["percentage"].sum()

    assert pytest.approx(total_pct, abs=0.1) == 100.0


def test_8_duplicate_pattern_detection(mock_classifications):
    """8. Test no duplicate pattern rows in output."""
    dist_df = generate_distribution_summary(2024, mock_classifications)
    patterns = dist_df["pattern"].tolist()

    assert len(patterns) == len(set(patterns)), "Duplicate pattern rows found!"


def test_9_invalid_pattern_detection():
    """9. Test invalid/unknown pattern or rating fallback mapping."""
    assert map_rating_to_pattern("EXCELLENT") == "Reinvestor"
    assert map_rating_to_pattern("UNKNOWN_RATING") == "Mixed"
    assert map_rating_to_pattern(None) == "Mixed"


def test_10_missing_data_handling():
    """10. Test handling empty data without crashing."""
    empty_df = pd.DataFrame(
        columns=[
            "company_id",
            "company_name",
            "sector",
            "latest_year",
            "capital_allocation_rating",
            "capital_allocation_pattern",
        ]
    )
    dist_df = generate_distribution_summary(2024, empty_df)

    assert len(dist_df) == 8
    assert (dist_df["company_count"] == 0).all()
    assert (dist_df["percentage"] == 0.0).all()


def test_11_output_csv_generation():
    """11. Test pipeline CSV output generation in a temporary directory."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        results = run_module4b_pipeline(output_dir=tmp_path)

        dist_csv = tmp_path / "capital_allocation_distribution.csv"
        latest_csv = tmp_path / "capital_allocation_latest_year.csv"

        assert dist_csv.exists()
        assert latest_csv.exists()

        df_dist = pd.read_csv(dist_csv)
        assert len(df_dist) == 8
        assert list(df_dist.columns) == [
            "latest_year",
            "pattern",
            "company_count",
            "percentage",
        ]
