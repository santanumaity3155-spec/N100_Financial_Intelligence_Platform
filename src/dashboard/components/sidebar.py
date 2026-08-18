"""Reusable sidebar components for the N100 Financial Intelligence Platform dashboard."""

import streamlit as st
import pandas as pd
from typing import Optional, List, Tuple, Dict, Any


def render_year_selector(
    years: Optional[List[int]] = None,
    default_index: Optional[int] = None,
    key: str = "year_selector",
    help_text: str = "Select a year to filter all analytics"
) -> int:
    """
    Render a year selector in the sidebar.

    Args:
        years: List of available years (if None, defaults to 2019-2024)
        default_index: Index of default selection (if None, defaults to latest)
        key: Session state key
        help_text: Help text for the selector

    Returns:
        int: Selected year
    """
    if years is None:
        years = list(range(2019, 2025))  # 2019-2024

    if default_index is None:
        default_index = len(years) - 1  # Default to latest year

    st.sidebar.header("📅 Year Filter")

    selected_year = st.sidebar.selectbox(
        "Select Financial Year",
        options=years,
        index=default_index,
        key=key,
        help=help_text
    )

    st.sidebar.markdown("---")
    st.sidebar.caption(f"**Selected Year:** {selected_year}")

    return selected_year


def render_company_selector(
    companies_df: pd.DataFrame,
    key: str = "company_selector",
    help_text: str = "Search for a company by name (case-insensitive)",
    placeholder: str = "Type to search..."
) -> Tuple[Optional[str], Optional[str]]:
    """
    Render a company search/selector in the sidebar.

    Args:
        companies_df: DataFrame with company information (must have 'company_id' and 'company_name' columns)
        key: Session state key
        help_text: Help text for the search
        placeholder: Placeholder text for search input

    Returns:
        Tuple[Optional[str], Optional[str]]: (selected_company_id, selected_company_name)
    """
    st.sidebar.header("🏢 Company Selection")

    if companies_df.empty:
        st.sidebar.warning("No companies available")
        return None, None

    # Ensure required columns exist
    if 'company_id' not in companies_df.columns or 'company_name' not in companies_df.columns:
        st.sidebar.error("Company data missing required columns")
        return None, None

    # Get unique company names
    company_names = companies_df["company_name"].dropna().astype(str).tolist()
    company_names = sorted(set(company_names))

    # Search/autocomplete
    search_query = st.sidebar.text_input(
        "Search Company",
        placeholder=placeholder,
        help=help_text,
        key=f"{key}_search"
    ).strip().lower()

    # Filter companies
    if search_query:
        filtered_names = [name for name in company_names if search_query in name.lower()]
    else:
        filtered_names = company_names

    if not filtered_names:
        st.sidebar.info("No companies match your search")
        return None, None

    selected_name = st.sidebar.selectbox(
        "Select Company",
        options=filtered_names,
        help="Choose a company to view details",
        key=f"{key}_select"
    )

    # Get company_id
    try:
        selected_id = companies_df.loc[
            companies_df["company_name"] == selected_name, "company_id"
        ].iloc[0]
    except (KeyError, IndexError):
        st.sidebar.warning("Selected company not found")
        return None, None

    return selected_id, selected_name


def render_sidebar_header(title: str, icon: str = "") -> None:
    """
    Render a sidebar header with optional icon.

    Args:
        title: Header title
        icon: Optional icon to display before title
    """
    if icon:
        st.sidebar.header(f"{icon} {title}")
    else:
        st.sidebar.header(title)


def render_sidebar_section(title: str, icon: str = "📋") -> None:
    """
    Render a sidebar section header.

    Args:
        title: Section title
        icon: Optional icon to display before title
    """
    if icon:
        st.sidebar.subheader(f"{icon} {title}")
    else:
        st.sidebar.subheader(title)
    st.sidebar.markdown("---")


def render_sidebar_metric(
    label: str,
    value: str,
    delta: Optional[str] = None,
    help_text: Optional[str] = None
) -> None:
    """
    Render a metric in the sidebar.

    Args:
        label: Metric label
        value: Metric value
        delta: Optional change value
        help_text: Optional help text
    """
    if help_text:
        st.sidebar.metric(
            label=label,
            value=value,
            delta=delta,
            help=help_text
        )
    else:
        st.sidebar.metric(
            label=label,
            value=value,
            delta=delta
        )


def render_sidebar_info(title: str, content: str, icon: str = "ℹ️") -> None:
    """
    Render an info block in the sidebar.

    Args:
        title: Info title
        content: Info content
        icon: Optional icon to display
    """
    with st.sidebar.container():
        st.markdown(f"### {icon} {title}")
        st.markdown(content)
        st.markdown("---")


def render_sidebar_warning(title: str, content: str, icon: str = "⚠️") -> None:
    """
    Render a warning block in the sidebar.

    Args:
        title: Warning title
        content: Warning content
        icon: Optional icon to display
    """
    with st.sidebar.container():
        st.markdown(f"### {icon} {title}")
        st.markdown(content)
        st.markdown("---")


def render_collapsible_section(
    title: str,
    content_func: callable,
    expanded: bool = False,
    icon: str = "▶️"
) -> None:
    """
    Render a collapsible section in the sidebar.

    Args:
        title: Section title
        content_func: Function to call to render section content
        expanded: Whether section starts expanded
        icon: Icon to display
    """
    with st.sidebar.expander(f"{icon} {title}", expanded=expanded):
        content_func()


def render_sidebar_divider() -> None:
    """
    Render a divider in the sidebar.
    """
    st.sidebar.markdown("---")


def render_sidebar_caption(text: str) -> None:
    """
    Render a caption in the sidebar.

    Args:
        text: Caption text
    """
    st.sidebar.caption(text)


def render_sidebar_info_box(
    title: str,
    content: str,
    box_type: str = "info"
) -> None:
    """
    Render an info/warning/error/success box in the sidebar.

    Args:
        title: Box title
        content: Box content
        box_type: Type of box ("info", "success", "warning", "error")
    """
    if box_type == "success":
        st.sidebar.success(f"**{title}**: {content}")
    elif box_type == "warning":
        st.sidebar.warning(f"**{title}**: {content}")
    elif box_type == "error":
        st.sidebar.error(f"**{title}**: {content}")
    else:  # default to info
        st.sidebar.info(f"**{title}**: {content}")


def render_sidebar_filter_reset(
    key_prefix: str = "filter",
    help_text: str = "Reset all filters to default values"
) -> bool:
    """
    Render a sidebar filter reset button.

    Args:
        key_prefix: Prefix used for filter session state keys
        help_text: Help text for the button

    Returns:
        bool: True if button was clicked
    """
    return st.sidebar.button(
        "🔄 Reset Filters",
        help=help_text,
        use_container_width=True,
        key=f"{key_prefix}_reset_sidebar"
    )


def render_sidebar_expanded_state(
    label: str,
    value: Any,
    expanded: bool = False
) -> None:
    """
    Render expandable state information in the sidebar.

    Args:
        label: Label for the state
        value: Value to display
        expanded: Whether to start expanded
    """
    with st.sidebar.expander(f"📊 {label}", expanded=expanded):
        st.json(value) if isinstance(value, (dict, list)) else st.write(value)