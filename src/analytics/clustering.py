"""
clustering.py

KMeans Clustering Module for the N100 Financial Intelligence Platform.
Sprint 6 — Module 6A: KMeans Clustering (Day 36)

This module extracts company financial features, performs sector median imputation,
normalizes features with StandardScaler, runs KMeans clustering (n_clusters=5, random_state=42),
computes centroid distances, generates elbow plot (k=2..10), and produces cluster_labels.csv.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

from src.config.logging_config import get_logger
from src.database.connection import get_connection
from src.analytics.cagr import calculate_revenue_cagr
from src.analytics.cashflow_intelligence import compute_fcf_cagr_5yr

logger = get_logger(__name__)

# =============================================================================
# CONSTANTS
# =============================================================================

REQUIRED_FEATURES = [
    "return_on_equity_pct",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "fcf_cagr_5yr",
    "operating_profit_margin_pct"
]

DEFAULT_N_CLUSTERS = 5
DEFAULT_RANDOM_STATE = 42
DEFAULT_N_INIT = 10
ELBOW_K_RANGE = range(2, 11)

OUTPUT_DIR = Path("output")
REPORTS_DIR = Path("reports")
CLUSTER_LABELS_CSV = OUTPUT_DIR / "cluster_labels.csv"
ELBOW_PLOT_PNG = REPORTS_DIR / "elbow_plot.png"

# Explicit sector overrides for companies missing in the sectors table
SECTOR_OVERRIDES = {
    "ULTRACEMCO": "Cement",
    "UNIONBANK": "Public Sector Banks"
}


# =============================================================================
# DATA PREPARATION & FEATURE EXTRACTION
# =============================================================================

def load_clustering_dataset(conn=None) -> pd.DataFrame:
    """
    Extract the company-level dataset with the five required clustering features
    from authoritative database sources.

    Returns
    -------
    pd.DataFrame
        DataFrame containing company_id, sector, and the 5 features.
    """
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    try:
        logger.info("Loading company base data and sector mappings...")
        df_comp = pd.read_sql_query(
            "SELECT company_id, company_name, roe_percentage FROM companies ORDER BY company_id",
            conn
        )
        df_sec = pd.read_sql_query(
            "SELECT company_id, broad_sector, sub_sector FROM sectors",
            conn
        )

        # Merge sectors onto companies
        merged = df_comp.merge(df_sec, on="company_id", how="left")

        # Apply explicit sector overrides for companies not present in sectors table
        for cid, sec_val in SECTOR_OVERRIDES.items():
            merged.loc[merged["company_id"] == cid, "sub_sector"] = merged.loc[
                merged["company_id"] == cid, "sub_sector"
            ].fillna(sec_val)

        merged["sector"] = merged["sub_sector"].fillna("Unknown")

        # Extract features for each company
        results = []
        for idx, row in merged.iterrows():
            cid = row["company_id"]
            sec = row["sector"]

            # Feature 1: return_on_equity_pct
            roe_val = row["roe_percentage"]
            if pd.isna(roe_val):
                kpi_roe = pd.read_sql_query(
                    "SELECT roe FROM financial_kpis WHERE company_id = ? AND roe IS NOT NULL ORDER BY id DESC LIMIT 1",
                    conn, params=(cid,)
                )
                if not kpi_roe.empty:
                    roe_val = kpi_roe.iloc[0]["roe"]
                else:
                    rat_roe = pd.read_sql_query(
                        "SELECT roe FROM financial_ratios WHERE company_id = ? AND roe IS NOT NULL ORDER BY id DESC LIMIT 1",
                        conn, params=(cid,)
                    )
                    if not rat_roe.empty:
                        roe_val = rat_roe.iloc[0]["roe"]

            # Feature 2: debt_to_equity
            kpi_de = pd.read_sql_query(
                "SELECT debt_to_equity FROM financial_kpis WHERE company_id = ? AND debt_to_equity IS NOT NULL ORDER BY id DESC LIMIT 1",
                conn, params=(cid,)
            )
            de_val = kpi_de.iloc[0]["debt_to_equity"] if not kpi_de.empty else None
            if de_val is None:
                rat_de = pd.read_sql_query(
                    "SELECT debt_to_equity FROM financial_ratios WHERE company_id = ? AND debt_to_equity IS NOT NULL ORDER BY id DESC LIMIT 1",
                    conn, params=(cid,)
                )
                if not rat_de.empty:
                    de_val = rat_de.iloc[0]["debt_to_equity"]

            # Feature 3: revenue_cagr_5yr
            kpi_rev = pd.read_sql_query(
                "SELECT revenue_cagr FROM financial_kpis WHERE company_id = ? AND revenue_cagr IS NOT NULL ORDER BY id DESC LIMIT 1",
                conn, params=(cid,)
            )
            rev_cagr = kpi_rev.iloc[0]["revenue_cagr"] if not kpi_rev.empty else None
            if rev_cagr is None:
                pl_df = pd.read_sql_query(
                    "SELECT * FROM profit_loss WHERE company_id = ? ORDER BY period ASC",
                    conn, params=(cid,)
                )
                if not pl_df.empty:
                    cagr_res = calculate_revenue_cagr(pl_df, company_id=cid)
                    rev_cagr = cagr_res.get("revenue_cagr_5yr", {}).get("value")

            # Feature 4: fcf_cagr_5yr
            cf_df = pd.read_sql_query(
                "SELECT * FROM cash_flow WHERE company_id = ? ORDER BY id ASC",
                conn, params=(cid,)
            )
            fcf_cagr = None
            if not cf_df.empty:
                fcf_res = compute_fcf_cagr_5yr(cf_df)
                fcf_cagr = fcf_res.get("value")

            # Feature 5: operating_profit_margin_pct
            pl_opm = pd.read_sql_query(
                "SELECT opm_percentage FROM profit_loss WHERE company_id = ? AND opm_percentage IS NOT NULL ORDER BY id DESC LIMIT 1",
                conn, params=(cid,)
            )
            opm_val = pl_opm.iloc[0]["opm_percentage"] if not pl_opm.empty else None
            if opm_val is None:
                kpi_opm = pd.read_sql_query(
                    "SELECT operating_margin FROM financial_kpis WHERE company_id = ? AND operating_margin IS NOT NULL ORDER BY id DESC LIMIT 1",
                    conn, params=(cid,)
                )
                if not kpi_opm.empty:
                    opm_val = kpi_opm.iloc[0]["operating_margin"]

            results.append({
                "company_id": cid,
                "sector": sec,
                "return_on_equity_pct": float(roe_val) if roe_val is not None and not pd.isna(roe_val) else np.nan,
                "debt_to_equity": float(de_val) if de_val is not None and not pd.isna(de_val) else np.nan,
                "revenue_cagr_5yr": float(rev_cagr) if rev_cagr is not None and not pd.isna(rev_cagr) else np.nan,
                "fcf_cagr_5yr": float(fcf_cagr) if fcf_cagr is not None and not pd.isna(fcf_cagr) else np.nan,
                "operating_profit_margin_pct": float(opm_val) if opm_val is not None and not pd.isna(opm_val) else np.nan,
            })

        df = pd.DataFrame(results)
        logger.info(f"Loaded feature dataset with {len(df)} companies.")
        return df

    finally:
        if close_conn and conn:
            conn.close()


# =============================================================================
# MISSING DATA IMPUTATION
# =============================================================================

def impute_missing_values(df: pd.DataFrame, features: List[str] = REQUIRED_FEATURES) -> pd.DataFrame:
    """
    Impute missing feature values using sector median for each metric.
    If an entire sector lacks valid data for a feature, fall back to the overall median.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing sector and feature columns.
    features : List[str]
        List of feature column names to impute.

    Returns
    -------
    pd.DataFrame
        Imputed DataFrame with no NaN or infinite values.
    """
    if df.empty:
        raise ValueError("Cannot impute missing values on an empty DataFrame.")

    imputed_df = df.copy()

    for feat in features:
        if feat not in imputed_df.columns:
            raise KeyError(f"Feature column '{feat}' not found in DataFrame.")

        # Check initial missing count
        missing_cnt = imputed_df[feat].isna().sum()
        if missing_cnt > 0:
            logger.info(f"Imputing {missing_cnt} missing values for feature '{feat}'...")
            
            # Sector median imputation
            sector_medians = imputed_df.groupby("sector")[feat].transform("median")
            imputed_df[feat] = imputed_df[feat].fillna(sector_medians)

            # Check if any NaNs remain (e.g., sector has no non-null entries)
            remaining_nans = imputed_df[feat].isna().sum()
            if remaining_nans > 0:
                overall_median = imputed_df[feat].median()
                if pd.isna(overall_median):
                    overall_median = 0.0
                logger.warning(
                    f"Feature '{feat}' has {remaining_nans} remaining NaNs after sector median imputation. "
                    f"Imputing overall median ({overall_median:.4f})."
                )
                imputed_df[feat] = imputed_df[feat].fillna(overall_median)

    # Validate that no NaNs or Inf values remain
    feature_matrix = imputed_df[features].to_numpy()
    if np.isnan(feature_matrix).any():
        raise ValueError("Feature matrix contains unresolved NaN values after imputation.")
    if np.isinf(feature_matrix).any():
        raise ValueError("Feature matrix contains infinite values.")

    return imputed_df


# =============================================================================
# FEATURE SCALING
# =============================================================================

def scale_features(
    df: pd.DataFrame,
    features: List[str] = REQUIRED_FEATURES
) -> Tuple[np.ndarray, StandardScaler]:
    """
    Standardize features using sklearn StandardScaler (mean=0, std=1).

    Parameters
    ----------
    df : pd.DataFrame
        Imputed DataFrame.
    features : List[str]
        Features to scale.

    Returns
    -------
    Tuple[np.ndarray, StandardScaler]
        Scaled feature matrix (shape N x 5) and fitted scaler.
    """
    if df.empty:
        raise ValueError("Cannot scale features on an empty DataFrame.")

    X = df[features].values.astype(float)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    logger.info(f"StandardScaler fit and transformed {X_scaled.shape[0]} rows across {X_scaled.shape[1]} features.")
    return X_scaled, scaler


# =============================================================================
# KMEANS CLUSTERING & DISTANCE CALCULATION
# =============================================================================

def run_kmeans(
    X_scaled: np.ndarray,
    n_clusters: int = DEFAULT_N_CLUSTERS,
    random_state: int = DEFAULT_RANDOM_STATE,
    n_init: int = DEFAULT_N_INIT
) -> KMeans:
    """
    Fit KMeans model with specified clusters and random state.

    Parameters
    ----------
    X_scaled : np.ndarray
        Scaled feature matrix.
    n_clusters : int
        Number of clusters (default 5).
    random_state : int
        Random state seed (default 42).
    n_init : int
        Number of initializations (default 10).

    Returns
    -------
    KMeans
        Fitted KMeans instance.
    """
    if X_scaled.shape[0] < n_clusters:
        raise ValueError(f"Number of samples ({X_scaled.shape[0]}) is less than n_clusters ({n_clusters}).")

    kmeans = KMeans(
        n_clusters=n_clusters,
        random_state=random_state,
        n_init=n_init
    )
    kmeans.fit(X_scaled)
    logger.info(f"KMeans fitted with n_clusters={n_clusters}, random_state={random_state}, inertia={kmeans.inertia_:.4f}.")
    return kmeans


def compute_centroid_distances(
    X_scaled: np.ndarray,
    labels: np.ndarray,
    centroids: np.ndarray
) -> np.ndarray:
    """
    Calculate Euclidean distance between each company's scaled feature vector
    and its assigned cluster centroid.

    Parameters
    ----------
    X_scaled : np.ndarray
        Scaled feature matrix of shape (N, D).
    labels : np.ndarray
        Assigned cluster label array of shape (N,).
    centroids : np.ndarray
        Cluster centroids matrix of shape (K, D).

    Returns
    -------
    np.ndarray
        Distance array of shape (N,). All distances >= 0.
    """
    N = X_scaled.shape[0]
    distances = np.zeros(N, dtype=float)

    for i in range(N):
        cluster_id = labels[i]
        centroid = centroids[cluster_id]
        dist = np.linalg.norm(X_scaled[i] - centroid)
        distances[i] = round(float(dist), 4)

    if (distances < 0).any():
        raise ValueError("Negative distance detected in centroid distance calculation.")

    return distances


# =============================================================================
# ELBOW PLOT GENERATION
# =============================================================================

def compute_elbow_inertia(
    X_scaled: np.ndarray,
    k_range: range = ELBOW_K_RANGE,
    random_state: int = DEFAULT_RANDOM_STATE,
    n_init: int = DEFAULT_N_INIT
) -> Dict[int, float]:
    """
    Compute inertia for k = 2..10.

    Returns
    -------
    Dict[int, float]
        Dictionary mapping k -> inertia.
    """
    inertia_dict = {}
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=random_state, n_init=n_init)
        km.fit(X_scaled)
        inertia_dict[k] = float(km.inertia_)
    return inertia_dict


def generate_elbow_plot(
    inertia_dict: Dict[int, float],
    output_path: Path = ELBOW_PLOT_PNG,
    highlight_k: int = DEFAULT_N_CLUSTERS
) -> Path:
    """
    Generate and save elbow plot (Inertia vs k) for k = 2..10.

    Parameters
    ----------
    inertia_dict : Dict[int, float]
        Mapping k -> inertia.
    output_path : Path
        Target file path for saving PNG.
    highlight_k : int
        Selected k value to highlight visually.

    Returns
    -------
    Path
        Saved image path.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    ks = sorted(list(inertia_dict.keys()))
    inertias = [inertia_dict[k] for k in ks]

    plt.figure(figsize=(9, 5), dpi=150)
    plt.plot(ks, inertias, 'o-', color='#1f77b4', linewidth=2, markersize=7, label='Inertia')

    if highlight_k in inertia_dict:
        plt.scatter(
            [highlight_k], [inertia_dict[highlight_k]],
            color='#d62728', s=120, zorder=5,
            label=f'Selected k={highlight_k}'
        )

    plt.title('KMeans Clustering — Elbow Method (Inertia vs k)', fontsize=14, fontweight='bold', pad=12)
    plt.xlabel('Number of Clusters (k)', fontsize=11, fontweight='semibold')
    plt.ylabel('Inertia (Within-Cluster Sum of Squares)', fontsize=11, fontweight='semibold')
    plt.xticks(ks)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(loc='upper right', frameon=True)
    plt.tight_layout()

    plt.savefig(output_path, dpi=150)
    plt.close()

    logger.info(f"Saved elbow plot to {output_path}")
    return output_path


# =============================================================================
# OUTPUT CSV GENERATION
# =============================================================================

def generate_cluster_output(
    df: pd.DataFrame,
    labels: np.ndarray,
    distances: np.ndarray,
    output_path: Path = CLUSTER_LABELS_CSV
) -> pd.DataFrame:
    """
    Generate output DataFrame and save cluster_labels.csv.

    Columns required:
    - company_id
    - cluster_id
    - cluster_name
    - distance_from_centroid

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame containing company_id.
    labels : np.ndarray
        Assigned cluster IDs (0..4).
    distances : np.ndarray
        Distance from assigned centroid.
    output_path : Path
        Target CSV output path.

    Returns
    -------
    pd.DataFrame
        Formatted result DataFrame.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    out_df = pd.DataFrame({
        "company_id": df["company_id"],
        "cluster_id": labels.astype(int),
        "cluster_name": [f"Cluster {cid}" for cid in labels],
        "distance_from_centroid": distances
    })

    out_df = out_df.sort_values("company_id").reset_index(drop=True)
    out_df.to_csv(output_path, index=False)
    logger.info(f"Saved cluster labels CSV to {output_path} ({len(out_df)} rows).")
    return out_df


# =============================================================================
# MAIN PIPELINE EXECUTION
# =============================================================================

def run_kmeans_clustering(
    conn=None,
    n_clusters: int = DEFAULT_N_CLUSTERS,
    random_state: int = DEFAULT_RANDOM_STATE,
    output_csv_path: Path = CLUSTER_LABELS_CSV,
    elbow_plot_path: Path = ELBOW_PLOT_PNG
) -> Dict[str, Any]:
    """
    Run end-to-end Module 6A KMeans Clustering workflow.

    Returns
    -------
    Dict[str, Any]
        Dictionary containing datasets, model, scaler, inertia dict, and output path.
    """
    logger.info("=== Starting Sprint 6 — Module 6A: KMeans Clustering ===")

    # Step 1: Load raw dataset
    raw_df = load_clustering_dataset(conn=conn)

    # Step 2: Impute missing values
    imputed_df = impute_missing_values(raw_df)

    # Step 3: Scale features
    X_scaled, scaler = scale_features(imputed_df)

    # Step 4: Run KMeans clustering
    kmeans = run_kmeans(X_scaled, n_clusters=n_clusters, random_state=random_state)

    # Step 5: Compute distances from centroid
    distances = compute_centroid_distances(X_scaled, kmeans.labels_, kmeans.cluster_centers_)

    # Step 6: Compute elbow curve and save plot
    inertia_dict = compute_elbow_inertia(X_scaled, random_state=random_state)
    generate_elbow_plot(inertia_dict, output_path=elbow_plot_path, highlight_k=n_clusters)

    # Step 7: Export cluster labels CSV
    out_df = generate_cluster_output(imputed_df, kmeans.labels_, distances, output_path=output_csv_path)

    logger.info("=== Module 6A KMeans Clustering Complete ===")
    return {
        "raw_df": raw_df,
        "imputed_df": imputed_df,
        "X_scaled": X_scaled,
        "scaler": scaler,
        "kmeans": kmeans,
        "distances": distances,
        "inertia_dict": inertia_dict,
        "cluster_labels_df": out_df,
        "csv_path": output_csv_path,
        "plot_path": elbow_plot_path
    }


if __name__ == "__main__":
    results = run_kmeans_clustering()
    print("Execution complete. Output CSV generated with", len(results["cluster_labels_df"]), "rows.")
