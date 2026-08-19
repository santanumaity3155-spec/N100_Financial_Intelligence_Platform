"""
Sector Analysis Page - N100 Financial Intelligence Platform
Sprint 4 - Module 4 Implementation

Provides comprehensive sector analysis with bubble charts and median KPI comparisons
for Nifty 100 companies.

Features
--------
1. Sector dropdown selector
2. Interactive Plotly bubble chart (Revenue vs ROE, sized by Market Cap, colored by Sub-sector)
3. Sector median KPI bar chart (ROE, ROCE, Revenue CAGR, Debt to Equity, Net Profit Margin, Composite Score)
4. Hover tooltips with company details
5. Responsive design with zoom and pan
"""

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.dashboard.utils.db import get_all_screener_data, get_companies
from src.config.logging_config import get_logger

logger = get_logger(__name__)

# CONSTANTS
# =============================================================================

# Median KPI metrics to display
MEDIAN_KPI_METRICS = [
    ("ROE", "roe", "{:.2f}%"),
    ("ROCE", "roce", "{:.2f}%"),
    ("Revenue CAGR", "revenue_cagr_5yr", "{:.2f}%"),
    ("Debt to Equity", "debt_to_equity", "{:.2f}"),
    ("Net Profit Margin", "net_profit_margin", "{:.2f}%"),
    ("Composite Score", "composite_quality_score", "{:.2f}"),
]

# Color palette for sub-sectors
SUB_SECTOR_COLORS = px.colors.qualitative.Set3


# =============================================================================
# DATA LOADING (cached)
# =============================================================================


@st.cache_data(ttl=600, show_spinner=False)
def load_sector_data() -> pd.DataFrame:
    """
    Load consolidated sector data for all companies.

    Returns
    -------
    pd.DataFrame
        DataFrame with company, sector, sub-sector, and all financial metrics.
    """
    try:
        # Get screener data which has all metrics
        df = get_all_screener_data()

        if df.empty:
            logger.warning("No sector data available")
            return pd.DataFrame()

        # Ensure required columns exist
        required_cols = ["company_id", "company_name", "sector", "industry"]
        for col in required_cols:
            if col not in df.columns:
                logger.error(f"Required column '{col}' missing from sector data")
                return pd.DataFrame()

        # Add sub_sector column if not present (use industry as sub_sector)
        if "sub_sector" not in df.columns:
            df["sub_sector"] = df["industry"].fillna("Unknown")
        else:
            df["sub_sector"] = df["sub_sector"].fillna(df["industry"]).fillna("Unknown")

        # Ensure market_cap exists
        if "market_cap" not in df.columns:
            df["market_cap"] = np.nan

        logger.info(f"Loaded sector data for {len(df)} companies")
        return df
    except Exception as e:
        logger.error(f"Failed to load sector data: {str(e)}", exc_info=True)
        return pd.DataFrame()


@st.cache_data(ttl=600, show_spinner=False)
def get_available_sectors(df: pd.DataFrame) -> List[str]:
    """
    Get list of available sectors from the data.

    Parameters
    ----------
    df : pd.DataFrame
        Sector data DataFrame.

    Returns
    -------
    List[str]
        Sorted list of sector names.
    """
    if df.empty or "sector" not in df.columns:
        return []

    sectors = df["sector"].dropna().astype(str).unique().tolist()
    sectors = sorted([s for s in sectors if s and s != "nan"])

    logger.info(f"Found {len(sectors)} sectors")
    return sectors


# =============================================================================
# DATA PROCESSING
# =============================================================================


def calculate_sector_medians(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate median KPIs for each sector.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with company data.

    Returns
    -------
    pd.DataFrame
        DataFrame with sector medians for each KPI metric.
    """
    try:
        if df.empty:
            return pd.DataFrame()

        # Define metrics to calculate medians for
        median_cols = {
            "roe": "Median ROE",
            "roce": "Median ROCE",
            "revenue_cagr_5yr": "Median Revenue CAGR",
            "debt_to_equity": "Median Debt to Equity",
            "net_profit_margin": "Median Net Profit Margin",
            "composite_quality_score": "Median Composite Score",
        }

        # Calculate medians by sector
        median_data = []
        for sector in df["sector"].unique():
            if pd.isna(sector) or sector == "nan":
                continue

            sector_df = df[df["sector"] == sector]
            row = {"Sector": sector}

            for col, display_name in median_cols.items():
                if col in sector_df.columns:
                    median_val = sector_df[col].median()
                    row[display_name] = median_val
                else:
                    row[display_name] = np.nan

            median_data.append(row)

        median_df = pd.DataFrame(median_data)
        logger.info(f"Calculated medians for {len(median_df)} sectors")

        return median_df
    except Exception as e:
        logger.error(f"Failed to calculate sector medians: {str(e)}", exc_info=True)
        return pd.DataFrame()


# =============================================================================
# VISUALIZATION
# =============================================================================


def build_bubble_chart(df: pd.DataFrame, sector: str) -> go.Figure:
    """
    Build interactive bubble chart for sector analysis.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with company data.
    sector : str
        Selected sector name.

    Returns
    -------
    go.Figure
        Plotly figure object.
    """
    try:
        # Filter to selected sector
        sector_df = df[df["sector"] == sector].copy()

        if sector_df.empty:
            logger.warning(f"No data available for sector: {sector}")
            return go.Figure()

        # Ensure required columns exist
        if "revenue" not in sector_df.columns:
            sector_df["revenue"] = np.nan
        if "roe" not in sector_df.columns:
            sector_df["roe"] = np.nan
        if "market_cap" not in sector_df.columns:
            sector_df["market_cap"] = np.nan
        if "sub_sector" not in sector_df.columns:
            sector_df["sub_sector"] = "Unknown"

        # Convert to numeric
        sector_df["revenue"] = pd.to_numeric(sector_df["revenue"], errors="coerce")
        sector_df["roe"] = pd.to_numeric(sector_df["roe"], errors="coerce")
        sector_df["market_cap"] = pd.to_numeric(
            sector_df["market_cap"], errors="coerce"
        )

        # Remove rows with missing critical data
        sector_df = sector_df.dropna(subset=["revenue", "roe"])

        if sector_df.empty:
            logger.warning(f"No valid data for bubble chart in sector: {sector}")
            return go.Figure()

        # Create bubble chart
        fig = px.scatter(
            sector_df,
            x="revenue",
            y="roe",
            size="market_cap",
            color="sub_sector",
            hover_name="company_name",
            hover_data={
                "company_name": True,
                "revenue": ":,.0f",
                "roe": ":.2f%",
                "market_cap": ":,.0f",
                "sector": True,
                "sub_sector": True,
            },
            color_discrete_sequence=SUB_SECTOR_COLORS,
            title=f"{sector} Sector Analysis - Revenue vs ROE",
            labels={
                "revenue": "Revenue (₹)",
                "roe": "ROE (%)",
                "market_cap": "Market Cap (₹)",
                "sub_sector": "Sub-Sector",
            },
            height=600,
        )

        # Update layout
        fig.update_layout(
            xaxis_title="Revenue (₹)",
            yaxis_title="ROE (%)",
            legend_title="Sub-Sector",
            hovermode="closest",
            template="plotly_white",
            xaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor="LightGray",
                showline=True,
                linewidth=1,
                linecolor="Gray",
                type="log",  # Log scale for better visualization
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
            showlegend=True,
        )

        # Update marker properties
        fig.update_traces(
            marker=dict(
                line=dict(width=1, color="DarkSlateGrey"),
                opacity=0.7,
            ),
            selector=dict(mode="markers"),
        )

        logger.info(
            f"Bubble chart built for sector: {sector} with {len(sector_df)} companies"
        )
        return fig
    except Exception as e:
        logger.error(
            f"Failed to build bubble chart for sector {sector}: {str(e)}", exc_info=True
        )
        return go.Figure()


def build_median_kpi_chart(median_df: pd.DataFrame, sector: str) -> go.Figure:
    """
    Build bar chart for sector median KPIs.

    Parameters
    ----------
    median_df : pd.DataFrame
        DataFrame with sector median KPIs.
    sector : str
        Selected sector name.

    Returns
    -------
    go.Figure
        Plotly figure object.
    """
    try:
        # Filter to selected sector
        sector_medians = median_df[median_df["Sector"] == sector]

        if sector_medians.empty:
            logger.warning(f"No median data available for sector: {sector}")
            return go.Figure()

        # Prepare data for plotting
        metrics = []
        values = []

        for display_name, col_name, _ in MEDIAN_KPI_METRICS:
            if display_name in sector_medians.columns:
                val = sector_medians[display_name].iloc[0]
                if pd.notna(val):
                    metrics.append(display_name)
                    values.append(val)

        if not metrics:
            logger.warning(f"No valid median KPI data for sector: {sector}")
            return go.Figure()

        # Create bar chart
        fig = go.Figure()

        # Color bars based on metric type
        bar_colors = []
        for metric in metrics:
            if (
                "CAGR" in metric
                or "ROE" in metric
                or "ROCE" in metric
                or "Margin" in metric
            ):
                bar_colors.append("#2E86AB")  # Blue for positive metrics
            elif "Debt" in metric:
                bar_colors.append("#C73E1D")  # Red for debt (lower is better)
            else:
                bar_colors.append("#A23B72")  # Purple for others

        fig.add_trace(
            go.Bar(
                x=metrics,
                y=values,
                marker=dict(
                    color=bar_colors, line=dict(color="DarkSlateGrey", width=1)
                ),
                text=[f"{v:.2f}" for v in values],
                textposition="outside",
                hovertemplate="<b>%{x}</b><br>Value: %{y:.2f}<extra></extra>",
            )
        )

        # Update layout
        fig.update_layout(
            title=f"{sector} - Sector Median KPIs",
            xaxis_title="KPI Metric",
            yaxis_title="Value",
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
        )

        logger.info(f"Median KPI chart built for sector: {sector}")
        return fig
    except Exception as e:
        logger.error(
            f"Failed to build median KPI chart for sector {sector}: {str(e)}",
            exc_info=True,
        )
        return go.Figure()


# =============================================================================
# SIDEBAR SELECTION
# =============================================================================


def render_sidebar(sectors: List[str]) -> Optional[str]:
    """
    Render sidebar with sector dropdown.

    Parameters
    ----------
    sectors : List[str]
        List of available sector names.

    Returns
    -------
    Optional[str]
        Selected sector name, or None if no selection.
    """
    st.sidebar.header("🏭 Sector Selection")

    if not sectors:
        st.sidebar.warning("No sectors available")
        return None

    selected_sector = st.sidebar.selectbox(
        "Select Sector",
        options=sectors,
        help="Choose a sector to analyze",
        index=0,
    )

    logger.info(f"Sector selected: {selected_sector}")
    return selected_sector


# =============================================================================
# MAIN
# =============================================================================


def main() -> None:
    """
    Render the Sector Analysis page.
    """
    logger.info("Sector Analysis page accessed")
    st.title("🏭 Sector Analysis")
    st.markdown("### Compare sectors and analyze sector-level financial metrics")
    st.markdown("---")

    # Load sector data
    with st.spinner("Loading sector data..."):
        sector_data = load_sector_data()

    if sector_data.empty:
        st.error("No sector data available. Please check the database.")
        logger.error("No sector data available")
        return

    # Get available sectors
    sectors = get_available_sectors(sector_data)

    if not sectors:
        st.error("No sectors found in the data.")
        logger.error("No sectors found")
        return

    # Sidebar selection
    selected_sector = render_sidebar(sectors)

    if selected_sector is None:
        st.info("👈 Select a sector from the sidebar to view analysis")
        return

    # Calculate sector medians
    with st.spinner("Calculating sector medians..."):
        median_df = calculate_sector_medians(sector_data)

    if median_df.empty:
        st.warning("Unable to calculate sector medians.")
        logger.warning("Median calculation failed")
        return

    # Display sector overview
    st.subheader(f"📊 {selected_sector} Sector Overview")

    # Count companies in sector
    sector_companies = sector_data[sector_data["sector"] == selected_sector]
    company_count = len(sector_companies)
    sub_sector_count = (
        sector_companies["sub_sector"].nunique() if not sector_companies.empty else 0
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Companies in Sector", company_count)
    with col2:
        st.metric("Sub-Sectors", sub_sector_count)
    with col3:
        if not sector_companies.empty and "market_cap" in sector_companies.columns:
            total_market_cap = sector_companies["market_cap"].sum()
            st.metric("Total Market Cap", f"₹{total_market_cap:,.0f}")
        else:
            st.metric("Total Market Cap", "N/A")

    st.markdown("---")

    # Bubble Chart
    st.subheader("🫧 Bubble Chart: Revenue vs ROE")
    st.markdown(
        f"**{selected_sector}** - Bubble size represents Market Cap, color represents Sub-Sector"
    )

    try:
        bubble_fig = build_bubble_chart(sector_data, selected_sector)

        if bubble_fig.data:
            st.plotly_chart(bubble_fig, use_container_width=True)
        else:
            st.warning(f"No data available for bubble chart in {selected_sector}")
    except Exception as e:
        logger.error(f"Failed to render bubble chart: {str(e)}", exc_info=True)
        st.error("Unable to render bubble chart.")

    st.markdown("---")

    # Median KPI Chart
    st.subheader("📊 Sector Median KPIs")
    st.markdown(f"**{selected_sector}** - Median values across key financial metrics")

    try:
        median_fig = build_median_kpi_chart(median_df, selected_sector)

        if median_fig.data:
            st.plotly_chart(median_fig, use_container_width=True)
        else:
            st.warning(f"No median KPI data available for {selected_sector}")
    except Exception as e:
        logger.error(f"Failed to render median KPI chart: {str(e)}", exc_info=True)
        st.error("Unable to render median KPI chart.")

    st.markdown("---")

    # Display sector median table
    with st.expander("📋 View Sector Median Data"):
        sector_medians = median_df[median_df["Sector"] == selected_sector]
        if not sector_medians.empty:
            # Transpose for better display
            display_df = sector_medians.T
            display_df.columns = ["Value"]
            display_df = display_df.drop("Sector", errors="ignore")

            st.dataframe(
                display_df,
                use_container_width=True,
            )
        else:
            st.warning("No median data available")

    # Display company list
    with st.expander(f"🏢 View Companies in {selected_sector}"):
        if not sector_companies.empty:
            display_cols = [
                "company_name",
                "sub_sector",
                "market_cap",
                "roe",
                "roce",
                "composite_quality_score",
            ]
            display_cols = [
                col for col in display_cols if col in sector_companies.columns
            ]

            st.dataframe(
                sector_companies[display_cols],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.warning("No companies in this sector")

    # Footer
    st.markdown("---")
    st.caption(
        "💡 **Tip:** Bubble chart shows Revenue vs ROE relationship. "
        "Larger bubbles indicate higher market cap. Different colors represent sub-sectors."
    )
    logger.info(
        f"Sector Analysis page rendered successfully for sector: {selected_sector}"
    )


if __name__ == "__main__":
    main()
