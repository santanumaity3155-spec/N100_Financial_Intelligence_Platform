"""
Company Profile Screen - N100 Financial Intelligence Platform
Module 2 Implementation

This page provides detailed company profiles with financial metrics,
charts, and analysis for individual Nifty 100 companies.
"""

import logging
from typing import Optional, Dict, Any, List, Tuple

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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
    get_bs,
    get_cf,
)
from src.config.logging_config import get_logger

logger = get_logger(__name__)

# CONSTANTS
# =============================================================================

# KPI metrics to display
KPI_METRICS = [
    ("ROE", "roe", "%"),
    ("ROCE", "roce", "%"),
    ("Net Profit Margin", "net_profit_margin", "%"),
    ("Debt-to-Equity", "debt_to_equity", ""),
    ("Revenue CAGR 5Y", "revenue_cagr_5yr", "%"),
    ("Latest FCF", "free_cash_flow", "₹ Cr"),
]

# =============================================================================
# DATA RETRIEVAL FUNCTIONS
# =============================================================================

@st.cache_data(ttl=600)
def get_company_list() -> pd.DataFrame:
    """
    Get list of all companies for search/autocomplete.

    Returns
    -------
    pd.DataFrame
        DataFrame with ticker and company name
    """
    try:
        companies_df = get_companies()

        if companies_df.empty:
            return pd.DataFrame()

        # Select relevant columns
        if "ticker" in companies_df.columns and "name" in companies_df.columns:
            result = companies_df[["ticker", "name"]].copy()
            result = result.sort_values("ticker")
            return result

        return pd.DataFrame()

    except Exception as e:
        logger.error(f"Error getting company list: {str(e)}", exc_info=True)
        return pd.DataFrame()


@st.cache_data(ttl=600)
def get_company_profile(ticker: str) -> Optional[Dict[str, Any]]:
    """
    Get company profile information.

    Parameters
    ----------
    ticker : str
        Company ticker symbol

    Returns
    -------
    Optional[Dict[str, Any]]
        Dictionary with company profile data
    """
    logger.info(f"Getting company profile for {ticker}")

    try:
        companies_df = get_companies()

        if companies_df.empty:
            return None

        # Filter by ticker (case-insensitive)
        company_data = companies_df[
            companies_df["ticker"].str.upper() == ticker.upper()
        ]

        if company_data.empty:
            return None

        # Convert to dictionary
        profile = company_data.iloc[0].to_dict()

        # Clean up NaN values
        for key, value in profile.items():
            if pd.isna(value):
                profile[key] = None

        return profile

    except Exception as e:
        logger.error(f"Error getting company profile for {ticker}: {str(e)}", exc_info=True)
        return None


@st.cache_data(ttl=600)
def get_company_kpis(ticker: str) -> Dict[str, Optional[float]]:
    """
    Get latest KPIs for a company.

    Parameters
    ----------
    ticker : str
        Company ticker symbol

    Returns
    -------
    Dict[str, Optional[float]]
        Dictionary with KPI values
    """
    logger.info(f"Getting KPIs for {ticker}")

    kpis = {metric[0]: None for metric in KPI_METRICS}

    try:
        ratios_df = get_ratios(ticker=ticker)

        if ratios_df.empty:
            return kpis

        # Get latest year data
        latest_year = ratios_df["year"].max() if "year" in ratios_df.columns else None

        if latest_year is not None:
            latest_ratios = ratios_df[ratios_df["year"] == latest_year].iloc[0]
        else:
            latest_ratios = ratios_df.iloc[0]

        # Extract KPIs
        for display_name, column_name, _ in KPI_METRICS:
            if column_name in latest_ratios:
                value = latest_ratios[column_name]
                # Handle NaN/None
                if pd.isna(value):
                    kpis[display_name] = None
                else:
                    kpis[display_name] = float(value)

        return kpis

    except Exception as e:
        logger.error(f"Error getting KPIs for {ticker}: {str(e)}", exc_info=True)
        return kpis


@st.cache_data(ttl=600)
def get_revenue_data(ticker: str) -> pd.DataFrame:
    """
    Get revenue and profit data for last 10 years.

    Parameters
    ----------
    ticker : str
        Company ticker symbol

    Returns
    -------
    pd.DataFrame
        DataFrame with year, revenue, and net profit
    """
    logger.info(f"Getting revenue data for {ticker}")

    try:
        pl_df = get_pl(ticker=ticker)

        if pl_df.empty:
            return pd.DataFrame()

        # Select relevant columns
        required_cols = ["year", "revenue", "net_profit"]

        if not all(col in pl_df.columns for col in required_cols):
            logger.warning(f"Required columns not found in P&L data for {ticker}")
            return pd.DataFrame()

        # Select and sort
        revenue_df = pl_df[required_cols].copy()
        revenue_df = revenue_df.sort_values("year", ascending=True)

        # Take last 10 years
        revenue_df = revenue_df.tail(10)

        # Clean up NaN values
        revenue_df = revenue_df.fillna(0)

        return revenue_df

    except Exception as e:
        logger.error(f"Error getting revenue data for {ticker}: {str(e)}", exc_info=True)
        return pd.DataFrame()


@st.cache_data(ttl=600)
def get_roe_roce_data(ticker: str) -> pd.DataFrame:
    """
    Get ROE and ROCE data for last 10 years.

    Parameters
    ----------
    ticker : str
        Company ticker symbol

    Returns
    -------
    pd.DataFrame
        DataFrame with year, ROE, and ROCE
    """
    logger.info(f"Getting ROE/ROCE data for {ticker}")

    try:
        ratios_df = get_ratios(ticker=ticker)

        if ratios_df.empty:
            return pd.DataFrame()

        # Select relevant columns
        required_cols = ["year", "roe", "roce"]

        if not all(col in ratios_df.columns for col in required_cols):
            logger.warning(f"Required columns not found in ratios data for {ticker}")
            return pd.DataFrame()

        # Select and sort
        roe_roce_df = ratios_df[required_cols].copy()
        roe_roce_df = roe_roce_df.sort_values("year", ascending=True)

        # Take last 10 years
        roe_roce_df = roe_roce_df.tail(10)

        return roe_roce_df

    except Exception as e:
        logger.error(f"Error getting ROE/ROCE data for {ticker}: {str(e)}", exc_info=True)
        return pd.DataFrame()


@st.cache_data(ttl=600)
def get_pros_cons(ticker: str) -> Tuple[List[str], List[str]]:
    """
    Get pros and cons for a company.

    Parameters
    ----------
    ticker : str
        Company ticker symbol

    Returns
    -------
    Tuple[List[str], List[str]]
        Tuple of (pros_list, cons_list)
    """
    logger.info(f"Getting pros/cons for {ticker}")

    pros = []
    cons = []

    try:
        # Try to get from pros_cons table
        # For now, generate based on available data
        ratios_df = get_ratios(ticker=ticker)

        if ratios_df.empty:
            return pros, cons

        # Get latest ratios
        latest = ratios_df.iloc[0]

        # Analyze pros
        if latest.get("roe", 0) and latest.get("roe", 0) > 15:
            pros.append("Strong ROE (>15%)")

        if latest.get("roce", 0) and latest.get("roce", 0) > 15:
            pros.append("Excellent ROCE (>15%)")

        if latest.get("revenue_cagr_5yr", 0) and latest.get("revenue_cagr_5yr", 0) > 10:
            pros.append("High revenue growth (CAGR >10%)")

        if latest.get("debt_equity", 1) == 0:
            pros.append("Debt-free company")
        elif latest.get("debt_equity", 1) < 0.5:
            pros.append("Low debt levels")

        if latest.get("net_profit_margin", 0) and latest.get("net_profit_margin", 0) > 10:
            pros.append("Healthy profit margins")

        if latest.get("free_cash_flow", 0) and latest.get("free_cash_flow", 0) > 0:
            pros.append("Positive free cash flow")

        # Analyze cons
        if latest.get("roe", 100) and latest.get("roe", 100) < 10:
            cons.append("Low ROE (<10%)")

        if latest.get("debt_equity", 0) and latest.get("debt_equity", 0) > 2:
            cons.append("High debt-to-equity ratio")

        if latest.get("revenue_cagr_5yr", 100) and latest.get("revenue_cagr_5yr", 100) < 0:
            cons.append("Negative revenue growth")

        if latest.get("net_profit_margin", 100) and latest.get("net_profit_margin", 100) < 5:
            cons.append("Low profit margins")

        if latest.get("free_cash_flow", 0) and latest.get("free_cash_flow", 0) < 0:
            cons.append("Negative free cash flow")

        return pros, cons

    except Exception as e:
        logger.error(f"Error getting pros/cons for {ticker}: {str(e)}", exc_info=True)
        return pros, cons


# =============================================================================
# UI RENDERING FUNCTIONS
# =============================================================================

def render_company_search() -> Optional[str]:
    """
    Render company search with autocomplete.

    Returns
    -------
    Optional[str]
        Selected company ticker or None
    """
    st.sidebar.header("🔍 Company Search")

    # Get company list
    companies_df = get_company_list()

    if companies_df.empty:
        st.sidebar.warning("No companies available in database")
        return None

    # Create search options
    search_options = companies_df.apply(
        lambda row: f"{row['ticker']} - {row['name']}", axis=1
    ).tolist()

    # Search input
    search_query = st.sidebar.text_input(
        "Search by Ticker or Company Name",
        placeholder="Type to search...",
        help="Search is case-insensitive"
    ).strip()

    # Filter options based on search
    if search_query:
        filtered_options = [
            opt for opt in search_options
            if search_query.upper() in opt.upper()
        ]
    else:
        filtered_options = search_options

    if not filtered_options:
        st.sidebar.info("No companies found matching your search")
        return None

    # Selectbox with filtered options
    selected_option = st.sidebar.selectbox(
        "Select Company",
        options=filtered_options,
        help="Select a company to view its profile"
    )

    if selected_option:
        # Extract ticker from selection
        ticker = selected_option.split(" - ")[0].strip()
        return ticker

    return None


def render_company_card(profile: Dict[str, Any]) -> None:
    """
    Render company information card.

    Parameters
    ----------
    profile : Dict[str, Any]
        Company profile data
    """
    st.header("🏢 Company Information")
    st.markdown("---")

    if not profile:
        st.warning("No company information available")
        return

    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        # Company logo placeholder
        st.markdown("### 🖼️ Logo")
        st.info("Logo placeholder\n\nCompany logo will be displayed here")

    with col2:
        # Company details
        st.markdown("### 📋 Company Details")

        # Create info grid
        info_items = [
            ("Company Name", profile.get("name", "N/A")),
            ("Ticker", profile.get("ticker", "N/A")),
            ("Sector", profile.get("sector", "N/A")),
            ("Sub-sector", profile.get("sub_sector", profile.get("industry", "N/A"))),
            ("Industry", profile.get("industry", "N/A")),
            ("Broad Sector", profile.get("broad_sector", "N/A")),
        ]

        for label, value in info_items:
            if value and value != "N/A":
                st.markdown(f"**{label}:** {value}")

        # Market Cap
        market_cap = profile.get("market_cap")
        if market_cap and not pd.isna(market_cap):
            st.markdown(f"**Market Cap:** ₹{market_cap:,.2f} Cr")
        else:
            st.markdown("**Market Cap:** N/A")

    with col3:
        # About section
        st.markdown("### ℹ️ About")
        about = profile.get("about_company", profile.get("description", "No description available"))
        if about and about != "N/A":
            st.markdown(about[:500] + "..." if len(str(about)) > 500 else about)
        else:
            st.info("No company description available")


def render_kpi_cards(kpis: Dict[str, Optional[float]]) -> None:
    """
    Render KPI cards section.

    Parameters
    ----------
    kpis : Dict[str, Optional[float]]
        Dictionary with KPI values
    """
    st.header("📈 Key Financial Metrics")
    st.markdown("---")

    cols = st.columns(3)

    for idx, (display_name, _, unit) in enumerate(KPI_METRICS):
        col_idx = idx % 3
        value = kpis.get(display_name)

        with cols[col_idx]:
            if value is not None:
                # Format value based on metric
                if display_name == "Latest FCF":
                    formatted_value = f"₹{value:,.0f} Cr"
                elif display_name in ["ROE", "ROCE", "Net Profit Margin", "Revenue CAGR 5Y"]:
                    formatted_value = f"{value:.2f}%"
                else:
                    formatted_value = f"{value:.2f}"

                st.metric(
                    label=display_name,
                    value=formatted_value,
                    help=f"{display_name} metric"
                )
            else:
                st.metric(
                    label=display_name,
                    value="N/A",
                    help=f"{display_name} data not available"
                )

    st.markdown("---")


def render_revenue_chart(revenue_df: pd.DataFrame, ticker: str) -> None:
    """
    Render revenue and profit chart.

    Parameters
    ----------
    revenue_df : pd.DataFrame
        DataFrame with revenue and profit data
    ticker : str
        Company ticker symbol
    """
    st.header("💰 Revenue & Profit Trend")
    st.markdown("---")

    if revenue_df.empty:
        st.warning("No revenue data available")
        return

    col1, col2 = st.columns([3, 1])

    with col1:
        # Create grouped bar chart
        fig = go.Figure()

        # Revenue bars
        fig.add_trace(
            go.Bar(
                x=revenue_df["year"],
                y=revenue_df["revenue"],
                name="Revenue",
                marker_color="rgb(55, 83, 109)",
                hovertemplate="<b>%{x}</b><br>" +
                             "Revenue: ₹%{y:,.0f} Cr<br>" +
                             "<extra></extra>"
            )
        )

        # Net Profit bars
        fig.add_trace(
            go.Bar(
                x=revenue_df["year"],
                y=revenue_df["net_profit"],
                name="Net Profit",
                marker_color="rgb(26, 118, 255)",
                hovertemplate="<b>%{x}</b><br>" +
                             "Net Profit: ₹%{y:,.0f} Cr<br>" +
                             "<extra></extra>"
            )
        )

        # Update layout
        fig.update_layout(
            title=f"{ticker} - Revenue & Net Profit (Last 10 Years)",
            xaxis_title="Year",
            yaxis_title="Amount (₹ Crores)",
            barmode="group",
            hovermode="x unified",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            height=400,
            margin=dict(l=20, r=20, t=40, b=20)
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Summary")
        st.markdown("---")

        # Calculate totals
        total_revenue = revenue_df["revenue"].sum()
        total_profit = revenue_df["net_profit"].sum()
        avg_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0

        st.metric(
            label="Total Revenue",
            value=f"₹{total_revenue:,.0f} Cr",
            help="Sum of revenue over displayed years"
        )

        st.metric(
            label="Total Net Profit",
            value=f"₹{total_profit:,.0f} Cr",
            help="Sum of net profit over displayed years"
        )

        st.metric(
            label="Avg Profit Margin",
            value=f"{avg_margin:.1f}%",
            help="Average net profit margin"
        )


def render_roe_roce_chart(roe_roce_df: pd.DataFrame, ticker: str) -> None:
    """
    Render ROE and ROCE dual-axis line chart.

    Parameters
    ----------
    roe_roce_df : pd.DataFrame
        DataFrame with ROE and ROCE data
    ticker : str
        Company ticker symbol
    """
    st.header("📊 ROE & ROCE Trend")
    st.markdown("---")

    if roe_roce_df.empty:
        st.warning("No ROE/ROCE data available")
        return

    # Create dual-axis line chart
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # ROE line
    fig.add_trace(
        go.Scatter(
            x=roe_roce_df["year"],
            y=roe_roce_df["roe"],
            name="ROE",
            mode="lines+markers",
            line=dict(color="rgb(55, 83, 109)", width=3),
            marker=dict(size=8),
            hovertemplate="<b>%{x}</b><br>" +
                         "ROE: %{y:.2f}%<br>" +
                         "<extra></extra>"
        ),
        secondary_y=False,
    )

    # ROCE line
    fig.add_trace(
        go.Scatter(
            x=roe_roce_df["year"],
            y=roe_roce_df["roce"],
            name="ROCE",
            mode="lines+markers",
            line=dict(color="rgb(26, 118, 255)", width=3),
            marker=dict(size=8),
            hovertemplate="<b>%{x}</b><br>" +
                         "ROCE: %{y:.2f}%<br>" +
                         "<extra></extra>"
        ),
        secondary_y=True,
    )

    # Update layout
    fig.update_layout(
        title=f"{ticker} - ROE & ROCE Trend (Last 10 Years)",
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        height=400,
        margin=dict(l=20, r=20, t=40, b=20)
    )

    # Update axes
    fig.update_xaxes(title_text="Year")
    fig.update_yaxes(title_text="ROE (%)", secondary_y=False)
    fig.update_yaxes(title_text="ROCE (%)", secondary_y=True)

    st.plotly_chart(fig, use_container_width=True)


def render_pros_cons(pros: List[str], cons: List[str]) -> None:
    """
    Render pros and cons section.

    Parameters
    ----------
    pros : List[str]
        List of pros
    cons : List[str]
        List of cons
    """
    st.header("✅ Pros & ❌ Cons")
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("✅ Strengths")
        if pros:
            for pro in pros:
                st.success(f"✓ {pro}")
        else:
            st.info("No specific strengths identified")

    with col2:
        st.subheader("❌ Concerns")
        if cons:
            for con in cons:
                st.error(f"✗ {con}")
        else:
            st.info("No specific concerns identified")

    st.markdown("---")


def render_not_found_message(ticker: str) -> None:
    """
    Render not found message.

    Parameters
    ----------
    ticker : str
        Ticker that was not found
    """
    st.header("🔍 Company Search")
    st.markdown("---")

    st.error(f"**{ticker}** not found.")
    st.info("Please try another company.")

    st.markdown("""
    ### Suggestions:
    - Check the ticker symbol spelling
    - Try searching by company name
    - Use the autocomplete suggestions
    - Ensure the company is part of Nifty 100
    """)


# =============================================================================
# MAIN PAGE FUNCTION
# =============================================================================

def main() -> None:
    """
    Main function to render the company profile screen.
    """
    logger.info("Company Profile screen accessed")

    # Page header
    st.title("👤 Company Profile")
    st.markdown("### Detailed Financial Analysis for Nifty 100 Companies")
    st.markdown("---")

    # Company search
    selected_ticker = render_company_search()

    if not selected_ticker:
        st.info("👈 Use the sidebar to search and select a company")
        logger.info("No company selected")
        return

    logger.info(f"Company selected: {selected_ticker}")

    # Load company data
    with st.spinner(f"Loading profile for {selected_ticker}..."):
        profile = get_company_profile(selected_ticker)

        if not profile:
            render_not_found_message(selected_ticker)
            logger.warning(f"Company not found: {selected_ticker}")
            return

        kpis = get_company_kpis(selected_ticker)
        revenue_df = get_revenue_data(selected_ticker)
        roe_roce_df = get_roe_roce_data(selected_ticker)
        pros, cons = get_pros_cons(selected_ticker)

    # Render sections
    render_company_card(profile)
    render_kpi_cards(kpis)
    render_revenue_chart(revenue_df, selected_ticker)
    render_roe_roce_chart(roe_roce_df, selected_ticker)
    render_pros_cons(pros, cons)

    # Footer
    st.markdown("---")
    st.caption(
        "💡 **Tip:** All data is cached for 10 minutes for optimal performance. "
        "Use the sidebar to search for different companies."
    )

    logger.info(f"Company profile rendered successfully for {selected_ticker}")


if __name__ == "__main__":
    main()