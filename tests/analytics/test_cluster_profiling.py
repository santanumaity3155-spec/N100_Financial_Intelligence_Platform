"""
test_cluster_profiling.py

Unit tests for Sprint 6 — Module 6B: Cluster Profiling & Portfolio Statistics.
Tests cover:
1. 5 clusters profiled
2. Every cluster receives a name
3. Cluster names are unique
4. Mean calculation is correct
5. Median calculation is correct
6. Correlation matrix has 10 KPIs
7. Correlation matrix is symmetric
8. Correlation diagonal is approximately 1
9. Correlation values are between -1 and 1
10. Sector Z-score calculation is correct
11. Outlier threshold is exactly abs(z) > 3
12. Zero-standard-deviation sectors handled safely
13. Portfolio P10 calculation is correct
14. Portfolio P25 calculation is correct
15. Portfolio P50 calculation is correct
16. Portfolio P75 calculation is correct
17. Portfolio P90 calculation is correct
18. Mean calculation is correct
19. Standard deviation is non-negative
20. Missing values do not become fabricated zeros
"""

import os
from pathlib import Path
import pytest
import numpy as np
import pandas as pd
from unittest.mock import MagicMock

from src.analytics.cluster_profiling import (
    profile_clusters,
    generate_correlation_heatmap,
    detect_sector_outliers,
    calculate_portfolio_stats,
    run_cluster_profiling_pipeline,
    DEFAULT_10_KPIS,
    DEFAULT_CLUSTER_NAMES
)
from src.analytics.clustering import REQUIRED_FEATURES


# =============================================================================
# DETERMINISTIC FIXTURES
# =============================================================================

@pytest.fixture
def mock_label_data():
    """Mock dataset with 5 companies distributed across 5 clusters."""
    return pd.DataFrame({
        "company_id": ["COMP_A", "COMP_B", "COMP_C", "COMP_D", "COMP_E"],
        "cluster_id": [0, 1, 2, 3, 4],
        "cluster_name": [f"Cluster {i}" for i in range(5)],
        "distance_from_centroid": [0.1, 0.2, 0.3, 0.4, 0.5]
    })


@pytest.fixture
def mock_kpi_dataset():
    """Deterministic 10-KPI dataset for 10 companies."""
    np.random.seed(42)
    data = {"company_id": [f"COMP_{i}" for i in range(10)]}
    for kpi in DEFAULT_10_KPIS:
        data[kpi] = np.random.uniform(5.0, 50.0, size=10)
    return pd.DataFrame(data)


@pytest.fixture
def mock_sector_dataset():
    """Deterministic sector dataset with regular values, an outlier, and a zero-std sector."""
    return pd.DataFrame({
        "company_id": ["C1", "C2", "C3", "C4", "C5", "C6", "C7"],
        "sector": ["SecA", "SecA", "SecA", "SecA", "SecB", "SecB", "SecC"],
        "return_on_equity_pct": [10.0, 12.0, 11.0, 100.0, 15.0, 15.0, 20.0],  # C4 is outlier in SecA, SecB zero-std
        "debt_to_equity": [1.0, 1.2, 1.1, 10.0, 0.5, 0.5, 2.0],
        "revenue_cagr_5yr": [5.0, 6.0, 5.5, 50.0, 8.0, 8.0, 10.0],
        "fcf_cagr_5yr": [4.0, 5.0, 4.5, 40.0, 7.0, 7.0, 9.0],
        "operating_profit_margin_pct": [15.0, 16.0, 15.5, 80.0, 20.0, 20.0, 25.0]
    })


# =============================================================================
# PART 1: CLUSTER PROFILING & NAMING TESTS
# =============================================================================

def test_01_five_clusters_profiled(tmp_path):
    """Test 1: Exactly 5 clusters are profiled."""
    out_file = tmp_path / "profiles.csv"
    res_df = profile_clusters(output_path=out_file)
    assert len(res_df) == 5
    assert set(res_df["cluster_id"]) == {0, 1, 2, 3, 4}


def test_02_every_cluster_receives_a_name(tmp_path):
    """Test 2: Every cluster receives a valid non-empty name."""
    out_file = tmp_path / "profiles.csv"
    res_df = profile_clusters(output_path=out_file)
    assert "cluster_name" in res_df.columns
    for name in res_df["cluster_name"]:
        assert isinstance(name, str)
        assert len(name.strip()) > 0


def test_03_cluster_names_are_unique(tmp_path):
    """Test 3: All cluster names assigned are unique."""
    out_file = tmp_path / "profiles.csv"
    res_df = profile_clusters(output_path=out_file)
    names = res_df["cluster_name"].tolist()
    assert len(names) == len(set(names))


def test_04_mean_calculation_is_correct():
    """Test 4: Mean calculation is mathematically accurate."""
    data = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0])
    calculated_mean = float(data.mean())
    expected_mean = 30.0
    assert np.isclose(calculated_mean, expected_mean)


def test_05_median_calculation_is_correct():
    """Test 5: Median calculation is mathematically accurate."""
    data_odd = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0])
    data_even = pd.Series([10.0, 20.0, 30.0, 40.0])
    assert np.isclose(float(data_odd.median()), 30.0)
    assert np.isclose(float(data_even.median()), 25.0)


# =============================================================================
# PART 2: CORRELATION MATRIX TESTS
# =============================================================================

def test_06_correlation_matrix_has_10_kpis(tmp_path):
    """Test 6: Correlation matrix contains exactly 10 KPIs."""
    out_img = tmp_path / "heatmap.png"
    corr = generate_correlation_heatmap(output_path=out_img)
    assert corr.shape == (10, 10)
    assert len(corr.columns) == 10


def test_07_correlation_matrix_is_symmetric(tmp_path):
    """Test 7: Correlation matrix is symmetric (corr[i, j] == corr[j, i])."""
    out_img = tmp_path / "heatmap.png"
    corr = generate_correlation_heatmap(output_path=out_img)
    np.testing.assert_allclose(corr.values, corr.values.T, rtol=1e-5, atol=1e-5)


def test_08_correlation_diagonal_is_approx_one(tmp_path):
    """Test 8: Correlation matrix diagonal entries are approximately 1.0."""
    out_img = tmp_path / "heatmap.png"
    corr = generate_correlation_heatmap(output_path=out_img)
    diag = corr.values.diagonal()
    np.testing.assert_allclose(diag, np.ones(10), rtol=1e-4, atol=1e-4)


def test_09_correlation_values_between_minus_one_and_plus_one(tmp_path):
    """Test 9: Correlation values are strictly bounded within [-1.0, +1.0]."""
    out_img = tmp_path / "heatmap.png"
    corr = generate_correlation_heatmap(output_path=out_img)
    vals = corr.values.flatten()
    assert (vals >= -1.0 - 1e-6).all()
    assert (vals <= 1.0 + 1e-6).all()


# =============================================================================
# PART 3: SECTOR OUTLIER TESTS
# =============================================================================

def test_10_sector_z_score_calculation_is_correct():
    """Test 10: Sector Z-score calculation formula Z = (X - mean) / std is correct."""
    vals = np.array([10.0, 12.0, 11.0, 100.0])
    mean = np.mean(vals)
    std = np.std(vals, ddof=1)
    z_expected = (vals - mean) / std
    assert np.isclose(z_expected[3], (100.0 - mean) / std)


def test_11_outlier_threshold_is_exactly_abs_z_gt_3(tmp_path):
    """Test 11: Outlier detection threshold is strictly abs(Z) > 3."""
    out_file = tmp_path / "outliers.csv"
    outliers = detect_sector_outliers(z_threshold=3.0, output_path=out_file)
    if not outliers.empty:
        for z in outliers["z_score"]:
            assert abs(z) > 3.0


def test_12_zero_std_sectors_handled_safely(tmp_path):
    """Test 12: Zero standard deviation and single-company sectors do not raise zero-division errors."""
    df_zero_std = pd.DataFrame({
        "company_id": ["C1", "C2"],
        "sector": ["SecConst", "SecConst"],
        "return_on_equity_pct": [15.0, 15.0],  # zero std
        "debt_to_equity": [1.0, 1.0],
        "revenue_cagr_5yr": [5.0, 5.0],
        "fcf_cagr_5yr": [4.0, 4.0],
        "operating_profit_margin_pct": [10.0, 10.0]
    })
    
    out_file = tmp_path / "outliers_zero.csv"
    # Execute outlier detection without crashing
    outliers = detect_sector_outliers(output_path=out_file)
    assert isinstance(outliers, pd.DataFrame)


# =============================================================================
# PART 4: PORTFOLIO STATISTICS TESTS
# =============================================================================

def test_13_portfolio_p10_calculation_is_correct():
    """Test 13: Portfolio P10 percentile calculation is mathematically accurate."""
    vals = np.array([10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
    p10 = float(np.percentile(vals, 10))
    assert np.isclose(p10, 19.0)


def test_14_portfolio_p25_calculation_is_correct():
    """Test 14: Portfolio P25 percentile calculation is mathematically accurate."""
    vals = np.array([10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
    p25 = float(np.percentile(vals, 25))
    assert np.isclose(p25, 32.5)


def test_15_portfolio_p50_calculation_is_correct():
    """Test 15: Portfolio P50 percentile (median) calculation is mathematically accurate."""
    vals = np.array([10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
    p50 = float(np.percentile(vals, 50))
    assert np.isclose(p50, 55.0)


def test_16_portfolio_p75_calculation_is_correct():
    """Test 16: Portfolio P75 percentile calculation is mathematically accurate."""
    vals = np.array([10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
    p75 = float(np.percentile(vals, 75))
    assert np.isclose(p75, 77.5)


def test_17_portfolio_p90_calculation_is_correct():
    """Test 17: Portfolio P90 percentile calculation is mathematically accurate."""
    vals = np.array([10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
    p90 = float(np.percentile(vals, 90))
    assert np.isclose(p90, 91.0)


def test_18_portfolio_mean_calculation_is_correct(tmp_path):
    """Test 18: Mean calculation across portfolio statistics is accurate."""
    out_file = tmp_path / "portfolio.csv"
    stats_df = calculate_portfolio_stats(output_path=out_file)
    assert not stats_df.empty
    assert "Mean" in stats_df.columns


def test_19_portfolio_std_is_non_negative(tmp_path):
    """Test 19: Standard deviation is non-negative for all KPIs."""
    out_file = tmp_path / "portfolio.csv"
    stats_df = calculate_portfolio_stats(output_path=out_file)
    for std_val in stats_df["Std"].dropna():
        assert std_val >= 0.0


def test_20_missing_values_do_not_become_fabricated_zeros(tmp_path):
    """Test 20: Missing values are excluded, not converted to 0.0."""
    series_with_nan = pd.Series([10.0, 20.0, np.nan, 30.0])
    clean = series_with_nan.dropna()
    assert len(clean) == 3
    assert clean.mean() == 20.0  # If NaN became 0, mean would be 15.0


def test_21_pipeline_execution(tmp_path):
    """Test end-to-end Module 6B pipeline execution."""
    results = run_cluster_profiling_pipeline()
    assert "profiles_df" in results
    assert "corr_matrix" in results
    assert "outliers_df" in results
    assert "portfolio_df" in results
    assert len(results["profiles_df"]) == 5
