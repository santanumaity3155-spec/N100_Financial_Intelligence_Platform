"""Reusable filter components for the N100 Financial Intelligence Platform dashboard."""

import streamlit as st
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
import numpy as np


def numeric_bounds(
    series: pd.Series, default: Tuple[float, float] = (0.0, 100.0)
) -> Tuple[float, float]:
    """
    Compute safe numeric bounds from a series using percentiles.

    Args:
        series: Data series to compute bounds from
        default: Fallback (min, max) when data is unusable

    Returns:
        Tuple[float, float]: (min, max) bounds suitable for a slider
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


def get_slider_ranges(
    data: pd.DataFrame,
    columns: List[str],
    defaults: Optional[Dict[str, Tuple[float, float]]] = None,
) -> Dict[str, Tuple[float, float]]:
    """
    Compute slider ranges for specified columns from the dataset.

    Args:
        data: DataFrame containing the data
        columns: List of column names to compute ranges for
        defaults: Optional mapping of column -> (min, max) defaults

    Returns:
        Dict[str, Tuple[float, float]]: Mapping of column -> (min, max)
    """
    if defaults is None:
        defaults = {}

    ranges: Dict[str, Tuple[float, float]] = {}
    for col in columns:
        if col not in data.columns:
            ranges[col] = defaults.get(col, (0.0, 100.0))
            continue
        default = defaults.get(col, (0.0, 100.0))
        ranges[col] = numeric_bounds(data[col], default)
    return ranges


def render_slider(
    label: str,
    min_val: float,
    max_val: float,
    default_val: float,
    step: Optional[float] = None,
    key: Optional[str] = None,
    help_text: Optional[str] = None,
) -> float:
    """
    Render a single slider widget.

    Args:
        label: Slider label
        min_val: Minimum value
        max_val: Maximum value
        default_val: Default value
        step: Step size (if None, calculated as range/100)
        key: Session state key
        help_text: Optional help text

    Returns:
        float: Selected slider value
    """
    if step is None:
        step = max((max_val - min_val) / 100.0, 0.01)

    return st.slider(
        label=label,
        min_value=float(min_val),
        max_value=float(max_val),
        value=float(st.session_state.get(key, default_val)) if key else default_val,
        step=float(step),
        key=key,
        help=help_text,
    )


def render_slider_group(
    data: pd.DataFrame,
    filter_defs: List[Tuple[str, str, str]],
    min_filters: List[str],
    max_filters: List[str],
    key_prefix: str = "filter",
) -> Dict[str, float]:
    """
    Render a group of slider filters with dynamic ranges.

    Args:
        data: DataFrame used to derive slider ranges
        filter_defs: List of (label, column, unit_suffix) tuples
        min_filters: List of column names that use >= logic
        max_filters: List of column names that use <= logic
        key_prefix: Prefix for session state keys

    Returns:
        Dict[str, float]: Dictionary of slider values keyed by column name
    """
    # Extract column names
    columns = [col for _, col, _ in filter_defs]

    # Compute dynamic ranges
    ranges = get_slider_ranges(data, columns)

    # Render sliders
    slider_values: Dict[str, float] = {}

    for label, col, unit in filter_defs:
        lo, hi = ranges.get(col, (0.0, 100.0))
        step = round((hi - lo) / 100.0, 4) if hi > lo else 1.0
        step = max(step, 0.01)

        # Determine default based on filter type
        if col in min_filters:
            default = lo  # For min filters, start at minimum (no constraint)
        elif col in max_filters:
            default = hi  # For max filters, start at maximum (no constraint)
        else:
            default = (lo + hi) / 2  # Default to middle

        # Format label with unit
        display_label = f"{label} ({unit})".strip()

        # Render slider
        key = f"{key_prefix}_{col}"
        value = render_slider(
            label=display_label,
            min_val=lo,
            max_val=hi,
            default_val=default,
            step=step,
            key=key,
            help_text=f"Range: {lo:.2f} to {hi:.2f}",
        )

        slider_values[col] = value

    return slider_values


def apply_preset_values(
    preset: Dict[str, float],
    ranges: Dict[str, Tuple[float, float]],
    min_filters: List[str],
    max_filters: List[str],
) -> Dict[str, float]:
    """
    Clamp preset values to the dynamic slider ranges.

    Args:
        preset: Preset slider values keyed by filter column
        ranges: Dynamic slider ranges (column -> (min, max))
        min_filters: List of column names that use >= logic
        max_filters: List of column names that use <= logic

    Returns:
        Dict[str, float]: Clamped preset values
    """
    result: Dict[str, float] = {}
    for col, value in preset.items():
        if col not in ranges:
            continue

        lo, hi = ranges[col]

        if col in min_filters:
            # For MIN filters: permissive bound is minimum (no constraint)
            result[col] = lo if value <= lo + 1e-12 else min(max(value, lo), hi)
        elif col in max_filters:
            # For MAX filters: permissive bound is maximum (no constraint)
            result[col] = hi if value >= hi - 1e-12 else min(max(value, lo), hi)
        else:
            result[col] = min(max(value, lo), hi)

    return result


def render_reset_button(
    key_prefix: str = "filter", help_text: str = "Reset all filters to default values"
) -> bool:
    """
    Render a reset filters button.

    Args:
        key_prefix: Prefix used for filter session state keys
        help_text: Help text for the button

    Returns:
        bool: True if button was clicked
    """
    return st.button(
        "🔄 Reset Filters",
        help=help_text,
        use_container_width=True,
        key=f"{key_prefix}_reset",
    )


def render_preset_buttons(
    presets: Dict[str, Dict[str, float]], key_prefix: str = "preset", cols: int = 2
) -> Optional[str]:
    """
    Render preset strategy buttons.

    Args:
        presets: Dictionary of preset_name -> preset_values
        key_prefix: Prefix for session state keys
        cols: Number of columns to display buttons in

    Returns:
        Optional[str]: Name of selected preset, or None
    """
    if not presets:
        return None

    selected_preset: Optional[str] = None
    preset_items = list(presets.items())

    # Create columns for buttons
    button_cols = st.columns(cols)

    for idx, (preset_name, preset_values) in enumerate(preset_items):
        col_idx = idx % cols
        with button_cols[col_idx]:
            if st.button(
                preset_name, key=f"{key_prefix}_{preset_name}", use_container_width=True
            ):
                selected_preset = preset_name

    return selected_preset


def build_filter_conditions(
    slider_values: Dict[str, float],
    ranges: Dict[str, Tuple[float, float]],
    min_filters: List[str],
    max_filters: List[str],
    eps: float = 1e-9,
) -> List[Dict[str, Any]]:
    """
    Build filter conditions from slider values.

    Args:
        slider_values: Current slider values keyed by filter column
        ranges: Dynamic slider ranges (column -> (min, max))
        min_filters: List of column names that use >= logic
        max_filters: List of column names that use <= logic
        eps: Epsilon for floating point comparisons

    Returns:
        List[Dict[str, Any]]: List of filter condition dictionaries
    """
    conditions: List[Dict[str, Any]] = []

    for col, value in slider_values.items():
        if col not in ranges:
            continue

        lo, hi = ranges[col]

        if col in min_filters:
            # For MIN filters: permissive bound is minimum (no constraint)
            if value <= lo + eps:
                continue  # Skip - no constraint
            conditions.append({"field": col, "operator": ">=", "value": value})
        elif col in max_filters:
            # For MAX filters: permissive bound is maximum (no constraint)
            if value >= hi - eps:
                continue  # Skip - no constraint
            conditions.append({"field": col, "operator": "<=", "value": value})
        # For other filter types, could add equality, range, etc.

    return conditions
