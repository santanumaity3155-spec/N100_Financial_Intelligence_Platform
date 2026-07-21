# Module 5 - Financial Health Score Engine - TODO

## Steps

### 1. Create Constants File
- [ ] Create `src/health_score/constants.py` with score weights, thresholds, rating bands, remark templates

### 2. Update Database Schema
- [ ] Add `financial_health_scores` table schema to `src/database/schema.py`
- [ ] Register in TABLE_SCHEMAS dict
- [ ] Add indexes for the new table

### 3. Implement Core Engine
- [ ] Create `src/health_score/engine.py` with `HealthScoreEngine` class
  - [ ] `load_data()` - read from financial_ratios
  - [ ] `_clean_numeric()` - sanitize values
  - [ ] `_normalize_score()` - normalize to 0-100
  - [ ] `calculate_profitability_score()` - ROE, ROCE, ROA, NPM, OPM
  - [ ] `calculate_growth_score()` - Revenue/PAT/EPS CAGR
  - [ ] `calculate_cashflow_score()` - FCF, FCF Margin, Cash Conversion, Cash ROA, CapAlloc
  - [ ] `calculate_leverage_score()` - D/E, Interest Coverage, High Leverage Flag
  - [ ] `calculate_efficiency_score()` - Asset Turnover
  - [ ] `calculate_overall_score()` - Weighted average
  - [ ] `generate_rating()` - Qualitative rating
  - [ ] `generate_remarks()` - Auto-generated remarks
  - [ ] `save_to_database()` - UPSERT with transactions
  - [ ] `export_csv()` - CSV output
  - [ ] `run()` - Full pipeline

### 4. Update Package Init
- [ ] Update `src/health_score/__init__.py` to export engine

### 5. Create Test Suite
- [ ] Create `tests/health_score/__init__.py`
- [ ] Create `tests/health_score/test_health_score_engine.py` with 50+ test cases
  - [ ] Individual score calculation tests
  - [ ] Overall score tests
  - [ ] Rating tests
  - [ ] Remarks tests
  - [ ] Missing/edge case tests
  - [ ] Database operation tests
  - [ ] CSV export tests
  - [ ] End-to-end tests

### 6. Update Existing Test Placeholder
- [ ] Update `src/tests/test_health_score.py`

### 7. Run Tests & Validate
- [ ] Run `python -m pytest tests/health_score/test_health_score_engine.py -v`
- [ ] Fix any failures

