-- ====================================================
-- N100 Financial Intelligence Platform
-- Exploratory SQL Queries - Sprint 1
-- ====================================================
-- Database: SQLite (n100.db)
-- Purpose: Professional exploratory data analysis
-- ====================================================

-- ====================================================
-- Query 1: Total Companies in Database
-- ====================================================
-- Purpose: Get the total count of companies in the Nifty 100 index
SELECT 
    COUNT(*) AS total_companies,
    COUNT(DISTINCT sector) AS total_sectors,
    COUNT(DISTINCT industry) AS total_industries
FROM companies;

-- ====================================================
-- Query 2: Companies Distribution by Sector
-- ====================================================
-- Purpose: Analyze sector-wise distribution of companies
SELECT 
    sector,
    COUNT(*) AS company_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM companies), 2) AS percentage
FROM companies
GROUP BY sector
ORDER BY company_count DESC;

-- ====================================================
-- Query 3: Total Profit & Loss Records
-- ====================================================
-- Purpose: Count total financial records in profit_loss table
SELECT 
    COUNT(*) AS total_profit_loss_records,
    COUNT(DISTINCT company_id) AS companies_with_pl_data,
    COUNT(DISTINCT period) AS unique_periods,
    MIN(period) AS earliest_period,
    MAX(period) AS latest_period
FROM profit_loss;

-- ====================================================
-- Query 4: Total Balance Sheet Records
-- ====================================================
-- Purpose: Count total financial records in balance_sheet table
SELECT 
    COUNT(*) AS total_balance_sheet_records,
    COUNT(DISTINCT company_id) AS companies_with_bs_data,
    COUNT(DISTINCT period) AS unique_periods,
    MIN(period) AS earliest_period,
    MAX(period) AS latest_period
FROM balance_sheet;

-- ====================================================
-- Query 5: Total Cash Flow Records
-- ====================================================
-- Purpose: Count total financial records in cash_flow table
SELECT 
    COUNT(*) AS total_cash_flow_records,
    COUNT(DISTINCT company_id) AS companies_with_cf_data,
    COUNT(DISTINCT period) AS unique_periods,
    MIN(period) AS earliest_period,
    MAX(period) AS latest_period
FROM cash_flow;

-- ====================================================
-- Query 6: Top 10 Companies by Sales (Latest Period)
-- ====================================================
-- Purpose: Identify top revenue-generating companies
SELECT 
    c.company_name,
    c.sector,
    pl.period,
    pl.sales,
    pl.net_profit,
    ROUND(pl.net_profit * 100.0 / NULLIF(pl.sales, 0), 2) AS net_profit_margin_pct
FROM profit_loss pl
JOIN companies c ON pl.company_id = c.company_id
WHERE pl.period = (SELECT MAX(period) FROM profit_loss)
    AND pl.sales IS NOT NULL
ORDER BY pl.sales DESC
LIMIT 10;

-- ====================================================
-- Query 7: Average Net Profit Across All Companies
-- ====================================================
-- Purpose: Calculate average net profit metrics
SELECT 
    COUNT(DISTINCT company_id) AS total_companies,
    ROUND(AVG(net_profit), 2) AS avg_net_profit,
    ROUND(MIN(net_profit), 2) AS min_net_profit,
    ROUND(MAX(net_profit), 2) AS max_net_profit,
    ROUND(MEDIAN(net_profit), 2) AS median_net_profit
FROM profit_loss
WHERE net_profit IS NOT NULL;

-- ====================================================
-- Query 8: Companies with Highest ROE (Return on Equity)
-- ====================================================
-- Purpose: Identify top performers by Return on Equity
SELECT 
    c.company_name,
    c.sector,
    pl.period,
    pl.net_profit,
    bs.equity_capital,
    ROUND(pl.net_profit * 100.0 / NULLIF(bs.equity_capital, 0), 2) AS roe_percentage
FROM profit_loss pl
JOIN companies c ON pl.company_id = c.company_id
JOIN balance_sheet bs ON pl.company_id = bs.company_id 
    AND pl.period = bs.period
WHERE pl.net_profit IS NOT NULL 
    AND bs.equity_capital IS NOT NULL 
    AND bs.equity_capital > 0
ORDER BY roe_percentage DESC
LIMIT 15;

-- ====================================================
-- Query 9: Companies with Negative Profit (Loss-Making)
-- ====================================================
-- Purpose: Identify companies reporting losses in latest period
SELECT 
    c.company_name,
    c.sector,
    pl.period,
    pl.sales,
    pl.net_profit,
    ROUND(pl.net_profit * 100.0 / NULLIF(pl.sales, 0), 2) AS net_profit_margin_pct
FROM profit_loss pl
JOIN companies c ON pl.company_id = c.company_id
WHERE pl.period = (SELECT MAX(period) FROM profit_loss)
    AND pl.net_profit < 0
ORDER BY pl.net_profit ASC;

-- ====================================================
-- Query 10: Year-wise Financial Records Summary
-- ====================================================
-- Purpose: Analyze data availability and trends across years
SELECT 
    period AS year,
    COUNT(DISTINCT company_id) AS companies_reported,
    COUNT(*) AS total_records,
    ROUND(SUM(sales), 2) AS total_sales,
    ROUND(SUM(net_profit), 2) AS total_net_profit,
    ROUND(AVG(sales), 2) AS avg_sales,
    ROUND(AVG(net_profit), 2) AS avg_net_profit
FROM profit_loss
GROUP BY period
ORDER BY period DESC;

-- ====================================================
-- Query 11: Sector-wise Financial Performance Analysis
-- ====================================================
-- Purpose: Aggregate financial metrics by sector
SELECT 
    c.sector,
    COUNT(DISTINCT c.company_id) AS company_count,
    ROUND(SUM(pl.sales), 2) AS total_sector_sales,
    ROUND(AVG(pl.sales), 2) AS avg_company_sales,
    ROUND(SUM(pl.net_profit), 2) AS total_sector_profit,
    ROUND(AVG(pl.net_profit), 2) AS avg_company_profit,
    ROUND(AVG(pl.net_profit) * 100.0 / NULLIF(AVG(pl.sales), 0), 2) AS avg_profit_margin_pct
FROM profit_loss pl
JOIN companies c ON pl.company_id = c.company_id
WHERE pl.period = (SELECT MAX(period) FROM profit_loss)
GROUP BY c.sector
ORDER BY total_sector_sales DESC;

-- ====================================================
-- Query 12: Data Completeness Analysis
-- ====================================================
-- Purpose: Check data completeness across financial tables
SELECT 
    'Profit & Loss' AS table_name,
    COUNT(*) AS total_records,
    SUM(CASE WHEN sales IS NULL THEN 1 ELSE 0 END) AS missing_sales,
    SUM(CASE WHEN expenses IS NULL THEN 1 ELSE 0 END) AS missing_expenses,
    SUM(CASE WHEN net_profit IS NULL THEN 1 ELSE 0 END) AS missing_net_profit,
    SUM(CASE WHEN eps IS NULL THEN 1 ELSE 0 END) AS missing_eps
FROM profit_loss
UNION ALL
SELECT 
    'Balance Sheet',
    COUNT(*),
    SUM(CASE WHEN share_capital IS NULL THEN 1 ELSE 0 END),
    SUM(CASE WHEN reserves IS NULL THEN 1 ELSE 0 END),
    SUM(CASE WHEN total_assets IS NULL THEN 1 ELSE 0 END),
    SUM(CASE WHEN total_liabilities IS NULL THEN 1 ELSE 0 END)
FROM balance_sheet
UNION ALL
SELECT 
    'Cash Flow',
    COUNT(*),
    SUM(CASE WHEN cash_from_operating_activity IS NULL THEN 1 ELSE 0 END),
    SUM(CASE WHEN cash_from_investing_activity IS NULL THEN 1 ELSE 0 END),
    SUM(CASE WHEN free_cash_flow IS NULL THEN 1 ELSE 0 END),
    SUM(CASE WHEN net_cash_flow IS NULL THEN 1 ELSE 0 END)
FROM cash_flow;

-- ====================================================
-- Query 13: Duplicate Records Check
-- ====================================================
-- Purpose: Identify any duplicate financial records
SELECT 
    company_id,
    period,
    COUNT(*) AS duplicate_count
FROM profit_loss
GROUP BY company_id, period
HAVING COUNT(*) > 1
UNION ALL
SELECT 
    company_id,
    period,
    COUNT(*) AS duplicate_count
FROM balance_sheet
GROUP BY company_id, period
HAVING COUNT(*) > 1
UNION ALL
SELECT 
    company_id,
    period,
    COUNT(*) AS duplicate_count
FROM cash_flow
GROUP BY company_id, period
HAVING COUNT(*) > 1;

-- ====================================================
-- Query 14: Foreign Key Integrity Check
-- ====================================================
-- Purpose: Verify referential integrity across tables
-- Check for orphaned profit_loss records
SELECT 
    'profit_loss' AS table_name,
    COUNT(*) AS orphaned_records
FROM profit_loss pl
WHERE NOT EXISTS (
    SELECT 1 FROM companies c WHERE c.company_id = pl.company_id
)
UNION ALL
-- Check for orphaned balance_sheet records
SELECT 
    'balance_sheet',
    COUNT(*)
FROM balance_sheet bs
WHERE NOT EXISTS (
    SELECT 1 FROM companies c WHERE c.company_id = bs.company_id
)
UNION ALL
-- Check for orphaned cash_flow records
SELECT 
    'cash_flow',
    COUNT(*)
FROM cash_flow cf
WHERE NOT EXISTS (
    SELECT 1 FROM companies c WHERE c.company_id = cf.company_id
)
UNION ALL
-- Check for orphaned sectors records
SELECT 
    'sectors',
    COUNT(*)
FROM sectors s
WHERE NOT EXISTS (
    SELECT 1 FROM companies c WHERE c.company_id = s.company_id
);

-- ====================================================
-- Query 15: Financial KPI Coverage Analysis
-- ====================================================
-- Purpose: Analyze KPI calculation coverage
SELECT 
    COUNT(DISTINCT company_id) AS companies_with_kpis,
    COUNT(DISTINCT period) AS periods_covered,
    COUNT(*) AS total_kpi_records,
    ROUND(AVG(roe), 2) AS avg_roe,
    ROUND(AVG(roce), 2) AS avg_roce,
    ROUND(AVG(roa), 2) AS avg_roa,
    ROUND(AVG(net_profit_margin), 2) AS avg_net_profit_margin,
    ROUND(AVG(operating_margin), 2) AS avg_operating_margin
FROM financial_kpis;

-- ====================================================
-- Query 16: Market Cap and Valuation Metrics
-- ====================================================
-- Purpose: Analyze market capitalization data
SELECT 
    c.company_name,
    c.sector,
    mc.period,
    mc.market_cap,
    mc.enterprise_value,
    mc.pe_ratio,
    mc.pb_ratio,
    mc.dividend_yield,
    ROUND(mc.market_cap / 10000000, 2) AS market_cap_cr  -- Convert to crores
FROM market_cap mc
JOIN companies c ON mc.company_id = c.company_id
WHERE mc.period = (SELECT MAX(period) FROM market_cap)
ORDER BY mc.market_cap DESC
LIMIT 20;

-- ====================================================
-- Query 17: Stock Price Data Coverage
-- ====================================================
-- Purpose: Analyze stock price data availability
SELECT 
    c.company_name,
    c.sector,
    COUNT(sp.date) AS trading_days,
    MIN(sp.date) AS first_trading_day,
    MAX(sp.date) AS last_trading_day,
    ROUND(AVG(sp.close_price), 2) AS avg_closing_price,
    ROUND(MAX(sp.close_price), 2) AS max_closing_price,
    ROUND(MIN(sp.close_price), 2) AS min_closing_price,
    SUM(sp.volume) AS total_volume
FROM stock_prices sp
JOIN companies c ON sp.company_id = c.company_id
GROUP BY c.company_id, c.company_name, c.sector
ORDER BY trading_days DESC
LIMIT 20;

-- ====================================================
-- Query 18: Peer Group Analysis
-- ====================================================
-- Purpose: Analyze peer group assignments
SELECT 
    pg.peer_group_name,
    COUNT(*) AS company_count,
    SUM(CASE WHEN pg.is_benchmark = 1 THEN 1 ELSE 0 END) AS benchmark_companies,
    GROUP_CONCAT(c.company_name) AS companies_in_group
FROM peer_groups pg
JOIN companies c ON pg.company_id = c.company_id
GROUP BY pg.peer_group_name
ORDER BY company_count DESC;

-- ====================================================
-- Query 19: Cash Flow Health Analysis
-- ====================================================
-- Purpose: Analyze operating cash flow vs free cash flow
SELECT 
    c.company_name,
    c.sector,
    cf.period,
    cf.cash_from_operating_activity,
    cf.cash_from_investing_activity,
    cf.cash_from_financing_activity,
    cf.free_cash_flow,
    cf.net_cash_flow,
    ROUND(cf.free_cash_flow * 100.0 / NULLIF(cf.cash_from_operating_activity, 0), 2) AS fcf_to_ocf_ratio
FROM cash_flow cf
JOIN companies c ON cf.company_id = c.company_id
WHERE cf.period = (SELECT MAX(period) FROM cash_flow)
    AND cf.cash_from_operating_activity IS NOT NULL
ORDER BY cf.free_cash_flow DESC
LIMIT 15;

-- ====================================================
-- Query 20: Financial Ratios Overview
-- ====================================================
-- Purpose: Comprehensive view of financial ratios
SELECT 
    c.company_name,
    c.sector,
    fr.period,
    fr.pe_ratio,
    fr.pb_ratio,
    fr.ps_ratio,
    fr.roe,
    fr.roa,
    fr.debt_to_equity,
    fr.current_ratio,
    fr.quick_ratio,
    fr.dividend_yield
FROM financial_ratios fr
JOIN companies c ON fr.company_id = c.company_id
WHERE fr.period = (SELECT MAX(period) FROM financial_ratios)
ORDER BY fr.roe DESC
LIMIT 20;

-- ====================================================
-- End of Exploratory Queries
-- ====================================================