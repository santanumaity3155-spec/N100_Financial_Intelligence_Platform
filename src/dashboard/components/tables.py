"""Reusable table components for the N100 Financial Intelligence Platform dashboard."""

import streamlit as st
import pandas as pd
import io
from typing import List, Dict, Any, Optional, Union


def render_dataframe(
    data: pd.DataFrame,
    use_container_width: bool = True,
    hide_index: bool = True,
    height: Optional[int] = None,
    column_config: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Render a dataframe with sensible defaults.

    Args:
        data: DataFrame to display
        use_container_width: Whether to use full container width
        hide_index: Whether to hide the index
        height: Optional height in pixels
        column_config: Optional column configuration dictionary
    """
    if data.empty:
        st.info("No data to display")
        return

    st.dataframe(
        data,
        use_container_width=use_container_width,
        hide_index=hide_index,
        height=height,
        column_config=column_config,
    )


def render_formatted_table(
    data: pd.DataFrame,
    format_dict: Optional[Dict[str, str]] = None,
    title: Optional[str] = None,
    use_container_width: bool = True,
    hide_index: bool = True,
) -> None:
    """
    Render a formatted table with specific number formatting.

    Args:
        data: DataFrame to display
        format_dict: Dictionary mapping column names to format strings
                    (e.g., {"Price": "₹{:.2f}", "Percentage": "{:.2f}%"})
        title: Optional table title
        use_container_width: Whether to use full container width
        hide_index: Whether to hide the index
    """
    if data.empty:
        st.info("No data to display")
        return

    if title:
        st.subheader(title)

    # Create display copy to avoid modifying original
    display_df = data.copy()

    # Apply formatting if provided
    if format_dict:
        for col, fmt in format_dict.items():
            if col in display_df.columns:
                try:
                    if data[col].dtype in ["int64", "float64"]:
                        display_df[col] = data[col].apply(
                            lambda x: fmt.format(x) if pd.notnull(x) else "N/A"
                        )
                    else:
                        display_df[col] = data[col].astype(str)
                except (ValueError, AttributeError):
                    # If formatting fails, keep original data
                    pass

    st.dataframe(
        display_df, use_container_width=use_container_width, hide_index=hide_index
    )


def render_numeric_table(
    data: pd.DataFrame,
    numeric_columns: Optional[List[str]] = None,
    precision: int = 2,
    title: Optional[str] = None,
    use_container_width: bool = True,
    hide_index: bool = True,
) -> None:
    """
    Render a table with automatic numeric formatting.

    Args:
        data: DataFrame to display
        numeric_columns: List of column names to format as numbers
                        (if None, auto-detect numeric columns)
        precision: Number of decimal places for numeric columns
        title: Optional table title
        use_container_width: Whether to use full container width
        hide_index: Whether to hide the index
    """
    if data.empty:
        st.info("No data to display")
        return

    if title:
        st.subheader(title)

    # Auto-detect numeric columns if not provided
    if numeric_columns is None:
        numeric_columns = data.select_dtypes(
            include=["int64", "float64"]
        ).columns.tolist()

    # Create display copy
    display_df = data.copy()

    # Format numeric columns
    for col in numeric_columns:
        if col in display_df.columns:
            try:
                display_df[col] = display_df[col].apply(
                    lambda x: f"{x:,.{precision}f}" if pd.notnull(x) else "N/A"
                )
            except (ValueError, TypeError):
                # If formatting fails, keep original data
                pass

    st.dataframe(
        display_df, use_container_width=use_container_width, hide_index=hide_index
    )


def render_clickable_table(
    data: pd.DataFrame,
    clickable_columns: List[str],
    base_url: str = "",
    title: Optional[str] = None,
    use_container_width: bool = True,
    hide_index: bool = True,
) -> None:
    """
    Render a table with clickable links in specified columns.

    Args:
        data: DataFrame to display
        clickable_columns: List of column names containing URLs or path components
        base_url: Base URL to prepend to path components (if not full URL)
        title: Optional table title
        use_container_width: Whether to use full container width
        hide_index: Whether to hide the index
    """
    if data.empty:
        st.info("No data to display")
        return

    if title:
        st.subheader(title)

    # Create display copy
    display_df = data.copy()

    # Convert specified columns to clickable links
    for col in clickable_columns:
        if col in display_df.columns:

            def make_clickable(val):
                """Make clickable functionality."""
                if pd.isnull(val) or val == "":
                    return ""
                str_val = str(val)
                # Check if it's already a full URL
                if str_val.startswith(("http://", "https://")):
                    return f'<a href="{str_val}" target="_blank">🔗 Link</a>'
                else:
                    # Treat as path component
                    full_url = base_url.rstrip("/") + "/" + str_val.lstrip("/")
                    return f'<a href="{full_url}" target="_blank">🔗 Link</a>'

            display_df[col] = display_df[col].apply(make_clickable)

    # Display with HTML rendering
    st.write(display_df.to_html(escape=False, index=hide_index), unsafe_allow_html=True)


def render_export_buttons(
    data: pd.DataFrame, filename_prefix: str = "data", key_prefix: str = "export"
) -> None:
    """
    Render export buttons for CSV and Excel formats.

    Args:
        data: DataFrame to export
        filename_prefix: Prefix for exported filenames
        key_prefix: Prefix for button keys
    """
    if data.empty:
        st.info("No data to export")
        return

    col1, col2 = st.columns(2)

    with col1:
        # CSV export
        csv_buffer = io.StringIO()
        data.to_csv(csv_buffer, index=False, encoding="utf-8")
        st.download_button(
            label="📥 Download CSV",
            data=csv_buffer.getvalue(),
            file_name=f"{filename_prefix}.csv",
            mime="text/csv",
            use_container_width=True,
            key=f"{key_prefix}_csv",
        )

    with col2:
        # Excel export (requires openpyxl or xlsxwriter)
        try:
            excel_buffer = io.BytesIO()
            data.to_excel(excel_buffer, index=False, engine="openpyxl")
            excel_data = excel_buffer.getvalue()
            st.download_button(
                label="📥 Download Excel",
                data=excel_data,
                file_name=f"{filename_prefix}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key=f"{key_prefix}_excel",
            )
        except ImportError:
            st.button(
                "📥 Download Excel",
                disabled=True,
                help="Excel export requires openpyxl package",
                use_container_width=True,
                key=f"{key_prefix}_excel_disabled",
            )


def render_paginated_table(
    data: pd.DataFrame, page_size: int = 20, title: Optional[str] = None
) -> None:
    """
    Render a paginated table (simplified version).

    Args:
        data: DataFrame to display
        page_size: Number of rows per page
        title: Optional table title
    """
    if data.empty:
        st.info("No data to display")
        return

    if title:
        st.subheader(title)

    # Initialize page state
    page_key = f"page_{hash(str(data.columns.tolist()))}"
    if page_key not in st.session_state:
        st.session_state[page_key] = 0

    total_rows = len(data)
    total_pages = max(1, (total_rows + page_size - 1) // page_size)
    current_page = st.session_state[page_key]

    # Calculate slice indices
    start_idx = current_page * page_size
    end_idx = min(start_idx + page_size, total_rows)

    # Display page info
    st.caption(f"Page {current_page + 1} of {total_pages} ({total_rows} total rows)")

    # Display current page data
    page_data = data.iloc[start_idx:end_idx]
    st.dataframe(page_data, use_container_width=True, hide_index=True)

    # Pagination controls
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if current_page > 0:
            if st.button(
                "◀ Previous", use_container_width=True, key=f"{page_key}_prev"
            ):
                st.session_state[page_key] -= 1
                st.rerun()

    with col3:
        if current_page < total_pages - 1:
            if st.button("Next ▶", use_container_width=True, key=f"{page_key}_next"):
                st.session_state[page_key] += 1
                st.rerun()

    with col2:
        # Page selector
        page_options = list(range(total_pages))
        selected_page = st.selectbox(
            "Go to page",
            options=page_options,
            index=current_page,
            key=f"{page_key}_selector",
            label_visibility="collapsed",
        )
        if selected_page != current_page:
            st.session_state[page_key] = selected_page
            st.rerun()


def render_styled_dataframe(
    data: pd.DataFrame,
    style_functions: Optional[List[callable]] = None,
    title: Optional[str] = None,
    use_container_width: bool = True,
    hide_index: bool = True,
) -> None:
    """
    Render a dataframe with custom styling functions.

    Args:
        data: DataFrame to display
        style_functions: List of styling functions to apply
        title: Optional table title
        use_container_width: Whether to use full container width
        hide_index: Whether to hide the index
    """
    if data.empty:
        st.info("No data to display")
        return

    if title:
        st.subheader(title)

    # Apply styling if functions provided
    if style_functions:
        try:
            styled_df = data.style
            for func in style_functions:
                styled_df = func(styled_df)
            st.dataframe(
                styled_df,
                use_container_width=use_container_width,
                hide_index=hide_index,
            )
        except Exception:
            # Fallback to regular dataframe if styling fails
            st.dataframe(
                data, use_container_width=use_container_width, hide_index=hide_index
            )
    else:
        st.dataframe(
            data, use_container_width=use_container_width, hide_index=hide_index
        )


def render_summary_table(
    data: pd.DataFrame,
    summary_fields: List[Tuple[str, str, str]],
    title: Optional[str] = None,
) -> None:
    """
    Render a summary table with label-value pairs.

    Args:
        data: DataFrame containing the data
        summary_fields: List of (label, column, format) tuples
        title: Optional table title
    """
    if data.empty or len(data) == 0:
        st.info("No data to summarize")
        return

    if title:
        st.subheader(title)

    # Create summary rows
    summary_rows = []
    for label, column, fmt in summary_fields:
        if column in data.columns and len(data) > 0:
            value = data[column].iloc[0]  # Take first value
            try:
                if fmt:
                    formatted_value = fmt.format(value)
                else:
                    formatted_value = str(value)
            except (ValueError, AttributeError):
                formatted_value = str(value)
            summary_rows.append({"Metric": label, "Value": formatted_value})

    if summary_rows:
        summary_df = pd.DataFrame(summary_rows)
        st.dataframe(
            summary_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Metric": st.column_config.TextColumn("Metric", width="medium"),
                "Value": st.column_config.TextColumn("Value", width="medium"),
            },
        )


def render_grouped_table(
    data: pd.DataFrame,
    group_column: str,
    value_columns: List[str],
    agg_funcs: Optional[Dict[str, List[str]]] = None,
    title: Optional[str] = None,
) -> None:
    """
    Render a grouped and aggregated table.

    Args:
        data: DataFrame to group and aggregate
        group_column: Column name to group by
        value_columns: Columns to aggregate
        agg_funcs: Dictionary mapping column -> list of aggregation functions
        title: Optional table title
    """
    if data.empty:
        st.info("No data to display")
        return

    if title:
        st.subheader(title)

    # Default aggregation functions
    if agg_funcs is None:
        agg_funcs = {col: ["mean", "sum", "count"] for col in value_columns}

    # Filter to existing columns
    available_value_cols = [col for col in value_columns if col in data.columns]
    if not available_value_cols:
        st.warning("No valid value columns for aggregation")
        return

    # Filter agg_funcs to available columns
    filtered_agg_funcs = {
        col: funcs for col, funcs in agg_funcs.items() if col in available_value_cols
    }

    if not filtered_agg_funcs:
        st.warning("No valid aggregation functions specified")
        return

    try:
        # Perform groupby and aggregation
        grouped = data.groupby(group_column)[available_value_cols].agg(
            filtered_agg_funcs
        )

        # Flatten column multi-index if needed
        if isinstance(grouped.columns, pd.MultiIndex):
            grouped.columns = ["_".join(col).strip() for col in grouped.columns.values]

        # Reset index to make group column regular column
        grouped = grouped.reset_index()

        st.dataframe(grouped, use_container_width=True, hide_index=True)
    except Exception as e:
        st.error(f"Error creating grouped table: {str(e)}")
        # Fallback to original data
        st.dataframe(data, use_container_width=True, hide_index=True)
