"""
Screener Screen - N100 Financial Intelligence Platform
Sprint 4 - Module 3 Implementation

Provides an interactive investment screener that filters Nifty 100 companies
using fundamental financial metrics. Reuses the Sprint 3 Screener Engine for
all filtering logic and offers six preset screening strategies.

Screen Layout
-------------
1. Sidebar: 10 dynamically-ranged sliders + 6 preset buttons
2. Main: Live result counter, sortable results table, CSV export
"""

import io
import time
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st

import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config.logging_config import get_logger
from src.dashboard.utils.db import (
    get_all_screener_data,
)
from src.screener.engine import ScreenerEngine
from src.screener.filters import (
    FilterCondition,
    FilterOperator,
)

logger = get_logger(__name__)

# CONSTANTS - FILTER DEFINITIONS
# =============================================================================

# Order of filters in the sidebar (display label, data column, unit suffix)
FILTER_DEFS: List[Tuple[str, str, str]] = [
    ("ROE Minimum", "roe", "%"),
    ("Debt to Equity Maximum", "debt_to_equity", ""),
    ("Free Cash Flow Minimum", "free_cash_flow", "₹ Cr"),
    ("Revenue CAGR 5 Year Minimum", "revenue_cagr_5yr", "%"),
    ("PAT CAGR Minimum", "pat_cagr_5yr", "%"),
    ("Operating Profit Margin Minimum", "operating_profit_margin", "%"),
    ("PE Maximum", "pe_ratio", "x"),
    ("PB Maximum", "pb_ratio", "x"),
    ("Dividend Yield Minimum", "dividend_yield", "%"),
    ("Interest Coverage Minimum", "interest_coverage", "x"),
]

# Which filters are "minimum" (>=) vs "maximum" (<=)
MIN_FILTERS = {
    "roe",
    "free_cash_flow",
    "revenue_cagr_5yr",
    "pat_cagr_5yr",
    "operating_profit_margin",
    "dividend_yield",
    "interest_coverage",
}
MAX_FILTERS = {"debt_to_equity", "pe_ratio", "pb_ratio"}

# Preset strategies - populate every slider then run filter immediately
PRESETS: Dict[str, Dict[str, float]] = {
    "Quality Compounder": {
        "roe": 18.0,
        "debt_to_equity": 0.5,
        "free_cash_flow": 500.0,
        "revenue_cagr_5yr": 12.0,
        "pat_cagr_5yr": 12.0,
        "operating_profit_margin": 10.0,
        "pe_ratio": 45.0,
        "pb_ratio": 12.0,
        "dividend_yield": 0.0,
        "interest_coverage": 3.0,
    },
    "Value Pick": {
        "roe": 12.0,
        "debt_to_equity": 0.8,
        "free_cash_flow": -1e18,  # no constraint
        "revenue_cagr_5yr": -1e18,
        "pat_cagr_5yr": -1e18,
        "operating_profit_margin": -1e18,
        "pe_ratio": 18.0,
        "pb_ratio": 3.0,
        "dividend_yield": 1.0,
        "interest_coverage": 2.0,
    },
    "Growth Accelerator": {
        "roe": 15.0,
        "debt_to_equity": 1.2,
        "free_cash_flow": -1e18,
        "revenue_cagr_5yr": 15.0,
        "pat_cagr_5yr": 18.0,
        "operating_profit_margin": -1e18,
        "pe_ratio": 60.0,
        "pb_ratio": 15.0,
        "dividend_yield": 0.0,
        "interest_coverage": -1e18,
    },
    "Dividend Champion": {
        "roe": 10.0,
        "debt_to_equity": 1.0,
        "free_cash_flow": -1e18,
        "revenue_cagr_5yr": -1e18,
        "pat_cagr_5yr": -1e18,
        "operating_profit_margin": -1e18,
        "pe_ratio": 40.0,
        "pb_ratio": 10.0,
        "dividend_yield": 2.5,
        "interest_coverage": 2.0,
    },
    "Debt-Free Blue Chip": {
        "roe": 14.0,
        "debt_to_equity": 0.15,
        "free_cash_flow": 0.0,
        "revenue_cagr_5yr": 8.0,
        "pat_cagr_5yr": 8.0,
        "operating_profit_margin": 12.0,
        "pe_ratio": 55.0,
        "pb_ratio": 12.0,
        "dividend_yield": 0.0,
        "interest_coverage": 4.0,
    },
    "Turnaround Watch": {
        "roe": -1e18,
        "debt_to_equity": 2.5,
        "free_cash_flow": -1e18,
        "revenue_cagr_5yr": -1e18,
        "pat_cagr_5yr": -20.0,
        "operating_profit_margin": -1e18,
        "pe_ratio": 1e18,
        "pb_ratio": 20.0,
        "dividend_yield": 0.0,
        "interest_coverage": -1e18,
    },
}

# Result table column order (display label, source column)
RESULT_COLUMNS: List[Tuple[str, str]] = [
    ("Company ID", "company_id"),
    ("Ticker", "ticker"),
    ("Company Name", "company_name"),
    ("Sector", "sector"),
    ("Composite Quality Score", "composite_quality_score"),
    ("ROE", "roe"),
    ("ROCE", "roce"),
    ("Debt to Equity", "debt_to_equity"),
    ("Revenue CAGR", "revenue_cagr_5yr"),
    ("PAT CAGR", "pat_cagr_5yr"),
    ("PE", "pe_ratio"),
    ("PB", "pb_ratio"),
    ("Dividend Yield", "dividend_yield"),
    ("Interest Coverage", "interest_coverage"),
    ("Latest Free Cash Flow", "free_cash_flow"),
]


# =============================================================================
# DATA LOADING
# =============================================================================


@st.cache_data(ttl=600, show_spinner=False)
def load_screener_data() -> pd.DataFrame:
    """
    Load the consolidated screener dataset.

    Returns
    -------
    pd.DataFrame
        Consolidated screener metrics for all companies.
    """
    df = get_all_screener_data()
    if df.empty:
        logger.warning("Screener dataset is empty")
    return df


# =============================================================================
# FILTER RANGE HELPERS
# =============================================================================


def _numeric_bounds(
    series: pd.Series, default: Tuple[float, float]
) -> Tuple[float, float]:
    """
    Compute safe numeric bounds from a series using percentiles.

    Parameters
    ----------
    series : pd.Series
        Data column.
    default : Tuple[float, float]
        Fallback (min, max) when data is unusable.

    Returns
    -------
    Tuple[float, float]
        (min, max) bounds suitable for a slider.
    """
    vals = pd.to_numeric(series, errors="coerce").dropna()
    if vals.empty:
        return default
    lo = float(vals.quantile(0.02))
    hi = float(vals.quantile(0.98))
    if lo == hi:
        lo, hi = float(vals.min()), float(vals.max())
    if lo == hi:  # still constant
        lo, hi = default
    return lo, hi


def get_filter_ranges(data: pd.DataFrame) -> Dict[str, Tuple[float, float]]:
    """
    Dynamically compute slider ranges for every filter from the dataset.

    Parameters
    ----------
    data : pd.DataFrame
        Consolidated screener dataset.

    Returns
    -------
    Dict[str, Tuple[float, float]]
        Mapping of filter column -> (min, max).
    """
    ranges: Dict[str, Tuple[float, float]] = {}
    for _, col, _ in FILTER_DEFS:
        if col not in data.columns:
            ranges[col] = (0.0, 100.0)
            continue
        default = (0.0, 100.0) if col in MIN_FILTERS else (0.0, 10.0)
        ranges[col] = _numeric_bounds(data[col], default)
    return ranges


# =============================================================================
# PRESET LOGIC
# =============================================================================


def apply_preset_values(
    preset: Dict[str, float], ranges: Dict[str, Tuple[float, float]]
) -> Dict[str, float]:
    """
    Clamp preset values to the dynamic slider ranges.

    Values of -1e18 / 1e18 represent "no constraint" and are mapped to the
    most permissive bound of the slider (min for MIN_FILTERS, max for MAX_FILTERS).

    Parameters
    ----------
    preset : Dict[str, float]
        Preset slider values keyed by filter column.
    ranges : Dict[str, Tuple[float, float]]
        Dynamic slider ranges.

    Returns
    -------
    Dict[str, float]
        Clamped preset values.
    """
    result: Dict[str, float] = {}
    for col, value in preset.items():
        lo, hi = ranges.get(col, (0.0, 100.0))
        if col in MIN_FILTERS:
            result[col] = lo if value <= -1e12 else min(max(value, lo), hi)
        elif col in MAX_FILTERS:
            result[col] = hi if value >= 1e12 else min(max(value, lo), hi)
        else:
            result[col] = min(max(value, lo), hi)
    return result


# =============================================================================
# FILTERING - REUSES SCREENER ENGINE
# =============================================================================


def build_filter_conditions(
    slider_values: Dict[str, float], ranges: Dict[str, Tuple[float, float]]
) -> List[FilterCondition]:
    """
    Build Screener Engine filter conditions from slider values.

    A slider positioned at its most permissive bound imposes no constraint and
    is skipped. For MIN filters the permissive bound is the range minimum; for
    MAX filters it is the range maximum.

    Parameters
    ----------
    slider_values : Dict[str, float]
        Current slider values keyed by filter column.
    ranges : Dict[str, Tuple[float, float]]
        Dynamic slider ranges (col -> (min, max)).

    Returns
    -------
    List[FilterCondition]
        Filter conditions for the Screener Engine.
    """
    conditions: List[FilterCondition] = []
    eps = 1e-9
    for _, col, _ in FILTER_DEFS:
        value = slider_values.get(col)
        if value is None or pd.isna(value):
            continue
        lo, hi = ranges.get(col, (0.0, 100.0))
        if col in MIN_FILTERS:
            # Permissive bound -> no constraint
            if value <= lo + eps:
                continue
            conditions.append(
                FilterCondition(
                    field=col,
                    operator=FilterOperator.GREATER_THAN_OR_EQUAL,
                    value=value,
                )
            )
        elif col in MAX_FILTERS:
            # Permissive bound -> no constraint
            if value >= hi - eps:
                continue
            conditions.append(
                FilterCondition(
                    field=col, operator=FilterOperator.LESS_THAN_OR_EQUAL, value=value
                )
            )
    return conditions


def run_screener(data: pd.DataFrame, slider_values: Dict[str, float]) -> pd.DataFrame:
    """
    Execute screening using the Sprint 3 Screener Engine.

    Parameters
    ----------
    data : pd.DataFrame
        Consolidated screener dataset.
    slider_values : Dict[str, float]
        Slider values keyed by filter column.

    Returns
    -------
    pd.DataFrame
        Filtered results (empty if none match or an error occurs).
    """
    try:
        engine = ScreenerEngine()
        engine.data = data.copy()
        ranges = get_filter_ranges(data)
        conditions = build_filter_conditions(slider_values, ranges)
        if conditions:
            engine.apply_filters(conditions, logic="AND")
            result = engine.filtered_data
        else:
            result = engine.data
        return result if result is not None else pd.DataFrame()
    except Exception as e:
        logger.error(f"Screener Engine failed: {str(e)}", exc_info=True)
        return pd.DataFrame()


# =============================================================================
# UI RENDERING
# =============================================================================


def _preset_state_key(col: str) -> str:
    """Return the session-state key for a filter slider."""
    return f"slider_{col}"


def render_sidebar_filters(
    data: pd.DataFrame,
) -> Tuple[Dict[str, float], Optional[str]]:
    """
    Render the sidebar filter sliders and preset buttons.

    Parameters
    ----------
    data : pd.DataFrame
        Consolidated screener dataset used to derive slider ranges.

    Returns
    -------
    Tuple[Dict[str, float], Optional[str]]
        (slider_values, selected_preset_id_or_None)
    """
    ranges = get_filter_ranges(data)

    st.sidebar.header("🎛️ Screening Filters")
    st.sidebar.caption("Ranges are derived from the dataset automatically.")

    # Preset buttons
    st.sidebar.subheader("⚡ Preset Strategies")
    preset_cols = st.sidebar.columns(2)
    selected_preset: Optional[str] = None
    for idx, preset_name in enumerate(PRESETS.keys()):
        col = preset_cols[idx % 2]
        if col.button(
            preset_name, key=f"preset_{preset_name}", use_container_width=True
        ):
            selected_preset = preset_name
            logger.info(f"Preset selected: {preset_name}")

    # When a preset is clicked, populate every slider's session state.
    if selected_preset is not None:
        preset_values = apply_preset_values(PRESETS[selected_preset], ranges)
        for col, value in preset_values.items():
            st.session_state[_preset_state_key(col)] = float(value)
        logger.info(f"Preset {selected_preset} values applied to all sliders")

    st.sidebar.markdown("---")

    # Lookup label by column (built once)
    label_by_col = {col: label for label, col, _ in FILTER_DEFS}

    # Sliders
    slider_values: Dict[str, float] = {}
    for _, col, unit in FILTER_DEFS:
        lo, hi = ranges.get(col, (0.0, 100.0))
        step = round((hi - lo) / 100.0, 4) if hi > lo else 1.0
        step = max(step, 0.01)
        is_min = col in MIN_FILTERS
        default = lo if is_min else hi
        key = _preset_state_key(col)

        label = f"{label_by_col[col]} ({unit})".strip()
        slider_values[col] = st.sidebar.slider(
            label,
            min_value=float(lo),
            max_value=float(hi),
            value=float(st.session_state.get(key, default)),
            step=float(step),
            key=key,
        )

    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Reset Filters", use_container_width=True):
        for _, col, _ in FILTER_DEFS:
            st.session_state.pop(_preset_state_key(col), None)
        st.rerun()

    return slider_values, selected_preset


def format_result_table(data: pd.DataFrame) -> pd.DataFrame:
    """
    Format the filtered data into the display-ready result table.

    Parameters
    ----------
    data : pd.DataFrame
        Filtered screener results.

    Returns
    -------
    pd.DataFrame
        Renamed, rounded table for display/export.
    """
    out = pd.DataFrame()
    for label, col in RESULT_COLUMNS:
        if col in data.columns:
            out[label] = data[col]
    # Round numeric columns
    numeric_labels = [label for label, col in RESULT_COLUMNS if col in data.columns]
    for label in numeric_labels:
        if label not in out.columns:
            continue
        try:
            out[label] = pd.to_numeric(out[label], errors="coerce").round(2)
        except Exception:
            pass
    return out


def render_results_table(result_df: pd.DataFrame) -> None:
    """
    Render the sortable, scrollable, responsive results table.

    Parameters
    ----------
    result_df : pd.DataFrame
        Formatted result table.
    """
    st.dataframe(
        result_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            col: st.column_config.Column(col, width="medium")
            for col in result_df.columns
        },
    )


def render_csv_export(result_df: pd.DataFrame) -> None:
    """
    Render a download button for the visible (filtered) results.

    Parameters
    ----------
    result_df : pd.DataFrame
        Formatted result table (visible rows only).
    """
    if result_df.empty:
        return
    csv_buffer = io.StringIO()
    result_df.to_csv(csv_buffer, index=False, encoding="utf-8")
    st.download_button(
        label="⬇️ Download CSV",
        data=csv_buffer.getvalue(),
        file_name="screener_results.csv",
        mime="text/csv",
        use_container_width=True,
    )
    logger.info(f"CSV exported with {len(result_df)} rows")


# =============================================================================
# MAIN
# =============================================================================


def main() -> None:
    """
    Render the Investment Screener screen.
    """
    logger.info("Screer screen accessed")
    st.title("🔍 Investment Screener")
    st.markdown("### Filter Nifty 100 companies using financial metrics.")
    st.markdown("---")

    start_time = time.time()

    # Load data
    with st.spinner("Loading screening data..."):
        data = load_screener_data()

    if data.empty:
        st.error(
            "No financial data is available. Please check the database connection."
        )
        logger.error("Screener dataset empty - cannot render screen")
        return

    # Sidebar controls
    slider_values, selected_preset = render_sidebar_filters(data)

    if selected_preset:
        st.info(f"⚡ Preset **{selected_preset}** applied to all filters.")
        logger.info(f"Preset applied: {selected_preset}")

    # Run filter (live - every slider change updates results immediately)
    filtered = run_screener(data, slider_values)
    logger.info(
        f"Screening executed: {len(filtered)} results in {time.time() - start_time:.3f}s"
    )

    # Result count
    count = len(filtered)
    st.subheader(f"📊 Results")
    if count:
        st.markdown(f"### **{count} companies match your criteria**")
    else:
        st.markdown("### **0 companies match your criteria**")

    st.markdown("---")

    # Results table + export
    if count:
        result_df = format_result_table(filtered)
        col_table, col_export = st.columns([4, 1])
        with col_table:
            render_results_table(result_df)
        with col_export:
            render_csv_export(result_df)
    else:
        st.warning("No companies match the selected criteria.")
        st.info("Try relaxing one or more filter thresholds.")

    # Footer
    st.markdown("---")
    st.caption(
        "💡 **Tip:** Results update instantly as you move any slider. "
        "Use a preset strategy to quickly populate all filters."
    )
    logger.info(f"Screener screen rendered in {time.time() - start_time:.2f}s")


if __name__ == "__main__":
    main()
