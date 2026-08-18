"""
Company Intelligence Dashboard - N100 Financial Intelligence Platform
Module 5B Implementation

This page provides a comprehensive financial intelligence view for individual
Nifty 100 companies, integrating financial performance, health scores, cash flow
intelligence, pros/cons signals, capital allocation patterns, valuation metrics,
peer positioning, and multi-year historical trends.

Usage:
    streamlit run src/dashboard/app.py
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from src.dashboard.utils.db import (
    get_companies,
    get_ratios,
    get_pl,
    get_bs,
    get_cf,
    get_raw_statement,
    get_company_financial_health,
    get_company_pros_cons_signals,
    get_company_capital_allocation_detail,
    get_company_valuation_detail,
    get_company_peer_percentiles,
    get_peers,
)
from src.analytics.cashflow_intelligence import (
    compute_cfo_quality,
    compute_capex_intensity,
    compute_fcf_cagr_5yr,
    compute_fcf_conversion,
    compute_distress_flag,
    compute_deleveraging_flag,
    compute_capital_allocation_label,
)
from src.config.logging_config import get_logger

logger = get_logger(__name__)


# =============================================================================
# DATA RETRIEVAL HELPERS (Cached)
# =============================================================================

@st.cache_data(ttl=600, show_spinner=False)
def load_company_master_list() -> pd.DataFrame:
    """
    Retrieve authoritative company master data for company selector.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns: ticker, name, sector, industry.
    """
    try:
        df = get_companies()
        if df.empty:
            logger.warning("Company master table is empty")
            return pd.DataFrame()
        # Drop duplicates and fill missing labels safely
        df = df.drop_duplicates(subset=["ticker"]).copy()
        df["name"] = df["name"].fillna("Unknown Name")
        df["sector"] = df["sector"].fillna("Unclassified Sector")
        return df.sort_values("ticker")
    except Exception as e:
        logger.error(f"Error loading company master list: {str(e)}", exc_info=True)
        return pd.DataFrame()


@st.cache_data(ttl=600, show_spinner=False)
def load_company_full_intelligence(ticker: str) -> Dict[str, Any]:
    """
    Load and aggregate all company financial intelligence across modules.

    Parameters
    ----------
    ticker : str
        Company ticker / company_id

    Returns
    -------
    Dict[str, Any]
        Dictionary containing all intelligence datasets for the company.
    """
    if not ticker or not isinstance(ticker, str):
        return {}

    ticker = ticker.strip().upper()
    logger.info(f"Loading full financial intelligence for {ticker}")

    res: Dict[str, Any] = {
        "ticker": ticker,
        "profile": None,
        "health": None,
        "ratios_df": pd.DataFrame(),
        "pl_df": pd.DataFrame(),
        "bs_df": pd.DataFrame(),
        "cf_df": pd.DataFrame(),
        "raw_pl_df": pd.DataFrame(),
        "raw_bs_df": pd.DataFrame(),
        "raw_cf_df": pd.DataFrame(),
        "cashflow_intel": {},
        "pros_cons": {"pros": [], "cons": []},
        "capital_allocation": {},
        "valuation": {},
        "peer_percentiles_df": pd.DataFrame(),
    }

    try:
        # 1. Company profile info
        comps = load_company_master_list()
        if not comps.empty:
            m = comps[comps["ticker"].str.upper() == ticker]
            if not m.empty:
                res["profile"] = m.iloc[0].to_dict()

        # 2. Statements & Ratios
        res["ratios_df"] = get_ratios(ticker)
        res["pl_df"] = get_pl(ticker)
        res["bs_df"] = get_bs(ticker)
        res["cf_df"] = get_cf(ticker)

        # Raw statements for Module 3 Cash Flow functions
        res["raw_pl_df"] = get_raw_statement(ticker, "profit_loss")
        res["raw_bs_df"] = get_raw_statement(ticker, "balance_sheet")
        res["raw_cf_df"] = get_raw_statement(ticker, "cash_flow")

        # 3. Financial Health
        res["health"] = get_company_financial_health(ticker)

        # 4. Cash Flow Intelligence (Module 3)
        raw_cf = res["raw_cf_df"]
        raw_pl = res["raw_pl_df"]
        raw_bs = res["raw_bs_df"]

        if not raw_cf.empty and not raw_pl.empty:
            res["cashflow_intel"] = {
                "cfo_quality": compute_cfo_quality(raw_cf, raw_pl),
                "capex_intensity": compute_capex_intensity(raw_cf, raw_pl),
                "fcf_cagr_5yr": compute_fcf_cagr_5yr(raw_cf),
                "fcf_conversion": compute_fcf_conversion(raw_cf, raw_pl),
                "distress": compute_distress_flag(raw_cf),
                "deleveraging": compute_deleveraging_flag(raw_cf, raw_bs),
                "capital_allocation_label": compute_capital_allocation_label(raw_cf, raw_pl),
            }

        # 5. Pros & Cons (Module 2D)
        res["pros_cons"] = get_company_pros_cons_signals(ticker)

        # 6. Capital Allocation (Module 4)
        res["capital_allocation"] = get_company_capital_allocation_detail(ticker)

        # 7. Valuation (Module 4/Master)
        res["valuation"] = get_company_valuation_detail(ticker)

        # 8. Peer Percentiles
        res["peer_percentiles_df"] = get_company_peer_percentiles(ticker)

    except Exception as e:
        logger.error(f"Error compiling intelligence for {ticker}: {str(e)}", exc_info=True)

    return res


# =============================================================================
# FORMATTING UTILITIES
# =============================================================================

def format_currency(val: Any) -> str:
    """Format numeric value as currency in ₹ Crores."""
    if val is None or pd.isna(val):
        return "Data unavailable"
    try:
        fval = float(val)
        return f"₹{fval:,.2f} Cr"
    except (ValueError, TypeError):
        return "Data unavailable"


def format_pct(val: Any) -> str:
    """Format numeric value as percentage."""
    if val is None or pd.isna(val):
        return "Data unavailable"
    try:
        fval = float(val)
        return f"{fval:.2f}%"
    except (ValueError, TypeError):
        return "Data unavailable"


def format_num(val: Any, decimals: int = 2) -> str:
    """Format numeric value with fixed decimals."""
    if val is None or pd.isna(val):
        return "Data unavailable"
    try:
        fval = float(val)
        return f"{fval:.{decimals}f}"
    except (ValueError, TypeError):
        return "Data unavailable"


# =============================================================================
# SECTION RENDERERS
# =============================================================================

def render_company_selector(companies_df: pd.DataFrame) -> Optional[str]:
    """
    Render robust company selector dropdown in sidebar.

    Returns
    -------
    Optional[str]
        Selected company ticker symbol.
    """
    st.sidebar.markdown("### 🔍 Company Selector")

    if companies_df.empty:
        st.sidebar.error("❌ No companies available in database.")
        return None

    # Handle duplicates and create clear selection options
    companies_clean = companies_df.drop_duplicates(subset=["ticker"]).copy()
    options_map = {}
    options_list = []

    for _, row in companies_clean.iterrows():
        t = str(row["ticker"]).strip().upper()
        n = str(row["name"]).strip()
        s = str(row.get("sector", "N/A")).strip()
        label = f"{t} - {n} ({s})"
        options_map[label] = t
        options_list.append(label)

    # Maintain selected ticker in session state
    default_idx = 0
    if "selected_ticker" in st.session_state:
        current = st.session_state["selected_ticker"]
        for idx, opt_label in enumerate(options_list):
            if options_map[opt_label] == current:
                default_idx = idx
                break

    selected_label = st.sidebar.selectbox(
        "Select Company:",
        options=options_list,
        index=default_idx,
        help="Select a company to view company intelligence",
        key="company_intelligence_selector",
    )

    if selected_label and selected_label in options_map:
        selected_ticker = options_map[selected_label]
        st.session_state["selected_ticker"] = selected_ticker
        return selected_ticker

    return None


def render_section_1_header(profile: Optional[Dict[str, Any]], ticker: str) -> None:
    """Render Section 1 — Company Header."""
    st.markdown("## 🏢 Company Intelligence Header")

    if not profile:
        st.warning(f"⚠️ Company details for **{ticker}** could not be loaded from company master records.")
        return

    name = profile.get("name", ticker)
    sector = profile.get("sector", "N/A")
    industry = profile.get("industry", "N/A")
    isin = profile.get("isin", "N/A")
    listed_date = profile.get("listed_date", "N/A")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(label="Company Name", value=str(name)[:25])
        st.caption(f"**Ticker:** `{ticker}`")

    with col2:
        st.metric(label="Sector", value=str(sector)[:25])
        st.caption(f"**Industry:** {industry}")

    with col3:
        st.metric(label="ISIN", value=str(isin))
        st.caption(f"**Listed:** {listed_date}")

    with col4:
        st.metric(label="Analysis Period", value="FY2024 / Latest")
        st.caption("Status: Authoritative Data")

    st.markdown("---")


def render_section_2_health(health: Optional[Dict[str, Any]]) -> None:
    """Render Section 2 — Financial Health Score."""
    st.markdown("## 🎯 Financial Health")

    if not health:
        st.info("ℹ️ Financial Health Score data unavailable for this company.")
        st.markdown("---")
        return

    overall_score = health.get("overall_score")
    rating = health.get("rating", "Unrated")
    period = health.get("period", "N/A")
    remarks = health.get("remarks", "No remarks available.")

    # Main Health Score Banner
    col_score, col_rating, col_period = st.columns([1, 1, 2])

    with col_score:
        if overall_score is not None and not pd.isna(overall_score):
            st.metric(label="Overall Health Score", value=f"{overall_score:.1f} / 100")
        else:
            st.metric(label="Overall Health Score", value="Data unavailable")

    with col_rating:
        st.metric(label="Health Rating", value=str(rating))

    with col_period:
        st.metric(label="Health Period", value=str(period))
        st.caption(f"**Remarks:** {remarks}")

    # Sub-component Breakdown
    st.markdown("#### Component Scores")
    c1, c2, c3, c4, c5 = st.columns(5)

    comp_scores = [
        ("Profitability", health.get("profitability_score"), c1),
        ("Growth", health.get("growth_score"), c2),
        ("Cash Flow", health.get("cashflow_score"), c3),
        ("Leverage", health.get("leverage_score"), c4),
        ("Efficiency", health.get("efficiency_score"), c5),
    ]

    for label, score, col in comp_scores:
        with col:
            if score is not None and not pd.isna(score):
                col.metric(label=label, value=f"{float(score):.1f}")
            else:
                col.metric(label=label, value="Data unavailable")

    st.markdown("---")


def render_section_3_kpis(
    ratios_df: pd.DataFrame,
    pl_df: pd.DataFrame,
    cf_df: pd.DataFrame,
) -> None:
    """Render Section 3 — Key Financial KPIs."""
    st.markdown("## 🔑 Key Financial KPIs")

    latest_ratio = ratios_df.iloc[0].to_dict() if not ratios_df.empty else {}
    latest_pl = pl_df.iloc[0].to_dict() if not pl_df.empty else {}
    latest_cf = cf_df.iloc[0].to_dict() if not cf_df.empty else {}

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            label="Revenue / Sales",
            value=format_currency(latest_pl.get("sales")),
            help="Latest annual revenue from Profit & Loss statement",
        )
        st.metric(
            label="ROE",
            value=format_pct(latest_ratio.get("roe")),
            help="Return on Equity",
        )

    with c2:
        st.metric(
            label="Net Profit (PAT)",
            value=format_currency(latest_pl.get("net_profit")),
            help="Latest annual net profit",
        )
        st.metric(
            label="ROCE",
            value=format_pct(latest_ratio.get("roce")),
            help="Return on Capital Employed",
        )

    with c3:
        st.metric(
            label="EPS",
            value=format_num(latest_pl.get("eps") or latest_ratio.get("eps")),
            help="Earnings Per Share",
        )
        st.metric(
            label="Operating Margin (OPM)",
            value=format_pct(latest_pl.get("opm_percentage") or latest_ratio.get("operating_margin")),
            help="Operating profit margin percentage",
        )

    with c4:
        st.metric(
            label="Debt to Equity",
            value=format_num(latest_ratio.get("debt_equity")),
            help="Debt to Equity ratio",
        )
        st.metric(
            label="Net Profit Margin",
            value=format_pct(latest_ratio.get("net_profit_margin")),
            help="Net profit margin percentage",
        )

    st.markdown("---")


def render_section_4_profitability(
    pl_df: pd.DataFrame,
    ratios_df: pd.DataFrame,
    ticker: str,
) -> None:
    """Render Section 4 — Profitability & Growth Trends."""
    st.markdown("## 📈 Profitability & Growth Trends")

    if pl_df.empty and ratios_df.empty:
        st.info("ℹ️ Historical P&L and ratio data unavailable for chart rendering.")
        st.markdown("---")
        return

    # Clean & sort historical data ascending by year
    pl_clean = pl_df.copy()
    if not pl_clean.empty and "year" in pl_clean.columns:
        pl_clean = pl_clean.sort_values("year", ascending=True)

    ratios_clean = ratios_df.copy()
    if not ratios_clean.empty and "year" in ratios_clean.columns:
        ratios_clean = ratios_clean.sort_values("year", ascending=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Revenue & Net Profit Trend (₹ Crores)")
        if not pl_clean.empty and "sales" in pl_clean.columns and "net_profit" in pl_clean.columns:
            fig = go.Figure()
            fig.add_trace(
                go.Bar(
                    x=pl_clean["year"],
                    y=pl_clean["sales"],
                    name="Revenue",
                    marker_color="#1f77b4",
                )
            )
            fig.add_trace(
                go.Bar(
                    x=pl_clean["year"],
                    y=pl_clean["net_profit"],
                    name="Net Profit",
                    marker_color="#2ca02c",
                )
            )
            fig.update_layout(
                barmode="group",
                height=350,
                margin=dict(l=20, r=20, t=30, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                xaxis_title="Financial Period",
                yaxis_title="Amount (₹ Cr)",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Data unavailable for Revenue/Net Profit chart.")

    with col2:
        st.markdown("#### ROE vs ROCE Trend (%)")
        if not ratios_clean.empty and "roe" in ratios_clean.columns:
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=ratios_clean["year"],
                    y=ratios_clean["roe"],
                    mode="lines+markers",
                    name="ROE (%)",
                    line=dict(color="#ff7f0e", width=3),
                )
            )
            if "roce" in ratios_clean.columns:
                fig.add_trace(
                    go.Scatter(
                        x=ratios_clean["year"],
                        y=ratios_clean["roce"],
                        mode="lines+markers",
                        name="ROCE (%)",
                        line=dict(color="#d62728", width=3),
                    )
                )
            fig.update_layout(
                height=350,
                margin=dict(l=20, r=20, t=30, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                xaxis_title="Financial Period",
                yaxis_title="Percentage (%)",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Data unavailable for ROE/ROCE chart.")

    st.markdown("---")


def render_section_5_cashflow_intelligence(intel: Dict[str, Any]) -> None:
    """Render Section 5 — Cash Flow Intelligence (Module 3 Output)."""
    st.markdown("## 💰 Cash Flow Intelligence (Module 3)")

    if not intel:
        st.info("ℹ️ Cash Flow Intelligence metrics unavailable for this company.")
        st.markdown("---")
        return

    cfo_q = intel.get("cfo_quality", {})
    capex_i = intel.get("capex_intensity", {})
    fcf_cagr = intel.get("fcf_cagr_5yr", {})
    fcf_conv = intel.get("fcf_conversion", {})
    distress = intel.get("distress", {})
    deleveraging = intel.get("deleveraging", {})
    cap_alloc = intel.get("capital_allocation_label", "Insufficient Data")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="CFO Quality Score",
            value=format_num(cfo_q.get("score")),
            delta=cfo_q.get("label", "Insufficient Data"),
        )
        st.metric(
            label="CapEx Intensity",
            value=format_pct(capex_i.get("value")),
            delta=capex_i.get("label", "Insufficient Data"),
        )

    with col2:
        st.metric(
            label="5-Year FCF CAGR",
            value=format_pct(fcf_cagr.get("value")),
            delta=fcf_cagr.get("flag") or "Normal",
        )
        st.metric(
            label="FCF Conversion",
            value=format_pct(fcf_conv.get("value")),
            delta=fcf_conv.get("flag") or "Normal",
        )

    with col3:
        distress_flag = distress.get("flag", False)
        deleveraging_flag = deleveraging.get("flag", False)

        st.metric(
            label="Distress Signal",
            value="🚨 ALERT" if distress_flag else "✅ CLEAR",
            delta="CFO < 0 & CFF > 0" if distress_flag else "Normal",
        )
        st.metric(
            label="Deleveraging Flag",
            value="📉 DELEVERAGING" if deleveraging_flag else "➖ STABLE",
            delta="Borrowings Declining" if deleveraging_flag else "Normal",
        )

    st.markdown(f"**Capital Allocation Label (Module 3 Engine):** `{cap_alloc}`")
    st.markdown("---")


def render_section_6_pros_cons(pros_cons: Dict[str, List[Dict[str, Any]]]) -> None:
    """Render Section 6 — Pros & Cons (Module 2D Output)."""
    st.markdown("## ⚖️ Pros & Cons Signals (Module 2D)")

    pros = pros_cons.get("pros", [])
    cons = pros_cons.get("cons", [])

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### ✅ Strengths (Pros)")
        if pros:
            for p in pros:
                conf = p.get("confidence_pct")
                conf_str = f" [Confidence: {conf:.1f}%]" if conf is not None else ""
                rule_id = p.get("rule_id", "PRO")
                st.success(f"**[{rule_id}]** {p.get('text', '')}{conf_str}")
        else:
            st.info("No explicit positive signals identified for this company.")

    with col2:
        st.markdown("### ❌ Concerns (Cons)")
        if cons:
            for c in cons:
                conf = c.get("confidence_pct")
                conf_str = f" [Confidence: {conf:.1f}%]" if conf is not None else ""
                rule_id = c.get("rule_id", "CON")
                st.error(f"**[{rule_id}]** {c.get('text', '')}{conf_str}")
        else:
            st.info("No explicit negative concerns identified for this company.")

    st.markdown("---")


def render_section_7_capital_allocation(detail: Dict[str, Any]) -> None:
    """Render Section 7 — Capital Allocation (Module 4 Output)."""
    st.markdown("## 🏛️ Capital Allocation (Module 4)")

    if not detail:
        st.info("ℹ️ Capital allocation classification data unavailable.")
        st.markdown("---")
        return

    rating = detail.get("rating", "Unrated")
    pattern = detail.get("pattern", "Unclassified")
    prev_pattern = detail.get("previous_pattern")
    changed = detail.get("changed", False)

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric(label="Capital Allocation Rating", value=str(rating))

    with c2:
        st.metric(label="Current Pattern", value=str(pattern))

    with c3:
        if changed and prev_pattern:
            st.metric(label="Pattern Status", value="🔄 Shifted", delta=f"Prev: {prev_pattern}")
        else:
            st.metric(label="Pattern Status", value="✅ Stable", delta="No Shift")

    st.markdown("---")


def render_section_8_valuation(val_detail: Dict[str, Any]) -> None:
    """Render Section 8 — Valuation."""
    st.markdown("## 🏷️ Valuation Analytics")

    pe = val_detail.get("pe")
    pb = val_detail.get("pb")
    ev_ebitda = val_detail.get("ev_ebitda")
    sec_pe = val_detail.get("sector_median_pe")
    v_flag = val_detail.get("valuation_flag")
    diff_pct = val_detail.get("difference_pct")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(label="P/E Ratio", value=format_num(pe))

    with c2:
        st.metric(label="P/B Ratio", value=format_num(pb))

    with c3:
        st.metric(label="EV / EBITDA", value=format_num(ev_ebitda))

    with c4:
        st.metric(
            label="Valuation Status",
            value=str(v_flag) if v_flag else "Data unavailable",
            delta=f"{diff_pct:+.1f}% vs Sector" if diff_pct is not None else None,
        )

    st.markdown("---")


def render_section_9_peer_position(percentiles_df: pd.DataFrame, ticker: str) -> None:
    """Render Section 9 — Peer Position & Percentile Rankings."""
    st.markdown("## 📊 Peer Position & Percentiles")

    if percentiles_df.empty:
        st.info("ℹ️ Peer percentile rankings unavailable for this company.")
        st.markdown("---")
        return

    st.markdown("#### Metric Percentile Rankings Within Peer Group")

    # Render clean dataframe of metrics
    display_df = percentiles_df[["metric", "metric_value", "percentile_rank", "period"]].copy()
    display_df.columns = ["Metric", "Value", "Percentile Rank (0-1)", "Period"]
    display_df["Percentile Rank (0-1)"] = display_df["Percentile Rank (0-1)"].apply(
        lambda x: f"{float(x):.2f}" if x is not None and not pd.isna(x) else "N/A"
    )

    st.dataframe(display_df, use_container_width=True, hide_index=True)
    st.markdown("---")


def render_section_10_historical_trend(
    pl_df: pd.DataFrame,
    bs_df: pd.DataFrame,
    cf_df: pd.DataFrame,
) -> None:
    """Render Section 10 — Multi-Year Historical Financial Trend."""
    st.markdown("## 📜 Multi-Year Historical Financial Trend")

    tabs = st.tabs(["Profit & Loss", "Balance Sheet", "Cash Flow"])

    with tabs[0]:
        if not pl_df.empty:
            st.dataframe(pl_df, use_container_width=True, hide_index=True)
        else:
            st.info("P&L statement history unavailable.")

    with tabs[1]:
        if not bs_df.empty:
            st.dataframe(bs_df, use_container_width=True, hide_index=True)
        else:
            st.info("Balance sheet statement history unavailable.")

    with tabs[2]:
        if not cf_df.empty:
            st.dataframe(cf_df, use_container_width=True, hide_index=True)
        else:
            st.info("Cash flow statement history unavailable.")

    st.markdown("---")


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main() -> None:
    """Main execution function for Company Intelligence dashboard page."""
    logger.info("Accessing Company Intelligence Dashboard page")

    st.title("👤 Company Intelligence Dashboard")
    st.caption("Module 5B — Comprehensive Financial Intelligence & Analytics")
    st.markdown("---")

    # Load master company list
    companies_df = load_company_master_list()

    # Company selection
    selected_ticker = render_company_selector(companies_df)

    if not selected_ticker:
        st.info("👈 Please select a company from the sidebar dropdown to display financial intelligence.")
        return

    # Load all company intelligence with loading spinner
    with st.spinner(f"Loading financial intelligence for {selected_ticker}..."):
        intel = load_company_full_intelligence(selected_ticker)

    if not intel or not intel.get("profile"):
        st.error(f"❌ Intelligence records for ticker **{selected_ticker}** could not be compiled.")
        st.info("Please select another company from the list.")
        return

    # Render all 11 sections
    render_section_1_header(intel.get("profile"), selected_ticker)
    render_section_2_health(intel.get("health"))
    render_section_3_kpis(intel.get("ratios_df"), intel.get("pl_df"), intel.get("cf_df"))
    render_section_4_profitability(intel.get("pl_df"), intel.get("ratios_df"), selected_ticker)
    render_section_5_cashflow_intelligence(intel.get("cashflow_intel", {}))
    render_section_6_pros_cons(intel.get("pros_cons", {}))
    render_section_7_capital_allocation(intel.get("capital_allocation", {}))
    render_section_8_valuation(intel.get("valuation", {}))
    render_section_9_peer_position(intel.get("peer_percentiles_df"), selected_ticker)
    render_section_10_historical_trend(intel.get("pl_df"), intel.get("bs_df"), intel.get("cf_df"))

    # Footer
    st.caption(
        "💡 **Tip:** Data is automatically cached for 10 minutes for optimal performance. "
        "Use the sidebar to inspect other Nifty 100 companies."
    )


if __name__ == "__main__":
    main()