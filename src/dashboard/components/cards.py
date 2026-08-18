"""Reusable card components for the N100 Financial Intelligence Platform dashboard."""

import streamlit as st
from typing import Optional


def kpi_card(
    title: str,
    value: str,
    delta: Optional[str] = None,
    help_text: Optional[str] = None,
    delta_color: str = "normal"
) -> None:
    """
    Render a KPI (Key Performance Indicator) card.

    Args:
        title: The KPI title (e.g., "Average ROE")
        value: The KPI value to display (e.g., "15.2%")
        delta: Optional change value (e.g., "+2.1%")
        help_text: Optional help text to show on hover
        delta_color: Color for delta ("normal", "inverse", "off")
    """
    if help_text:
        st.metric(
            label=title,
            value=value,
            delta=delta,
            help=help_text,
            delta_color=delta_color
        )
    else:
        st.metric(
            label=title,
            value=value,
            delta=delta,
            delta_color=delta_color
        )


def metric_card(
    title: str,
    value: str,
    label_visibility: str = "visible"
) -> None:
    """
    Render a simple metric card.

    Args:
        title: The metric title
        value: The metric value
        label_visibility: Visibility of the label ("visible", "hidden", "collapsed")
    """
    st.metric(label=title, value=value, label_visibility=label_visibility)


def info_card(
    title: str,
    content: str,
    icon: str = "ℹ️"
) -> None:
    """
    Render an info card with title and content.

    Args:
        title: The card title
        content: The card content
        icon: Optional icon to display
    """
    with st.container():
        st.markdown(f"### {icon} {title}")
        st.markdown(content)
        st.markdown("---")


def alert_card(
    title: str,
    content: str,
    alert_type: str = "info"
) -> None:
    """
    Render an alert card.

    Args:
        title: The alert title
        content: The alert content
        alert_type: Type of alert ("info", "success", "warning", "error")
    """
    if alert_type == "success":
        st.success(f"**{title}**: {content}")
    elif alert_type == "warning":
        st.warning(f"**{title}**: {content}")
    elif alert_type == "error":
        st.error(f"**{title}**: {content}")
    else:  # default to info
        st.info(f"**{title}**: {content}")