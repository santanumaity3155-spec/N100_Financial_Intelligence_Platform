"""Reusable chart components for the N100 Financial Intelligence Platform dashboard."""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Optional, List, Dict, Any


def donut_chart(
    data: pd.DataFrame,
    values_col: str,
    names_col: str,
    title: str = "",
    hole: float = 0.4,
    height: int = 500,
    color_sequence: Optional[List[str]] = None,
) -> None:
    """
    Render a donut chart.

    Args:
        data: DataFrame containing the data
        values_col: Column name for values
        names_col: Column name for names/categories
        title: Chart title
        hole: Size of the hole (0 to 1, where 0 is pie, larger is more donut-like)
        height: Chart height in pixels
        color_sequence: Optional color sequence for chart
    """
    if data.empty:
        st.warning("No data available for chart")
        return

    fig = px.pie(
        data,
        values=values_col,
        names=names_col,
        hole=hole,
        title=title,
        color_discrete_sequence=color_sequence or px.colors.qualitative.Set3,
    )

    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>"
        + "Value: %{value}<br>"
        + "Percentage: %{percent}<br>"
        + "<extra></extra>",
    )

    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02),
        height=height,
        margin=dict(l=20, r=20, t=40, b=20),
    )

    st.plotly_chart(fig, use_container_width=True)


def bar_chart(
    data: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str = "",
    orientation: str = "v",
    height: int = 400,
    color: Optional[str] = None,
) -> None:
    """
    Render a bar chart.

    Args:
        data: DataFrame containing the data
        x_col: Column name for x-axis
        y_col: Column name for y-axis
        title: Chart title
        orientation: Orientation ("v" for vertical, "h" for horizontal)
        height: Chart height in pixels
        color: Optional column name for color encoding
    """
    if data.empty:
        st.warning("No data available for chart")
        return

    fig = px.bar(
        data,
        x=x_col,
        y=y_col,
        orientation=orientation,
        title=title,
        color=color,
        height=height,
    )

    fig.update_layout(
        xaxis_title=x_col.replace("_", " ").title(),
        yaxis_title=y_col.replace("_", " ").title(),
        margin=dict(l=20, r=20, t=40, b=20),
    )

    st.plotly_chart(fig, use_container_width=True)


def line_chart(
    data: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str = "",
    height: int = 400,
    color: Optional[str] = None,
    markers: bool = True,
) -> None:
    """
    Render a line chart.

    Args:
        data: DataFrame containing the data
        x_col: Column name for x-axis
        y_col: Column name for y-axis
        title: Chart title
        height: Chart height in pixels
        color: Optional column name for color encoding
        markers: Whether to show markers on points
    """
    if data.empty:
        st.warning("No data available for chart")
        return

    fig = px.line(
        data, x=x_col, y=y_col, title=title, color=color, height=height, markers=markers
    )

    fig.update_layout(
        xaxis_title=x_col.replace("_", " ").title(),
        yaxis_title=y_col.replace("_", " ").title(),
        margin=dict(l=20, r=20, t=40, b=20),
    )

    st.plotly_chart(fig, use_container_width=True)


def scatter_chart(
    data: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str = "",
    height: int = 500,
    color: Optional[str] = None,
    size: Optional[str] = None,
    hover_data: Optional[List[str]] = None,
) -> None:
    """
    Render a scatter chart.

    Args:
        data: DataFrame containing the data
        x_col: Column name for x-axis
        y_col: Column name for y-axis
        title: Chart title
        height: Chart height in pixels
        color: Optional column name for color encoding
        size: Optional column name for point size
        hover_data: Optional list of column names to show on hover
    """
    if data.empty:
        st.warning("No data available for chart")
        return

    fig = px.scatter(
        data,
        x=x_col,
        y=y_col,
        title=title,
        color=color,
        size=size,
        hover_data=hover_data,
        height=height,
    )

    fig.update_layout(
        xaxis_title=x_col.replace("_", " ").title(),
        yaxis_title=y_col.replace("_", " ").title(),
        margin=dict(l=20, r=20, t=40, b=20),
    )

    st.plotly_chart(fig, use_container_width=True)


def gauge_chart(
    value: float,
    title: str = "",
    min_val: float = 0,
    max_val: float = 100,
    height: int = 300,
    threshold_config: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Render a gauge chart.

    Args:
        value: Current value to display
        title: Chart title
        min_val: Minimum value of gauge
        max_val: Maximum value of gauge
        height: Chart height in pixels
        threshold_config: Optional threshold configuration
    """
    if threshold_config is None:
        threshold_config = {
            "line": {"color": "red", "width": 4},
            "thickness": 0.75,
            "value": max_val * 0.9,
        }

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=value,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": title},
            delta={"reference": max_val * 0.5},
            gauge={
                "axis": {"range": [min_val, max_val]},
                "bar": {"color": "darkblue"},
                "steps": [
                    {"range": [min_val, max_val * 0.5], "color": "lightgray"},
                    {"range": [max_val * 0.5, max_val * 0.8], "color": "gray"},
                ],
                "threshold": threshold_config,
            },
        )
    )

    fig.update_layout(height=height)
    st.plotly_chart(fig, use_container_width=True)


def metric_trend_chart(
    data: pd.DataFrame,
    date_col: str,
    value_col: str,
    title: str = "",
    height: int = 400,
    show_points: bool = True,
) -> None:
    """
    Render a metric trend chart over time.

    Args:
        data: DataFrame containing the data
        date_col: Column name for date/time
        value_col: Column name for metric value
        title: Chart title
        height: Chart height in pixels
        show_points: Whether to show individual points
    """
    if data.empty:
        st.warning("No data available for chart")
        return

    fig = px.line(
        data, x=date_col, y=value_col, title=title, height=height, markers=show_points
    )

    fig.update_layout(
        xaxis_title=date_col.replace("_", " ").title(),
        yaxis_title=value_col.replace("_", " ").title(),
        margin=dict(l=20, r=20, t=40, b=20),
    )

    st.plotly_chart(fig, use_container_width=True)
