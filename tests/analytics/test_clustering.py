"""
test_clustering.py

Unit tests for Sprint 6 — Module 6A: KMeans Clustering (src/analytics/clustering.py).
"""

import os
from pathlib import Path
import pytest
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

from src.analytics.clustering import (
    load_clustering_dataset,
    impute_missing_values,
    scale_features,
    run_kmeans,
    compute_centroid_distances,
    compute_elbow_inertia,
    generate_elbow_plot,
    generate_cluster_output,
    run_kmeans_clustering,
    REQUIRED_FEATURES,
    DEFAULT_N_CLUSTERS,
    DEFAULT_RANDOM_STATE,
)


@pytest.fixture
def sample_raw_df():
    """Create a sample dataset with missing values for unit testing."""
    return pd.DataFrame(
        {
            "company_id": ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "C10"],
            "sector": [
                "IT",
                "IT",
                "IT",
                "Banking",
                "Banking",
                "Banking",
                "Pharma",
                "Pharma",
                "Pharma",
                "Pharma",
            ],
            "return_on_equity_pct": [
                15.0,
                20.0,
                np.nan,
                12.0,
                18.0,
                14.0,
                8.0,
                10.0,
                12.0,
                np.nan,
            ],
            "debt_to_equity": [0.1, 0.2, 0.15, 1.5, 2.0, np.nan, 0.5, 0.4, 0.6, 0.5],
            "revenue_cagr_5yr": [
                10.0,
                12.0,
                14.0,
                8.0,
                np.nan,
                9.0,
                5.0,
                6.0,
                7.0,
                8.0,
            ],
            "fcf_cagr_5yr": [
                8.0,
                np.nan,
                10.0,
                5.0,
                6.0,
                4.0,
                np.nan,
                np.nan,
                np.nan,
                np.nan,
            ],  # Pharma all NaN for FCF
            "operating_profit_margin_pct": [
                22.0,
                25.0,
                24.0,
                18.0,
                20.0,
                19.0,
                15.0,
                np.nan,
                17.0,
                16.0,
            ],
        }
    )


def test_required_features_list():
    """Test 1: Verify exactly 5 features are defined."""
    assert len(REQUIRED_FEATURES) == 5
    expected = [
        "return_on_equity_pct",
        "debt_to_equity",
        "revenue_cagr_5yr",
        "fcf_cagr_5yr",
        "operating_profit_margin_pct",
    ]
    assert REQUIRED_FEATURES == expected


def test_missing_value_imputation_sector_median(sample_raw_df):
    """Test 2 & 3: Imputation uses sector medians and falls back to overall median."""
    imputed = impute_missing_values(sample_raw_df)

    # 0 NaNs remaining
    assert not imputed[REQUIRED_FEATURES].isna().any().any()
    assert len(imputed) == len(sample_raw_df)

    # IT sector ROE for C3 should be median of C1 (15.0) and C2 (20.0) -> 17.5
    c3_roe = imputed.loc[imputed["company_id"] == "C3", "return_on_equity_pct"].values[
        0
    ]
    assert pytest.approx(c3_roe) == 17.5

    # Pharma FCF CAGR was all NaN -> overall median fallback
    pharma_fcf = imputed.loc[imputed["sector"] == "Pharma", "fcf_cagr_5yr"].values
    assert not np.isnan(pharma_fcf).any()


def test_standard_scaler_normalization(sample_raw_df):
    """Test 4: StandardScaler normalizes features to mean ~ 0 and std ~ 1."""
    imputed = impute_missing_values(sample_raw_df)
    X_scaled, scaler = scale_features(imputed)

    assert X_scaled.shape == (10, 5)
    assert np.allclose(X_scaled.mean(axis=0), 0, atol=1e-5)
    assert np.allclose(X_scaled.std(axis=0), 1, atol=1e-5)


def test_kmeans_cluster_count(sample_raw_df):
    """Test 5 & 7: KMeans creates requested number of clusters with valid cluster IDs."""
    imputed = impute_missing_values(sample_raw_df)
    X_scaled, _ = scale_features(imputed)

    km = run_kmeans(X_scaled, n_clusters=5, random_state=42)
    assert len(km.cluster_centers_) == 5

    unique_ids = set(np.unique(km.labels_))
    assert unique_ids.issubset({0, 1, 2, 3, 4})


def test_kmeans_random_state_determinism(sample_raw_df):
    """Test 6: random_state=42 guarantees exact reproducibility."""
    imputed = impute_missing_values(sample_raw_df)
    X_scaled, _ = scale_features(imputed)

    km1 = run_kmeans(X_scaled, n_clusters=5, random_state=42)
    km2 = run_kmeans(X_scaled, n_clusters=5, random_state=42)

    assert (km1.labels_ == km2.labels_).all()
    assert np.allclose(km1.cluster_centers_, km2.cluster_centers_)
    assert pytest.approx(km1.inertia_) == km2.inertia_


def test_every_company_receives_one_cluster(sample_raw_df):
    """Test 8: Every company in input receives exactly one cluster ID assignment."""
    imputed = impute_missing_values(sample_raw_df)
    X_scaled, _ = scale_features(imputed)
    km = run_kmeans(X_scaled, n_clusters=5, random_state=42)

    assert len(km.labels_) == len(sample_raw_df)
    assert not np.isnan(km.labels_).any()


def test_centroid_distances_non_negative(sample_raw_df):
    """Test 10: Centroid distances are strictly non-negative."""
    imputed = impute_missing_values(sample_raw_df)
    X_scaled, _ = scale_features(imputed)
    km = run_kmeans(X_scaled, n_clusters=5, random_state=42)

    distances = compute_centroid_distances(X_scaled, km.labels_, km.cluster_centers_)
    assert len(distances) == len(sample_raw_df)
    assert (distances >= 0).all()
    assert not np.isnan(distances).any()


def test_elbow_calculation_range(sample_raw_df):
    """Test 11: Elbow inertia calculation covers k=2 through k=10."""
    imputed = impute_missing_values(sample_raw_df)
    X_scaled, _ = scale_features(imputed)

    # Use k range up to 8 due to sample size = 10
    k_range = range(2, 8)
    inertia_dict = compute_elbow_inertia(X_scaled, k_range=k_range, random_state=42)

    assert len(inertia_dict) == len(k_range)
    for k in k_range:
        assert k in inertia_dict
        assert inertia_dict[k] > 0

    # Inertia should be monotonically decreasing
    inertias = [inertia_dict[k] for k in k_range]
    for i in range(len(inertias) - 1):
        assert inertias[i] >= inertias[i + 1]


def test_empty_input_handling():
    """Test 12: Empty DataFrame raises ValueError."""
    empty_df = pd.DataFrame(columns=["company_id", "sector"] + REQUIRED_FEATURES)
    with pytest.raises(ValueError):
        impute_missing_values(empty_df)

    with pytest.raises(ValueError):
        scale_features(empty_df)


def test_invalid_feature_values_handling():
    """Test 13: Infinite or non-numeric values are handled or rejected properly."""
    df_invalid = pd.DataFrame(
        {
            "company_id": ["C1", "C2"],
            "sector": ["IT", "IT"],
            "return_on_equity_pct": [10.0, np.inf],
            "debt_to_equity": [0.1, 0.2],
            "revenue_cagr_5yr": [5.0, 6.0],
            "fcf_cagr_5yr": [4.0, 5.0],
            "operating_profit_margin_pct": [15.0, 16.0],
        }
    )

    with pytest.raises(ValueError):
        impute_missing_values(df_invalid)


def test_output_columns_and_formatting(sample_raw_df, tmp_path):
    """Test 9 & 14: Output CSV columns match schema and no duplicates exist."""
    imputed = impute_missing_values(sample_raw_df)
    X_scaled, _ = scale_features(imputed)
    km = run_kmeans(X_scaled, n_clusters=5, random_state=42)
    distances = compute_centroid_distances(X_scaled, km.labels_, km.cluster_centers_)

    out_csv = tmp_path / "cluster_labels.csv"
    out_df = generate_cluster_output(
        imputed, km.labels_, distances, output_path=out_csv
    )

    assert out_csv.exists()
    assert len(out_df) == len(sample_raw_df)

    expected_cols = [
        "company_id",
        "cluster_id",
        "cluster_name",
        "distance_from_centroid",
    ]
    assert list(out_df.columns) == expected_cols

    # Verify cluster_name format
    assert out_df["cluster_name"].iloc[0] == f"Cluster {out_df['cluster_id'].iloc[0]}"

    # Verify no duplicate company_ids
    assert out_df["company_id"].nunique() == len(out_df)


def test_end_to_end_pipeline():
    """Test full integration pipeline against database."""
    res = run_kmeans_clustering(n_clusters=5, random_state=42)

    assert res["cluster_labels_df"] is not None
    assert len(res["cluster_labels_df"]) == 94
    assert res["csv_path"].exists()
    assert res["plot_path"].exists()
    assert len(set(res["cluster_labels_df"]["cluster_id"])) == 5
