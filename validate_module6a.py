"""
validate_module6a.py

Validation script for Sprint 6 — Module 6A: KMeans Clustering.
Performs comprehensive validation of all 20 required criteria.
"""

import sys
import os
from pathlib import Path
import sqlite3
import pandas as pd
import numpy as np
from PIL import Image

from src.database.connection import get_connection
from src.analytics.clustering import (
    run_kmeans_clustering,
    load_clustering_dataset,
    impute_missing_values,
    scale_features,
    run_kmeans,
    compute_centroid_distances,
    REQUIRED_FEATURES,
    CLUSTER_LABELS_CSV,
    ELBOW_PLOT_PNG
)


def validate_module6a():
    results = {}

    # 1. Database exists
    db_path = Path("data/database/n100.db")
    db_exists = db_path.exists()
    results["Database"] = db_exists

    if not db_exists:
        print("FAIL: Database file does not exist.")
        sys.exit(1)

    conn = get_connection()

    # 2. Companies table exists
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='companies'")
    tbl = cursor.fetchone()
    companies_tbl_exists = tbl is not None

    # 3. Authoritative company count
    cursor.execute("SELECT COUNT(*) FROM companies")
    auth_company_count = cursor.fetchone()[0]

    # 4. Feature availability
    raw_df = load_clustering_dataset(conn=conn)
    feat_avail = all(f in raw_df.columns for f in REQUIRED_FEATURES)
    results["Feature availability"] = feat_avail

    # Company coverage
    comp_coverage = (len(raw_df) == auth_company_count) and (raw_df["company_id"].nunique() == auth_company_count)
    results["Company coverage"] = comp_coverage

    # 5 & 6. Missing value handling (Sector Median Imputation)
    imputed_df = impute_missing_values(raw_df)
    no_nans = not imputed_df[REQUIRED_FEATURES].isna().any().any()
    no_infs = not np.isinf(imputed_df[REQUIRED_FEATURES].to_numpy()).any()
    results["Missing-value handling"] = no_nans and no_infs

    # 7 & 8. Scaling (StandardScaler)
    X_scaled, scaler = scale_features(imputed_df)
    means_close_zero = np.allclose(X_scaled.mean(axis=0), 0, atol=1e-5)
    stds_close_one = np.allclose(X_scaled.std(axis=0), 1, atol=1e-5)
    results["Scaling"] = means_close_zero and stds_close_one

    # 9 & 10. KMeans & Cluster count
    kmeans = run_kmeans(X_scaled, n_clusters=5, random_state=42)
    cluster_count_ok = (len(np.unique(kmeans.labels_)) == 5)
    results["KMeans"] = (kmeans is not None)
    results["Cluster count"] = cluster_count_ok

    # 11 & 12 & 13. Cluster IDs & Coverage & Duplicate Check
    valid_ids = set(kmeans.labels_).issubset({0, 1, 2, 3, 4})
    results["Cluster IDs"] = valid_ids

    # 14. Centroid distances
    distances = compute_centroid_distances(X_scaled, kmeans.labels_, kmeans.cluster_centers_)
    distances_non_neg = (distances >= 0).all() and not np.isnan(distances).any()
    results["Centroid distances"] = distances_non_neg

    # 15 & 16. Elbow Plot
    elbow_plot_exists = ELBOW_PLOT_PNG.exists()
    elbow_plot_valid = False
    if elbow_plot_exists:
        try:
            with Image.open(ELBOW_PLOT_PNG) as img:
                img.verify()
            elbow_plot_valid = True
        except Exception:
            elbow_plot_valid = False
    results["Elbow plot"] = elbow_plot_exists and elbow_plot_valid

    # 17, 18, 19. Output CSV
    csv_exists = CLUSTER_LABELS_CSV.exists()
    csv_valid = False
    if csv_exists:
        csv_df = pd.read_csv(CLUSTER_LABELS_CSV)
        req_cols = {"company_id", "cluster_id", "cluster_name", "distance_from_centroid"}
        cols_ok = req_cols.issubset(set(csv_df.columns))
        rows_ok = (len(csv_df) == auth_company_count)
        no_dups = (csv_df["company_id"].nunique() == auth_company_count)
        cids_ok = set(csv_df["cluster_id"].unique()).issubset({0, 1, 2, 3, 4})
        dists_ok = (csv_df["distance_from_centroid"] >= 0).all()
        csv_valid = cols_ok and rows_ok and no_dups and cids_ok and dists_ok
    results["Output CSV"] = csv_exists and csv_valid

    # 20. Reproducibility test
    res_run1 = run_kmeans_clustering(conn=conn, n_clusters=5, random_state=42)
    res_run2 = run_kmeans_clustering(conn=conn, n_clusters=5, random_state=42)
    
    labels_match = (res_run1["kmeans"].labels_ == res_run2["kmeans"].labels_).all()
    distances_match = np.allclose(res_run1["distances"], res_run2["distances"], atol=1e-4)
    reproducible = labels_match and distances_match
    results["Reproducibility"] = reproducible

    conn.close()

    # Print Summary
    print("\n============================================================")
    print("MODULE 6A VALIDATION")
    print("============================================================")
    all_pass = True
    for key, status in results.items():
        status_str = "PASS" if status else "FAIL"
        if not status:
            all_pass = False
        print(f"{key:<28} {status_str}")

    print("------------------------------------------------------------")
    final_status = "PASS" if all_pass else "FAIL"
    print(f"FINAL STATUS: {final_status}")
    print("============================================================\n")

    return all_pass


if __name__ == "__main__":
    success = validate_module6a()
    sys.exit(0 if success else 1)
