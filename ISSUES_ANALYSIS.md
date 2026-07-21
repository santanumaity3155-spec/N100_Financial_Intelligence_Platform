# Module 5 Issues Analysis

## Issue 1: Foreign Key Constraint Errors
**Root Cause**: The `financial_health_scores` table has a foreign key constraint referencing `companies(company_id)`. When the engine processes records from `financial_ratios`, it may encounter company_ids that don't exist in the `companies` table, causing INSERT OR REPLACE to fail with foreign key violations.

**Current Behavior**: The error is caught and logged as a warning, but the record is skipped.

**Required Fix**: Validate company existence before attempting insert, or ensure data integrity upstream.

## Issue 2: Missing KPI Warnings
**Root Cause**: In `_process_company_row`, missing category scores are logged at WARNING level:
```python
for cat, score in category_scores.items():
    if score is None:
        w = f"No {cat} metrics available for {company_id}, period {period}"
        warnings.append(w)
        logger.warning(w)  # ← Too verbose for expected conditions
```

**Current Behavior**: Every missing metric generates a WARNING log, causing excessive spam.

**Required Fix**: 
- Change log level to DEBUG for expected missing data
- Only log WARNING when ALL categories are missing
- Document that early periods may lack historical data

## Issue 3: Health Score Validation
**Status**: Already properly implemented
- Scores clamped to 0-100 ✓
- Weights sum to 1.0 ✓
- NaN/Inf handled ✓
- Missing values return None ✓

## Issue 4: Rating Logic
**Status**: Already correct
- Bands properly defined ✓
- Edge cases handled ✓

## Issue 5: Remarks Engine
**Status**: Functional but could be enhanced
- Current templates are generic but acceptable
- Could add more business-specific insights

## Issue 6: Database Layer
**Issues Found**:
1. Connection never explicitly closed in `save_to_database()`
2. Duplicate detection logic is flawed (checks before INSERT OR REPLACE, which handles duplicates automatically)
3. Transaction handling could be improved

## Issue 7: CSV Export
**Status**: Functional
- UTF-8 encoding ✓
- Proper headers ✓
- No duplicate rows (exported from unique results list) ✓

## Issue 8: Logging
**Issues**:
1. Missing metrics logged at WARNING level (should be DEBUG)
2. No summary of companies processed vs skipped
3. Duplicate detection logged at DEBUG but counted separately

## Issue 9: Testing
**Status**: All 125 tests pass ✓

## Issue 10: Code Quality
**Status**: Good
- Type hints ✓
- Docstrings ✓
- Modular design ✓

## Priority Fixes Needed:
1. **HIGH**: Foreign key validation (Issue 1)
2. **HIGH**: Reduce warning spam for missing KPIs (Issue 2)
3. **MEDIUM**: Close database connections properly (Issue 6)
4. **LOW**: Improve remarks templates (Issue 5)
5. **LOW**: Enhance logging summary (Issue 8)