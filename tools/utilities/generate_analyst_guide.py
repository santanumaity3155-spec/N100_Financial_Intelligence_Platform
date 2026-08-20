"""
generate_analyst_guide.py

Generates docs/analyst_guide.pdf for N100 Financial Intelligence Platform.
Fulfills Phase 1 requirements: >= 10 pages (14 pages structured),
professional styling, headers, footers, page numbering, code snippets,
tables, and comprehensive operational guide.
"""

import sys
import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
import pypdf

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#4A5568"))

        # Skip header on page 1 (Title Page)
        if self._pageNumber > 1:
            self.drawString(54, 752, "N100 Financial Intelligence Platform — Analyst Guide")
            self.setStrokeColor(colors.HexColor("#CBD5E0"))
            self.setLineWidth(0.5)
            self.line(54, 744, 558, 744)

        # Footer on all pages
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 32, page_str)
        self.drawString(54, 32, "CONFIDENTIAL — Bluestock Financial Analytics")
        self.setStrokeColor(colors.HexColor("#CBD5E0"))
        self.setLineWidth(0.5)
        self.line(54, 44, 558, 44)

        self.restoreState()


def create_analyst_guide():
    docs_dir = Path("docs")
    docs_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = docs_dir / "analyst_guide.pdf"

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=48,
        bottomMargin=48
    )

    styles = getSampleStyleSheet()

    # Custom typography styles
    title_style = ParagraphStyle(
        "CoverTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#1A365D"),
        spaceAfter=8
    )

    subtitle_style = ParagraphStyle(
        "CoverSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=18,
        textColor=colors.HexColor("#2B6CB0"),
        spaceAfter=14
    )

    h1_style = ParagraphStyle(
        "Heading1_Custom",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#1A365D"),
        spaceAfter=8,
        spaceBefore=4
    )

    h2_style = ParagraphStyle(
        "Heading2_Custom",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11.5,
        leading=15,
        textColor=colors.HexColor("#2D3748"),
        spaceAfter=5,
        spaceBefore=6
    )

    body_style = ParagraphStyle(
        "Body_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#2D3748"),
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        "Bullet_Custom",
        parent=body_style,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=3
    )

    code_style = ParagraphStyle(
        "Code_Custom",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#1A202C"),
        backColor=colors.HexColor("#EDF2F7"),
        borderColor=colors.HexColor("#CBD5E0"),
        borderWidth=0.5,
        borderPadding=5,
        spaceAfter=6
    )

    callout_style = ParagraphStyle(
        "Callout_Custom",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#2C5282"),
        backColor=colors.HexColor("#EBF8FF"),
        borderColor=colors.HexColor("#3182CE"),
        borderWidth=1,
        borderPadding=6,
        spaceAfter=6
    )

    story = []

    # =========================================================================
    # PAGE 1: Cover & Executive Summary
    # =========================================================================
    story.append(Spacer(1, 10))
    story.append(Paragraph("N100 Financial Intelligence Platform", title_style))
    story.append(Paragraph("Comprehensive Analyst & Operational Guide", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#3182CE"), spaceAfter=12))

    story.append(Paragraph("Executive Summary & Platform Scope", h1_style))
    story.append(Paragraph(
        "The N100 Financial Intelligence Platform is a state-of-the-art financial analysis, peer benchmarking, "
        "and screening system engineered for institutional equity analysts, portfolio managers, and risk research teams. "
        "The platform ingests multi-year financial statements across Nifty 100 constituents, computes over 30 financial ratios, "
        "and delivers real-time screener capabilities, interactive visual analytics, and automated PDF tearsheets.",
        body_style
    ))

    story.append(Paragraph("Target Users", h2_style))
    story.append(Paragraph("• <b>Equity Research Analysts</b>: Perform deep-dive financial profile assessments and ratio analysis.", bullet_style))
    story.append(Paragraph("• <b>Portfolio Managers</b>: Evaluate sector allocations, peer rankings, and risk metrics.", bullet_style))
    story.append(Paragraph("• <b>Risk & Credit Officers</b>: Monitor financial distress alerts, leverage thresholds, and cash-flow health.", bullet_style))

    story.append(Paragraph("Major Platform Capabilities", h2_style))
    story.append(Paragraph("• <b>Automated ETL Engine</b>: Parses Excel statements into a normalized SQLite database with high data integrity.", bullet_style))
    story.append(Paragraph("• <b>Screener & Peer Benchmarking</b>: Real-time filtering across 20+ ratio metrics and 13 peer groups.", bullet_style))
    story.append(Paragraph("• <b>FastAPI REST Server</b>: High-performance JSON endpoints for automated integrations and data feeds.", bullet_style))
    story.append(Paragraph("• <b>Interactive Streamlit Dashboard</b>: 8 modular visualization screens with Plotly charts.", bullet_style))
    story.append(Paragraph("• <b>NLP & ML Engine</b>: Automated pros/cons text extraction and K-means company clustering.", bullet_style))
    story.append(Paragraph("• <b>ReportLab Tearsheet Generator</b>: Single-click institutional-grade PDF summary exports.", bullet_style))

    story.append(Spacer(1, 8))
    table_data = [
        ["Technology Layer", "Components & Libraries"],
        ["Core Language", "Python 3.10+"],
        ["Data Processing", "Pandas, NumPy, OpenPyXL"],
        ["Database Backend", "SQLite 3.25+"],
        ["API Framework", "FastAPI, Uvicorn, Pydantic v2"],
        ["Frontend UI", "Streamlit 1.42+, Plotly 6.0+"],
        ["Machine Learning / NLP", "Scikit-Learn, SciPy, Custom Pattern Rules"],
        ["Reporting & PDF", "ReportLab 5.0+, PyPDF"],
        ["Testing & Quality", "Pytest, Black, Ruff"]
    ]
    t = Table(table_data, colWidths=[140, 360])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (1,0), colors.HexColor("#2B6CB0")),
        ('TEXTCOLOR', (0,0), (1,0), colors.white),
        ('FONTNAME', (0,0), (1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8.5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F7FAFC")]),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t)
    story.append(PageBreak())

    # =========================================================================
    # PAGE 2: Getting Started & System Setup
    # =========================================================================
    story.append(Paragraph("Getting Started & Environment Setup", h1_style))
    story.append(Paragraph(
        "Setting up the N100 Financial Intelligence Platform requires Python 3.10+ and a standard virtual environment. "
        "The repository relies on standard directory conventions and SQLite for zero-configuration database deployment.",
        body_style
    ))

    story.append(Paragraph("1. Environment Prerequisites", h2_style))
    story.append(Paragraph("Ensure Python 3.10 or later is installed on your operating system (Windows, macOS, or Linux).", body_style))
    story.append(Paragraph("<code>python --version</code>", code_style))

    story.append(Paragraph("2. Virtual Environment Creation", h2_style))
    story.append(Paragraph("Create and activate an isolated Python virtual environment:", body_style))
    story.append(Paragraph("<code>python -m venv venv<br/># Windows:<br/>.\\venv\\Scripts\\activate<br/># macOS/Linux:<br/>source venv/bin/activate</code>", code_style))

    story.append(Paragraph("3. Dependency Installation", h2_style))
    story.append(Paragraph("Install required packages specified in the environment:", body_style))
    story.append(Paragraph("<code>pip install -r requirements-dashboard.txt</code>", code_style))

    story.append(Paragraph("4. Project Directory Hierarchy", h2_style))
    tree_text = (
        "N100_Financial_Intelligence_Platform/<br/>"
        "├── data/                       # Source Excel financial files<br/>"
        "├── docs/                       # Platform documentation & Analyst Guide PDF<br/>"
        "├── output/                     # Exported CSVs, Excel reports & final database<br/>"
        "│   ├── NIFTY_SMALL_100.db      # Authoritative SQLite Database<br/>"
        "│   └── final_deliverables/     # Consolidated 23 project deliverables<br/>"
        "├── reports/                    # Data quality reports & PNG figures<br/>"
        "├── src/                        # Core Python package<br/>"
        "│   ├── analytics/              # Valuation, Peer, Trend & Cashflow engines<br/>"
        "│   ├── api/                    # FastAPI server & REST router endpoints<br/>"
        "│   ├── dashboard/              # Streamlit app.py & modular page views<br/>"
        "│   ├── etl/                    # Extraction, normalization & SQLite loading<br/>"
        "│   ├── kpi_engine/             # 30+ financial ratio calculation engine<br/>"
        "│   └── nlp/                    # Sentiment & pros/cons text parser<br/>"
        "└── tests/                      # Pytest unit, integration & performance suite"
    )
    story.append(Paragraph(tree_text, code_style))
    story.append(PageBreak())

    # =========================================================================
    # PAGE 3: Running the ETL Pipeline
    # =========================================================================
    story.append(Paragraph("Running the ETL Pipeline", h1_style))
    story.append(Paragraph(
        "The N100 Data Engine ingests unstructured multi-year Excel balance sheets, profit & loss accounts, "
        "and cash flow statements. It normalizes financial metrics across divergent accounting line items and "
        "populates the SQLite database schema.",
        body_style
    ))

    story.append(Paragraph("ETL Process Workflow", h2_style))
    story.append(Paragraph("1. <b>Extraction</b>: Scans <code>data/</code> directory for raw company financial workbooks.", bullet_style))
    story.append(Paragraph("2. <b>Normalization</b>: Standardizes key line items (e.g. Total Revenue, EBITDA, PAT, Net Debt).", bullet_style))
    story.append(Paragraph("3. <b>Validation</b>: Asserts Balance Sheet equation (Assets = Liabilities + Equity) and handles missing values.", bullet_style))
    story.append(Paragraph("4. <b>KPI Calculation</b>: Calculates 30+ financial ratios across historical fiscal years.", bullet_style))
    story.append(Paragraph("5. <b>SQLite Loading</b>: Writes processed records into <code>output/NIFTY_SMALL_100.db</code>.", bullet_style))

    story.append(Paragraph("Executing the Pipeline", h2_style))
    story.append(Paragraph("Run the main ETL pipeline script directly from the repository root:", body_style))
    story.append(Paragraph("<code>python run_etl.py</code>", code_style))

    story.append(Paragraph("ETL Output Verification", h2_style))
    story.append(Paragraph(
        "Upon successful completion, the pipeline outputs summary logs to console and updates the SQLite database. "
        "Detailed HTML data quality reports are automatically written to <code>reports/</code>.",
        body_style
    ))

    etl_table = [
        ["Database Table", "Description", "Primary Key"],
        ["companies", "Company metadata, sector, industry", "company_id"],
        ["financial_kpis", "Calculated annual ratios (ROE, ROCE, P/E)", "id (company_id, period)"],
        ["balance_sheet", "Normalized balance sheet items", "id (company_id, period)"],
        ["income_statement", "Normalized P&L items", "id (company_id, period)"],
        ["cash_flow", "Normalized cash flow items", "id (company_id, period)"],
        ["peer_percentiles", "Peer-relative metric percentiles", "id (company_id, metric)"]
    ]
    t_etl = Table(etl_table, colWidths=[120, 250, 130])
    t_etl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2B6CB0")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8.5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F7FAFC")]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_etl)
    story.append(PageBreak())

    # =========================================================================
    # PAGE 4: Streamlit Dashboard Setup & Navigation
    # =========================================================================
    story.append(Paragraph("Streamlit Dashboard Overview", h1_style))
    story.append(Paragraph(
        "The N100 Streamlit Dashboard provides a responsive, web-based analytics portal. "
        "It connects directly to the SQLite backend and leverages Streamlit caching for sub-second page transition times.",
        body_style
    ))

    story.append(Paragraph("Launching the Application", h2_style))
    story.append(Paragraph("Execute the exact Streamlit entry point command from the repository root:", body_style))
    story.append(Paragraph("<code>streamlit run src/dashboard/app.py</code>", code_style))

    story.append(Paragraph("Accessing the Portal", h2_style))
    story.append(Paragraph(
        "Once initialized, open your browser and navigate to:<br/>"
        "<b>Local URL:</b> <code>http://localhost:8501</code><br/>"
        "<b>Network URL:</b> <code>http://&lt;your-ip&gt;:8501</code>",
        body_style
    ))

    story.append(Paragraph("Dashboard Architecture & Pages", h2_style))
    story.append(Paragraph(
        "The dashboard features a persistent sidebar with navigation controls, company filters, and global settings. "
        "The 8 main analytics screens are structured as follows:",
        body_style
    ))

    dash_table = [
        ["Page Number", "Module Name", "Primary Analytics Function"],
        ["01", "Home", "Platform Overview, System Health & Key Performance Cards"],
        ["02", "Company Profile", "Deep-dive Financial Statements, Ratio Grids & Historical Trends"],
        ["03", "Screener", "Multi-criteria Filter Engine with Custom Sliders & Preset Scenarios"],
        ["04", "Peers", "Industry Benchmarking, Percentile Ranks & Radar Overlay"],
        ["05", "Trends", "12-Year CAGR Analysis, Multi-Metric Plots & Growth Tracking"],
        ["06", "Sectors", "Sector Performance Heatmaps, Aggregations & Distribution Charts"],
        ["07", "Capital", "Capital Allocation Distribution & Cash Flow Intelligence Grid"],
        ["08", "Reports", "Valuation Flagging, PDF Tearsheet Generation & Batch Export"]
    ]
    t_dash = Table(dash_table, colWidths=[65, 125, 310])
    t_dash.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2B6CB0")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8.5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F7FAFC")]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_dash)
    story.append(PageBreak())

    # =========================================================================
    # PAGE 5: Dashboard — Home & Company Profile
    # =========================================================================
    story.append(Paragraph("Dashboard — Home & Company Profile", h1_style))
    story.append(Paragraph(
        "The Home and Company Profile screens provide the primary entry points for qualitative and quantitative stock analysis.",
        body_style
    ))

    story.append(Paragraph("1. Home Screen Features", h2_style))
    story.append(Paragraph("• <b>KPI Snapshot</b>: Displays total coverage metrics (92 Companies, 9 Sectors, 12 Fiscal Years).", bullet_style))
    story.append(Paragraph("• <b>System Health Check</b>: Live status indicator of database connection and loaded tables.", bullet_style))
    story.append(Paragraph("• <b>Quick Search</b>: Instant ticker look-up to auto-redirect to dedicated company profiles.", bullet_style))

    story.append(Paragraph("2. Company Profile Navigation", h2_style))
    story.append(Paragraph(
        "Select any company from the sidebar drop-down menu (e.g. TCS, RELIANCE, INFYS). "
        "The Profile view renders five core tab views:",
        body_style
    ))
    story.append(Paragraph("• <b>Financial Overview</b>: Summary KPI cards including Market Cap, P/E Ratio, ROE, ROCE, and Debt/Equity.", bullet_style))
    story.append(Paragraph("• <b>Income Statement</b>: Multi-year breakdown of Revenue, Operating Profit, EBITDA, and Net Income.", bullet_style))
    story.append(Paragraph("• <b>Balance Sheet</b>: Assets, Equity, Non-Current Liabilities, and Working Capital trend lines.", bullet_style))
    story.append(Paragraph("• <b>Cash Flow Statement</b>: Operating Cash Flow (CFO), Capital Expenditure (CapEx), and Free Cash Flow (FCF).", bullet_style))
    story.append(Paragraph("• <b>Ratio Analytics Grid</b>: Complete 30+ ratio breakdown grouped by Profitability, Liquidity, Solvency, and Efficiency.", bullet_style))

    story.append(Spacer(1, 4))
    story.append(Paragraph("Analyst Interpretation Guidance", callout_style))
    story.append(Paragraph(
        "<b>Tip for Analysts:</b> Examine the FCF vs Net Profit relationship over a 3-year trailing window. "
        "Companies displaying strong Net Income growth without corresponding OCF generation may indicate aggressive revenue recognition "
        "or working capital deterioration.",
        body_style
    ))
    story.append(PageBreak())

    # =========================================================================
    # PAGE 6: Dashboard — Screener & Peer Comparison
    # =========================================================================
    story.append(Paragraph("Dashboard — Screener & Peer Comparison", h1_style))
    story.append(Paragraph(
        "The Screener and Peer Comparison engines enable institutional investors to identify investment candidates "
        "and benchmark company performance against industry cohorts.",
        body_style
    ))

    story.append(Paragraph("1. Stock Screener Usage", h2_style))
    story.append(Paragraph("Navigate to <b>03_screener</b> from the sidebar. Analysts can apply custom criteria sliders:", body_style))
    story.append(Paragraph("• <b>Profitability Filters</b>: Min Return on Equity (ROE >= 15%), Min ROCE (>= 18%).", bullet_style))
    story.append(Paragraph("• <b>Valuation Filters</b>: Max P/E Ratio (<= 25.0), Max P/B Ratio (<= 3.5).", bullet_style))
    story.append(Paragraph("• <b>Financial Health Filters</b>: Max Debt-to-Equity (<= 0.5), Min Interest Coverage (>= 4.0).", bullet_style))
    story.append(Paragraph("• <b>Growth Filters</b>: Min 3-Yr Revenue CAGR (>= 10%), Min 3-Yr Profit CAGR (>= 12%).", bullet_style))

    story.append(Paragraph("Preset Screening Scenarios", h2_style))
    story.append(Paragraph("Click preset scenario buttons for instant filter setup:", body_style))
    story.append(Paragraph("• <b>Quality Compounders</b>: High ROE (>20%), Low Debt (D/E <0.3), Positive FCF.", bullet_style))
    story.append(Paragraph("• <b>Deep Value</b>: Low P/E (<15), Low P/B (<1.5), Solvent Balance Sheet.", bullet_style))
    story.append(Paragraph("• <b>High Growth</b>: Revenue CAGR >15%, Profit CAGR >20%.", bullet_style))

    story.append(Paragraph("2. Peer Comparison & Radar Analysis", h2_style))
    story.append(Paragraph("Navigate to <b>04_peers</b> to evaluate company positioning across its designated peer group (e.g. IT Services, Banking, Pharma):", body_style))
    story.append(Paragraph("• <b>Percentile Rankings</b>: Shows company percentile (0–100th percentile) across 10 key metrics.", bullet_style))
    story.append(Paragraph("• <b>Radar Overlay</b>: Generates a 10-axis polar plot comparing the company's percentile profile against the peer benchmark mean.", bullet_style))
    story.append(PageBreak())

    # =========================================================================
    # PAGE 7: Dashboard — Trends, Sectors & Capital Allocation
    # =========================================================================
    story.append(Paragraph("Dashboard — Trends, Sectors & Capital Allocation", h1_style))
    story.append(Paragraph(
        "Macro analytics pages synthesize cross-sectional industry data to highlight secular growth patterns and capital deployment efficiency.",
        body_style
    ))

    story.append(Paragraph("1. Trend Analysis (05_trends)", h2_style))
    story.append(Paragraph(
        "Analyze 12-year historical financial trajectories (2012–2024). "
        "Select up to 4 financial metrics simultaneously to compare growth momentum and margin trends over time. "
        "Calculates compound annual growth rates (CAGR) automatically.",
        body_style
    ))

    story.append(Paragraph("2. Sector Analytics (06_sectors)", h2_style))
    story.append(Paragraph(
        "Aggregates metrics across 9 industry sectors (Information Technology, Banking & Financials, Pharmaceuticals, Consumer Goods, Industrial, Energy, Automobile, Materials, Telecom).",
        body_style
    ))
    story.append(Paragraph("• <b>Sector Heatmaps</b>: Visualizes median ROE, Operating Margin, and Valuation Multiples across sectors.", bullet_style))
    story.append(Paragraph("• <b>Sector Bubble Chart</b>: Plots Sector ROE vs P/E Multiple with bubble size scaled by Total Market Cap.", bullet_style))

    story.append(Paragraph("3. Capital Allocation Intelligence (07_capital)", h2_style))
    story.append(Paragraph(
        "Evaluates corporate cash deployment strategies over multi-year cycles. "
        "Categorizes cash utilization across CapEx (Reinvestment), Dividends/Buybacks (Shareholder Returns), Debt Reduction, and Cash Accumulation.",
        body_style
    ))

    story.append(Spacer(1, 4))
    story.append(Paragraph("Cash Flow Matrix Categories", callout_style))
    story.append(Paragraph(
        "• <b>Reinvestment Champions</b>: CapEx / Operating Cash Flow > 60% with ROIC > 15%.<br/>"
        "• <b>Shareholder Value Creators</b>: Dividend Yield + Buyback Yield > 4% with FCF Conversion > 80%.<br/>"
        "• <b>Capital Consumptive</b>: Operating Cash Flow < CapEx over 3 consecutive fiscal years.",
        body_style
    ))
    story.append(PageBreak())

    # =========================================================================
    # PAGE 8: Dashboard — Reports & Valuation
    # =========================================================================
    story.append(Paragraph("Dashboard — Reports & Valuation", h1_style))
    story.append(Paragraph(
        "The Reports & Valuation page (<b>08_reports</b>) serves as the primary output hub for institutional reporting, "
        "valuation anomaly detection, and PDF tearsheet generation.",
        body_style
    ))

    story.append(Paragraph("1. Automated Valuation Engine", h2_style))
    story.append(Paragraph(
        "Computes absolute and peer-relative valuation metrics including Price-to-Earnings (P/E), Price-to-Book (P/B), "
        "and Enterprise Value to EBITDA (EV/EBITDA). "
        "Applies automated valuation flagging rules:",
        body_style
    ))
    story.append(Paragraph("• <b>Overvalued Flag</b>: P/E > 1.5x Peer Group Median AND ROE < Peer Group Median.", bullet_style))
    story.append(Paragraph("• <b>Undervalued Flag</b>: P/E < 0.7x Peer Group Median AND ROE > Peer Group Median.", bullet_style))
    story.append(Paragraph("• <b>Fair Value</b>: Multiples within +/- 15% of peer median.", bullet_style))

    story.append(Paragraph("2. Generating PDF Tearsheets", h2_style))
    story.append(Paragraph(
        "Analysts can generate instant institutional PDF tearsheets directly from the Streamlit UI:",
        body_style
    ))
    story.append(Paragraph("1. Select Target Company from the drop-down menu on page 08_reports.", bullet_style))
    story.append(Paragraph("2. Click the <b>Generate PDF Tearsheet</b> button.", bullet_style))
    story.append(Paragraph("3. Preview the generated tearsheet online or download the compiled PDF file.", bullet_style))

    story.append(Paragraph("3. Export Capabilities", h2_style))
    story.append(Paragraph(
        "Supports one-click export of underlying datasets to Excel and CSV formats:<br/>"
        "• <code>output/valuation_summary.xlsx</code>: Complete valuation master spreadsheet.<br/>"
        "• <code>output/valuation_flags.csv</code>: Mispricing flags and anomaly alerts.",
        body_style
    ))
    story.append(PageBreak())

    # =========================================================================
    # PAGE 9: FastAPI Architecture & Endpoint Reference
    # =========================================================================
    story.append(Paragraph("FastAPI Server & REST API Reference", h1_style))
    story.append(Paragraph(
        "The N100 backend exposes a high-performance REST API built on FastAPI and Uvicorn. "
        "It features automatic Pydantic request validation, CORS middleware, OpenAPI specifications, and Swagger UI documentation.",
        body_style
    ))

    story.append(Paragraph("API Startup & Interactive Docs", h2_style))
    story.append(Paragraph("Start the production FastAPI server using Uvicorn:", body_style))
    story.append(Paragraph("<code>uvicorn src.api.main:app --reload --port 8000</code>", code_style))
    story.append(Paragraph(
        "<b>Base URL:</b> <code>http://localhost:8000/api/v1</code> | "
        "<b>Interactive Docs:</b> <code>http://localhost:8000/docs</code> | "
        "<b>OpenAPI JSON:</b> <code>http://localhost:8000/openapi.json</code>",
        body_style
    ))

    story.append(Paragraph("Authoritative Endpoint Curl Examples", h2_style))

    curl_examples = [
        ("1. Health Endpoint", "curl -X GET http://localhost:8000/api/v1/health"),
        ("2. Companies Endpoint", "curl -X GET http://localhost:8000/api/v1/companies"),
        ("3. Specific Company (TCS)", "curl -X GET http://localhost:8000/api/v1/companies/TCS"),
        ("4. Screener Endpoint", "curl -X GET \"http://localhost:8000/api/v1/screener?min_roe=15&max_pe=25\""),
        ("5. Sectors Endpoint", "curl -X GET http://localhost:8000/api/v1/sectors"),
        ("6. Peers Endpoint", "curl -X GET http://localhost:8000/api/v1/peers/TCS"),
        ("7. Valuation Endpoint", "curl -X GET http://localhost:8000/api/v1/valuation/TCS"),
        ("8. Portfolio Endpoint", "curl -X GET http://localhost:8000/api/v1/portfolio")
    ]

    for title, cmd in curl_examples:
        story.append(Paragraph(title, h2_style))
        story.append(Paragraph(f"<code>{cmd}</code>", code_style))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 10: PDF Reports & Tearsheet Generation Engine
    # =========================================================================
    story.append(Paragraph("PDF Reports & Tearsheet Generation Engine", h1_style))
    story.append(Paragraph(
        "The Report Generation Engine (<code>src/reports/</code>) builds publication-grade PDF documents using ReportLab. "
        "It features dynamic table layout, vector chart embedding, and two-pass page numbering.",
        body_style
    ))

    story.append(Paragraph("Report Types & Output Directories", h2_style))
    story.append(Paragraph("• <b>Company Tearsheets</b>: Single/multi-page summary of financial health, ratios, and peer ranks. Saved to <code>reports/tearsheets/</code>.", bullet_style))
    story.append(Paragraph("• <b>Peer Comparison Reports</b>: Detailed markdown & PDF peer comparison files. Saved to <code>output/peer_reports/</code>.", bullet_style))
    story.append(Paragraph("• <b>Sector Analysis Reports</b>: Sector-wide financial summaries. Saved to <code>reports/sector/</code>.", bullet_style))
    story.append(Paragraph("• <b>Portfolio Analysis Report</b>: Aggregate portfolio risk and exposure breakdown. Saved to <code>reports/portfolio/</code>.", bullet_style))

    story.append(Paragraph("Programmatic Batch Generation Command", h2_style))
    story.append(Paragraph("Generate tearsheets for all companies programmatically:", body_style))
    story.append(Paragraph("<code>python -m src.reports.tearsheet_generator --all</code>", code_style))

    story.append(Paragraph("Handling Skipped Companies", h2_style))
    story.append(Paragraph(
        "If a company lacks sufficient historical balance sheet data to compute required ratio metrics, "
        "the generator logs a diagnostic entry to <code>output/skipped_tearsheets.csv</code> and continues batch execution without failing.",
        body_style
    ))

    story.append(Spacer(1, 4))
    story.append(Paragraph("PDF Quality Inspection Checklist", callout_style))
    story.append(Paragraph(
        "1. Open compiled PDF in any standard reader (Adobe Acrobat, Chrome, Preview).<br/>"
        "2. Verify clean header line and page numbers ('Page X of Y').<br/>"
        "3. Assert no overlapping text boxes or table column truncations.<br/>"
        "4. Confirm vector graphics and colors render crisply.",
        body_style
    ))
    story.append(PageBreak())

    # =========================================================================
    # PAGE 11: Advanced Analytics & Intelligence
    # =========================================================================
    story.append(Paragraph("Advanced Analytics & Intelligence Engines", h1_style))
    story.append(Paragraph(
        "Beyond traditional ratio analysis, the platform incorporates advanced mathematical models, "
        "NLP sentiment engines, and machine learning algorithms.",
        body_style
    ))

    story.append(Paragraph("1. NLP Pros & Cons Generator (src/nlp/)", h2_style))
    story.append(Paragraph(
        "Parses quantitative financial statements and qualitative commentary to generate human-readable investment highlights and risk alerts. "
        "Outputs consolidated findings to <code>output/pros_cons_generated.csv</code>.",
        body_style
    ))

    story.append(Paragraph("2. Unsupervised ML Clustering (src/analytics/)", h2_style))
    story.append(Paragraph(
        "Applies K-Means clustering across standardized financial metrics (ROE, Leverage, Margin, Asset Turnover) "
        "to group companies into behavioral peer clusters independent of broad sector classifications. "
        "Outputs cluster labels to <code>output/cluster_labels.csv</code> and centroids to <code>output/cluster_profiles.csv</code>.",
        body_style
    ))

    story.append(Paragraph("3. Financial Distress & Early Warning Alert System", h2_style))
    story.append(Paragraph(
        "Evaluates Altman Z-Score equivalents, Interest Coverage ratios, and CFO-to-Debt metrics to flag potential solvency distress. "
        "Flags are written to <code>output/distress_alerts.csv</code>.",
        body_style
    ))

    story.append(Paragraph("4. Ratio Correlation Analysis", h2_style))
    story.append(Paragraph(
        "Computes cross-metric Pearson correlation matrices across all constituent companies. "
        "Visual correlation heatmaps are generated and saved to <code>reports/correlation_heatmap.png</code>.",
        body_style
    ))
    story.append(PageBreak())

    # =========================================================================
    # PAGE 12: Troubleshooting & Known Issue Resolution
    # =========================================================================
    story.append(Paragraph("Troubleshooting & Operational FAQ", h1_style))
    story.append(Paragraph(
        "This section details diagnostic steps and practical shell commands for resolving common environment, database, and service issues.",
        body_style
    ))

    trouble_data = [
        ["Symptom / Error", "Root Cause", "Practical Solution Command"],
        ["Database Not Found", "SQLite file missing at expected path", "Run <code>python run_etl.py</code> to rebuild database."],
        ["Streamlit Entry Point Error", "Invoking wrong path like app.py", "Run command: <code>streamlit run src/dashboard/app.py</code>."],
        ["Port 8501 Already in Use", "Previous Streamlit instance active", "Kill process on 8501 or use <code>--server.port 8502</code>."],
        ["Port 8000 Already in Use", "FastAPI server running in background", "Kill process on port 8000."],
        ["API Unavailable / 404", "FastAPI server not started", "Launch API: <code>uvicorn src.api.main:app --reload --port 8000</code>."],
        ["Missing Python Module", "Virtual environment missing package", "Run <code>pip install -r requirements-dashboard.txt</code>."],
        ["Empty Dashboard Charts", "No company selected or DB locked", "Select company from sidebar or verify DB path."],
        ["PDF Generation Failure", "ReportLab missing or directory unwritable", "Ensure ReportLab installed and directory exists."]
    ]
    t_trouble = Table(trouble_data, colWidths=[110, 150, 240])
    t_trouble.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2B6CB0")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F7FAFC")]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_trouble)
    story.append(PageBreak())

    # =========================================================================
    # PAGE 13: Quality Assurance & Testing Suite
    # =========================================================================
    story.append(Paragraph("Quality Assurance & Testing Suite", h1_style))
    story.append(Paragraph(
        "The platform includes a robust Pytest suite covering unit calculations, API endpoint validation, "
        "NLP rule accuracy, report generation integrity, and load performance.",
        body_style
    ))

    story.append(Paragraph("Executing Test Commands", h2_style))

    test_commands = [
        ("1. Run Full Regression Suite", "python -m pytest tests/ -q"),
        ("2. Run API Endpoint Tests", "python -m pytest tests/api/ -q"),
        ("3. Run Analytics & KPI Engine Tests", "python -m pytest tests/analytics/ -q"),
        ("4. Run NLP Engine Tests", "python -m pytest tests/nlp/ -q"),
        ("5. Run Reports & Tearsheet Tests", "python -m pytest tests/reports/ -q"),
        ("6. Run Performance & Load Benchmarks", "python -m pytest tests/performance/ -q"),
        ("7. Run Integration End-to-End Suite", "python -m pytest tests/integration/ -q")
    ]

    for title, cmd in test_commands:
        story.append(Paragraph(title, h2_style))
        story.append(Paragraph(f"<code>{cmd}</code>", code_style))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 14: Recommended Analyst Operational Workflow
    # =========================================================================
    story.append(Paragraph("Recommended Analyst Operational Workflow", h1_style))
    story.append(Paragraph(
        "Follow this 12-step standardized operational workflow for daily financial research, screening, and report compilation:",
        body_style
    ))

    workflow_steps = [
        ("Step 1", "Verify Database", "Check that <code>output/NIFTY_SMALL_100.db</code> exists and is populated."),
        ("Step 2", "Validate Data Quality", "Run <code>python run_etl.py</code> if raw Excel files have updated."),
        ("Step 3", "Start FastAPI Server", "Launch backend: <code>uvicorn src.api.main:app --reload --port 8000</code>."),
        ("Step 4", "Launch Dashboard UI", "Start frontend: <code>streamlit run src/dashboard/app.py</code>."),
        ("Step 5", "Select Target Company", "Use sidebar company selector on Page 02_profile to view statements."),
        ("Step 6", "Analyze Key Ratios", "Review Profitability, Solvency, and Free Cash Flow metrics."),
        ("Step 7", "Run Custom Screener", "Navigate to Page 03_screener to filter candidates matching thesis."),
        ("Step 8", "Benchmark Peer Group", "Navigate to Page 04_peers to inspect percentile ranks and radar plots."),
        ("Step 9", "Evaluate Sector Context", "Navigate to Page 06_sectors to review sector margin heatmaps."),
        ("Step 10", "Review Cash Deployment", "Navigate to Page 07_capital to analyze CapEx vs Dividend ratios."),
        ("Step 11", "Inspect Valuation Flags", "Navigate to Page 08_reports to check automated P/E mispricing flags."),
        ("Step 12", "Export Tearsheet PDF", "Generate and download institutional PDF tearsheet for presentations.")
    ]

    wf_table = []
    wf_table.append(["Step", "Action Item", "Operational Instructions"])
    for s, a, d in workflow_steps:
        wf_table.append([s, a, Paragraph(d, body_style)])

    t_wf = Table(wf_table, colWidths=[45, 130, 325])
    t_wf.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2B6CB0")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F7FAFC")]),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_wf)

    # Build PDF with custom NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)

    # Verify Page Count using pypdf
    reader = pypdf.PdfReader(str(pdf_path))
    num_pages = len(reader.pages)
    print(f"Successfully generated {pdf_path}. Total Page Count: {num_pages}")
    return num_pages

if __name__ == "__main__":
    create_analyst_guide()
