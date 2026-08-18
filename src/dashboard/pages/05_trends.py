"""
Trend Analysis Page - N100 Financial Intelligence Platform
Sprint 4 - Module 4 Implementation

Provides interactive trend analysis for Nifty 100 companies with multi-metric
visualization, year-over-year calculations, and 10-year historical data.

Features
--------
1. Company search with autocomplete
2. Year selector
3. Multi-metric selector (up to 3 metrics)
4. Interactive Plotly line chart with YoY annotations
5. Hover tooltips with Year, Value, and YoY %
6. Zoom, pan, legend, responsive design
"""

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.dashboard.utils.db import (
    get_companies,
    get_ratios,
    get_pl,
    get_cf,
    get_bs,
)
from src.config.logging_config import get_logger

logger = get_logger(__name__)

# Available metrics for trend analysis
TREND_METRICS = [
    ("Revenue CAGR", "financial_ratios", "revenue_cagr_5yr", "{:.2f}%"),
    ("PAT CAGR", "financial_ratios", "pat_cagr_5yr", "{:.2f}%"),
    ("EPS", "profit_loss", "eps", "{:.2f}"),
    ("Free Cash Flow", "cash_flow", "free_cash_flow", "{:,.0f}"),
]

# Color palette for multiple metrics
METRIC_COLORS = [
    "#2E86AB",  # Blue
    "#A23B72",  # Purple
    "#F18F01",  # Orange
    "#C73E1D",  # Red
    "#3B1F2B",  # Dark
    "#95C623",  # Green
]

# =============================================================================
# DATA LOADING (cached)
# =============================================================================

@st.cache_data(ttl=600, show_spinner=False)
def load_companies() -> pd.DataFrame:
    """
    Load all companies for search/selection.

    Returns
    -------
    pd.DataFrame
        DataFrame with company_id, company_name, sector, industry.
    """
    try:
        df = get_companies()
        if df.empty:
            logger.warning("No companies found in database")
            return pd.DataFrame()

        # Standardize column names
        df = df.rename(columns={
            "ticker": "company_id",
            "name": "company_name",
        })

        logger.info(f"Loaded {len(df)} companies for trend analysis")
        return df[["company_id", "company_name", "sector", "industry"]]
    except Exception as e:
        logger.error(f"Failed to load companies: {str(e)}", exc_info=True)
        return pd.DataFrame()


@st.cache_data(ttl=600, show_spinner=False)
def load_financial_data(company_id: str) -> Dict[str, pd.DataFrame]:
    """
    Load all financial data for a company from multiple tables.

    Parameters
    ----------
    company_id : str
        Company identifier.

    Returns
    -------
    Dict[str, pd.DataFrame]
        Dictionary with keys: 'profit_loss', 'ratios', 'cash_flow', 'balance_sheet'.
    """
    try:
        data = {}

        # Load Profit & Loss
        pl_df = get_pl(company_id)
        if not pl_df.empty:
            data["profit_loss"] = pl_df
        else:
            data["profit_loss"] = pd.DataFrame()

        # Load Financial Ratios
        ratios_df = get_ratios(company_id)
        if not ratios_df.empty:
            data["ratios"] = ratios_df
        else:
            data["ratios"] = pd.DataFrame()

        # Load Cash Flow
        cf_df = get_cf(company_id)
        if not cf_df.empty:
            data["cash_flow"] = cf_df
        else:
            data["cash_flow"] = pd.DataFrame()

        # Load Balance Sheet
        bs_df = get_bs(company_id)
        if not bs_df.empty:
            data["balance_sheet"] = bs_df
        else:
            data["balance_sheet"] = pd.DataFrame()

        logger.info(
            f"Loaded financial data for {company_id}: "
            f"PL={len(data['profit_loss'])}, "
            f"Ratios={len(data['ratios'])}, "
            f"CF={len(data['cash_flow'])}, "
            f"BS={len(data['balance_sheet'])}"
        )

        return data
    except Exception as e:
        logger.error(f"Failed to load financial data for {company_id}: {str(e)}", exc_info=True)
        return {
            "profit_loss": pd.DataFrame(),
            "ratios": pd.DataFrame(),
            "cash_flow": pd.DataFrame(),
            "balance_sheet": pd.DataFrame(),
        }


# =============================================================================
# DATA PROCESSING
# =============================================================================

def prepare_trend_data(
    financial_data: Dict[str, pd.DataFrame],
    metric_name: str,
    source_table: str,
    column_name: str,
) -> pd.DataFrame:
    """
    Prepare time-series data for a specific metric.

    Parameters
    ----------
    financial_data : Dict[str, pd.DataFrame]
        Dictionary of financial data tables.
    metric_name : str
        Display name of the metric.
    source_table : str
        Source table name ('profit_loss', 'ratios', 'cash_flow', 'balance_sheet').
    column_name : str
        Column name in the source table.

    Returns
    -------
    pd.DataFrame
        DataFrame with 'year' and 'value' columns, sorted by year ascending.
    """
    try:
        # Map source table to data key
        table_map = {
            "profit_loss": "profit_loss",
            "financial_ratios": "ratios",
            "cash_flow": "cash_flow",
            "balance_sheet": "balance_sheet",
        }

        data_key = table_map.get(source_table)
        if not data_key or data_key not in financial_data:
            logger.warning(f"Source table '{source_table}' not found in financial data")
            return pd.DataFrame()

        df = financial_data[data_key]
        if df.empty:
            logger.warning(f"Empty DataFrame for source table '{source_table}'")
            return pd.DataFrame()

        # Check if column exists
        if column_name not in df.columns:
            logger.warning(f"Column '{column_name}' not found in {source_table}")
            return pd.DataFrame()

        # Extract year and value
        if "year" not in df.columns:
            logger.warning(f"'year' column not found in {source_table}")
            return pd.DataFrame()

        # Create trend dataframe
        trend_df = df[["year", column_name]].copy()
        trend_df.columns = ["year", "value"]

        # Convert to numeric, coercing errors to NaN
        trend_df["value"] = pd.to_numeric(trend_df["value"], errors="coerce")

        # Drop NaN values
        trend_df = trend_df.dropna()

        # Convert year to int
        trend_df["year"] = pd.to_numeric(trend_df["year"], errors="coerce").astype(int)

        # Sort by year ascending
        trend_df = trend_df.sort_values("year").reset_index(drop=True)

        logger.info(
            f"Prepared trend data for {metric_name}: {len(trend_df)} data points, "
            f"years {trend_df['year'].min()}-{trend_df['year'].max() if not trend_df.empty else 'N/A'}"
        )

        return trend_df
    except Exception as e:
        logger.error(f"Failed to prepare trend data for {metric_name}: {str(e)}", exc_info=True)
        return pd.DataFrame()


def calculate_yoy(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate year-over-year percentage change.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with 'year' and 'value' columns.

    Returns
    -------
    pd.DataFrame
        DataFrame with added 'yoy_pct' column.
    """
    if df.empty or len(df) < 2:
        return df

    df = df.copy()
    df["yoy_pct"] = df["value"].pct_change() * 100

    # Round to 2 decimal places
    df["yoy_pct"] = df["yoy_pct"].round(2)

    return df


# =============================================================================
# VISUALIZATION
# =============================================================================

def build_trend_chart(
    trend_data: Dict[str, pd.DataFrame],
    selected_metrics: List[Tuple[str, str, str, str]],
) -> go.Figure:
    """
    Build interactive Plotly line chart for trend analysis.

    Parameters
    ----------
    trend_data : Dict[str, pd.DataFrame]
        Dictionary mapping metric keys to DataFrames with 'year' and 'value' columns.
    selected_metrics : List[Tuple[str, str, str, str]]
        List of (display_name, source_table, column_name, format_string) tuples.

    Returns
    -------
    go.Figure
        Plotly figure object.
    """
    try:
        fig = go.Figure()

        # Add a trace for each selected metric
        for idx, (metric_name, _, _, _) in enumerate(selected_metrics):
            metric_key = metric_name.lower().replace(" ", "_")

            if metric_key not in trend_data or trend_data[metric_key].empty:
                logger.warning(f"No data available for metric: {metric_name}")
                continue

            df = trend_data[metric_key]
            color = METRIC_COLORS[idx % len(METRIC_COLORS)]

            # Add line trace
            fig.add_trace(
                go.Scatter(
                    x=df["year"],
                    y=df["value"],
                    mode="lines+markers",
                    name=metric_name,
                    line=dict(color=color, width=3),
                    marker=dict(size=8, color=color),
                    hovertemplate=(
                        f"<b>{metric_name}</b><br>"
                        "Year: %{x}<br>"
                        "Value: %{y:,.2f}<br>"
                        "<extra></extra>"
                    ),
                )
            )

            # Add YoY % annotations if available
            if "yoy_pct" in df.columns and not df["yoy_pct"].isna().all():
                # Add annotations for YoY % (only for non-null values)
                for _, row in df.iterrows():
                    if pd.notna(row["yoy_pct"]):
                        yoy_val = row["yoy_pct"]
                        # Color code: green for positive, red for negative
                        yoy_color = "#2E7D32" if yoy_val >= 0 else "#C62828"
                        yoy_text = f"+{yoy_val:.1f}%" if yoy_val >= 0 else f"{yoy_val:.1f}%"

                        fig.add_annotation(
                            x=row["year"],
                            y=row["value"],
                            text=yoy_text,
                            showarrow=False,
                            yshift=10,
                            font=dict(size=9, color=yoy_color),
                            xanchor="center",
                        )

        # Update layout
        fig.update_layout(
            title="Financial Metrics Trend Analysis (10-Year Historical Data)",
            xaxis_title="Year",
            yaxis_title="Value",
            hovermode="x unified",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5,
            ),
            height=600,
            margin=dict(l=60, r=60, t=80, b=120),
            template="plotly_white",
            xaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor="LightGray",
                showline=True,
                linewidth=1,
                linecolor="Gray",
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

        # Enable zoom and pan
        fig.update_xaxes(rangeslider_visible=False)

        logger.info(f"Trend chart built successfully with {len(selected_metrics)} metrics")
        return fig
    except Exception as e:
        logger.error(f"Failed to build trend chart: {str(e)}", exc_info=True)
        return go.Figure()


# =============================================================================
# SIDEBAR SELECTION
# =============================================================================

def render_sidebar(companies_df: pd.DataFrame) -> Tuple[Optional[str], Optional[str], Optional[List[Tuple[str, str, str, str]]]]:
    """
    Render sidebar with company search, year selector, and metric selector.

    Parameters
    ----------
    companies_df : pd.DataFrame
        DataFrame with company information.

    Returns
    -------
    Tuple[Optional[str], Optional[str], Optional[List[Tuple[str, str, str, str]]]]
        (selected_company_id, selected_company_name, selected_metrics)
    """
    st.sidebar.header("🔍 Company Selection")

    # Company search
    if companies_df.empty:
        st.sidebar.warning("No companies available")
        return None, None, None

    company_names = companies_df["company_name"].dropna().astype(str).tolist()
    company_names = sorted(set(company_names))

    # Search/autocomplete
    search_query = st.sidebar.text_input(
        "Search Company",
        placeholder="Type to search...",
        help="Search for a company by name (case-insensitive)",
    ).strip().lower()

    # Filter companies
    if search_query:
        filtered_names = [name for name in company_names if search_query in name.lower()]
    else:
        filtered_names = company_names

    if not filtered_names:
        st.sidebar.info("No companies match your search")
        return None, None, None

    selected_name = st.sidebar.selectbox(
        "Select Company",
        options=filtered_names,
        help="Choose a company to analyze",
    )

    # Get company_id
    try:
        selected_id = companies_df.loc[
            companies_df["company_name"] == selected_name, "company_id"
        ].iloc[0]
    except (KeyError, IndexError):
        st.sidebar.warning("Selected company not found")
        return None, None, None

    st.sidebar.markdown("---")
    st.sidebar.header("📊 Metric Selection")

    # Metric selector (multi-select, max 3)
    metric_options = [metric[0] for metric in TREND_METRICS]
    selected_metrics = st.sidebar.multiselect(
        "Select Metrics (max 3)",
        options=metric_options,
        default=["Revenue CAGR", "PAT CAGR"],
        max_selections=3,
        help="Select up to 3 metrics to display on the chart",
    )

    if not selected_metrics:
        st.sidebar.warning("Please select at least one metric")
        return selected_id, selected_name, None

    # Get metric details
    selected_metric_details = [
        metric for metric in TREND_METRICS if metric[0] in selected_metrics
    ]

    return selected_id, selected_name, selected_metric_details


# =============================================================================
# MAIN
# =============================================================================

def main() -> None:
    """
    Render the Trend Analysis page.
    """
    logger.info("Trend Analysis page accessed")
    st.title("📈 Trend Analysis")
    st.markdown("### Analyze financial metrics trends over time for Nifty 100 companies")
    st.markdown("---")

    # Load companies
    companies_df = load_companies()

    if companies_df.empty:
        st.error("No companies available. Please check the database.")
        logger.error("No companies available for trend analysis")
        return

    # Sidebar selection
    selected_id, selected_name, selected_metrics = render_sidebar(companies_df)

    if selected_id is None or selected_name is None:
        st.info("👈 Select a company from the sidebar to view trend analysis")
        return

    if not selected_metrics:
        st.info("👈 Select at least one metric from the sidebar")
        return

    # Load financial data
    with st.spinner(f"Loading financial data for {selected_name}..."):
        financial_data = load_financial_data(selected_id)

    # Check if any data is available
    total_records = sum(len(df) for df in financial_data.values())
    if total_records == 0:
        st.warning(f"No financial data available for {selected_name}")
        logger.warning(f"No financial data for company {selected_id}")
        return

    # Prepare trend data for selected metrics
    trend_data = {}
    for metric_name, source_table, column_name, _ in selected_metrics:
        metric_key = metric_name.lower().replace(" ", "_")
        df = prepare_trend_data(financial_data, metric_name, source_table, column_name)

        if not df.empty:
            # Calculate YoY
            df = calculate_yoy(df)
            trend_data[metric_key] = df

    if not trend_data:
        st.warning(f"No trend data available for the selected metrics")
        logger.warning(f"No trend data for selected metrics for company {selected_id}")
        return

    # Display data availability info
    all_years = set()
    for df in trend_data.values():
        if not df.empty:
            all_years.update(df["year"].tolist())

    if all_years:
        min_year = min(all_years)
        max_year = max(all_years)
        year_count = len(all_years)

        if year_count < 10:
            st.info(f"📊 Data available for {year_count} years ({min_year} - {max_year})")
        else:
            st.success(f"📊 Data available for {year_count} years ({min_year} - {max_year})")

    # Build and display trend chart
    try:
        fig = build_trend_chart(trend_data, selected_metrics)

        if fig.data:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Unable to generate chart for the selected metrics")
    except Exception as e:
        logger.error(f"Failed to render trend chart: {str(e)}", exc_info=True)
        st.error("Unable to render trend chart. Please try different metrics.")

    st.markdown("---")

    # Display data tables
    with st.expander("📋 View Raw Data"):
        for metric_name, _, _, _ in selected_metrics:
            metric_key = metric_name.lower().replace(" ", "_")
            if metric_key in trend_data and not trend_data[metric_key].empty:
                st.subheader(metric_name)
                st.dataframe(
                    trend_data[metric_key],
                    use_container_width=True,
                    hide_index=True,
                )

    # Footer
    st.markdown("---")
    st.caption(
        "💡 **Tip:** Select different metrics to compare trends. "
        "YoY % shows year-over-year growth/decline. Green = positive growth, Red = decline."
    )
    logger.info(f"Trend Analysis page rendered successfully for {selected_id}")


if __name__ == "__main__":
    main()