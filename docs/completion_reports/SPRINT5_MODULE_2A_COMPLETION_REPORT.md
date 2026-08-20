# Sprint 5 – Module 2A Completion Report
## Auto Pros/Cons Generator Foundation

**Status:** ✅ COMPLETE
**Scope:** Architecture, data layer, rule framework, confidence framework,
validation framework, and testing foundation for the future Pro/Con rules.
**Date:** 2026-08-11

---

## 1. Files Created

| File | Purpose |
|------|---------|
| `src/nlp/pros_cons_generator.py` | Module 2A foundation (data access layer, company context, safe/historical helpers, rule engine, confidence, validation, sector support, logging). |
| `tests/nlp/test_pros_cons_generator.py` | 89 focused tests covering all 22 required test points. |
| `SPRINT5_MODULE_2A_COMPLETION_REPORT.md` | This report. |

## 2. Files Modified

**None.** No completed module was modified.

- `src/nlp/parser.py` (Sprint 5 Module 1) — untouched.
- Existing `src/analytics/*`, `src/kpi_engine/*`, `src/database/*` — untouched.

## 3. Database Tables Inspected

Live SQLite database: `data/database/n100.db`

| Table | Rows | Notes |
|-------|------|-------|
| `companies` | 94 | Master table; `sector`/`industry` are NULL in the live DB |
| `sectors` | 92 | `broad_sector` NULL; **`sub_sector` is the actual sector source** |
| `profit_loss` | 1,263 | `sales`, `net_profit`, `opm_percentage`, `operating_profit`, `depreciation`, `eps`, `dividend_payout`, `interest` |
| `balance_sheet` | 1,225 | `borrowings`, `reserves`, `investments`, `total_assets`, `equity_capital` |
| `cash_flow` | 1,164 | `cash_from_operating_activity`, `cash_from_financing_activity`, `free_cash_flow` |
| `financial_kpis` | 1,164 | Primary ratio source: `roe`, `roce`, `debt_to_equity`, `interest_coverage`, CAGR fields |
| `financial_ratios` | 1,065 | Fallback ratio source |
| `market_cap` | 92 | Preferred `dividend_yield` source (92/92 populated) |
| `analysis` | 5 | Sprint 5 Module 1 raw text source |

Also inspected: `documents`, `peer_groups`, `peer_percentiles`, `stock_prices`,
`financial_health_scores` (present but not required for Module 2A).

## 4. Data Sources Used

Primary metric → source mapping implemented in `METRIC_SOURCES` (table.column):

| Metric | Source(s) |
|--------|-----------|
| ROE | `financial_kpis.roe` → `financial_ratios.roe` → `companies.roe_percentage` |
| ROCE | `financial_kpis.roce` → `companies.roce_percentage` |
| D/E | `financial_kpis.debt_to_equity` |
| ICR | `financial_kpis.interest_coverage` |
| FCF | `cash_flow.free_cash_flow` → `financial_kpis.free_cash_flow` |
| Revenue / Net Profit / OPM / EPS / Div. Payout | `profit_loss.sales / net_profit / opm_percentage / eps / dividend_payout` |
| Dividend Yield | `market_cap.dividend_yield` → `financial_kpis.dividend_yield` |
| PAT / Rev / EPS CAGR | `financial_kpis.profit_cagr / revenue_cagr / eps_cagr` (TTM / trailing) |
| Borrowings / Assets / Reserves / Investments | `balance_sheet.*` |
| CFO / CFF | `cash_flow.cash_from_operating_activity / cash_from_financing_activity` |
| Net Debt (derived) | `borrowings − investments` |
| EBITDA (derived) | `operating_profit + depreciation` |

Period parsing: `"Mar 2024"` → year 2024; `"Mar 2023 15"` artifact → 2023;
`"TTM"` excluded from the annual series (kept as trailing metrics).

## 5. Number of Companies Detected

- **94** companies in `companies` master table.
- **92** in `sectors` (with `sub_sector` populated).
- **100** distinct company_id present across the financial statement tables
  (some IDs exist in statements but not in the companies master → noted as a
  data-consistency limitation).

## 6. Historical Data Coverage (calendar-year granularity)

| Table | Companies | Median years | Max | ≥3yrs | ≥5yrs |
|-------|-----------|--------------|-----|-------|-------|
| `profit_loss` | 100 | 12 | 12 | 99 | 99 |
| `balance_sheet` | 98 | 12 | 12 | 97 | 97 |
| `cash_flow` | 100 | 12 | 12 | 99 | 99 |
| `financial_kpis` | 92 | 12 | 12 | 91 | 91 |

Company contexts built for all 94 companies: **94/94 have a latest year (2024)**
and **0/94 lack ≥3 years of history**.

## 7. Missing-Data Statistics (Module 2A foundation run)

- Companies with latest-year ROE: 91/94 (**3 missing**).
- Companies with ≥3yr history: 94/94 (0 missing).
- Financial companies detected: **22** (7 financial sub-sectors).
- `profit_loss` annual rows: 1,164 → missing `opm_percentage` 13 rows,
  `dividend_payout` 4, `eps` 4, `sales`/`net_profit` 0.
- Reported honestly — no fabricated values.

## 8. Rule Framework Design

- **`RuleResult`** dataclass: `company_id, rule_id, rule_type, triggered,
  text, confidence_pct, reason` with `validate()` and `to_dict()`.
- **`FinancialRule`** abstract base: `evaluate(context, conn)` contract.
- **Registry:** `PRO_RULES = []`, `CON_RULES = []` (EMPTY in Module 2A) with
  `register_pro_rule()` / `register_con_rule()` / `get_registered_rules()`.
- **Entry point:** `evaluate_rules_for_company(context)` returns `[]` now;
  Modules 2B/2C register PRO_01–PRO_12 and CON_01–CON_12 without touching the
  engine.

## 9. Confidence Framework

- Constants: `CONFIDENCE_MIN=0.0`, `CONFIDENCE_MAX=100.0`,
  `CONFIDENCE_THRESHOLD=60.0`, `CONFIDENCE_DECIMALS=2`.
- `validate_confidence()` — range/numeric check.
- `format_confidence()` — clamp + round to 2 decimals.
- `calculate_confidence(factors, weights=None)` — generic weighted aggregation
  (infrastructure only; no financial signal-strength formulas invented).

## 10. Validation Framework

- **`validate_output_schema(df)`** — required columns
  (`company_id, type, rule_id, text, confidence_pct`), `type` ∈ {pro, con},
  numeric/0–100 confidence, non-null `company_id`/`rule_id`,
  no `(company_id, type, rule_id)` duplicates.
- **`validate_company_coverage(companies, results_df)`** — reports
  missing_pro/missing_con. With zero rules implemented the correct output is
  `missing_pro = missing_con = N` (no fabricated rows).

## 11. Test Results

Module 2A suite: **89 / 89 passed** covering the 22 required test points:

1. Data loading ✅  2. Context creation ✅  3. Latest-year ✅
4. Historical extraction ✅  5. Missing values ✅  6. NaN ✅
7. inf ✅  8. Zero denominator ✅  9. 3-year detection ✅
10. 5-year detection ✅  11. Improving ✅  12. Declining ✅
13. Consecutive positive ✅  14. Consecutive negative ✅
15. RuleResult ✅  16. Rule registry ✅  17. Confidence range ✅
18. Output schema ✅  19. Duplicate detection ✅
20. Empty-result coverage ✅  21. Financial-sector ✅
22. Module 1 regression ✅

Command:
```
python -m pytest tests/nlp/test_pros_cons_generator.py -q
```

## 12. Module 1 Regression Results

- `output/analysis_parsed.csv` and `output/parse_failures.csv` exist and are
  non-empty with expected columns.
- `python -m pytest tests/nlp/test_parser.py -q` → **37 / 37 passed**.
- Combined nlp suite: **126 passed**.

## 13. Known Limitations

1. `companies.sector` and `sectors.broad_sector` are NULL in the live DB;
   sector classification relies entirely on `sectors.sub_sector`.
2. `financial_kpis.roe` values are materially mis-scaled in the source data
   (e.g. RELIANCE ROE ≈ 1167.9). Module 2A serves data faithfully; calibration
   belongs to the rule phases (2B/2C), not this foundation.
3. 100 distinct company_id exist in statements vs. 94 in the master table
   (master table is the canonical coverage universe).
4. Some companies report two same-calendar-year periods (e.g. `Mar 2024` +
   `Sep 2024`); rows are combined per year favoring the most complete row.
5. `RuleResult`/`FinancialRule` are generic; no thresholds are validated.

## 14. Confirmation — NO Pro/Con Rules Implemented

❌ **PRO_01 … PRO_12 — NOT implemented.**
❌ **CON_01 … CON_12 — NOT implemented.**
❌ **No fabricated Pros/Cons generated.**
❌ **No 24-rule thresholds encoded.**
❌ **No claim of 92-company coverage.**

Both registries are empty; `evaluate_rules_for_company()` returns `[]`.

## 15. Final Module 2A Status

✅ Module 2A Definition of Done **satisfied**:

- `pros_cons_generator.py` foundation exists
- Actual project schema inspected
- Company / financial data loading works
- Latest-year and historical context work
- Missing data handled safely
- Trend helpers work
- Generic `RuleResult` + empty rule registry exist
- Confidence framework exists
- Output-schema / duplicate / coverage validation exist
- Financial-sector helper exists
- Logging & defensive error handling exist
- Module 2A tests pass (89/89)
- Module 1 regression tests pass (37/37)

**Next phases (NOT started automatically):** Module 2B (Pro rule
implementation) and Module 2C (Con rule implementation).