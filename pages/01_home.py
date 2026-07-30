"""
Home Page - N100 Financial Intelligence Platform

This page serves as the dashboard overview and landing page.
It provides a welcome message, quick navigation guide, and
application status information.

This is a placeholder page for Module 1. Analytics will be
implemented in subsequent modules.
"""

import logging
import streamlit as st

# Configure page logger
logger = logging.getLogger(__name__)

# Page header
st.title("🏠 Home")
st.markdown("---")

# Welcome section
st.header("👋 Welcome to N100 Analytics")
st.markdown("""
This is your comprehensive analytics platform for **Nifty 100 companies**.
Explore financial data, analyze trends, compare peers, and make informed
investment decisions.
""")

st.markdown("---")

# Quick overview
st.subheader("📊 Dashboard Overview")

col1, col2, col3 = st.columns(3)

with col1:
    st.info("""
    ### 📈 100 Companies
    Complete coverage of Nifty 100 index with comprehensive financial data
    """)

with col2:
    st.success("""
    ### 📅 Multi-Year Data
    Historical financial statements spanning multiple years for trend analysis
    """)

with col3:
    st.warning("""
    ### 🔍 Advanced Analytics
    Screening, peer comparison, sector analysis, and automated reporting
    """)

st.markdown("---")

# Navigation guide
st.subheader("🧭 Quick Navigation Guide")

st.markdown("""
### Available Pages

Use the **sidebar** or **page selector** above to navigate between different analytics modules:

| Page | Icon | Description |
|------|------|-------------|
| **Home** | 🏠 | Dashboard overview and welcome |
| **Profile** | 👤 | Deep dive into individual companies |
| **Screener** | 🔍 | Filter and screen stocks based on criteria |
| **Peers** | 👥 | Compare companies with peer groups |
| **Trends** | 📈 | Analyze financial trends over time |
| **Sectors** | 🏭 | Sector-wide performance analysis |
| **Capital** | 💰 | Capital structure and valuation metrics |
| **Reports** | 📑 | Generate and export comprehensive reports |
""")

st.markdown("---")

# Getting started
st.subheader("🚀 Getting Started")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### First Steps
    
    1. **Explore the Dashboard**
       - Navigate through different pages using the sidebar
       - Each page is designed for specific analytics tasks
    
    2. **Select a Company**
       - Use dropdown selectors to choose companies
       - View detailed financial statements and metrics
    
    3. **Analyze Data**
       - Interactive charts and tables
       - Compare with peers and sectors
       - Export data for further analysis
    """)

with col2:
    st.markdown("""
    ### Key Features
    
    - **Real-time Data**: Cached for optimal performance
    - **Interactive Visualizations**: Powered by Plotly
    - **Comprehensive Coverage**: All Nifty 100 companies
    - **Multi-year Analysis**: Historical trend analysis
    - **Peer Comparison**: Benchmark against industry peers
    - **Automated Reports**: Generate professional reports
    """)

st.markdown("---")

# Status information
st.subheader("ℹ️ Application Status")

col1, col2, col3, col4 = st.columns(4)

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
        value="1.0.0",
        delta="Stable"
    )

with col4:
    st.metric(
        label="Database",
        value="Ready",
        delta="Connected"
    )

st.markdown("---")

# Placeholder for future features
st.subheader("🔜 Coming Soon")

st.info("""
**Module 2 & Beyond** will include:

- 📊 **Interactive Charts**: Financial statement visualizations
- 🔍 **Advanced Screening**: Multi-criteria stock screening
- 👥 **Peer Analysis**: Detailed peer comparison metrics
- 📈 **Trend Analysis**: Year-over-year growth trends
- 🏭 **Sector Heatmaps**: Sector performance visualization
- 💰 **Valuation Models**: DCF and relative valuation
- 📑 **Report Generation**: PDF and Excel exports
- 📧 **Email Reports**: Automated report delivery
""")

st.markdown("---")

# Footer
st.caption("""
💡 **Tip**: This dashboard is optimized for desktop viewing. 
Data is cached for 10 minutes to ensure fast performance.
""")

# Log page visit
logger.info("Home page accessed")