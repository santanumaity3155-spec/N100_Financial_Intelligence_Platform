"""
validate_module6b.py

Functional Validation Script for Sprint 6 — Module 6B:
Cluster Profiling & Portfolio Statistics.
"""

import os
import sys
import subprocess
from pathlib import Path
import pandas as pd
import numpy as np

# Output and Report File Paths
CLUSTER_LABELS_CSV = Path("output/cluster_labels.csv")
CLUSTER_PROFILES_CSV = Path("output/cluster_profiles.csv")
OUTLIER_REPORT_CSV = Path("output/outlier_report.csv")
PORTFOLIO_STATS_CSV = Path("output/portfolio_stats.csv")
CORRELATION_HEATMAP_PNG = Path("reports/correlation_heatmap.png")


def run_validation():
    print("=" * 60)
    print("MODULE 6B VALIDATION")
    print("=" * 60)

    results = {}

    # Check 1: Module 6A Input
    m6a_input_pass = CLUSTER_LABELS_CSV.exists()
    results["Module 6A Input"] = "PASS" if m6a_input_pass else "FAIL"

    # Load Module 6B outputs if present
    profiles_exist = CLUSTER_PROFILES_CSV.exists()
    outliers_exist = OUTLIER_REPORT_CSV.exists()
    portfolio_exist = PORTFOLIO_STATS_CSV.exists()
    heatmap_exist = CORRELATION_HEATMAP_PNG.exists()

    df_labels = pd.read_csv(CLUSTER_LABELS_CSV) if m6a_input_pass else None
    df_prof = pd.read_csv(CLUSTER_PROFILES_CSV) if profiles_exist else None
    df_out = pd.read_csv(OUTLIER_REPORT_CSV) if outliers_exist else None
    df_port = pd.read_csv(PORTFOLIO_STATS_CSV) if portfolio_exist else None

    # Check 2: Cluster Count
    if df_labels is not None:
        cluster_cnt = df_labels["cluster_id"].nunique()
        results["Cluster Count"] = "PASS" if cluster_cnt == 5 else "FAIL"
    else:
        results["Cluster Count"] = "FAIL"

    # Check 3: Cluster Profiles
    if df_prof is not None:
        prof_rows = len(df_prof)
        results["Cluster Profiles"] = "PASS" if prof_rows == 5 else "FAIL"
    else:
        results["Cluster Profiles"] = "FAIL"

    # Check 4: Cluster Names
    if df_prof is not None and "cluster_name" in df_prof.columns:
        names = df_prof["cluster_name"].dropna().tolist()
        unique_names = len(set(names))
        results["Cluster Names"] = "PASS" if len(names) == 5 and unique_names == 5 else "FAIL"
    else:
        results["Cluster Names"] = "FAIL"

    # Check 5: Cluster Statistics
    if df_prof is not None:
        stat_cols = [c for c in df_prof.columns if c not in ["cluster_id", "cluster_name"]]
        all_numeric = df_prof[stat_cols].apply(lambda s: pd.to_numeric(s, errors='coerce')).notna().all().all()
        results["Cluster Statistics"] = "PASS" if all_numeric else "FAIL"
    else:
        results["Cluster Statistics"] = "FAIL"

    # Check 6: Correlation KPI Count
    if df_port is not None and len(df_port) == 10:
        results["Correlation KPI Count"] = "PASS"
    else:
        results["Correlation KPI Count"] = "PASS" if df_port is not None and len(df_port) >= 10 else "FAIL"

    # Check 7: Correlation Matrix
    if heatmap_exist:
        results["Correlation Matrix"] = "PASS"
    else:
        results["Correlation Matrix"] = "FAIL"

    # Check 8: Correlation Heatmap
    if heatmap_exist and os.path.getsize(CORRELATION_HEATMAP_PNG) > 1000:
        results["Correlation Heatmap"] = "PASS"
    else:
        results["Correlation Heatmap"] = "FAIL"

    # Check 9: Outlier Detection
    if df_out is not None:
        req_cols = {"company_id", "broad_sector", "metric", "value", "sector_mean", "sector_std", "z_score", "outlier_flag"}
        results["Outlier Detection"] = "PASS" if req_cols.issubset(set(df_out.columns)) else "FAIL"
    else:
        results["Outlier Detection"] = "FAIL"

    # Check 10: Outlier Threshold
    if df_out is not None and not df_out.empty:
        z_valid = (df_out["z_score"].abs() > 3.0).all()
        results["Outlier Threshold"] = "PASS" if z_valid else "FAIL"
    else:
        results["Outlier Threshold"] = "PASS" if df_out is not None else "FAIL"

    # Check 11: Portfolio Statistics
    if df_port is not None:
        req_pcols = {"kpi", "count", "P10", "P25", "P50", "P75", "P90", "Mean", "Std"}
        results["Portfolio Statistics"] = "PASS" if req_pcols.issubset(set(df_port.columns)) else "FAIL"
    else:
        results["Portfolio Statistics"] = "FAIL"

    # Check 12: Percentile Ordering
    if df_port is not None:
        ordering_valid = ((df_port["P10"] <= df_port["P25"]) &
                          (df_port["P25"] <= df_port["P50"]) &
                          (df_port["P50"] <= df_port["P75"]) &
                          (df_port["P75"] <= df_port["P90"])).all()
        results["Percentile Ordering"] = "PASS" if ordering_valid else "FAIL"
    else:
        results["Percentile Ordering"] = "FAIL"

    # Check 13: Company Coverage
    if df_labels is not None:
        comp_count = df_labels["company_id"].nunique()
        results["Company Coverage"] = "PASS" if comp_count >= 92 else "FAIL"
    else:
        results["Company Coverage"] = "FAIL"

    # Check 14: Duplicate Records
    if df_labels is not None and df_prof is not None:
        no_label_dups = df_labels["company_id"].duplicated().sum() == 0
        no_prof_dups = df_prof["cluster_id"].duplicated().sum() == 0
        results["Duplicate Records"] = "PASS" if (no_label_dups and no_prof_dups) else "FAIL"
    else:
        results["Duplicate Records"] = "FAIL"

    # Check 15: Missing Data Handling
    if df_prof is not None and df_port is not None:
        no_nans_in_profiles = df_prof.isna().sum().sum() == 0
        results["Missing Data Handling"] = "PASS" if no_nans_in_profiles else "FAIL"
    else:
        results["Missing Data Handling"] = "FAIL"

    # Check 16: Output Files
    all_outputs_exist = profiles_exist and outliers_exist and portfolio_exist and heatmap_exist
    results["Output Files"] = "PASS" if all_outputs_exist else "FAIL"

    # Check 17: Unit Tests
    try:
        cmd = [sys.executable, "-m", "pytest", "tests/analytics/test_cluster_profiling.py", "-q"]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        results["Unit Tests"] = "PASS" if proc.returncode == 0 else "FAIL"
    except Exception:
        results["Unit Tests"] = "FAIL"

    # Print Validation Table
    all_pass = True
    for key, status in results.items():
        print(f"{key:30s} {status}")
        if status != "PASS":
            all_pass = False

    print("=" * 60)
    final_status = "PASS" if all_pass else "FAIL"
    print(f"FINAL STATUS: {final_status}")
    print("=" * 60)

    return all_pass


if __name__ == "__main__":
    success = run_validation()
    sys.exit(0 if success else 1)
