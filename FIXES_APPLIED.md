# Module 5 Production Issues - Root Cause Analysis & Fixes

## Root Causes Identified

### Issue 1: Foreign Key Constraint Failures
**Root Cause**: 2 companies (ULTRACEMCO, UNIONBANK) exist in financial_ratios but NOT in companies table
**Impact**: 24 rows skipped during database insert

### Issues 2, 3, 4: Scores Always Zero
**Root Cause**: The financial_ratios table has ONLY 13 columns:
- id, company_id, period, pe_ratio, pb_ratio, ps_ratio, roe, roa, debt_to_equity, current_ratio, quick_ratio, dividend_yield, created_at

But the engine expects 20+ columns including:
- **Growth**: revenue_cagr_3yr, pat_cagr_3yr, eps_cagr_3yr (MISSING)
- **Cash Flow**: free_cash_flow, fcf_margin, cash_conversion, cash_return_on_assets, capital_allocation_rating (MISSING)
- **Efficiency**: asset_turnover (MISSING)
- **Additional**: roce, net_profit_margin, operating_profit_margin, interest_coverage, high_leverage_flag (MISSING)

**Impact**: Growth, Cash Flow, and Efficiency scores always zero because data doesn't exist

### Issue 5: Thousands of Warnings
**Root Cause**: Engine tries to read non-existent columns for all 1065 records, generating warnings for each missing metric
**Impact**: 3220+ warnings in logs

## Solution Strategy

The engine must be updated to:
1. Check which columns actually exist in the database
2. Only calculate scores for available metrics
3. Gracefully handle missing data without excessive logging
4. Provide meaningful summary statistics instead of individual warnings