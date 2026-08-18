# Module 4C Completion Report — Year-over-Year Capital Allocation Pattern Changes

**Sprint:** Sprint 5 — Intelligence, NLP & PDF Reports  
**Module:** Module 4 — Capital Allocation Intelligence  
**Sub-Module:** Module 4C — Year-over-Year Capital Allocation Pattern Changes  
**Date:** August 18, 2026  
**Status:** ✅ COMPLETE  

---

## 1. Objective

Module 4C identifies companies whose Capital Allocation pattern changed between their previous valid financial year and their latest valid financial year in the N100 Financial Intelligence Platform. It analyzes historical financial statements, evaluates capital allocation classifications for all available financial years, compares each company's latest valid classification against its previous valid classification, and exports the pattern changes to `output/pattern_changes.csv`.

---

## 2. Source of Capital Allocation Data

- **Database:** `data/database/n100.db` (SQLite)
- **Authoritative Companies Source:** `companies` master table (94 companies)
- **Financial Statements:** `cash_flow` and `profit_loss` tables
- **Classification Engine:** `classify_capital_allocation` from `src/analytics/cashflow_kpis.py`
- **Pattern Mapping:** `map_rating_to_pattern` (reusing authoritative Module 4B mapping)

---

## 3. Methodology & Pattern Change Logic

1. **Available Years Detection:** Dynamically detects all distinct financial years with statement data (2011 to 2024).
2. **Yearly Classifications:** Evaluates Free Cash Flow (FCF), Operating Cash Flow (OCF), Cash Conversion, and CapEx Intensity for every authoritative company for each financial year.
3. **Valid History Determination:** For each company, iterates backward through years to find the most recent two years with valid financial data (`latest_year` and `previous_year`).
4. **Pattern Comparison:** 
   - `changed = True` if `previous_pattern != latest_pattern`.
   - Only companies with `changed = True` are exported to `output/pattern_changes.csv`.
   - Unchanged companies (`previous_pattern == latest_pattern`) and companies with insufficient history (<2 valid financial years) are excluded from the primary pattern changes output file.

---

## 4. Analysis & Output Results

Summary statistics across 94 authoritative companies:

- **Total Authoritative Companies:** `94`
- **Companies with Valid Historical Data (>=2 years):** `93`
- **Companies with Changed Pattern:** `44`
- **Companies with Unchanged Pattern:** `49`
- **Companies with Insufficient History:** `1` (`ATGL` - missing historical cash flow data)

Output File generated:
- `output/pattern_changes.csv` (44 rows, 8 columns)
- `output/pattern_change_summary.csv` (Transition Matrix summary)

---

## 5. Output File Schema (`output/pattern_changes.csv`)

| Column Name | Description |
| :--- | :--- |
| `company_id` | Authoritative Ticker / ID |
| `company_name` | Full Company Name |
| `sector` | Industry Sector |
| `previous_year` | Previous Financial Year with Data |
| `previous_pattern` | Capital Allocation Pattern in Previous Year |
| `latest_year` | Latest Financial Year (2024) |
| `latest_pattern` | Capital Allocation Pattern in Latest Year |
| `changed` | Boolean (`True`) |

---

## 6. Validation Results

Execution of `validate_module4c.py`:

```
============================================================
MODULE 4C VALIDATION
============================================================
Required Columns              PASS
Company IDs (44 valid)        PASS
Pattern Validity              PASS
Year Ordering (prev < latest) PASS
Pattern Change Logic (0 invalid) PASS
Duplicate Check (0 duplicates) PASS
Output Readability (3531 bytes) PASS
============================================================
VALIDATION SUMMARY
============================================================
Required Columns              : PASS
Company IDs                   : PASS
Pattern Validity              : PASS
Year Ordering                 : PASS
Pattern Change Logic          : PASS
Duplicate Check               : PASS
Output Readability            : PASS
============================================================
FINAL STATUS: PASS
============================================================
```

---

## 7. Testing

- **Test Suite:** `tests/analytics/test_module4c_pattern_changes.py`
- **Test Scenarios (11/11 passed):**
  1. Available years extraction (returns sorted descending integer years)
  2. Computing year classifications for a specific year
  3. Computing pattern changes pipeline returns valid DataFrame & summary dict
  4. Year ordering check: `previous_year < latest_year` for all rows
  5. Pattern change check: `previous_pattern != latest_pattern` for all rows
  6. Supported pattern validity: all patterns in `SUPPORTED_PATTERNS`
  7. No duplicate companies in pattern changes output
  8. Summary count reconciliation (`total = with_prev + insufficient`)
  9. Output CSV file generation
  10. Integration pipeline execution (`run_module4c_pipeline`)
  11. Insufficient history handling

---

## 8. Definition of Done Checklist

- [x] Year-over-year pattern change logic implemented
- [x] Authoritative 94 company scope preserved
- [x] Missing historical data handled gracefully
- [x] Unchanged companies excluded from `pattern_changes.csv`
- [x] All 44 changed companies accurately reported
- [x] `output/pattern_changes.csv` generated and formatted
- [x] `validate_module4c.py` created and passes (PASS)
- [x] Module 4C tests created and pass (`11 passed`)
- [x] Completion report created (`MODULE_4C_COMPLETION_REPORT.md`)