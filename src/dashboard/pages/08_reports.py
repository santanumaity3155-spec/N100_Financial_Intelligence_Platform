"""
Annual Reports Page - N100 Financial Intelligence Platform
Sprint 4 - Module 4 Implementation

Provides access to annual reports for Nifty 100 companies with URL validation
and status indicators.

Features
--------
1. Company search with autocomplete
2. Year list of available reports
3. Display year, report link, and status
4. Open report button using st.link_button()
5. URL validation - 404 detection with red "Report unavailable" badge
6. Green "Available" badge for valid URLs
7. Never crash - comprehensive error handling
"""

import logging
from typing import Dict, List, Optional, Tuple

import requests
import pandas as pd
import streamlit as st

import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.dashboard.utils.db import (
    get_companies,
    _read_df,
)
from src.config.logging_config import get_logger

logger = get_logger(__name__)

# CONSTANTS
# =============================================================================

# Timeout for URL validation requests (seconds)
URL_VALIDATION_TIMEOUT = 5

# Cache TTL for report data (seconds)
REPORT_CACHE_TTL = 600


# =============================================================================
# DATA LOADING (cached)
# =============================================================================


@st.cache_data(ttl=REPORT_CACHE_TTL, show_spinner=False)
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
        df = df.rename(
            columns={
                "ticker": "company_id",
                "name": "company_name",
            }
        )

        logger.info(f"Loaded {len(df)} companies for annual reports")
        return df[["company_id", "company_name", "sector", "industry"]]
    except Exception as e:
        logger.error(f"Failed to load companies: {str(e)}", exc_info=True)
        return pd.DataFrame()


@st.cache_data(ttl=REPORT_CACHE_TTL, show_spinner=False)
def load_annual_reports(company_id: str) -> pd.DataFrame:
    """
    Load annual reports for a specific company.

    Parameters
    ----------
    company_id : str
        Company identifier.

    Returns
    -------
    pd.DataFrame
        DataFrame with report information including year, URL, and document type.
    """
    try:
        # Query the documents table for annual reports
        query = """
            SELECT
                year,
                document_url,
                document_type,
                annual_report,
                upload_date
            FROM documents
            WHERE company_id = ?
                AND (document_type = 'annual_report' OR annual_report IS NOT NULL)
            ORDER BY year DESC
        """

        df = _read_df(query, params=[company_id])

        if df.empty:
            logger.warning(f"No annual reports found for company: {company_id}")
            return pd.DataFrame()

        # Clean and standardize
        df["year"] = df["year"].astype(str)
        df["document_url"] = df["document_url"].fillna("")
        df["annual_report"] = df["annual_report"].fillna("")

        # Use annual_report field if document_url is empty
        df["report_url"] = df.apply(
            lambda row: (
                row["document_url"] if row["document_url"] else row["annual_report"]
            ),
            axis=1,
        )

        # Filter to only rows with URLs
        df = df[df["report_url"].str.len() > 0].copy()

        logger.info(f"Loaded {len(df)} annual reports for company {company_id}")
        return df[["year", "report_url", "document_type", "upload_date"]]
    except Exception as e:
        logger.error(
            f"Failed to load annual reports for {company_id}: {str(e)}", exc_info=True
        )
        return pd.DataFrame()


# =============================================================================
# URL VALIDATION
# =============================================================================


@st.cache_data(ttl=REPORT_CACHE_TTL, show_spinner=False)
def validate_url(url: str) -> Tuple[bool, Optional[str]]:
    """
    Validate if a URL is accessible (not 404).

    Parameters
    ----------
    url : str
        URL to validate.

    Returns
    -------
    Tuple[bool, Optional[str]]
        (is_valid, error_message)
        - is_valid: True if URL is accessible, False otherwise
        - error_message: Error message if validation fails, None if successful
    """
    if not url or not isinstance(url, str):
        return False, "Invalid URL"

    url = url.strip()

    if not url.startswith(("http://", "https://")):
        return False, "Invalid URL format"

    try:
        # Use HEAD request first for efficiency
        response = requests.head(
            url,
            timeout=URL_VALIDATION_TIMEOUT,
            allow_redirects=True,
        )

        # If HEAD is not allowed, try GET
        if response.status_code == 405:  # Method Not Allowed
            response = requests.get(
                url,
                timeout=URL_VALIDATION_TIMEOUT,
                allow_redirects=True,
                stream=True,  # Don't download content
            )

        if response.status_code == 200:
            return True, None
        elif response.status_code == 404:
            return False, "Report unavailable (404)"
        else:
            return False, f"HTTP {response.status_code}"

    except requests.exceptions.Timeout:
        return False, "Request timeout"
    except requests.exceptions.ConnectionError:
        return False, "Connection error"
    except requests.exceptions.RequestException as e:
        return False, f"Request error: {str(e)}"
    except Exception as e:
        return False, f"Validation error: {str(e)}"


def validate_report_urls(reports_df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate all report URLs in the DataFrame.

    Parameters
    ----------
    reports_df : pd.DataFrame
        DataFrame with report information.

    Returns
    -------
    pd.DataFrame
        DataFrame with added 'is_valid' and 'status_message' columns.
    """
    if reports_df.empty:
        return reports_df

    try:
        # Add validation columns
        reports_df = reports_df.copy()
        reports_df["is_valid"] = False
        reports_df["status_message"] = "Not checked"

        # Validate each URL
        for idx, row in reports_df.iterrows():
            url = row.get("report_url", "")
            if url:
                is_valid, error_msg = validate_url(url)
                reports_df.at[idx, "is_valid"] = is_valid
                reports_df.at[idx, "status_message"] = (
                    "Available" if is_valid else error_msg
                )

        logger.info(f"Validated {len(reports_df)} report URLs")
        return reports_df
    except Exception as e:
        logger.error(f"Failed to validate report URLs: {str(e)}", exc_info=True)
        return reports_df


# =============================================================================
# SIDEBAR SELECTION
# =============================================================================


def render_sidebar(companies_df: pd.DataFrame) -> Tuple[Optional[str], Optional[str]]:
    """
    Render sidebar with company search.

    Parameters
    ----------
    companies_df : pd.DataFrame
        DataFrame with company information.

    Returns
    -------
    Tuple[Optional[str], Optional[str]]
        (selected_company_id, selected_company_name)
    """
    st.sidebar.header("🏢 Company Selection")

    if companies_df.empty:
        st.sidebar.warning("No companies available")
        return None, None

    company_names = companies_df["company_name"].dropna().astype(str).tolist()
    company_names = sorted(set(company_names))

    # Search/autocomplete
    search_query = (
        st.sidebar.text_input(
            "Search Company",
            placeholder="Type to search...",
            help="Search for a company by name (case-insensitive)",
        )
        .strip()
        .lower()
    )

    # Filter companies
    if search_query:
        filtered_names = [
            name for name in company_names if search_query in name.lower()
        ]
    else:
        filtered_names = company_names

    if not filtered_names:
        st.sidebar.info("No companies match your search")
        return None, None

    selected_name = st.sidebar.selectbox(
        "Select Company",
        options=filtered_names,
        help="Choose a company to view annual reports",
    )

    # Get company_id
    try:
        selected_id = companies_df.loc[
            companies_df["company_name"] == selected_name, "company_id"
        ].iloc[0]
    except (KeyError, IndexError):
        st.sidebar.warning("Selected company not found")
        return None, None

    logger.info(f"Company selected for reports: {selected_id} ({selected_name})")
    return selected_id, selected_name


# =============================================================================
# MAIN
# =============================================================================


def main() -> None:
    """
    Render the Annual Reports page.
    """
    logger.info("Annual Reports page accessed")
    st.title("📄 Annual Reports")
    st.markdown("### Access and view annual reports for Nifty 100 companies")
    st.markdown("---")

    # Load companies
    companies_df = load_companies()

    if companies_df.empty:
        st.error("No companies available. Please check the database.")
        logger.error("No companies available for annual reports")
        return

    # Sidebar selection
    selected_id, selected_name = render_sidebar(companies_df)

    if selected_id is None or selected_name is None:
        st.info("👈 Select a company from the sidebar to view annual reports")
        return

    # Load annual reports
    with st.spinner(f"Loading annual reports for {selected_name}..."):
        reports_df = load_annual_reports(selected_id)

    if reports_df.empty:
        st.warning(f"No annual reports available for {selected_name}")
        logger.warning(f"No annual reports for company {selected_id}")
        return

    # Validate URLs
    with st.spinner("Validating report URLs..."):
        reports_df = validate_report_urls(reports_df)

    # Display company header
    st.subheader(f"📄 Annual Reports for {selected_name}")
    st.markdown(f"**Company ID:** {selected_id}")

    # Summary statistics
    total_reports = len(reports_df)
    valid_reports = (
        reports_df["is_valid"].sum() if "is_valid" in reports_df.columns else 0
    )
    invalid_reports = total_reports - valid_reports

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Reports", total_reports)
    with col2:
        st.metric("Available", int(valid_reports))
    with col3:
        st.metric("Unavailable", int(invalid_reports))

    st.markdown("---")

    # Display reports
    st.subheader("📋 Available Reports")

    # Create a nice table display
    for idx, row in reports_df.iterrows():
        year = row.get("year", "N/A")
        url = row.get("report_url", "")
        is_valid = row.get("is_valid", False)
        status_msg = row.get("status_message", "Unknown")

        # Create a container for each report
        with st.container():
            col1, col2, col3, col4 = st.columns([1, 2, 1, 1])

            with col1:
                st.markdown(f"**Year:** {year}")

            with col2:
                if url:
                    st.markdown(f"🔗 [Report Link]({url})")
                else:
                    st.markdown("No URL available")

            with col3:
                # Status badge
                if is_valid:
                    st.success("✅ Available")
                else:
                    st.error("❌ Report unavailable")

            with col4:
                # Open report button
                if url and is_valid:
                    st.link_button(
                        "Open Report",
                        url,
                        help=f"Open annual report for {year}",
                    )
                elif url and not is_valid:
                    st.button(
                        "Unavailable",
                        disabled=True,
                        help=f"Report for {year} is not available (404 or other error)",
                    )
                else:
                    st.button(
                        "No Link",
                        disabled=True,
                        help="No URL available for this report",
                    )

            # Display status message if there's an error
            if not is_valid and status_msg != "Available":
                st.caption(f"⚠️ Status: {status_msg}")

            st.markdown("---")

    # Display all reports in a table format
    with st.expander("📊 View All Reports Table"):
        if not reports_df.empty:
            # Prepare display dataframe
            display_df = reports_df.copy()
            display_df["Status"] = display_df.apply(
                lambda row: (
                    "✅ Available" if row.get("is_valid", False) else "❌ Unavailable"
                ),
                axis=1,
            )
            display_df["Action"] = display_df.apply(
                lambda row: (
                    "Open"
                    if row.get("is_valid", False) and row.get("report_url")
                    else "N/A"
                ),
                axis=1,
            )

            # Select columns for display
            display_cols = ["year", "report_url", "Status", "Action"]
            display_cols = [col for col in display_cols if col in display_df.columns]

            st.dataframe(
                display_df[display_cols],
                use_container_width=True,
                hide_index=True,
            )

    # Bulk validation section
    with st.expander("🔍 Re-validate All URLs"):
        st.markdown(
            "Click the button below to re-validate all report URLs. This may take a few moments."
        )

        if st.button("Re-validate URLs", type="primary"):
            with st.spinner("Validating URLs..."):
                # Clear cache and reload
                st.cache_data.clear()
                reports_df = load_annual_reports(selected_id)
                reports_df = validate_report_urls(reports_df)

                # Show results
                valid_count = (
                    reports_df["is_valid"].sum()
                    if "is_valid" in reports_df.columns
                    else 0
                )
                total_count = len(reports_df)

                st.success(
                    f"Validation complete: {int(valid_count)}/{total_count} reports available"
                )

                # Display updated status
                for idx, row in reports_df.iterrows():
                    year = row.get("year", "N/A")
                    is_valid = row.get("is_valid", False)
                    status_msg = row.get("status_message", "Unknown")

                    if is_valid:
                        st.success(f"✅ {year}: Available")
                    else:
                        st.error(f"❌ {year}: {status_msg}")

    # Footer
    st.markdown("---")
    st.caption(
        "💡 **Tip:** Click 'Open Report' to view the annual report in a new tab. "
        "Red badges indicate reports that are currently unavailable (404 or other errors)."
    )
    logger.info(f"Annual Reports page rendered successfully for company: {selected_id}")


if __name__ == "__main__":
    main()
