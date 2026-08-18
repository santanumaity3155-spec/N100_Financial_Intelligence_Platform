"""
N100 Financial Intelligence Platform - Main Dashboard Application

This is the main Streamlit application entry point for the N100 Financial
Intelligence Platform dashboard. It provides the application bootstrap,
sidebar navigation, and routing to all dashboard pages.

Usage:
    streamlit run src/dashboard/app.py
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import logging
import time
from typing import Optional

import streamlit as st

# Configure application logger
logger = logging.getLogger(__name__)

# Application metadata
APP_TITLE = "Nifty 100 Analytics"
APP_VERSION = "1.0.0"
APP_MODULE = "Module 1 - Streamlit Dashboard Scaffold"
APP_DESCRIPTION = """
Welcome to the N100 Financial Intelligence Platform dashboard. This application
provides comprehensive analytics and insights for Nifty 100 companies including:

- 📊 Company Profiles & Financial Statements
- 🔍 Stock Screening & Peer Comparison
- 📈 Trend Analysis & Sector Performance
- 💰 Valuation Metrics & Capital Structure
- 📑 Automated Reports & Exports

Navigate through the pages using the sidebar to explore different analytics modules.
"""


def configure_page() -> None:
    """
    Configure Streamlit page settings.
    
    Sets page title, layout, icon, and initial sidebar state.
    Should be called before any other Streamlit operations.
    """
    try:
        st.set_page_config(
            page_title=APP_TITLE,
            page_icon="📈",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        logger.info("Streamlit page configured successfully")
    except Exception as e:
        logger.error(f"Error configuring page: {str(e)}", exc_info=True)
        st.error("Failed to configure application. Please refresh the page.")


def render_sidebar() -> None:
    """
    Render the application sidebar with navigation and metadata.
    
    Displays:
    - Application title and logo
    - Current module information
    - Navigation guidance
    - App version
    - Footer with additional info
    """
    with st.sidebar:
        # Application header
        st.title("📈 N100 Analytics")
        st.markdown("---")
        
        # Module information
        st.subheader("📦 Current Module")
        st.info(f"**{APP_MODULE}**")
        st.markdown("---")
        
        # Navigation guidance
        st.subheader("🧭 Navigation")
        st.markdown("""
        **Available Pages:**
        
        1. 🏠 **Home** - Dashboard overview
        2. 👤 **Profile** - Company profiles
        3. 🔍 **Screener** - Stock screening
        4. 👥 **Peers** - Peer comparison
        5. 📈 **Trends** - Trend analysis
        6. 🏭 **Sectors** - Sector analysis
        7. 💰 **Capital** - Capital structure
        8. 📑 **Reports** - Reports & exports
        
        Use the page selector above to navigate.
        """)
        st.markdown("---")
        
        # Application status
        st.subheader("⚙️ Application Status")
        
        # Check database status
        try:
            from src.dashboard.utils.db import get_database_info
            db_info = get_database_info()
            
            if db_info["exists"]:
                st.success("✅ Database Connected")
                st.caption(f"Size: {db_info['size_mb']} MB")
                st.caption(f"Tables: {len(db_info['tables'])}")
            else:
                st.warning("⚠️ Database Not Found")
                st.caption("Run ETL pipeline to initialize database")
        except Exception as e:
            st.error("❌ Database Error")
            logger.error(f"Error checking database status: {str(e)}")
        
        st.markdown("---")
        
        # App version and info
        st.subheader("ℹ️ Information")
        st.caption(f"**Version:** {APP_VERSION}")
        st.caption(f"**Module:** Module 1")
        st.caption("**Status:** Development")
        
        # Footer
        st.markdown("---")
        st.markdown(
            "<div style='text-align: center; color: #666666; font-size: 0.8em;'>"
            "N100 Financial Intelligence Platform<br>"
            "© 2025 Bluestock"
            "</div>",
            unsafe_allow_html=True
        )


def render_main_content() -> None:
    """
    Render the main content area of the dashboard.
    
    Displays welcome message, instructions, and application status.
    This is the default view when no specific page is selected.
    """
    # Application header
    st.title(f"📈 {APP_TITLE}")
    st.markdown("---")
    
    # Welcome section
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.success("## 👋 Welcome to N100 Analytics!")
        st.markdown("---")
    
    # Description
    st.markdown(APP_DESCRIPTION)
    st.markdown("---")
    
    # Instructions
    st.subheader("📋 How to Use This Dashboard")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### Getting Started
        
        1. **Navigate** using the sidebar menu
        2. **Select** a company from dropdowns
        3. **Explore** financial data and analytics
        4. **Compare** with peers and sectors
        5. **Export** reports for further analysis
        """)
    
    with col2:
        st.markdown("""
        ### Features
        
        - **Real-time Data**: Cached for 10 minutes
        - **Interactive Charts**: Powered by Plotly
        - **Comprehensive Coverage**: All Nifty 100 companies
        - **Multi-year Analysis**: Historical trends
        - **Peer Comparison**: Benchmark performance
        """)
    
    st.markdown("---")
    
    # Application status
    st.subheader("🔍 Application Status")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Module",
            value="Module 1",
            delta="Dashboard Scaffold"
        )
    
    with col2:
        st.metric(
            label="Status",
            value="Active",
            delta="Development"
        )
    
    with col3:
        st.metric(
            label="Version",
            value=APP_VERSION,
            delta="Stable"
        )
    
    st.markdown("---")
    
    # Navigation guidance
    st.subheader("🧭 Navigation Guidance")
    
    st.info("""
    **👈 Use the sidebar to navigate between pages**
    
    Each page is designed for specific analytics:
    - **Home**: Overview and getting started
    - **Profile**: Deep dive into individual companies
    - **Screener**: Filter and screen stocks
    - **Peers**: Compare with peer groups
    - **Trends**: Analyze trends over time
    - **Sectors**: Sector-wide analysis
    - **Capital**: Capital structure analysis
    - **Reports**: Generate and export reports
    """)
    
    st.markdown("---")
    
    # Technical information
    with st.expander("🔧 Technical Information"):
        st.markdown("""
        ### Technology Stack
        
        - **Framework**: Streamlit
        - **Database**: SQLite3
        - **Data Processing**: Pandas
        - **Visualization**: Plotly
        - **Language**: Python 3.11+
        
        ### Performance
        
        - **Cache TTL**: 600 seconds (10 minutes)
        - **Query Optimization**: Indexed database
        - **Lazy Loading**: On-demand data retrieval
        
        ### Architecture
        
        - **Modular Design**: Separation of concerns
        - **Error Handling**: Comprehensive exception management
        - **Logging**: Full audit trail
        - **Type Safety**: Type hints throughout
        """)
    
    st.markdown("---")
    
    # Footer message
    st.caption(
        "💡 **Tip**: Bookmark this dashboard for quick access to Nifty 100 analytics. "
        "Data is cached for 10 minutes to optimize performance."
    )


def initialize_logging() -> None:
    """
    Initialize application logging.
    
    Configures logging to capture application events, errors,
    and performance metrics.
    """
    try:
        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "dashboard.log"),
                logging.StreamHandler()
            ]
        )
        
        logger.info("=" * 80)
        logger.info(f"{APP_TITLE} - Application Starting")
        logger.info(f"Version: {APP_VERSION}")
        logger.info(f"Module: {APP_MODULE}")
        logger.info("=" * 80)
        
    except Exception as e:
        print(f"Warning: Could not initialize logging: {str(e)}")


def main() -> None:
    """
    Main application entry point.
    
    Orchestrates the application bootstrap and rendering:
    1. Initialize logging
    2. Configure page settings
    3. Render sidebar
    4. Render main content
    """
    try:
        # Initialize logging first
        initialize_logging()
        
        # Configure Streamlit page
        configure_page()
        
        # Render sidebar
        render_sidebar()
        
        # Render main content
        render_main_content()
        
        logger.info("Application rendered successfully")
        
    except Exception as e:
        logger.error(f"Critical error in main(): {str(e)}", exc_info=True)
        st.error("An unexpected error occurred. Please check the logs and try again.")


if __name__ == "__main__":
    main()