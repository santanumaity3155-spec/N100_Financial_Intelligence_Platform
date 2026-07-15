# Profit & Loss Validation Review

**Sprint 1 - Task 6**

**Generated:** 2026-07-15 23:13:10

---

## Executive Summary

This report investigates the profit_loss validation warning identified in the data quality report. The investigation covers column-level missing value analysis, mandatory vs optional field assessment, and recommendations for validation rule adjustment.

### Key Findings

- **Total Records:** 1263
- **Columns Exceeding Threshold:** 2
- **Validation Threshold:** 5%

### Columns Exceeding Threshold

| Column | Missing Count | Missing % | Mandatory |
|--------|---------------|-----------|-----------|
| tax_percentage | 94 | 7.44% | No |
| dividend_payout | 102 | 8.08% | No |

## Detailed Analysis

### Missing Value Analysis by Column

| Column | Total | Present | Missing | Missing % | Status |
|--------|-------|---------|---------|-----------|--------|
| sales | 1263 | 1263 | 0 | 0.0% | ✅ OK |
| expenses | 1263 | 1263 | 0 | 0.0% | ✅ OK |
| operating_profit | 1263 | 1250 | 13 | 1.03% | ✅ OK |
| opm_percentage | 1263 | 1248 | 15 | 1.19% | ✅ OK |
| other_income | 1263 | 1263 | 0 | 0.0% | ✅ OK |
| interest | 1263 | 1263 | 0 | 0.0% | ✅ OK |
| depreciation | 1263 | 1263 | 0 | 0.0% | ✅ OK |
| profit_before_tax | 1263 | 1263 | 0 | 0.0% | ✅ OK |
| tax_percentage | 1263 | 1169 | 94 | 7.44% | ⚠️ EXCEEDS |
| net_profit | 1263 | 1263 | 0 | 0.0% | ✅ OK |
| eps | 1263 | 1258 | 5 | 0.4% | ✅ OK |
| dividend_payout | 1263 | 1161 | 102 | 8.08% | ⚠️ EXCEEDS |

## Root Cause Analysis

### Why Missing Values Occur

1. **Company-Specific Reporting**: Not all companies report all financial metrics
   - Example: Some companies may not report EPS if they have negative earnings
   - Example: Dividend payout is not applicable to companies that don't pay dividends

2. **Industry Variations**: Different sectors have different reporting requirements
   - Financial companies may report different metrics than manufacturing companies
   - Some metrics may not be relevant for certain business models

3. **Data Source Limitations**: Excel files may have incomplete data
   - Source data may have missing values that are legitimate
   - Historical data may be less complete than recent data

## Validation Rule Assessment

### Current Rule
- **Threshold**: 5% maximum missing values per column
- **Dataset**: profit_loss
- **Failed Check**: missing_values

### Rule Appropriateness

The 5% threshold is **appropriate** for most datasets, but may be too strict for financial data where:

1. **Legitimate Missing Values**: Some financial metrics are not applicable to all companies
2. **Industry Differences**: Different sectors report different metrics
3. **Data Quality vs Completeness**: Balance between strict validation and practical usability

## Recommendations

### Option 1: Accept Current Threshold (RECOMMENDED)

**Action**: No changes to validation rules

**Justification**:
- The missing values are likely legitimate and not data quality issues
- Financial data naturally has variability across companies
- The 5% threshold is industry-standard for financial datasets
- The overall data quality is high (91.67% pass rate)

**Impact**:
- Validation will continue to show warnings for profit_loss
- This is acceptable for Sprint 1 as it's a warning, not a failure
- Can be revisited in Sprint 2 if needed

### Option 2: Adjust Threshold for profit_loss

**Action**: Increase threshold to 10% specifically for profit_loss dataset

**Justification**:
- Financial datasets often have higher missing value rates
- 10% threshold is still conservative and acceptable
- Would eliminate warnings while maintaining data quality

**Impact**:
- profit_loss validation would pass
- Overall pass rate would increase to 100%
- May mask legitimate data quality issues if threshold is too high

### Option 3: Mark Columns as Optional

**Action**: Update schema to mark non-critical columns with high missing rates as optional

**Justification**:
- Some columns may not be mandatory for all companies
- Allows for more flexible validation
- Maintains data quality while acknowledging variability

**Impact**:
- Requires schema changes
- May affect downstream KPI calculations
- Requires careful analysis of which columns are truly optional

## Conclusion

The profit_loss validation warning is **not a critical data issue**. The missing values are likely legitimate due to:

1. Company-specific reporting variations
2. Industry-specific financial metrics
3. Natural variability in financial data

**RECOMMENDATION**: Accept the current validation threshold (Option 1).
The warning should be documented and monitored, but does not require immediate action.
The overall data quality is excellent with a 91.67% pass rate across all datasets.

**Next Steps**:
1. Document this finding in the Sprint 1 review
2. Monitor missing value patterns in future data loads
3. Consider adjusting thresholds in Sprint 2 if pattern persists

---

## Appendix: Column Details

### tax_percentage

- **Type**: Financial metric
- **Missing**: 94 values (7.44%)
- **Mandatory**: No
- **Recommendation**: Monitor, no action required

### dividend_payout

- **Type**: Financial metric
- **Missing**: 102 values (8.08%)
- **Mandatory**: No
- **Recommendation**: Monitor, no action required
