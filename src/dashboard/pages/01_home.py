"""
Home Screen - N100 Financial Intelligence Platform
Module 2 Implementation

This page provides a comprehensive dashboard overview with KPIs,
sector breakdown, and top quality companies.
"""

import logging
from typing import Optional

import pandas as pd
import plotly.express as px
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
    get_database_info,
)
from src.config.logging_config import get_logger

logger = get_logger(__name__)

# SIDEBAR - YEAR FILTER
# =============================================================================


def render_year_filter() -> int:
    """
    Render year selector in sidebar.

    Returns
    -------
    int
        Selected year
    """
    st.sidebar.header("📅 Year Filter")

    available_years = list(range(2019, 2025))  # 2019-2024

    selected_year = st.sidebar.selectbox(
        "Select Financial Year",
        options=available_years,
        index=len(available_years) - 1,  # Default to latest year
        help="Select a year to filter all analytics",
    )

    st.sidebar.markdown("---")
    st.sidebar.caption(f"**Selected Year:** {selected_year}")

    return selected_year


# =============================================================================
# KPI CALCULATION FUNCTIONS
# =============================================================================


@st.cache_data(ttl=600)
def calculate_home_kpis(year: int) -> dict:
    """
    Calculate summary KPIs for the home screen.

    Parameters
    ----------
    year : int
        Financial year to calculate KPIs for

    Returns
    -------
    dict
        Dictionary containing calculated KPIs
    """
    logger.info(f"Calculating home KPIs for year {year}")

    kpis = {
        "avg_roe": None,
        "median_pe": None,
        "median_debt_to_equity": None,
        "total_companies": 0,
        "median_revenue_cagr_5yr": None,
        "debt_free_companies": 0,
    }

    try:
        # Get all companies
        companies_df = get_companies()
        if companies_df.empty:
            logger.warning("No companies data available")
            return kpis

        kpis["total_companies"] = len(companies_df)

        # Get ratios for the selected year
        ratios_df = get_ratios(year=year)

        if ratios_df.empty:
            logger.warning(f"No ratios data available for year {year}")
            return kpis

        # Average ROE
        if "roe" in ratios_df.columns:
            roe_values = ratios_df["roe"].dropna()
            if not roe_values.empty:
                kpis["avg_roe"] = roe_values.mean()

        # Median PE Ratio
        if "pe_ratio" in ratios_df.columns:
            pe_values = ratios_df["pe_ratio"].dropna()
            pe_values = pe_values[pe_values > 0]  # Filter out negative/zero PE
            if not pe_values.empty:
                kpis["median_pe"] = pe_values.median()

        # Median Debt-to-Equity
        if "debt_equity" in ratios_df.columns:
            de_values = ratios_df["debt_equity"].dropna()
            if not de_values.empty:
                kpis["median_debt_to_equity"] = de_values.median()

        # Median Revenue CAGR 5 Year
        if "revenue_cagr_5yr" in ratios_df.columns:
            cagr_values = ratios_df["revenue_cagr_5yr"].dropna()
            if not cagr_values.empty:
                kpis["median_revenue_cagr_5yr"] = cagr_values.median()

        # Debt-free companies count
        if "debt_equity" in ratios_df.columns:
            debt_free = ratios_df[ratios_df["debt_equity"] == 0]
            kpis["debt_free_companies"] = len(debt_free)

        logger.info(f"KPIs calculated successfully: {kpis}")
        return kpis

    except Exception as e:
        logger.error(f"Error calculating KPIs: {str(e)}", exc_info=True)
        return kpis


@st.cache_data(ttl=600)
def get_sector_breakdown(year: int) -> pd.DataFrame:
    """
    Get sector breakdown with company counts and percentages.

    Parameters
    ----------
    year : int
        Financial year

    Returns
    -------
    pd.DataFrame
        DataFrame with sector, company_count, and percentage
    """
    logger.info(f"Getting sector breakdown for year {year}")

    try:
        companies_df = get_companies()

        if companies_df.empty or "sector" not in companies_df.columns:
            logger.warning("No sector data available")
            return pd.DataFrame()

        # Count companies by sector
        sector_counts = companies_df["sector"].value_counts().reset_index()
        sector_counts.columns = ["Sector", "Company Count"]

        # Calculate percentage
        total = sector_counts["Company Count"].sum()
        sector_counts["Percentage"] = (
            sector_counts["Company Count"] / total * 100
        ).round(2)

        logger.info(f"Sector breakdown calculated: {len(sector_counts)} sectors")
        return sector_counts

    except Exception as e:
        logger.error(f"Error getting sector breakdown: {str(e)}", exc_info=True)
        return pd.DataFrame()


@st.cache_data(ttl=600)
def get_top_quality_companies(year: int, top_n: int = 5) -> pd.DataFrame:
    """
    Get top quality companies based on composite score.

    Parameters
    ----------
    year : int
        Financial year
    top_n : int, optional
        Number of top companies to return, by default 5

    Returns
    -------
    pd.DataFrame
        DataFrame with top quality companies
    """
    logger.info(f"Getting top {top_n} quality companies for year {year}")

    try:
        # Get ratios data
        ratios_df = get_ratios(year=year)

        if ratios_df.empty:
            logger.warning(f"No ratios data available for year {year}")
            return pd.DataFrame()

        # Get companies data for names and sectors
        companies_df = get_companies()

        # Calculate composite quality score
        # Components: ROE, Revenue CAGR 5Y, Debt-to-Equity (inverted)
        required_cols = ["ticker", "roe", "revenue_cagr_5yr", "debt_equity"]

        if not all(col in ratios_df.columns for col in required_cols):
            logger.warning("Required columns not found in ratios data")
            return pd.DataFrame()

        # Filter companies with at least some data
        quality_df = ratios_df[required_cols].copy()
        quality_df = quality_df.dropna(subset=["roe", "revenue_cagr_5yr"], how="all")

        if quality_df.empty:
            logger.warning("No companies with quality metrics available")
            return pd.DataFrame()

        # Normalize scores to 0-100
        # ROE score (higher is better)
        if "roe" in quality_df.columns:
            roe_min, roe_max = quality_df["roe"].min(), quality_df["roe"].max()
            if roe_max > roe_min:
                quality_df["roe_score"] = (
                    (quality_df["roe"] - roe_min) / (roe_max - roe_min) * 100
                ).fillna(50)
            else:
                quality_df["roe_score"] = 50.0
        else:
            quality_df["roe_score"] = 50.0

        # Revenue CAGR score (higher is better)
        if "revenue_cagr_5yr" in quality_df.columns:
            cagr_min, cagr_max = (
                quality_df["revenue_cagr_5yr"].min(),
                quality_df["revenue_cagr_5yr"].max(),
            )
            if cagr_max > cagr_min:
                quality_df["cagr_score"] = (
                    (quality_df["revenue_cagr_5yr"] - cagr_min)
                    / (cagr_max - cagr_min)
                    * 100
                ).fillna(50)
            else:
                quality_df["cagr_score"] = 50.0
        else:
            quality_df["cagr_score"] = 50.0

        # Debt-to-Equity score (lower is better, so invert)
        if "debt_equity" in quality_df.columns:
            de_values = quality_df["debt_equity"].fillna(
                quality_df["debt_equity"].median()
            )
            de_max = de_values.max()
            if de_max > 0:
                quality_df["de_score"] = ((de_max - de_values) / de_max * 100).clip(
                    0, 100
                )
            else:
                quality_df["de_score"] = 100.0
        else:
            quality_df["de_score"] = 50.0

        # Composite score (weighted average)
        quality_df["composite_score"] = (
            quality_df["roe_score"] * 0.40
            + quality_df["cagr_score"] * 0.35
            + quality_df["de_score"] * 0.25
        )

        # Get top N companies
        top_companies = quality_df.nlargest(top_n, "composite_score")

        # Merge with company info
        if not companies_df.empty:
            top_companies = top_companies.merge(
                companies_df[["ticker", "name", "sector"]], on="ticker", how="left"
            )

        # Select and rename columns
        result_columns = [
            "ticker",
            "name",
            "sector",
            "composite_score",
            "roe",
            "revenue_cagr_5yr",
        ]
        result_columns = [col for col in result_columns if col in top_companies.columns]

        result = top_companies[result_columns].copy()

        # Rename columns for display
        column_mapping = {
            "ticker": "Ticker",
            "name": "Company Name",
            "sector": "Sector",
            "composite_score": "Composite Score",
            "roe": "ROE (%)",
            "revenue_cagr_5yr": "Revenue CAGR 5Y (%)",
        }
        result = result.rename(columns=column_mapping)

        # Round numeric columns
        for col in ["Composite Score", "ROE (%)", "Revenue CAGR 5Y (%)"]:
            if col in result.columns:
                result[col] = result[col].round(2)

        logger.info(f"Top {top_n} quality companies identified")
        return result

    except Exception as e:
        logger.error(f"Error getting top quality companies: {str(e)}", exc_info=True)
        return pd.DataFrame()


# =============================================================================
# UI RENDERING FUNCTIONS
# =============================================================================


def render_kpi_cards(kpis: dict) -> None:
    """
    Render KPI cards section.

    Parameters
    ----------
    kpis : dict
        Dictionary containing calculated KPIs
    """
    st.header("📊 Summary KPIs")
    st.markdown("---")

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        avg_roe = kpis.get("avg_roe")
        if avg_roe is not None:
            st.metric(
                label="Average ROE",
                value=f"{avg_roe:.2f}%",
                help="Average Return on Equity across all companies",
            )
        else:
            st.metric(label="Average ROE", value="N/A")

    with col2:
        median_pe = kpis.get("median_pe")
        if median_pe is not None:
            st.metric(
                label="Median PE",
                value=f"{median_pe:.1f}x",
                help="Median Price-to-Earnings ratio",
            )
        else:
            st.metric(label="Median PE", value="N/A")

    with col3:
        median_de = kpis.get("median_debt_to_equity")
        if median_de is not None:
            st.metric(
                label="Median Debt-to-Equity",
                value=f"{median_de:.2f}",
                help="Median Debt-to-Equity ratio",
            )
        else:
            st.metric(label="Median Debt-to-Equity", value="N/A")

    with col4:
        total = kpis.get("total_companies", 0)
        st.metric(
            label="Total Companies",
            value=f"{total}",
            help="Total number of companies in database",
        )

    with col5:
        median_cagr = kpis.get("median_revenue_cagr_5yr")
        if median_cagr is not None:
            st.metric(
                label="Median Revenue CAGR 5Y",
                value=f"{median_cagr:.2f}%",
                help="Median 5-year Revenue CAGR",
            )
        else:
            st.metric(label="Median Revenue CAGR 5Y", value="N/A")

    with col6:
        debt_free = kpis.get("debt_free_companies", 0)
        st.metric(
            label="Debt-Free Companies",
            value=f"{debt_free}",
            help="Number of companies with zero debt",
        )

    st.markdown("---")


def render_sector_breakdown(sector_df: pd.DataFrame) -> None:
    """
    Render sector breakdown donut chart.

    Parameters
    ----------
    sector_df : pd.DataFrame
        DataFrame with sector breakdown data
    """
    st.header("🏭 Sector Breakdown")
    st.markdown("---")

    if sector_df.empty:
        st.warning("No sector data available")
        return

    col1, col2 = st.columns([2, 1])

    with col1:
        # Create donut chart
        fig = px.pie(
            sector_df,
            values="Company Count",
            names="Sector",
            hole=0.4,
            title="Sector Distribution",
            color_discrete_sequence=px.colors.qualitative.Set3,
        )

        # Update layout
        fig.update_traces(
            textposition="inside",
            textinfo="percent+label",
            hovertemplate="<b>%{label}</b><br>"
            + "Companies: %{value}<br>"
            + "Percentage: %{percent}<br>"
            + "<extra></extra>",
        )

        fig.update_layout(
            showlegend=True,
            legend=dict(
                orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02
            ),
            height=500,
            margin=dict(l=20, r=20, t=40, b=20),
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Sector Details")
        st.markdown("---")

        # Display sector table
        display_df = sector_df.copy()
        display_df = display_df.sort_values("Company Count", ascending=False)

        st.dataframe(
            display_df,
            column_config={
                "Sector": st.column_config.TextColumn("Sector", width="medium"),
                "Company Count": st.column_config.NumberColumn("Count", width="small"),
                "Percentage": st.column_config.NumberColumn(
                    "%", width="small", format="%.2f"
                ),
            },
            hide_index=True,
            use_container_width=True,
        )


def render_top_quality_companies(top_df: pd.DataFrame) -> None:
    """
    Render top quality companies section.

    Parameters
    ----------
    top_df : pd.DataFrame
        DataFrame with top quality companies
    """
    st.header("⭐ Top Quality Companies")
    st.markdown("---")

    if top_df.empty:
        st.warning("No quality data available")
        return

    st.markdown("### Top 5 Companies by Composite Quality Score")
    st.caption("Based on ROE, Revenue CAGR, and Debt-to-Equity metrics")

    # Display dataframe with custom styling
    st.dataframe(
        top_df,
        column_config={
            "Ticker": st.column_config.TextColumn("Ticker", width="small"),
            "Company Name": st.column_config.TextColumn("Company Name", width="medium"),
            "Sector": st.column_config.TextColumn("Sector", width="medium"),
            "Composite Score": st.column_config.NumberColumn(
                "Score", width="small", format="%.2f"
            ),
            "ROE (%)": st.column_config.NumberColumn(
                "ROE", width="small", format="%.2f"
            ),
            "Revenue CAGR 5Y (%)": st.column_config.NumberColumn(
                "CAGR", width="small", format="%.2f"
            ),
        },
        hide_index=True,
        use_container_width=True,
    )


def render_quick_stats() -> None:
    """Render quick stats section with database and application information."""
    st.header("ℹ️ Quick Stats")
    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)

    try:
        db_info = get_database_info()

        with col1:
            if db_info.get("exists"):
                st.success("✅ Database Status")
                st.caption("Connected")
            else:
                st.error("� Database Status")
                st.caption("Not Found")

        with col2:
            companies_df = get_companies()
            count = len(companies_df) if not companies_df.empty else 0
            st.metric(
                label="Companies Loaded",
                value=f"{count}",
                help="Total companies in database",
            )

        with col3:
            # Get latest financial year from ratios
            try:
                ratios_df = get_ratios()
                if not ratios_df.empty and "year" in ratios_df.columns:
                    latest_year = int(ratios_df["year"].max())
                else:
                    latest_year = "N/A"
            except:
                latest_year = "N/A"

            st.metric(
                label="Latest Financial Year",
                value=f"{latest_year}",
                help="Most recent year with financial data",
            )

        with col4:
            st.metric(
                label="Dashboard Version",
                value="2.0.0",
                help="Current dashboard version",
            )

    except Exception as e:
        logger.error(f"Error rendering quick stats: {str(e)}", exc_info=True)
        st.error("Unable to load statistics")


# =============================================================================
# MAIN PAGE FUNCTION
# =============================================================================


def main() -> None:
    """
    Main function to render the home screen.
    """
    logger.info("Home screen accessed")

    # Page header
    st.title("📊 N100 Financial Intelligence Dashboard")
    st.markdown("### Financial Analytics Platform for Nifty 100 Companies")
    st.markdown("---")

    # Render year filter in sidebar
    selected_year = render_year_filter()

    # Calculate KPIs for selected year
    with st.spinner(f"Loading analytics for {selected_year}..."):
        kpis = calculate_home_kpis(selected_year)
        sector_df = get_sector_breakdown(selected_year)
        top_companies_df = get_top_quality_companies(selected_year, top_n=5)

    # Render sections
    render_kpi_cards(kpis)
    render_sector_breakdown(sector_df)
    render_top_quality_companies(top_companies_df)
    render_quick_stats()

    # Footer
    st.markdown("---")
    st.caption(
        "💡 **Tip:** Use the year filter in the sidebar to view data for different financial years. "
        "All analytics are cached for optimal performance."
    )

    logger.info(f"Home screen rendered successfully for year {selected_year}")


if __name__ == "__main__":
    main()
