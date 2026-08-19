"""
cluster_profiling.py

Cluster Profiling & Portfolio Statistics Module for the N100 Financial Intelligence Platform.
Sprint 6 — Module 6B: Cluster Profiling & Statistics (Day 37)

This module performs:
1. Cluster profiling (Mean/Median of 5 features across 5 clusters with configurable financial names)
2. 10-KPI Pearson correlation matrix heatmap generation
3. Sector-based Z-score outlier detection (|Z| > 3)
4. Portfolio statistics (P10, P25, P50, P75, P90, Mean, Std across authoritative company universe)
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns

from src.config.logging_config import get_logger
from src.database.connection import get_connection
from src.analytics.clustering import (
    REQUIRED_FEATURES,
    load_clustering_dataset,
    impute_missing_values,
    CLUSTER_LABELS_CSV,
)
from src.reports.sector_report import SUB_SECTOR_TO_BROAD_SECTOR

logger = get_logger(__name__)

# =============================================================================
# CONSTANTS & PATHS
# =============================================================================

OUTPUT_DIR = Path("output")
REPORTS_DIR = Path("reports")

CLUSTER_PROFILES_CSV = OUTPUT_DIR / "cluster_profiles.csv"
OUTLIER_REPORT_CSV = OUTPUT_DIR / "outlier_report.csv"
PORTFOLIO_STATS_CSV = OUTPUT_DIR / "portfolio_stats.csv"
CORRELATION_HEATMAP_PNG = REPORTS_DIR / "correlation_heatmap.png"

# Default 10 KPIs for correlation matrix and portfolio statistics
DEFAULT_10_KPIS = [
    "roe",
    "roce",
    "roa",
    "net_profit_margin",
    "operating_margin",
    "ebit_margin",
    "debt_to_equity",
    "interest_coverage",
    "asset_turnover",
    "inventory_turnover",
]

# Human-readable labels for 10 KPIs
KPI_DISPLAY_NAMES = {
    "roe": "ROE (%)",
    "roce": "ROCE (%)",
    "roa": "ROA (%)",
    "net_profit_margin": "Net Profit Margin (%)",
    "operating_margin": "Operating Margin (%)",
    "ebit_margin": "EBIT Margin (%)",
    "debt_to_equity": "Debt to Equity",
    "interest_coverage": "Interest Coverage",
    "asset_turnover": "Asset Turnover",
    "inventory_turnover": "Inventory Turnover",
}

# Initial automatic / descriptive cluster naming based on empirical data
DEFAULT_CLUSTER_NAMES = {
    0: "Core Market Performers",
    1: "High Cash Flow Outlier",
    2: "Extreme ROE Outlier",
    3: "Banking Leverage Outlier",
    4: "Hyper Revenue Growth Outlier",
}


# =============================================================================
# PART 1 — CLUSTER PROFILING & DESCRIPTIVE NAMING
# =============================================================================


def profile_clusters(
    df_labels: Optional[pd.DataFrame] = None,
    conn: Any = None,
    custom_names: Optional[Dict[int, str]] = None,
    output_path: Path = CLUSTER_PROFILES_CSV,
) -> pd.DataFrame:
    """
    Profile all 5 KMeans clusters by calculating mean and median for the 5 clustering features.
    Assigns meaningful, configurable financial names to each cluster.

    Parameters
    ----------
    df_labels : Optional[pd.DataFrame]
        DataFrame with company_id and cluster_id (loaded from output/cluster_labels.csv if None).
    conn : Optional[sqlite3.Connection]
        Database connection.
    custom_names : Optional[Dict[int, str]]
        Optional user/team-lead specified mapping from cluster_id to cluster_name.
    output_path : Path
        Target CSV output path.

    Returns
    -------
    pd.DataFrame
        Cluster profile summary DataFrame (5 rows).
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if df_labels is None:
        if not CLUSTER_LABELS_CSV.exists():
            raise FileNotFoundError(
                f"Cluster labels file not found at {CLUSTER_LABELS_CSV}"
            )
        df_labels = pd.read_csv(CLUSTER_LABELS_CSV)

    # Load cleaned/imputed feature dataset from Module 6A
    raw_df = load_clustering_dataset(conn=conn)
    imputed_df = impute_missing_values(raw_df, features=REQUIRED_FEATURES)

    # Merge cluster_id onto feature dataset
    merged = imputed_df.merge(
        df_labels[["company_id", "cluster_id"]], on="company_id", how="inner"
    )

    # Name mapping resolution (custom names > default descriptive names)
    name_map = DEFAULT_CLUSTER_NAMES.copy()
    if custom_names:
        name_map.update(custom_names)

    profiles = []
    unique_cluster_ids = sorted(merged["cluster_id"].unique())

    for cid in range(5):
        c_data = merged[merged["cluster_id"] == cid]
        c_name = name_map.get(cid, f"Cluster {cid}")

        if c_data.empty:
            logger.warning(f"Cluster {cid} contains 0 companies.")
            row_dict = {
                "cluster_id": cid,
                "cluster_name": c_name,
                "roe_mean": np.nan,
                "roe_median": np.nan,
                "debt_to_equity_mean": np.nan,
                "debt_to_equity_median": np.nan,
                "revenue_cagr_5yr_mean": np.nan,
                "revenue_cagr_5yr_median": np.nan,
                "fcf_cagr_5yr_mean": np.nan,
                "fcf_cagr_5yr_median": np.nan,
                "opm_mean": np.nan,
                "opm_median": np.nan,
            }
        else:
            row_dict = {
                "cluster_id": cid,
                "cluster_name": c_name,
                "roe_mean": round(float(c_data["return_on_equity_pct"].mean()), 4),
                "roe_median": round(float(c_data["return_on_equity_pct"].median()), 4),
                "debt_to_equity_mean": round(float(c_data["debt_to_equity"].mean()), 4),
                "debt_to_equity_median": round(
                    float(c_data["debt_to_equity"].median()), 4
                ),
                "revenue_cagr_5yr_mean": round(
                    float(c_data["revenue_cagr_5yr"].mean()), 4
                ),
                "revenue_cagr_5yr_median": round(
                    float(c_data["revenue_cagr_5yr"].median()), 4
                ),
                "fcf_cagr_5yr_mean": round(float(c_data["fcf_cagr_5yr"].mean()), 4),
                "fcf_cagr_5yr_median": round(float(c_data["fcf_cagr_5yr"].median()), 4),
                "opm_mean": round(
                    float(c_data["operating_profit_margin_pct"].mean()), 4
                ),
                "opm_median": round(
                    float(c_data["operating_profit_margin_pct"].median()), 4
                ),
            }
        profiles.append(row_dict)

    profile_df = pd.DataFrame(profiles)
    profile_df.to_csv(output_path, index=False)
    logger.info(
        f"Saved cluster profiles to {output_path} ({len(profile_df)} clusters)."
    )
    return profile_df


# =============================================================================
# PART 3 — CORRELATION MATRIX & HEATMAP
# =============================================================================


def generate_correlation_heatmap(
    conn: Any = None,
    kpi_cols: List[str] = DEFAULT_10_KPIS,
    output_path: Path = CORRELATION_HEATMAP_PNG,
) -> pd.DataFrame:
    """
    Generate Pearson correlation matrix for exactly 10 KPIs across the latest year company data
    and render a Seaborn correlation heatmap.

    Parameters
    ----------
    conn : Optional[sqlite3.Connection]
        Active database connection.
    kpi_cols : List[str]
        List of 10 KPI column names.
    output_path : Path
        Target path for correlation heatmap PNG image.

    Returns
    -------
    pd.DataFrame
        10x10 Pearson correlation matrix DataFrame.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    try:
        # Load latest financial KPIs per company
        kpis_df = pd.read_sql_query("SELECT * FROM financial_kpis", conn)
        if kpis_df.empty:
            raise ValueError("financial_kpis table is empty.")

        # Take latest record per company_id based on id
        latest_kpis = (
            kpis_df.sort_values("id").groupby("company_id").last().reset_index()
        )

        # Validate that required 10 KPIs exist in columns
        missing_kpis = [k for k in kpi_cols if k not in latest_kpis.columns]
        if missing_kpis:
            raise KeyError(f"KPI columns missing from financial_kpis: {missing_kpis}")

        # Compute Pearson correlation matrix
        corr_matrix = latest_kpis[kpi_cols].corr(method="pearson")

        # Rerender labels for display
        display_labels = [KPI_DISPLAY_NAMES.get(k, k) for k in kpi_cols]
        corr_display = corr_matrix.copy()
        corr_display.columns = display_labels
        corr_display.index = display_labels

        # Create Seaborn Heatmap
        plt.figure(figsize=(10, 8), dpi=150)
        sns.heatmap(
            corr_display,
            annot=True,
            fmt=".2f",
            cmap="coolwarm",
            vmin=-1.0,
            vmax=1.0,
            center=0,
            square=True,
            linewidths=0.5,
            cbar_kws={"shrink": 0.8},
        )

        plt.title(
            "N100 10-KPI Pearson Correlation Heatmap (Latest Period)",
            fontsize=13,
            fontweight="bold",
            pad=12,
        )
        plt.xticks(rotation=45, ha="right", fontsize=9)
        plt.yticks(rotation=0, fontsize=9)
        plt.tight_layout()

        plt.savefig(output_path, dpi=150)
        plt.close()

        logger.info(f"Generated 10-KPI Pearson correlation heatmap to {output_path}")
        return corr_matrix

    finally:
        if close_conn and conn:
            conn.close()


# =============================================================================
# PART 4 — SECTOR-BASED OUTLIER DETECTION
# =============================================================================


def detect_sector_outliers(
    conn: Any = None,
    metrics: List[str] = REQUIRED_FEATURES,
    z_threshold: float = 3.0,
    output_path: Path = OUTLIER_REPORT_CSV,
) -> pd.DataFrame:
    """
    Perform Z-score outlier detection separately for each broad_sector.
    Z = (X - sector_mean) / sector_std.
    Flag company if abs(Z) > 3.0.

    Parameters
    ----------
    conn : Optional[sqlite3.Connection]
        Database connection.
    metrics : List[str]
        Metrics to evaluate for outlier detection.
    z_threshold : float
        Z-score absolute threshold for flagging outliers (default 3.0).
    output_path : Path
        Target path for outlier report CSV.

    Returns
    -------
    pd.DataFrame
        DataFrame of reported outliers.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load company feature dataset
    df_feat = load_clustering_dataset(conn=conn)

    # Map broad sector from sub_sector
    df_feat["broad_sector"] = (
        df_feat["sector"]
        .map(SUB_SECTOR_TO_BROAD_SECTOR)
        .fillna("Capital Goods & Engineering")
    )

    outliers = []

    for broad_sec, group in df_feat.groupby("broad_sector"):
        for m in metrics:
            if m not in group.columns:
                continue

            vals = group[m].dropna()
            if len(vals) <= 1:
                # 0 or 1 sample: standard deviation is undefined/0, skip without error
                continue

            sec_mean = vals.mean()
            sec_std = vals.std(ddof=1)  # sample standard deviation

            for _, row in group.iterrows():
                val = row[m]
                if pd.isna(val):
                    continue

                if sec_std is None or pd.isna(sec_std) or sec_std == 0:
                    z_val = np.nan
                    is_outlier = False
                else:
                    z_val = (val - sec_mean) / sec_std
                    is_outlier = abs(z_val) > z_threshold

                if is_outlier:
                    outliers.append(
                        {
                            "company_id": row["company_id"],
                            "broad_sector": broad_sec,
                            "metric": m,
                            "value": round(float(val), 4),
                            "sector_mean": round(float(sec_mean), 4),
                            "sector_std": round(float(sec_std), 4),
                            "z_score": round(float(z_val), 4),
                            "outlier_flag": True,
                        }
                    )

    outlier_df = pd.DataFrame(outliers)
    if outlier_df.empty:
        outlier_df = pd.DataFrame(
            columns=[
                "company_id",
                "broad_sector",
                "metric",
                "value",
                "sector_mean",
                "sector_std",
                "z_score",
                "outlier_flag",
            ]
        )
    else:
        outlier_df = outlier_df.sort_values(
            ["broad_sector", "company_id", "metric"]
        ).reset_index(drop=True)

    outlier_df.to_csv(output_path, index=False)
    logger.info(
        f"Saved sector outlier report to {output_path} ({len(outlier_df)} outlier records)."
    )
    return outlier_df


# =============================================================================
# PART 5 — PORTFOLIO STATISTICS
# =============================================================================


def calculate_portfolio_stats(
    conn: Any = None,
    kpis: List[str] = DEFAULT_10_KPIS,
    output_path: Path = PORTFOLIO_STATS_CSV,
) -> pd.DataFrame:
    """
    Calculate P10, P25, P50, P75, P90, Mean, and Std for each required KPI
    across the authoritative company universe for the latest year.

    Parameters
    ----------
    conn : Optional[sqlite3.Connection]
        Database connection.
    kpis : List[str]
        List of KPIs to analyze.
    output_path : Path
        Target CSV output path.

    Returns
    -------
    pd.DataFrame
        Portfolio statistics summary DataFrame.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    try:
        # Load latest financial KPIs per company
        kpis_df = pd.read_sql_query("SELECT * FROM financial_kpis", conn)
        if kpis_df.empty:
            raise ValueError("financial_kpis table is empty.")

        latest_kpis = (
            kpis_df.sort_values("id").groupby("company_id").last().reset_index()
        )

        stats_rows = []

        for k in kpis:
            if k not in latest_kpis.columns:
                logger.warning(
                    f"KPI column '{k}' not found in financial_kpis. Skipping."
                )
                continue

            vals = latest_kpis[k].dropna()
            if vals.empty:
                logger.warning(f"No valid non-null observations for KPI '{k}'.")
                row = {
                    "kpi": k,
                    "count": 0,
                    "P10": np.nan,
                    "P25": np.nan,
                    "P50": np.nan,
                    "P75": np.nan,
                    "P90": np.nan,
                    "Mean": np.nan,
                    "Std": np.nan,
                }
            else:
                p10 = float(np.percentile(vals, 10))
                p25 = float(np.percentile(vals, 25))
                p50 = float(np.percentile(vals, 50))
                p75 = float(np.percentile(vals, 75))
                p90 = float(np.percentile(vals, 90))
                mean_val = float(vals.mean())
                std_val = float(vals.std(ddof=1))  # sample standard deviation

                row = {
                    "kpi": k,
                    "count": len(vals),
                    "P10": round(p10, 4),
                    "P25": round(p25, 4),
                    "P50": round(p50, 4),
                    "P75": round(p75, 4),
                    "P90": round(p90, 4),
                    "Mean": round(mean_val, 4),
                    "Std": round(std_val, 4),
                }
            stats_rows.append(row)

        stats_df = pd.DataFrame(stats_rows)
        stats_df.to_csv(output_path, index=False)
        logger.info(
            f"Saved portfolio statistics to {output_path} ({len(stats_df)} KPIs analyzed)."
        )
        return stats_df

    finally:
        if close_conn and conn:
            conn.close()


# =============================================================================
# MAIN PIPELINE EXECUTION
# =============================================================================


def run_cluster_profiling_pipeline(
    conn: Any = None, custom_names: Optional[Dict[int, str]] = None
) -> Dict[str, Any]:
    """
    Run end-to-end Module 6B workflow: Cluster Profiling, Correlation Matrix,
    Sector Outliers, and Portfolio Statistics.

    Returns
    -------
    Dict[str, Any]
        Dictionary of output DataFrames and generated file paths.
    """
    logger.info("=== Starting Sprint 6 — Module 6B: Cluster Profiling & Statistics ===")

    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    try:
        # Part 1: Cluster profiling
        profiles_df = profile_clusters(conn=conn, custom_names=custom_names)

        # Part 3: Correlation heatmap
        corr_matrix = generate_correlation_heatmap(conn=conn)

        # Part 4: Sector outlier detection
        outliers_df = detect_sector_outliers(conn=conn)

        # Part 5: Portfolio statistics
        portfolio_df = calculate_portfolio_stats(conn=conn)

        logger.info("=== Module 6B Cluster Profiling & Statistics Complete ===")
        return {
            "profiles_df": profiles_df,
            "corr_matrix": corr_matrix,
            "outliers_df": outliers_df,
            "portfolio_df": portfolio_df,
            "profiles_csv": CLUSTER_PROFILES_CSV,
            "heatmap_png": CORRELATION_HEATMAP_PNG,
            "outlier_csv": OUTLIER_REPORT_CSV,
            "portfolio_csv": PORTFOLIO_STATS_CSV,
        }

    finally:
        if close_conn and conn:
            conn.close()


if __name__ == "__main__":
    results = run_cluster_profiling_pipeline()
    print("Module 6B execution complete. Output files generated:")
    print(" - Cluster profiles:", results["profiles_csv"])
    print(" - Correlation heatmap:", results["heatmap_png"])
    print(" - Outlier report:", results["outlier_csv"])
    print(" - Portfolio stats:", results["portfolio_csv"])
