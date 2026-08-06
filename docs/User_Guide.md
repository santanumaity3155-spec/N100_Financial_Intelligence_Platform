# N100 Financial Intelligence Platform - User Guide

**Version**: 1.0.0  
**Last Updated**: August 6, 2026  
**Platform**: N100 Financial Intelligence Platform  
**Organization**: Bluestock

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [How to Launch](#how-to-launch)
3. [How to Navigate](#how-to-navigate)
4. [How to Search Companies](#how-to-search-companies)
5. [How to Use the Screener](#how-to-use-the-screener)
6. [How to Compare Peers](#how-to-compare-peers)
7. [How to Use Trends](#how-to-use-trends)
8. [How to Export CSV](#how-to-export-csv)
9. [How Valuation Works](#how-valuation-works)
10. [Common Troubleshooting](#common-troubleshooting)

---

## Getting Started

### What is N100 Financial Intelligence Platform?

The N100 Financial Intelligence Platform is a comprehensive financial analysis tool for Nifty 100 companies. It provides:

- **Financial Statements**: Profit & Loss, Balance Sheet, Cash Flow
- **Financial Ratios**: 30+ KPIs including profitability, liquidity, leverage, and efficiency metrics
- **Peer Comparison**: Benchmark against industry peers
- **Trend Analysis**: 12-year historical performance tracking
- **Sector Analysis**: Sector-wise performance comparison
- **Valuation**: Automated valuation metrics with flagging
- **Reports**: Comprehensive financial reports with export capabilities

### Who Should Use This Platform?

- **Financial Analysts**: For company analysis and peer benchmarking
- **Investors**: For stock screening and valuation
- **Researchers**: For historical trend analysis
- **Students**: For learning financial analysis
- **Portfolio Managers**: For sector allocation and capital structure analysis

### Prerequisites

Before using the platform, ensure:

1. ✅ Database is initialized (run ETL pipeline)
2. ✅ Financial KPIs are calculated
3. ✅ Dashboard is accessible via browser
4. ✅ You have basic knowledge of financial metrics

---

## How to Launch

### Step 1: Start the Dashboard

Open your terminal or command prompt and run:

```bash
streamlit run src/dashboard/app.py
```

### Step 2: Access the Dashboard

The dashboard will automatically open in your default web browser at:

```
http://localhost:8501
```

If it doesn't open automatically, manually navigate to the URL above.

### Step 3: Verify Connection

Check the sidebar for database status:

- ✅ **Green "Database Connected"**: Database is ready
- ⚠️ **Yellow "Database Not Found"**: Run ETL pipeline first
- ❌ **Red "Database Error"**: Check logs for details

### Alternative Launch Options

```bash
# Custom port
streamlit run src/dashboard/app.py --server.port 8502

# Dark theme
streamlit run src/dashboard/app.py --theme.base dark

# Headless mode (no browser)
streamlit run src/dashboard/app.py --server.headless true
```

---

## How to Navigate

### Dashboard Structure

The dashboard consists of **8 specialized pages** accessible via the sidebar:

```
┌─────────────────────────────────────┐
│  📈 N100 Analytics                  │
│  ─────────────────────────────────  │
│  🏠 Home                            │
│  👤 Profile                         │
│  🔍 Screener                        │
│  👥 Peers                           │
│  📈 Trends                          │
│  🏭 Sectors                         │
│  💰 Capital                         │
│  📑 Reports                         │
└─────────────────────────────────────┘
```

### Navigation Tips

1. **Sidebar Navigation**: Click any page in the sidebar to navigate
2. **Page Persistence**: Your selections are maintained while navigating
3. **Cache**: Data is cached for 10 minutes for faster loading
4. **Responsive**: Dashboard works on desktop, tablet, and mobile

### Understanding the Interface

#### Sidebar Components

- **Application Title**: Platform name and logo
- **Current Module**: Shows active module information
- **Navigation Menu**: List of all 8 pages
- **Application Status**: Database connection and metrics
- **Information**: Version and status details

#### Main Content Area

- **Header**: Page title and description
- **Filters**: Dropdowns, sliders, and checkboxes
- **Charts**: Interactive visualizations
- **Tables**: Sortable data tables
- **Export Buttons**: Download data as CSV/Excel

---

## How to Search Companies

### Method 1: Quick Search (Home Page)

1. Navigate to **Home** page
2. Use the **Quick Company Search** dropdown
3. Start typing company name or ticker
4. Select from autocomplete suggestions
5. Click to view company profile

### Method 2: Company Profile Page

1. Navigate to **Profile** page
2. Use the **Select Company** dropdown
3. Browse alphabetically or search
4. Select company to view details

### Method 3: Any Page with Company Selector

Most pages have a company selector:

1. Look for "Select Company" or "Choose Company" dropdown
2. Type to search or browse list
3. Selection triggers data refresh
4. All charts and metrics update automatically

### Search Tips

- **Partial Matching**: Type "TCS" to find "TCS LTD"
- **Ticker Search**: Use ticker symbols like "INFY", "RELIANCE"
- **Case Insensitive**: "tcs" and "TCS" both work
- **Recent Selections**: Dropdown remembers recent selections

### Company Information Displayed

When you select a company, you'll see:

- **Basic Info**: Name, sector, industry, ticker
- **Financial Statements**: P&L, Balance Sheet, Cash Flow
- **Ratios**: 30+ financial KPIs
- **Charts**: Historical performance
- **Peers**: Similar companies for comparison

---

## How to Use the Screener

### Overview

The Stock Screener allows you to filter Nifty 100 companies based on financial criteria.

### Step-by-Step Guide

#### 1. Navigate to Screener Page

Click **🔍 Screener** in the sidebar.

#### 2. Understand the Interface

```
┌─────────────────────────────────────────┐
│  Stock Screener                         │
├─────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐     │
│  │ Filter Panel │  │   Results    │     │
│  │              │  │   Table      │     │
│  │ • Criteria 1 │  │              │     │
│  │ • Criteria 2 │  │ • Company 1  │     │
│  │ • Criteria 3 │  │ • Company 2  │     │
│  │              │  │ • Company 3  │     │
│  │ [Apply]      │  │              │     │
│  │ [Reset]      │  │ [Export CSV] │     │
│  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────┘
```

#### 3. Select Filter Criteria

**Available Filters** (20+ criteria):

**Profitability:**
- ROE (Return on Equity)
- ROCE (Return on Capital Employed)
- Net Profit Margin
- Operating Profit Margin
- Gross Profit Margin

**Liquidity:**
- Current Ratio
- Quick Ratio
- Cash Ratio

**Leverage:**
- Debt-to-Equity
- Interest Coverage Ratio
- Debt Ratio

**Efficiency:**
- Asset Turnover
- Inventory Turnover
- Receivables Turnover

**Valuation:**
- P/E Ratio
- P/B Ratio
- EV/EBITDA
- Market Cap

**Growth:**
- Revenue Growth (YoY)
- Profit Growth (YoY)
- CAGR (3-year, 5-year)

#### 4. Set Filter Values

For each criterion:

1. **Select Operator**: >, <, =, >=, <=, between
2. **Enter Value**: Numeric value
3. **Add to Filter**: Click "Add" button
4. **Combine Filters**: Use AND/OR logic

**Example:**
```
Filter 1: ROE > 15%
Filter 2: P/E Ratio < 25
Filter 3: Debt-to-Equity < 1
```

#### 5. Apply Filters

Click **"Apply Filters"** button.

**Results:**
- Table updates with matching companies
- Count of results shown
- Filters can be modified and reapplied

#### 6. Use Pre-built Presets

Quick access to common screening strategies:

- **Value Stocks**: Low P/E, high dividend yield
- **Growth Stocks**: High revenue growth, high ROE
- **Quality Stocks**: High ROCE, low debt, consistent profits
- **Dividend Stocks**: High dividend yield, stable payouts

**To use:**
1. Click preset name
2. Filters auto-populate
3. Click "Apply"
4. View results

#### 7. Sort and Analyze Results

**Sorting:**
- Click column headers to sort
- Click again for descending order
- Multi-column sort available

**Analysis:**
- Review company names and sectors
- Compare key metrics
- Identify investment opportunities

#### 8. Export Results

Click **"Export CSV"** button to download results.

**File includes:**
- All filtered companies
- All displayed columns
- Timestamp of export

---

## How to Compare Peers

### Overview

Peer Comparison allows you to benchmark a company against its industry peers.

### Step-by-Step Guide

#### 1. Navigate to Peers Page

Click **👥 Peers** in the sidebar.

#### 2. Select Company

1. Use **"Select Company"** dropdown
2. Choose company to analyze
3. Peer group auto-assigns based on sector

#### 3. Understand Peer Groups

**What are Peer Groups?**

Peer groups are collections of companies in the same sector/industry for comparison.

**Available Peer Groups (13):**
- Information Technology
- Financial Services
- Energy
- Pharmaceuticals
- Automobile
- FMCG
- Metals & Mining
- Telecom
- Infrastructure
- Consumer Goods
- Healthcare
- Real Estate
- Others

#### 4. View Radar Chart

The radar chart shows multi-dimensional comparison:

```
                    Profitability
                         ▲
                         │
    Liquidity ◄──────────┼──────────► Leverage
                         │
                         ▼
                    Efficiency
```

**How to Read:**
- **Outer shape**: Selected company
- **Inner shape**: Peer average
- **Further from center**: Better performance
- **Closer to center**: Below average

#### 5. Analyze Metrics Table

Side-by-side comparison table shows:

| Metric | Company | Peer Avg | Peer Median | Percentile |
|--------|---------|----------|--------------|------------|
| ROE | 25.5% | 18.2% | 17.5% | 85th |
| ROCE | 22.3% | 16.8% | 16.2% | 82nd |
| Debt/Equity | 0.45 | 0.68 | 0.65 | 75th |

**Interpretation:**
- **Percentile**: Company's rank among peers (higher is better)
- **Peer Avg**: Arithmetic mean of peer group
- **Peer Median**: Middle value of peer group

#### 6. Compare Multiple Companies

To compare multiple companies:

1. Select first company
2. Note metrics
3. Select second company
4. Compare differences
5. Repeat for additional companies

#### 7. Export Peer Analysis

Export options available:
- **CSV Export**: Metrics table
- **Radar Chart**: Download as PNG (if available)
- **Report**: Comprehensive peer report

---

## How to Use Trends

### Overview

Trend Analysis shows historical performance over 12 years.

### Step-by-Step Guide

#### 1. Navigate to Trends Page

Click **📈 Trends** in the sidebar.

#### 2. Select Company

1. Use **"Select Company"** dropdown
2. Choose company for trend analysis
3. Data loads for all available years

#### 3. Select Metrics

Choose metrics to display:

**Available Metrics:**
- Revenue
- Net Profit
- Operating Profit
- Total Assets
- Total Equity
- ROE
- ROCE
- Net Profit Margin
- Debt-to-Equity
- Current Ratio
- EPS (Earnings Per Share)
- Book Value Per Share

**Selection:**
- Check boxes to select multiple metrics
- Up to 5 metrics can be displayed simultaneously
- Metrics are color-coded for clarity

#### 4. View Trend Charts

**Line Chart Features:**
- **X-axis**: Years (2012-2024)
- **Y-axis**: Metric value
- **Multiple lines**: One per selected metric
- **Interactive**: Hover for values, zoom, pan

**How to Analyze:**
1. **Identify Trends**: Upward/downward trends
2. **Spot Patterns**: Seasonal or cyclical patterns
3. **Compare Metrics**: Correlation between metrics
4. **Anomalies**: Unusual spikes or drops

#### 5. Calculate Growth Rates

**Year-over-Year (YoY) Growth:**
```
Growth % = ((Current Year - Previous Year) / Previous Year) × 100
```

**CAGR (Compound Annual Growth Rate):**
```
CAGR = ((End Value / Start Value)^(1/n) - 1) × 100
Where n = number of years
```

**Display:**
- Growth rates shown in tooltips
- CAGR displayed in summary statistics
- Positive growth in green, negative in red

#### 6. Analyze Specific Periods

**Zoom Functionality:**
- Click and drag to zoom into specific years
- Double-click to reset zoom
- Use pan to move across timeline

**Period Selection:**
- Last 5 years
- Last 10 years
- All available years (12 years)

#### 7. Export Trend Data

Click **"Export CSV"** to download:
- Year-wise data for selected metrics
- Growth rates
- CAGR calculations

---

## How to Export CSV

### Overview

Export functionality allows you to download data for further analysis in Excel or other tools.

### Export Options

#### 1. Screener Results Export

**Location**: Screener page

**Steps:**
1. Apply filters in screener
2. Click **"Export CSV"** button
3. File downloads automatically

**File Contents:**
- Company name, ticker, sector
- All filtered metrics
- Timestamp

**Filename Format**: `screener_results_YYYYMMDD_HHMMSS.csv`

#### 2. Trend Data Export

**Location**: Trends page

**Steps:**
1. Select company and metrics
2. Click **"Export CSV"** button
3. File downloads automatically

**File Contents:**
- Year-wise data
- Selected metrics
- Growth rates

**Filename Format**: `trends_<company>_YYYYMMDD_HHMMSS.csv`

#### 3. Peer Comparison Export

**Location**: Peers page

**Steps:**
1. Select company
2. View peer comparison
3. Click **"Export CSV"** button
4. File downloads automatically

**File Contents:**
- Company metrics
- Peer average
- Peer median
- Percentile rankings

**Filename Format**: `peer_comparison_<company>_YYYYMMDD_HHMMSS.csv`

#### 4. Sector Analysis Export

**Location**: Sectors page

**Steps:**
1. Select sector or view all
2. Click **"Export CSV"** button
3. File downloads automatically

**File Contents:**
- Sector-wise metrics
- Rankings
- Performance indicators

**Filename Format**: `sector_analysis_YYYYMMDD_HHMMSS.csv`

### Using Exported CSV Files

**Open in Excel:**
1. Double-click CSV file
2. Opens in Excel by default
3. Format as needed
4. Save as .xlsx for further analysis

**Open in Python:**
```python
import pandas as pd

df = pd.read_csv('screener_results_20260806_170000.csv')
print(df.head())
```

**Open in Google Sheets:**
1. Go to Google Sheets
2. File → Import → Upload
3. Select CSV file
4. Data appears in spreadsheet

### Export Best Practices

- **Regular Exports**: Export data regularly for record-keeping
- **Timestamp**: Files include timestamps for version control
- **Naming**: Use descriptive filenames
- **Backup**: Save exports to cloud storage
- **Analysis**: Use exported data for custom analysis

---

## How Valuation Works

### Overview

The Valuation Module calculates key valuation metrics for Nifty 100 companies.

### Valuation Metrics

#### 1. P/E Ratio (Price-to-Earnings)

**Formula:**
```
P/E Ratio = Market Price per Share / Earnings Per Share (EPS)
```

**Interpretation:**
- **Low P/E**: Undervalued or low growth expectations
- **High P/E**: Overvalued or high growth expectations
- **Industry Comparison**: Compare with sector average

**Example:**
```
Market Price: ₹2,500
EPS: ₹100
P/E Ratio = 2500 / 100 = 25
```

#### 2. P/B Ratio (Price-to-Book)

**Formula:**
```
P/B Ratio = Market Price per Share / Book Value per Share
```

**Interpretation:**
- **P/B < 1**: Trading below book value (potential value)
- **P/B > 1**: Trading above book value (growth premium)
- **Industry Comparison**: Compare with sector average

**Example:**
```
Market Price: ₹2,500
Book Value: ₹500
P/B Ratio = 2500 / 500 = 5
```

#### 3. EV/EBITDA (Enterprise Value to EBITDA)

**Formula:**
```
EV = Market Cap + Debt - Cash
EBITDA = Operating Profit + Depreciation + Amortization

EV/EBITDA = Enterprise Value / EBITDA
```

**Interpretation:**
- **Lower EV/EBITDA**: Better value
- **Used for**: Comparing companies with different capital structures
- **Acquisition Valuation**: Common in M&A

#### 4. Market Capitalization

**Formula:**
```
Market Cap = Share Price × Total Shares Outstanding
```

**Categories:**
- **Large Cap**: > ₹20,000 crore
- **Mid Cap**: ₹5,000 - ₹20,000 crore
- **Small Cap**: < ₹5,000 crore

#### 5. Valuation Flags

The system automatically flags valuation concerns:

**Flags:**
- ⚠️ **Overvalued**: P/E significantly above sector average
- ⚠️ **Undervalued**: P/E significantly below sector average
- ⚠️ **High Debt**: Debt-to-Equity above threshold
- ⚠️ **Low Liquidity**: Current ratio below 1
- ✅ **Fair Valued**: Metrics within normal range

### Valuation Outputs

#### 1. valuation_summary.xlsx

**Location**: `output/valuation_summary.xlsx`

**Contents:**
- Company name and ticker
- Market cap
- P/E ratio
- P/B ratio
- EV/EBITDA
- Valuation flags
- Sector comparison

**Sheets:**
- **Summary**: All companies overview
- **Detailed**: Company-wise detailed analysis
- **Flags**: Companies with valuation flags

#### 2. valuation_flags.csv

**Location**: `output/valuation_flags.csv`

**Contents:**
- Company name
- Flag type (Overvalued, Undervalued, High Debt, etc.)
- Flag severity (High, Medium, Low)
- Recommended action
- Supporting metrics

### How to Use Valuation Data

#### Investment Decision Making

**Step 1: Check Valuation Flags**
```
Review valuation_flags.csv for red flags
```

**Step 2: Compare with Peers**
```
Use Peer Comparison page to see sector benchmarks
```

**Step 3: Analyze Trends**
```
Check Trend Analysis for historical valuation trends
```

**Step 4: Make Informed Decision**
```
Consider:
- Valuation metrics
- Peer comparison
- Historical trends
- Financial health
- Growth prospects
```

#### Valuation Best Practices

1. **Don't Rely on Single Metric**: Use multiple valuation ratios
2. **Compare with Peers**: Always compare with sector average
3. **Consider Growth**: High P/E may be justified for high growth
4. **Check Quality**: Low P/E may indicate fundamental problems
5. **Historical Context**: Compare current valuation with historical range

---

## Common Troubleshooting

### Issue 1: Dashboard Won't Load

**Symptoms:**
- Page shows "Loading..." indefinitely
- Browser shows "Site can't be reached"
- Streamlit command fails

**Solutions:**

1. **Check if Streamlit is installed:**
   ```bash
   pip show streamlit
   ```

2. **Reinstall Streamlit:**
   ```bash
   pip install --upgrade streamlit
   ```

3. **Check port availability:**
   ```bash
   # Windows
   netstat -ano | findstr :8501
   
   # Kill process if needed
   taskkill /PID <process_id> /F
   ```

4. **Try different port:**
   ```bash
   streamlit run src/dashboard/app.py --server.port 8502
   ```

5. **Check firewall settings:**
   - Allow Python through firewall
   - Allow port 8501

### Issue 2: Database Not Found

**Symptoms:**
- Sidebar shows "Database Not Found"
- Error: "Database file not found"
- Charts show no data

**Solutions:**

1. **Run ETL pipeline:**
   ```bash
   python run_etl.py
   ```

2. **Verify database location:**
   ```bash
   # Check if database exists
   ls data/database/n100.db
   
   # If not, run ETL
   python run_etl.py
   ```

3. **Calculate KPIs:**
   ```bash
   python populate_financial_kpis.py
   ```

4. **Check database permissions:**
   ```bash
   # Ensure read/write permissions
   chmod 644 data/database/n100.db
   ```

### Issue 3: Charts Not Rendering

**Symptoms:**
- Charts show blank areas
- Error: "No data available"
- Charts show "Loading..." indefinitely

**Solutions:**

1. **Check data availability:**
   - Ensure company has data for selected period
   - Try different company
   - Check if metrics are calculated

2. **Clear cache:**
   - Click "Clear Cache" in sidebar (if available)
   - Or restart dashboard

3. **Check browser console:**
   - Press F12 to open developer tools
   - Check Console tab for errors
   - Check Network tab for failed requests

4. **Update Plotly:**
   ```bash
   pip install --upgrade plotly
   ```

### Issue 4: Slow Performance

**Symptoms:**
- Pages load slowly
- Charts take long to render
- Filters are laggy

**Solutions:**

1. **Clear browser cache:**
   - Press Ctrl+Shift+Delete
   - Clear cached images and files
   - Restart browser

2. **Reduce data volume:**
   - Select fewer metrics
   - Use shorter time periods
   - Apply more specific filters

3. **Check database indexes:**
   ```bash
   # Verify database is optimized
   sqlite3 data/database/n100.db "ANALYZE;"
   ```

4. **Increase cache TTL:**
   - Edit `src/dashboard/utils/cache.py`
   - Increase TTL value (default: 600 seconds)

### Issue 5: CSV Export Not Working

**Symptoms:**
- Click "Export CSV" but no download
- Error: "Export failed"
- Empty CSV file

**Solutions:**

1. **Check browser download settings:**
   - Ensure downloads are allowed
   - Check download folder
   - Try different browser

2. **Check data availability:**
   - Ensure results table has data
   - Try with fewer filters
   - Verify data is loaded

3. **Check file permissions:**
   ```bash
   # Ensure write permissions
   chmod 755 output/
   ```

4. **Try manual export:**
   - Copy table data
   - Paste into Excel
   - Save as CSV

### Issue 6: Company Not Found

**Symptoms:**
- Search returns no results
- Company not in dropdown
- Error: "No data available"

**Solutions:**

1. **Check company name:**
   - Use official company name
   - Try ticker symbol
   - Check spelling

2. **Verify data exists:**
   ```bash
   # Check if company is in database
   sqlite3 data/database/n100.db "SELECT * FROM companies WHERE name LIKE '%TCS%';"
   ```

3. **Run ETL again:**
   ```bash
   python run_etl.py
   ```

4. **Check data source:**
   - Verify Excel file has company data
   - Check for data quality issues

### Issue 7: Login/Authentication Required

**Symptoms:**
- Dashboard asks for password
- Authentication error
- Access denied

**Solutions:**

1. **Check Streamlit configuration:**
   - No authentication is configured by default
   - If authentication is enabled, use provided credentials

2. **Disable authentication (if needed):**
   - Check `.streamlit/config.toml`
   - Remove authentication settings

3. **Contact administrator:**
   - If deployed on server, contact admin
   - Verify you have access permissions

### Issue 8: Module Import Errors

**Symptoms:**
- Error: "Module not found"
- ImportError in console
- Dashboard fails to load

**Solutions:**

1. **Check Python path:**
   ```bash
   # Ensure you're in project directory
   cd N100_Financial_Intelligence_Platform
   ```

2. **Install missing packages:**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dashboard.txt
   ```

3. **Verify PYTHONPATH:**
   ```bash
   # Add src to PYTHONPATH
   set PYTHONPATH=%PYTHONPATH%;src
   ```

4. **Reinstall package:**
   ```bash
   pip install -e .
   ```

### Getting Help

If issues persist:

1. **Check logs:**
   - View `logs/dashboard.log`
   - Look for error messages
   - Note timestamps

2. **Review documentation:**
   - README.md
   - Architecture.md
   - This User Guide

3. **Run tests:**
   ```bash
   python -m pytest src/tests/ -v
   ```

4. **Contact support:**
   - Email: support@bluestock.com
   - Include error messages and screenshots
   - Provide steps to reproduce

---

## Additional Resources

### Documentation

- **README.md**: Project overview and quick start
- **Architecture.md**: Technical architecture and design
- **Project_Summary.md**: Project objectives and achievements
- **Sprint4_Retrospective.md**: Sprint review and lessons learned

### Useful Commands

```bash
# Launch dashboard
streamlit run src/dashboard/app.py

# Run ETL pipeline
python run_etl.py

# Calculate KPIs
python populate_financial_kpis.py

# Run tests
python -m pytest src/tests/ -v

# Check database
sqlite3 data/database/n100.db ".tables"

# View logs
tail -f logs/dashboard.log
```

### Keyboard Shortcuts

- **R**: Rerun dashboard
- **C**: Clear cache
- **O**: Toggle settings
- **?**: Show keyboard shortcuts

---

**End of User Guide**

For technical details, see [Architecture.md](Architecture.md)  
For project overview, see [Project_Summary.md](Project_Summary.md)  
For sprint details, see [Sprint4_Retrospective.md](Sprint4_Retrospective.md)