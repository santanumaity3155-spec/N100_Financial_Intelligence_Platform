# Sprint 5 – Module 3 Completion Report
# Cash Flow Intelligence (Intelligence, NLP & PDF Reports)

## 1. Status

**MODULE 3 STATUS: COMPLETE**

This report supersedes the earlier Sprint 4 "Module 3" report (screener/peer
pages), which belonged to a different sprint.  The current Module 3 of
Sprint 5 is the **Cash Flow Intelligence Engine**.

## 2. Root Cause of Missing Excel Output

The required files `output/cashflow_intelligence.xlsx` and
`output/distress_alerts.csv` were missing from the project `output/`
directory for two compounding reasons:

1. **Wrong project-root resolution (primary root cause).**
   `src/module3_cashflow_intelligence.py` resolved the project root with

   ```python
   PROJECT_ROOT = Path(__file__).resolve().parents[2]
   ```

   Because the file lives at `<project_root>/src/module3_cashflow_intelligence.py`,
   `parents[2]` resolves to the *parent directory of the repository*
   (`...\N100 Financial Intelligence Platform\`), which contains a second,
   partial copy of the project.  That copy's `src/analytics/__init__.py` is
   corrupted (a literal `\n` inside a docstring, i.e. `"""Placeholder module."""\n`),
   which raised:

   ```
   SyntaxError: unexpected character after line continuation character
   ```

   as recorded in `module3.log`.  Every `import src.*` therefore failed and the
   script terminated before generating anything.

2. **Wrong output directory.**
   Even when an earlier variant ran successfully, `OUTPUT_DIR =
   parents[2] / "output"` pointed at the *parent* tree's `output/` directory,
   which is why stale `cashflow_intelligence.xlsx` / `distress_alerts.csv`
   files appeared there (with `sector` all `NaN` and empty
   `latest_net_profit`), while the real project `output/` stayed empty.

Additional data-quality issues that would have produced wrong output:

* `companies.sector` is NULL for every company row in the canonical database;
  sector data actually lives in `sectors.sub_sector`.
* The `cash_flow` table stores figures in `operating_activity` /
  `investing_activity` / `financing_activity`; the canonical
  `cash_from_*` columns exist in the schema but are NULL for every row.
* Periods mix canonical (`Mar 2024`) and legacy (`Mar-24`) formats, so
  naive lexical `ORDER BY period` sorting mis-orders TCS-style history.

## 3. Fixes

| File | Fix |
|------|-----|
| `src/module3_cashflow_intelligence.py` | Rewritten as the orchestrator. Resolves `PROJECT_ROOT = Path(__file__).resolve().parents[1]` (the real project root) and inserts it at `sys.path[0]`. Writes outputs into the real project `output/` via `src.config.constants.OUTPUT_DIR`. Fetches sector from `sectors.sub_sector`. Delegates every metric to the analytics engine. |
| `src/analytics/cashflow_intelligence.py` | Existing Sprint 5 metrics engine (kept and reused): CFO quality, CapEx intensity, FCF CAGR, FCF conversion, distress, deleveraging, capital allocation. Handles period canonicalisation/de-duplication, non-annual period exclusion, missing-value safety, and both cash-flow column families. |
| `src/analytics/cashflow.py` | Repaired a corrupted placeholder file (`"""Placeholder module."""\n` -> valid docstring) that would otherwise raise a `SyntaxError` if ever imported. |
| `validate_module3.py` | New standalone validator with the required PASS/FAIL report. |
| `tests/analytics/test_cashflow_intelligence.py` | New dedicated Module 3 tests (59 tests). |

## 4. Database Used

* Path: `data/database/n100.db` (the canonical database resolved by
  `src/config/constants.py` / `src/database/connection.py`).
* Company count: **94** (`SELECT COUNT(*) FROM companies`).
* Other `.db` files in the repo are 0-byte placeholders or the older
  parent-tree copy (92 companies, different schema) and are NOT used.

## 5. Calculations Implemented (Sprint 5 specification)

1. **CFO Quality Score** — average of `CFO / PAT` over the latest 5 valid
   years.  Classification: `> 1.0` High Quality; `0.5–1.0` Moderate;
   `< 0.5` Accrual Risk.  `PAT == 0` and missing values are skipped (never
   fabricated as zero).
2. **CapEx Intensity** — `abs(investing_activity) / sales * 100` (latest
   year).  Classification: `< 3%` Asset Light; `3–8%` Moderate; `> 8%`
   Capital Intensive.
3. **Free Cash Flow** — `FCF = CFO - CapEx`, reusing
   `cashflow_kpis.calculate_free_cash_flow` (CapEx = |investing_activity|).
4. **FCF CAGR (5-year)** — reuses `src/analytics/cagr.calculate_cagr`.
   Handles insufficient history, zero base, negative base, decline to loss,
   turnaround and both-negative cases.
5. **FCF Conversion** — `FCF / PAT * 100` (latest year); `PAT == 0` returns
   `None`.
6. **Distress Signal** — latest year `CFO < 0 AND CFF > 0` → `True`.
7. **Deleveraging** — latest year `CFF < 0` AND borrowings declining
   year-over-year.  Missing borrowings are never treated as zero.
8. **Capital Allocation** — reuses
   `cashflow_kpis.classify_capital_allocation`; missing data reports
   `"Insufficient Data"` (never a fabricated rating).

## 6. Output Files

| File | Rows | Columns |
|------|------|---------|
| `output/cashflow_intelligence.xlsx` | 94 (one per company) | `company_id`, `sector`, `cfo_quality_score`, `cfo_quality_label`, `capex_intensity_pct`, `capex_label`, `fcf_cagr_5yr`, `fcf_conversion_pct`, `distress_flag`, `deleveraging_flag`, `capital_allocation_label` |
| `output/distress_alerts.csv` | 13 | `company_id`, `sector`, `CFO`, `CFF`, `latest_net_profit` |

## 7. Validation Results

`python validate_module3.py`

```
============================================================
MODULE 3 VALIDATION
============================================================
Excel output: PASS
Distress CSV: PASS
Required columns: PASS
Company coverage: PASS
Duplicate rows: PASS
CFO Quality: PASS
CapEx Intensity: PASS
FCF CAGR: PASS
FCF Conversion: PASS
Distress Detection: PASS
Deleveraging: PASS
Capital Allocation: PASS

FINAL STATUS: PASS
============================================================
```

## 8. Test Results

| Suite | Result |
|-------|--------|
| `python -m pytest tests/kpi/test_cashflow.py -q` | 48 passed |
| `python -m pytest tests/analytics/test_cashflow_intelligence.py -q` | 59 passed |
| `python -m pytest tests/ -q` (full regression) | all pass (863 + 59 new) |

## 10. Additional Fix — IndentationError in `src/module3_cashflow_intelligence.py`

A subsequent review found that `src/module3_cashflow_intelligence.py` had an
`IndentationError` at line 228 inside `process_all_companies()`:

```python
                results: List[Dict[str, Any]] = []
    for _, company in companies_df.iterrows():
```

The extra indentation on `results:` caused Python to raise
`IndentationError: unexpected indent`, making the module un-importable.
Because `tests/analytics/test_cashflow_intelligence.py` and
`validate_module3.py` both import from this module, **every downstream
test and validation run failed** and the real generation pipeline could
not be executed.

**Fix applied:** corrected the indentation so that `results:` is aligned
with the other statements in the function body and the `for` loop is
properly nested:

```python
    results: List[Dict[str, Any]] = []
    for _, company in companies_df.iterrows():
        ...
```

After the fix, the module imports cleanly, the pipeline executes
successfully, and `output/distress_alerts.csv` is regenerated with the
correct 13 distress companies.

* `ATGL` has no cash-flow rows and `SBIN` has no balance-sheet rows in the
  canonical database; their metrics correctly report `Insufficient Data` /
  `False` rather than fabricated values.
* `ULTRACEMCO` and `UNIONBANK` have no `sectors` row, so their `sector` cell
  is empty (`None`) in the outputs.
* FCF CAGR is only reported where the existing `cagr` engine can produce a
  meaningful number; turnarounds, declines-to-loss, zero bases and negative
  FCF ranges are represented as `NaN` (flagged internally) instead of a
  misleading percentage.

