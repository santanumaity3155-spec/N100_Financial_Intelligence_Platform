# Dashboard Screenshots

**N100 Financial Intelligence Platform**

This directory contains screenshots of the dashboard pages for documentation and demonstration purposes.

---

## Screenshot Index

### 1. Home Dashboard
**File**: `01_home.png`  
**Page**: Home Dashboard  
**Description**: Main dashboard overview showing platform introduction, key metrics, quick company search, and navigation guide

**Key Elements**:
- Welcome message and platform description
- Database connection status
- Quick company search dropdown
- Navigation guide to all 8 pages
- Platform metrics and version info

### 2. Company Profile
**File**: `02_profile.png`  
**Page**: Company Profile  
**Description**: Detailed company analysis page showing financial statements, ratios, and charts

**Key Elements**:
- Company information header
- Profit & Loss statement
- Balance sheet
- Cash flow statement
- 30+ financial ratios
- Historical performance charts

### 3. Stock Screener
**File**: `03_screener.png`  
**Page**: Stock Screener  
**Description**: Stock screening interface with filter panel and results table

**Key Elements**:
- Filter panel with 20+ criteria
- Results table with 94+ companies
- Pre-built screening presets
- CSV export button
- Sortable columns

### 4. Peer Comparison
**File**: `04_peers.png`  
**Page**: Peer Comparison  
**Description**: Peer comparison page with radar chart and metrics table

**Key Elements**:
- Company selector
- Peer group display
- Radar chart (multi-dimensional)
- Side-by-side metrics table
- Percentile rankings

### 5. Trend Analysis
**File**: `05_trends.png`  
**Page**: Trend Analysis  
**Description**: Historical trend analysis with multi-metric line charts

**Key Elements**:
- Company selector
- Metric selector (up to 5 metrics)
- Multi-line chart (12 years)
- Growth rate calculations
- CAGR display

### 6. Sector Analysis
**File**: `06_sectors.png`  
**Page**: Sector Analysis  
**Description**: Sector-wise performance analysis with bubble charts

**Key Elements**:
- Sector selector
- Sector performance metrics
- Bubble chart (Market Cap vs Returns)
- Sector distribution
- Top performers ranking

### 7. Capital Allocation
**File**: `07_capital.png`  
**Page**: Capital Allocation  
**Description**: Cash flow analysis and capital structure visualization

**Key Elements**:
- Cash flow statement
- Treemap visualization
- Capital structure metrics
- Dividend analysis
- Free cash flow trends

### 8. Annual Reports
**File**: `08_reports.png`  
**Page**: Annual Reports  
**Description**: Comprehensive financial report generation page

**Key Elements**:
- Company search
- Report generation button
- Multi-section report display
- Export functionality

---

## Screenshot Guidelines

### Capture Instructions

1. **Resolution**: 1920x1080 (Full HD) or higher
2. **Browser**: Chrome, Firefox, or Edge (latest version)
3. **Theme**: Light theme (default)
4. **Data**: Use demo/example data if available
5. **Annotations**: Add callouts for key features (optional)

### File Naming Convention

```
XX_pagename.png
```

Where:
- `XX` = Two-digit page number (01-08)
- `pagename` = Descriptive name (home, profile, screener, etc.)

### Recommended Companies for Screenshots

Use these companies for consistent screenshots:

1. **Home**: No specific company (general view)
2. **Profile**: TCS or RELIANCE (large cap, well-known)
3. **Screener**: Show filtered results (10-20 companies)
4. **Peers**: TCS (IT sector, clear peer group)
5. **Trends**: HDFCBANK (consistent data, 12 years)
6. **Sectors**: Show all sectors or Financial Services
7. **Capital**: RELIANCE (diversified, complex structure)
8. **Reports**: INFY (clean financials)

---

## Placeholder Status

Currently, this directory contains placeholder descriptions. Actual screenshots should be captured when the dashboard is running.

### To Capture Screenshots:

1. Start the dashboard:
   ```bash
   streamlit run src/dashboard/app.py
   ```

2. Navigate to each page
3. Take screenshot using:
   - **Windows**: Snipping Tool or Win + Shift + S
   - **Mac**: Cmd + Shift + 4
   - **Linux**: gnome-screenshot or similar

4. Save with appropriate filename
5. Optimize image size (compress if needed)

---

## Usage in Documentation

Screenshots are referenced in:
- `README.md` - Example Screenshots section
- `docs/User_Guide.md` - Visual guides
- `docs/Project_Summary.md` - Dashboard capabilities
- Demo presentations

---

**Note**: Screenshots should be updated whenever the dashboard UI changes significantly.