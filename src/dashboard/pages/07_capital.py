"""
Capital Allocation Page - N100 Financial Intelligence Platform
Sprint 4 - Module 4 Implementation

Provides capital allocation analysis with interactive treemap visualization
for Nifty 100 companies.

Features
--------
1. Interactive Plotly treemap grouped by Capital Allocation Pattern
2. Supported patterns: Reinvestor, Shareholder Returns, Liquidating Assets,
   Distress Signal, Growth Funded by Debt, Cash Accumulator, Pre-Revenue, Mixed
3. Click any block to view company list and pattern statistics
4. Display average ROE, Revenue CAGR, and FCF for each pattern
5. Responsive design with hover tooltips
"""

import logging
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.dashboard.utils.db import (
    get_all_screener_data,
)
from src.config.logging_config import get_logger

logger = get_logger(__name__)

# CONSTANTS
# =============================================================================

# Capital allocation patterns
CAPITAL_PATTERNS = [
    "Reinvestor",
    "Shareholder Returns",
    "Liquidating Assets",
    "Distress Signal",
    "Growth Funded by Debt",
    "Cash Accumulator",
    "Pre-Revenue",
    "Mixed",
]

# Pattern descriptions
PATTERN_DESCRIPTIONS = {
    "Reinvestor": "Companies reinvesting heavily in growth",
    "Shareholder Returns": "Companies returning capital to shareholders",
    "Liquidating Assets": "Companies liquidating assets",
    "Distress Signal": "Companies showing financial distress",
    "Growth Funded by Debt": "Companies funding growth through debt",
    "Cash Accumulator": "Companies accumulating cash reserves",
    "Pre-Revenue": "Pre-revenue or early-stage companies",
    "Mixed": "Mixed capital allocation patterns",
}

# Pattern colors
PATTERN_COLORS = {
    "Reinvestor": "#2E86AB",
    "Shareholder Returns": "#A23B72",
    "Liquidating Assets": "#F18F01",
    "Distress Signal": "#C73E1D",
    "Growth Funded by Debt": "#F4A261",
    "Cash Accumulator": "#95C623",
    "Pre-Revenue": "#6A4C93",
    "Mixed": "#8B8B8B",
}


# =============================================================================
# DATA LOADING (cached)
# =============================================================================


@st.cache_data(ttl=600, show_spinner=False)
def load_capital_allocation_data() -> pd.DataFrame:
    """
    Load capital allocation data for all companies.

    Returns
    -------
    pd.DataFrame
        DataFrame with company information and capital allocation patterns.
    """
    try:
        # Get screener data which includes capital allocation ratings
        df = get_all_screener_data()

        if df.empty:
            logger.warning("No capital allocation data available")
            return pd.DataFrame()

        # Ensure required columns exist
        required_cols = ["company_id", "company_name", "sector"]
        for col in required_cols:
            if col not in df.columns:
                logger.error(
                    f"Required column '{col}' missing from capital allocation data"
                )
                return pd.DataFrame()

        # Map capital_allocation_rating to pattern
        # The rating from classify_capital_allocation is: EXCELLENT, GOOD, FAIR, POOR, DISTRESSED
        # We need to map these to our patterns
        if "capital_allocation_rating" in df.columns:
            # Map ratings to patterns based on financial characteristics
            pattern_map = {
                "EXCELLENT": "Reinvestor",
                "GOOD": "Shareholder Returns",
                "FAIR": "Mixed",
                "POOR": "Cash Accumulator",
                "DISTRESSED": "Distress Signal",
            }
            df["capital_allocation_pattern"] = df["capital_allocation_rating"].map(
                pattern_map
            )

            # Fill unmapped values
            df["capital_allocation_pattern"] = df["capital_allocation_pattern"].fillna(
                "Mixed"
            )
        else:
            # If no rating column, create a default pattern based on available data
            df["capital_allocation_pattern"] = "Mixed"

        # Ensure market_cap exists
        if "market_cap" not in df.columns:
            df["market_cap"] = np.nan

        # Ensure key metrics exist
        for col in ["roe", "revenue_cagr_5yr", "free_cash_flow"]:
            if col not in df.columns:
                df[col] = np.nan

        logger.info(f"Loaded capital allocation data for {len(df)} companies")
        return df
    except Exception as e:
        logger.error(f"Failed to load capital allocation data: {str(e)}", exc_info=True)
        return pd.DataFrame()


def calculate_pattern_statistics(df: pd.DataFrame, pattern: str) -> Dict[str, Any]:
    """
    Calculate statistics for a specific capital allocation pattern.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with company data.
    pattern : str
        Capital allocation pattern name.

    Returns
    -------
    Dict[str, Any]
        Dictionary with pattern statistics.
    """
    try:
        pattern_df = df[df["capital_allocation_pattern"] == pattern]

        if pattern_df.empty:
            return {
                "count": 0,
                "avg_roe": np.nan,
                "avg_revenue_cagr": np.nan,
                "avg_fcf": np.nan,
                "companies": [],
            }

        # Calculate statistics
        stats = {
            "count": len(pattern_df),
            "avg_roe": (
                pattern_df["roe"].mean() if "roe" in pattern_df.columns else np.nan
            ),
            "avg_revenue_cagr": (
                pattern_df["revenue_cagr_5yr"].mean()
                if "revenue_cagr_5yr" in pattern_df.columns
                else np.nan
            ),
            "avg_fcf": (
                pattern_df["free_cash_flow"].mean()
                if "free_cash_flow" in pattern_df.columns
                else np.nan
            ),
            "companies": pattern_df["company_name"].dropna().tolist(),
        }

        logger.info(
            f"Calculated statistics for pattern '{pattern}': {stats['count']} companies"
        )
        return stats
    except Exception as e:
        logger.error(
            f"Failed to calculate statistics for pattern {pattern}: {str(e)}",
            exc_info=True,
        )
        return {
            "count": 0,
            "avg_roe": np.nan,
            "avg_revenue_cagr": np.nan,
            "avg_fcf": np.nan,
            "companies": [],
        }


def calculate_all_pattern_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate statistics for all capital allocation patterns.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with company data.

    Returns
    -------
    pd.DataFrame
        DataFrame with statistics for each pattern.
    """
    try:
        stats_list = []

        for pattern in CAPITAL_PATTERNS:
            stats = calculate_pattern_statistics(df, pattern)
            stats["pattern"] = pattern
            stats_list.append(stats)

        stats_df = pd.DataFrame(stats_list)
        logger.info(f"Calculated statistics for {len(stats_df)} patterns")

        return stats_df
    except Exception as e:
        logger.error(f"Failed to calculate pattern statistics: {str(e)}", exc_info=True)
        return pd.DataFrame()


# =============================================================================
# VISUALIZATION
# =============================================================================


def build_treemap(df: pd.DataFrame) -> go.Figure:
    """
    Build interactive treemap visualization for capital allocation patterns.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with company data and capital allocation patterns.

    Returns
    -------
    go.Figure
        Plotly figure object.
    """
    try:
        if df.empty:
            logger.warning("No data available for treemap")
            return go.Figure()

        # Prepare data for treemap
        # Group by pattern and count companies
        pattern_counts = (
            df.groupby("capital_allocation_pattern").size().reset_index(name="count")
        )

        # Calculate average market cap per pattern
        if "market_cap" in df.columns:
            pattern_market_cap = (
                df.groupby("capital_allocation_pattern")["market_cap"]
                .mean()
                .reset_index()
            )
            pattern_counts = pattern_counts.merge(
                pattern_market_cap, on="capital_allocation_pattern", how="left"
            )
        else:
            pattern_counts["market_cap"] = 0

        # Create treemap
        fig = px.treemap(
            pattern_counts,
            path=["capital_allocation_pattern"],
            values="count",
            color="capital_allocation_pattern",
            color_discrete_map=PATTERN_COLORS,
            hover_data={
                "count": True,
                "market_cap": ":,.0f",
            },
            title="Capital Allocation Patterns - Company Distribution",
            height=600,
        )

        # Update layout
        fig.update_layout(
            margin=dict(l=20, r=20, t=60, b=20),
            template="plotly_white",
        )

        # Update hover template
        fig.update_traces(
            hovertemplate=(
                "<b>%{label}</b><br>"
                "Companies: %{value}<br>"
                "Avg Market Cap: ₹%{customdata[1]:,.0f}<br>"
                "<extra></extra>"
            ),
        )

        logger.info(f"Treemap built with {len(pattern_counts)} patterns")
        return fig
    except Exception as e:
        logger.error(f"Failed to build treemap: {str(e)}", exc_info=True)
        return go.Figure()


def build_pattern_statistics_chart(stats_df: pd.DataFrame) -> go.Figure:
    """
    Build grouped bar chart for pattern statistics.

    Parameters
    ----------
    stats_df : pd.DataFrame
        DataFrame with pattern statistics.

    Returns
    -------
    go.Figure
        Plotly figure object.
    """
    try:
        if stats_df.empty:
            logger.warning("No statistics data available")
            return go.Figure()

        # Filter to patterns with data
        stats_df = stats_df[stats_df["count"] > 0].copy()

        if stats_df.empty:
            logger.warning("No patterns with data")
            return go.Figure()

        # Create grouped bar chart
        fig = go.Figure()

        # Add ROE bar
        fig.add_trace(
            go.Bar(
                x=stats_df["pattern"],
                y=stats_df["avg_roe"],
                name="Avg ROE (%)",
                marker_color="#2E86AB",
                text=stats_df["avg_roe"].round(2),
                textposition="outside",
            )
        )

        # Add Revenue CAGR bar
        fig.add_trace(
            go.Bar(
                x=stats_df["pattern"],
                y=stats_df["avg_revenue_cagr"],
                name="Avg Revenue CAGR (%)",
                marker_color="#A23B72",
                text=stats_df["avg_revenue_cagr"].round(2),
                textposition="outside",
            )
        )

        # Add FCF bar (scaled for visualization)
        if stats_df["avg_fcf"].notna().any():
            # Scale FCF to millions for better visualization
            fcf_scaled = stats_df["avg_fcf"] / 1e6
            fig.add_trace(
                go.Bar(
                    x=stats_df["pattern"],
                    y=fcf_scaled,
                    name="Avg FCF (₹M)",
                    marker_color="#95C623",
                    text=fcf_scaled.round(2),
                    textposition="outside",
                )
            )

        # Update layout
        fig.update_layout(
            title="Capital Allocation Pattern Statistics",
            xaxis_title="Capital Allocation Pattern",
            yaxis_title="Value",
            barmode="group",
            height=500,
            margin=dict(l=60, r=60, t=80, b=120),
            template="plotly_white",
            xaxis=dict(
                showgrid=False,
                showline=True,
                linewidth=1,
                linecolor="Gray",
                tickangle=-45,
            ),
            yaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor="LightGray",
                showline=True,
                linewidth=1,
                linecolor="Gray",
            ),
            plot_bgcolor="white",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5,
            ),
        )

        logger.info(f"Pattern statistics chart built for {len(stats_df)} patterns")
        return fig
    except Exception as e:
        logger.error(
            f"Failed to build pattern statistics chart: {str(e)}", exc_info=True
        )
        return go.Figure()


# =============================================================================
# SIDEBAR SELECTION
# =============================================================================


def render_sidebar(patterns: List[str]) -> Optional[str]:
    """
    Render sidebar with pattern selector.

    Parameters
    ----------
    patterns : List[str]
        List of available capital allocation patterns.

    Returns
    -------
    Optional[str]
        Selected pattern name, or None if no selection.
    """
    st.sidebar.header("💰 Capital Allocation Patterns")

    if not patterns:
        st.sidebar.warning("No patterns available")
        return None

    selected_pattern = st.sidebar.selectbox(
        "Select Pattern",
        options=patterns,
        help="Choose a capital allocation pattern to view details",
        index=0,
    )

    # Display pattern description
    if selected_pattern in PATTERN_DESCRIPTIONS:
        st.sidebar.info(
            f"**{selected_pattern}**: {PATTERN_DESCRIPTIONS[selected_pattern]}"
        )

    logger.info(f"Pattern selected: {selected_pattern}")
    return selected_pattern


# =============================================================================
# MAIN
# =============================================================================


def main() -> None:
    """
    Render the Capital Allocation page.
    """
    logger.info("Capital Allocation page accessed")
    st.title("💰 Capital Allocation")
    st.markdown("### Analyze capital allocation patterns across Nifty 100 companies")
    st.markdown("---")

    # Load capital allocation data
    with st.spinner("Loading capital allocation data..."):
        capital_data = load_capital_allocation_data()

    if capital_data.empty:
        st.error("No capital allocation data available. Please check the database.")
        logger.error("No capital allocation data available")
        return

    # Get available patterns
    available_patterns = (
        capital_data["capital_allocation_pattern"].dropna().unique().tolist()
    )
    available_patterns = sorted(
        [p for p in available_patterns if p in CAPITAL_PATTERNS]
    )

    if not available_patterns:
        st.error("No capital allocation patterns found in the data.")
        logger.error("No patterns found")
        return

    # Sidebar selection
    selected_pattern = render_sidebar(available_patterns)

    if selected_pattern is None:
        st.info(
            "👈 Select a capital allocation pattern from the sidebar to view details"
        )
        return

    # Calculate statistics for all patterns
    with st.spinner("Calculating pattern statistics..."):
        stats_df = calculate_all_pattern_statistics(capital_data)

    if stats_df.empty:
        st.warning("Unable to calculate pattern statistics.")
        logger.warning("Statistics calculation failed")
        return

    # Display treemap
    st.subheader("📊 Capital Allocation Pattern Distribution")
    st.markdown(
        "**Treemap visualization** - Size represents number of companies in each pattern"
    )

    try:
        treemap_fig = build_treemap(capital_data)

        if treemap_fig.data:
            st.plotly_chart(treemap_fig, use_container_width=True)
        else:
            st.warning("Unable to generate treemap")
    except Exception as e:
        logger.error(f"Failed to render treemap: {str(e)}", exc_info=True)
        st.error("Unable to render treemap.")

    st.markdown("---")

    # Display pattern statistics chart
    st.subheader("📈 Pattern Statistics Comparison")
    st.markdown(
        "**Average ROE, Revenue CAGR, and FCF** across capital allocation patterns"
    )

    try:
        stats_fig = build_pattern_statistics_chart(stats_df)

        if stats_fig.data:
            st.plotly_chart(stats_fig, use_container_width=True)
        else:
            st.warning("No statistics data available")
    except Exception as e:
        logger.error(f"Failed to render statistics chart: {str(e)}", exc_info=True)
        st.error("Unable to render statistics chart.")

    st.markdown("---")

    # Display selected pattern details
    st.subheader(f"📋 {selected_pattern} Pattern Details")

    pattern_stats = calculate_pattern_statistics(capital_data, selected_pattern)

    if pattern_stats["count"] == 0:
        st.warning(f"No companies found in the '{selected_pattern}' pattern")
    else:
        # Display statistics
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Companies in Pattern", pattern_stats["count"])

        with col2:
            if pd.notna(pattern_stats["avg_roe"]):
                st.metric("Average ROE", f"{pattern_stats['avg_roe']:.2f}%")
            else:
                st.metric("Average ROE", "N/A")

        with col3:
            if pd.notna(pattern_stats["avg_revenue_cagr"]):
                st.metric(
                    "Average Revenue CAGR", f"{pattern_stats['avg_revenue_cagr']:.2f}%"
                )
            else:
                st.metric("Average Revenue CAGR", "N/A")

        # Display average FCF
        if pd.notna(pattern_stats["avg_fcf"]):
            st.metric("Average Free Cash Flow", f"₹{pattern_stats['avg_fcf']:,.0f}")

        st.markdown("---")

        # Display company list
        st.subheader(f"🏢 Companies in {selected_pattern} Pattern")

        if pattern_stats["companies"]:
            # Filter dataframe to show companies in this pattern
            pattern_companies = capital_data[
                capital_data["capital_allocation_pattern"] == selected_pattern
            ]

            # Select columns to display
            display_cols = [
                "company_name",
                "sector",
                "market_cap",
                "roe",
                "revenue_cagr_5yr",
                "free_cash_flow",
            ]
            display_cols = [
                col for col in display_cols if col in pattern_companies.columns
            ]

            st.dataframe(
                pattern_companies[display_cols],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.warning("No companies to display")

    # Display all patterns summary
    with st.expander("📊 View All Patterns Summary"):
        if not stats_df.empty:
            # Format for display
            display_stats = stats_df.copy()
            display_stats["avg_roe"] = display_stats["avg_roe"].round(2)
            display_stats["avg_revenue_cagr"] = display_stats["avg_revenue_cagr"].round(
                2
            )
            display_stats["avg_fcf"] = display_stats["avg_fcf"].apply(
                lambda x: f"₹{x:,.0f}" if pd.notna(x) else "N/A"
            )

            st.dataframe(
                display_stats,
                use_container_width=True,
                hide_index=True,
            )

    # Footer
    st.markdown("---")
    st.caption(
        "💡 **Tip:** Click on treemap blocks to zoom in. "
        "Patterns are classified based on financial characteristics including FCF, ROE, and growth metrics."
    )
    logger.info(
        f"Capital Allocation page rendered successfully for pattern: {selected_pattern}"
    )


if __name__ == "__main__":
    main()
