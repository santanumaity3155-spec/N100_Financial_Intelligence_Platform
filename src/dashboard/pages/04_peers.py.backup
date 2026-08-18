"""
Peer Comparison Screen - N100 Financial Intelligence Platform
Sprint 4 - Module 3 Implementation

Provides an interactive peer comparison dashboard for Nifty 100 companies.
Reuses the Sprint 3 Peer Percentile Engine and Radar Chart Engine.

Features
--------
1. Peer group dropdown (11 groups loaded from the database)
2. Company selector with case-insensitive search / autocomplete
3. Plotly Scatterpolar radar chart (selected company vs peer group average)
4. Peer KPI table with selected / benchmark / best / worst highlighting

Layout
------
- Sidebar: peer group + company selection + search
- Main: radar chart + KPI comparison table
"""

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.analytics.peer import INVERTED_METRICS, calculate_percentile_rank
from src.config.logging_config import get_logger
from src.dashboard.utils.db import (
    get_peer_group_companies,
    get_peer_group_metrics,
    get_peer_groups_list,
)

logger = get_logger(__name__)

# =============================================================================
# PAGE CONFIGURATION
# =============================================================================

st.set_page_config(
    page_title="Peer Comparison - N100 Financial Intelligence",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# CONSTANTS - RADAR METRICS (8 required metrics)
# =============================================================================

# (source column, display label)
RADAR_METRICS: List[Tuple[str, str]] = [
    ("roe", "ROE"),
    ("roce", "ROCE"),
    ("net_profit_margin", "Net Profit Margin"),
    ("debt_to_equity", "Debt to Equity"),
    ("free_cash_flow", "Free Cash Flow"),
    ("revenue_cagr_5yr", "Revenue CAGR"),
    ("pat_cagr_5yr", "PAT CAGR"),
    ("composite_quality_score", "Composite Score"),
]

# =============================================================================
# CONSTANTS - KPI TABLE COLUMNS
# =============================================================================

# (display label, source column)
KPI_COLUMNS: List[Tuple[str, str]] = [
    ("Company", "company_name"),
    ("Composite Score", "composite_quality_score"),
    ("ROE", "roe"),
    ("ROCE", "roce"),
    ("Debt to Equity", "debt_to_equity"),
    ("Revenue CAGR", "revenue_cagr_5yr"),
    ("PAT CAGR", "pat_cagr_5yr"),
    ("Free Cash Flow", "free_cash_flow"),
    ("Percentile", "avg_percentile"),
]

# Colors for row highlighting
COLOR_SELECTED = "#D4E6F1"   # Light blue
COLOR_BENCHMARK = "#E8DAEF"  # Light purple
COLOR_BEST = "#D5F5E3"       # Light green
COLOR_WORST = "#FADBD8"      # Light red


# =============================================================================
# DATA LOADING (cached)
# =============================================================================

@st.cache_data(ttl=600, show_spinner=False)
def load_peer_groups() -> List[str]:
    """
    Load the list of available peer group names from the database.

    Returns
    -------
    List[str]
        Sorted list of peer group names. Empty list on error.
    """
    try:
        groups = get_peer_groups_list()
        logger.info(f"Loaded {len(groups)} peer groups")
        return groups
    except Exception as e:
        logger.error(f"Failed to load peer groups: {str(e)}", exc_info=True)
        return []


@st.cache_data(ttl=600, show_spinner=False)
def load_group_metrics(peer_group: str) -> pd.DataFrame:
    """
    Load consolidated metrics for all companies in a peer group.

    Parameters
    ----------
    peer_group : str
        Peer group name.

    Returns
    -------
    pd.DataFrame
        DataFrame with company_id, company_name, sector, is_benchmark and
        all financial metrics. Empty DataFrame on error.
    """
    try:
        df = get_peer_group_metrics()
        if df.empty:
            logger.warning("Peer group metrics dataset is empty")
            return pd.DataFrame()
        # Filter to the selected group
        df = df[df["peer_group_name"] == peer_group].copy()
        # A company should appear only once per group
        df = df.drop_duplicates(subset=["company_id"], keep="first")
        logger.info(f"Loaded {len(df)} companies for peer group '{peer_group}'")
        return df
    except Exception as e:
        logger.error(
            f"Failed to load metrics for peer group '{peer_group}': {str(e)}",
            exc_info=True,
        )
        return pd.DataFrame()


@st.cache_data(ttl=600, show_spinner=False)
def load_benchmark_flags(peer_group: str) -> Dict[str, bool]:
    """
    Load benchmark flags for companies in a peer group.

    Parameters
    ----------
    peer_group : str
        Peer group name.

    Returns
    -------
    Dict[str, bool]
        Mapping of company_id -> is_benchmark (bool).
    """
    try:
        df = get_peer_group_companies(peer_group)
        if df.empty:
            return {}
        flags = {}
        for _, row in df.iterrows():
            cid = row.get("company_id")
            if cid:
                flags[str(cid)] = bool(row.get("is_benchmark", 0))
        return flags
    except Exception as e:
        logger.error(f"Failed to load benchmark flags: {str(e)}", exc_info=True)
        return {}


# =============================================================================
# PERCENTILE COMPUTATION (reuses Peer Engine)
# =============================================================================

def compute_peer_percentiles(group_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute within-group percentile ranks for every radar metric.

    Reuses ``calculate_percentile_rank`` from the Sprint 3 Peer Engine and
    applies inversion for metrics where lower is better (debt_to_equity).

    Parameters
    ----------
    group_df : pd.DataFrame
        DataFrame with all companies in a peer group.

    Returns
    -------
    pd.DataFrame
        Copy of group_df with added ``<metric>_pct`` and ``avg_percentile``
        columns.
    """
    df = group_df.copy()
    pct_cols: List[str] = []
    for col, _ in RADAR_METRICS:
        pct_col = f"{col}_pct"
        if col not in df.columns:
            df[pct_col] = np.nan
            continue
        invert = col in INVERTED_METRICS
        series = pd.to_numeric(df[col], errors="coerce")
        df[pct_col] = calculate_percentile_rank(series, invert=invert)
        pct_cols.append(pct_col)

    if pct_cols:
        df["avg_percentile"] = df[pct_cols].mean(axis=1)
    else:
        df["avg_percentile"] = np.nan
    return df


# =============================================================================
# RADAR CHART (Plotly Scatterpolar)
# =============================================================================

def build_radar_chart(
    group_df: pd.DataFrame,
    selected_id: str,
    selected_name: str,
    peer_group: str,
) -> go.Figure:
    """
    Build an interactive Plotly Scatterpolar radar chart.

    Displays the selected company's percentile profile vs the peer group
    average percentile profile across the 8 required metrics.

    Parameters
    ----------
    group_df : pd.DataFrame
        Peer group DataFrame with ``<metric>_pct`` columns.
    selected_id : str
        Selected company id.
    selected_name : str
        Selected company display name.
    peer_group : str
        Peer group name (used in the title).

    Returns
    -------
    go.Figure
        Plotly figure. Returns an empty figure on error.
    """
    import time
    start_time = time.time()
    
    # -------------------------------------------------------------------------
    # Validation 1: Empty dataframe check
    # -------------------------------------------------------------------------
    if group_df is None or group_df.empty:
        logger.warning("Radar chart skipped: group_df is None or empty")
        return go.Figure()
    
    # Log the call
    logger.debug(
        f"Building radar chart: company={selected_id}, "
        f"peer_group={peer_group}, df_shape={group_df.shape}"
    )
    
    # -------------------------------------------------------------------------
    # Validation 2: Required columns check
    # -------------------------------------------------------------------------
    if "company_id" not in group_df.columns:
        logger.warning("Radar chart skipped: 'company_id' column missing from group_df")
        return go.Figure()
    
    # -------------------------------------------------------------------------
    # Define labels for radar chart
    # -------------------------------------------------------------------------
    labels = [label for _, label in RADAR_METRICS]
    
    # -------------------------------------------------------------------------
    # Validation 3: Check for required metric columns
    # -------------------------------------------------------------------------
    required_metrics = [col for col, _ in RADAR_METRICS]
    missing_metrics = [col for col in required_metrics if col not in group_df.columns]
    if missing_metrics:
        logger.warning(
            f"Radar chart: {len(missing_metrics)} required metrics missing from group_df: "
            f"{missing_metrics}"
        )
        # Continue anyway - we'll handle missing metrics gracefully
    
    # -------------------------------------------------------------------------
    # Validation 4: Selected company exists in peer group
    # -------------------------------------------------------------------------
    try:
        company_mask = group_df["company_id"] == selected_id
        if not company_mask.any():
            logger.warning(
                f"Radar chart skipped: selected company {selected_id} not found in peer group"
            )
            st.warning("No peer comparison data available.")
            return go.Figure()
        
        row = group_df[company_mask].iloc[0]
    except (IndexError, KeyError) as e:
        logger.error(
            f"Radar chart failed: error accessing selected company {selected_id}: {str(e)}"
        )
        st.warning("No peer comparison data available.")
        return go.Figure()
    
    # -------------------------------------------------------------------------
    # Build company values (with NaN handling)
    # -------------------------------------------------------------------------
    company_values: List[float] = []
    metrics_with_nan = []
    
    for col, label in RADAR_METRICS:
        pct_col = f"{col}_pct"
        
        # Check if percentile column exists
        if pct_col not in group_df.columns:
            logger.debug(f"Radar chart: percentile column '{pct_col}' missing, using 0.0")
            company_values.append(0.0)
            continue
        
        # Get value with NaN handling
        val = row.get(pct_col, np.nan)
        
        # Handle NaN/None/invalid values
        if pd.isna(val) or val is None:
            company_values.append(0.0)
            metrics_with_nan.append(label)
        else:
            try:
                float_val = float(val)
                # Validate range [0, 1] for percentiles
                if 0 <= float_val <= 1:
                    company_values.append(float_val)
                else:
                    logger.warning(
                        f"Radar chart: invalid percentile {float_val} for {label}, using 0.0"
                    )
                    company_values.append(0.0)
                    metrics_with_nan.append(label)
            except (TypeError, ValueError) as e:
                logger.warning(
                    f"Radar chart: cannot convert value to float for {label}: {str(e)}"
                )
                company_values.append(0.0)
                metrics_with_nan.append(label)
    
    if metrics_with_nan:
        logger.info(
            f"Radar chart: {len(metrics_with_nan)} metrics have NaN/invalid values for "
            f"company {selected_id}: {metrics_with_nan}"
        )
    
    # -------------------------------------------------------------------------
    # Build peer average values (with NaN handling)
    # -------------------------------------------------------------------------
    peer_avg_values: List[float] = []
    
    for col, label in RADAR_METRICS:
        pct_col = f"{col}_pct"
        
        # Check if percentile column exists
        if pct_col not in group_df.columns:
            peer_avg_values.append(0.0)
            continue
        
        # Calculate mean, skipping NaN values
        try:
            mean_val = group_df[pct_col].mean(skipna=True)
            
            # Handle NaN mean (e.g., all values are NaN)
            if pd.isna(mean_val):
                peer_avg_values.append(0.0)
                logger.debug(
                    f"Radar chart: peer average for {label} is NaN (all values missing)"
                )
            else:
                float_val = float(mean_val)
                # Validate range
                if 0 <= float_val <= 1:
                    peer_avg_values.append(float_val)
                else:
                    logger.warning(
                        f"Radar chart: invalid peer average {float_val} for {label}, using 0.0"
                    )
                    peer_avg_values.append(0.0)
        except Exception as e:
            logger.warning(
                f"Radar chart: error calculating peer average for {label}: {str(e)}"
            )
            peer_avg_values.append(0.0)
    
    # -------------------------------------------------------------------------
    # Handle single-company peer group
    # -------------------------------------------------------------------------
    if len(group_df) == 1:
        logger.info(
            f"Radar chart: single-company peer group for {selected_id}, "
            f"peer average equals company values"
        )
        # Peer average should equal company values (already calculated above)
    
    # -------------------------------------------------------------------------
    # Create radar chart
    # -------------------------------------------------------------------------
    try:
        # Close the radar loop
        company_plot = company_values + company_values[:1]
        peer_plot = peer_avg_values + peer_avg_values[:1]
        theta = labels + labels[:1]

        fig = go.Figure()

        fig.add_trace(
            go.Scatterpolar(
                r=company_plot,
                theta=theta,
                fill="toself",
                name=selected_name,
                line=dict(color="#2E86AB", width=3),
                fillcolor="rgba(46,134,171,0.25)",
                hovertemplate="<b>%{theta}</b><br>Percentile: %{r:.0%}<extra></extra>",
            )
        )

        fig.add_trace(
            go.Scatterpolar(
                r=peer_plot,
                theta=theta,
                fill="toself",
                name="Peer Group Average",
                line=dict(color="#A23B72", width=3, dash="dash"),
                fillcolor="rgba(162,59,114,0.15)",
                hovertemplate="<b>%{theta}</b><br>Percentile: %{r:.0%}<extra></extra>",
            )
        )

        fig.update_layout(
            title=f"{selected_name} vs {peer_group} Peer Average",
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1],
                    tickvals=[0, 0.25, 0.5, 0.75, 1.0],
                    ticktext=["0%", "25%", "50%", "75%", "100%"],
                )
            ),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.15),
            height=600,
            margin=dict(l=40, r=40, t=60, b=40),
        )
        
        elapsed_time = time.time() - start_time
        logger.info(
            f"Radar chart generated successfully for {selected_id} in {peer_group} "
            f"(elapsed: {elapsed_time:.3f}s, peers: {len(group_df)}, "
            f"metrics_with_nan: {len(metrics_with_nan)})"
        )
        
        return fig
        
    except Exception as e:
        logger.error(
            f"Radar chart failed: error creating Plotly figure for {selected_id}: {str(e)}",
            exc_info=True,
        )
        return go.Figure()


# =============================================================================
# KPI TABLE
# =============================================================================

def prepare_kpi_table(group_df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare the display-ready KPI comparison table.

    Parameters
    ----------
    group_df : pd.DataFrame
        Peer group DataFrame with percentile columns.

    Returns
    -------
    pd.DataFrame
        Table with labelled columns and a rounded Percentile (%) column.
    """
    out = pd.DataFrame()
    for label, col in KPI_COLUMNS:
        if col not in group_df.columns:
            out[label] = np.nan
        else:
            out[label] = group_df[col]

    # Percentile as percentage
    if "Percentile" in out.columns:
        out["Percentile"] = pd.to_numeric(out["Percentile"], errors="coerce") * 100

    # Round numeric columns
    for label, _ in KPI_COLUMNS:
        if label == "Company" or label not in out.columns:
            continue
        out[label] = pd.to_numeric(out[label], errors="coerce").round(2)

    # Keep company_id alongside for highlighting logic
    out["_company_id"] = group_df["company_id"].values
    out["_is_benchmark"] = group_df["is_benchmark"].fillna(0).astype(int).values
    return out


def _row_style(
    row: pd.Series,
    selected_id: str,
    benchmark_ids: set,
    best_id: Optional[str],
    worst_id: Optional[str],
) -> List[str]:
    """
    Compute CSS background styles for a KPI table row.

    Parameters
    ----------
    row : pd.Series
        Row of the KPI table.
    selected_id : str
        Selected company id.
    benchmark_ids : set
        Set of benchmark company ids.
    best_id : Optional[str]
        Best performer company id.
    worst_id : Optional[str]
        Worst performer company id.

    Returns
    -------
    List[str]
        CSS style string per column.
    """
    cid = str(row.get("_company_id", ""))
    n_cols = len(row)
    if cid == selected_id:
        return [f"background-color: {COLOR_SELECTED}"] * n_cols
    if cid in benchmark_ids:
        return [f"background-color: {COLOR_BENCHMARK}"] * n_cols
    if best_id is not None and cid == best_id:
        return [f"background-color: {COLOR_BEST}"] * n_cols
    if worst_id is not None and cid == worst_id:
        return [f"background-color: {COLOR_WORST}"] * n_cols
    return [""] * n_cols


def render_kpi_table(
    group_df: pd.DataFrame,
    selected_id: str,
    benchmark_ids: set,
) -> None:
    """
    Render the peer KPI comparison table with row highlighting.

    Parameters
    ----------
    group_df : pd.DataFrame
        Peer group DataFrame with percentile columns.
    selected_id : str
        Selected company id.
    benchmark_ids : set
        Set of benchmark company ids.
    """
    st.subheader("📋 Peer KPI Comparison")

    table = prepare_kpi_table(group_df)
    if table.empty:
        st.warning("No KPI data available for this peer group.")
        logger.warning("KPI table empty - no data to render")
        return

    # Best / worst performers based on composite score
    best_id: Optional[str] = None
    worst_id: Optional[str] = None
    score_col = "Composite Score"
    if score_col in table.columns:
        scores = pd.to_numeric(table[score_col], errors="coerce")
        if scores.notna().any():
            best_id = str(table.loc[scores.idxmax(), "_company_id"])
            worst_id = str(table.loc[scores.idxmin(), "_company_id"])

    # Drop internal helper columns for display
    display_cols = [label for label, _ in KPI_COLUMNS if label in table.columns]
    styled = (
        table[display_cols]
        .style.apply(
            _row_style,
            axis=1,
            selected_id=str(selected_id),
            benchmark_ids=benchmark_ids,
            best_id=best_id,
            worst_id=worst_id,
        )
    )

    st.dataframe(
        styled,
        use_container_width=True,
        hide_index=True,
    )

    # Legend
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            f"<span style='background-color:{COLOR_SELECTED};padding:2px 8px;"
            f"border-radius:4px'>Selected Company</span>",
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"<span style='background-color:{COLOR_BENCHMARK};padding:2px 8px;"
            f"border-radius:4px'>Benchmark</span>",
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"<span style='background-color:{COLOR_BEST};padding:2px 8px;"
            f"border-radius:4px'>Best Performer</span>",
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            f"<span style='background-color:{COLOR_WORST};padding:2px 8px;"
            f"border-radius:4px'>Worst Performer</span>",
            unsafe_allow_html=True,
        )

    logger.info(
        f"KPI table rendered for {len(table)} companies "
        f"(selected={selected_id})"
    )


# =============================================================================
# SIDEBAR SELECTION
# =============================================================================

def render_sidebar(groups: List[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Render peer-group dropdown, company search and company selector.

    Parameters
    ----------
    groups : List[str]
        Available peer group names.

    Returns
    -------
    Tuple[Optional[str], Optional[str]]
        (selected_peer_group, selected_company_id).
    """
    st.sidebar.header("🏢 Peer Group")

    selected_group = st.sidebar.selectbox(
        "Select Peer Group",
        options=groups,
        help="Choose a peer group to compare companies within it.",
    )
    logger.info(f"Peer group selected: {selected_group}")

    st.sidebar.markdown("---")

    # Load companies in the group
    group_df = load_group_metrics(selected_group)

    if group_df.empty:
        st.sidebar.warning("No companies found in this peer group.")
        return selected_group, None

    company_names = group_df["company_name"].dropna().astype(str).tolist()
    company_names = sorted(set(company_names))

    if not company_names:
        st.sidebar.warning("No company names available for this peer group.")
        return selected_group, None

    # Case-insensitive search filter
    st.sidebar.subheader("🔍 Search Company")
    query = st.sidebar.text_input(
        "Type to filter companies",
        placeholder="e.g. tcs",
        help="Search is case-insensitive and matches company names.",
    ).strip().lower()

    filtered_names = company_names
    if query:
        filtered_names = [n for n in company_names if query in n.lower()]

    if not filtered_names:
        st.sidebar.info("No companies match your search.")
        return selected_group, None

    selected_name = st.sidebar.selectbox(
        "Select Company",
        options=filtered_names,
        help="Choose a company to compare against its peers.",
    )

    # Map name -> company_id
    try:
        selected_id = group_df.loc[
            group_df["company_name"] == selected_name, "company_id"
        ].iloc[0]
        selected_id = str(selected_id)
    except (KeyError, IndexError):
        st.sidebar.warning("Selected company data is unavailable.")
        return selected_group, None

    logger.info(f"Company selected: {selected_id} ({selected_name})")
    return selected_group, selected_id


# =============================================================================
# MAIN
# =============================================================================

def main() -> None:
    """
    Render the Peer Comparison screen.
    """
    logger.info("Peer Comparison screen accessed")
    st.title("👥 Peer Comparison")
    st.markdown("### Compare Nifty 100 companies against their industry peers.")
    st.markdown("---")

    # Load peer groups
    groups = load_peer_groups()

    if not groups:
        st.error("No peer groups are available. Please check the database.")
        logger.error("No peer groups available - cannot render screen")
        return

    # Sidebar selection
    selected_group, selected_id = render_sidebar(groups)

    if selected_group is None or selected_id is None:
        st.info("👈 Select a peer group and company to view the comparison.")
        return

    # Load group data and compute percentiles on the fly
    with st.spinner("Loading peer comparison..."):
        group_df = load_group_metrics(selected_group)

        if group_df.empty:
            st.error("No financial data is available for this peer group.")
            logger.error("Peer group metrics empty - cannot render comparison")
            return

        group_df = compute_peer_percentiles(group_df)

        # Benchmark flags
        benchmark_flags = load_benchmark_flags(selected_group)
        benchmark_ids = {
            cid for cid, is_b in benchmark_flags.items() if is_b
        }

        # Company name for the selected id
        try:
            selected_name = group_df.loc[
                group_df["company_id"] == selected_id, "company_name"
            ].iloc[0]
        except (KeyError, IndexError):
            st.error("The selected company's data is missing.")
            logger.error(f"Company {selected_id} missing from peer group data")
            return

    # Radar chart
    try:
        fig = build_radar_chart(group_df, selected_id, selected_name, selected_group)
        if not fig.data:
            st.warning("Radar data is not available for the selected company.")
        else:
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        logger.error(f"Radar chart failed: {str(e)}", exc_info=True)
        st.error("Unable to render the radar chart for this company.")

    st.markdown("---")

    # KPI table
    try:
        render_kpi_table(group_df, selected_id, benchmark_ids)
    except Exception as e:
        logger.error(f"KPI table failed: {str(e)}", exc_info=True)
        st.error("Unable to render the KPI comparison table.")

    # Footer
    st.markdown("---")
    st.caption(
        "💡 **Tip:** Percentiles are computed live within the selected peer "
        "group. Select a different group or company to update the dashboard."
    )
    logger.info("Peer Comparison screen rendered successfully")


if __name__ == "__main__":
    main()

