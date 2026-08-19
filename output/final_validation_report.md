# Sprint 3 Final Validation Report

**Generated:** 2026-08-19 10:48:51
**Execution Time:** 0.01 seconds

## Overall Result

**Status:** ❌ FAIL
**Total Checks:** 39
**Passed:** 27
**Failed:** 6
**Warnings:** 6

## Module Validations

### Database

**Status:** ❌ FAIL
**Execution Time:** 0.00s

#### Checks

- ✅ **database_exists**: Database found: D:\New Project\Bluestock_Projects\Nifty 100\N100 Financial Intelligence Platform\N100_Financial_Intelligence_Platform\data\database\n100.db
- ✅ **database_connection**: Connection successful
- ✅ **foreign_keys_enabled**: Foreign keys are enabled
- ❌ **tables_exist**: Missing tables: ['companies', 'profit_loss', 'balance_sheet', 'cash_flow', 'analysis', 'documents', 'pros_cons', 'sectors', 'stock_prices', 'market_cap', 'financial_ratios', 'peer_groups', 'financial_health_scores', 'peer_percentiles']
- ✅ **indexes_defined**: Indexes defined for 13 tables in schema
- ❌ **database_integrity**: Database corruption: 100

#### Errors

- ❌ tables_exist: Missing tables: ['companies', 'profit_loss', 'balance_sheet', 'cash_flow', 'analysis', 'documents', 'pros_cons', 'sectors', 'stock_prices', 'market_cap', 'financial_ratios', 'peer_groups', 'financial_health_scores', 'peer_percentiles']
- ❌ database_integrity: Database corruption: 100

### Financial Ratios

**Status:** ❌ FAIL
**Execution Time:** 0.00s

#### Checks

- ✅ **ratios_populated**: Financial ratios table has 50 records
- ✅ **no_null_company_ids**: No NULL company IDs found
- ✅ **no_duplicates**: No duplicate rows found
- ❌ **required_kpis_available**: Missing core KPI columns: ['roe', 'roa', 'debt_to_equity']
- ✅ **no_invalid_values**: No obviously invalid values found
- ⚠️ **cagr_columns_exist**: No CAGR columns found in financial_ratios table

#### Errors

- ❌ required_kpis_available: Missing core KPI columns: ['roe', 'roa', 'debt_to_equity']

#### Warnings

- ⚠️ cagr_columns_exist: No CAGR columns found in financial_ratios table

### CAGR

**Status:** ✅ PASS
**Execution Time:** 0.00s

#### Checks

- ⚠️ **revenue_cagr**: Revenue CAGR columns not found (optional)
- ⚠️ **pat_cagr**: PAT CAGR columns not found (optional)
- ⚠️ **eps_cagr**: EPS CAGR columns not found (optional)
- ⚠️ **cagr_outputs_exist**: No CAGR columns found (optional)

#### Warnings

- ⚠️ revenue_cagr: Revenue CAGR columns not found (optional)
- ⚠️ pat_cagr: PAT CAGR columns not found (optional)
- ⚠️ eps_cagr: EPS CAGR columns not found (optional)
- ⚠️ cagr_outputs_exist: No CAGR columns found (optional)

### Health Score

**Status:** ❌ FAIL
**Execution Time:** 0.00s

#### Checks

- ✅ **health_scores_exist**: Health scores table has 10 records
- ✅ **scores_in_range**: All scores within 0-100 range
- ✅ **no_duplicates**: No duplicate records found
- ✅ **no_null_company_ids**: No NULL company IDs
- ❌ **rating_available**: Rating column not found
- ❌ **category_scores_exist**: Missing category scores: ['profitability_score', 'growth_score', 'cashflow_score', 'leverage_score', 'efficiency_score']

#### Errors

- ❌ rating_available: Rating column not found
- ❌ category_scores_exist: Missing category scores: ['profitability_score', 'growth_score', 'cashflow_score', 'leverage_score', 'efficiency_score']

### Screener

**Status:** ✅ PASS
**Execution Time:** 0.00s

#### Checks

- ✅ **screener_module_imports**: Screener modules import successfully
- ✅ **preset_filters_available**: Found 10 preset filters
- ✅ **screener_data_load**: Screener loaded 1 records
- ✅ **custom_filters_working**: Custom filter test returned 0 results
- ✅ **queries_return_companies**: Default query returned 1 companies

### Peer Ranking

**Status:** ❌ FAIL
**Execution Time:** 0.00s

#### Checks

- ✅ **peer_groups_exist**: Found ok peer group assignments
- ❌ **peer_rankings_validation**: Unexpected error: 

#### Errors

- ❌ peer_rankings_validation: Unexpected error: 

### Radar Charts

**Status:** ✅ PASS
**Execution Time:** 0.00s

#### Checks

- ✅ **radar_charts_directory_exists**: Directory exists: D:\New Project\Bluestock_Projects\Nifty 100\N100 Financial Intelligence Platform\N100_Financial_Intelligence_Platform\output\radar_charts
- ✅ **charts_generated**: Found 1 radar charts
- ✅ **png_files_valid**: All PNG files are valid
- ⚠️ **missing_charts_reported**: Could not check missing charts: 

#### Warnings

- ⚠️ missing_charts_reported: Could not check missing charts: 

### Peer Reports

**Status:** ✅ PASS
**Execution Time:** 0.00s

#### Checks

- ✅ **peer_reports_directory_exists**: Directory exists: D:\New Project\Bluestock_Projects\Nifty 100\N100 Financial Intelligence Platform\N100_Financial_Intelligence_Platform\output\peer_reports
- ✅ **reports_generated**: Found 1 peer reports
- ✅ **required_sections_exist**: All required sections found in sample report
- ✅ **kpi_table_exists**: KPI table found in sample report
- ✅ **summary_exists**: Summary section found in sample report
- ✅ **health_score_exists**: Health score found in sample report

## Overall Statistics

- **Total Companies:** 0
- **Reports Generated:** 0
- **Charts Generated:** 0
- **Execution Time:** 0.01s

## Sprint Status

❌ **Sprint 3 is INCOMPLETE**

Please fix 6 failing check(s) before marking Sprint 3 as complete.
