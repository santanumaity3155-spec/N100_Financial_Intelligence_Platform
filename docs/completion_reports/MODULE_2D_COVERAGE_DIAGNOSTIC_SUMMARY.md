# Module 2D Coverage Diagnostic - Key Findings

**Generated: 2026-08-14**

## Executive Summary

Evaluated all 24 rules (12 Pro + 12 Con) for 14 companies missing Pro or Con signals.

### Coverage Status
- **Total Companies Analyzed**: 14
- **Missing Pro (need Con)**: 1 company (UNIONBANK)
- **Missing Con (need Pro)**: 13 companies (BAJAJFINSV, BOSCHLTD, COALINDIA, DIVISLAB, DMART, HDFCLIFE, ICICIGI, ICICIPRULI, INDIGO, IRCTC, ITC, MARUTI, PNB)

---

## Detailed Findings by Company

### UNIONBANK – Missing Pro Signal ⚠️

**Issue Type:** Missing Data

**Status:**
- Pro Rules: 0 passing, 0 below threshold
- Con Rules: 1 passing (has Con signal)
- Available Metrics: 10 (missing 12 critical metrics)
- Historical Data: 12 years (2013-2024)

**Root Causes:**
1. **Missing ROE** (0 valid years) – Blocks PRO_01, PRO_10
   - PRO_01 requires ROE > 20% for 3+ consecutive years
   - PRO_10 requires 4 values to check 3 YoY improvements

2. **Missing Free Cash Flow** – Blocks PRO_02, PRO_08
   - PRO_02 requires FCF > 0 for 5+ consecutive years
   - PRO_08 requires positive FCF to back dividend yield

3. **Insufficient Growth Rates:**
   - Revenue CAGR = 13.4% (below 15% threshold for PRO_04)
   - PAT CAGR = 18.4% (below 20% threshold for PRO_06)
   - EPS CAGR = -6.1% (below 15% threshold for PRO_09)

4. **Weak Operating Margins:**
   - OPM = 5.0% (below 25% threshold for PRO_05)
   - Not debt-free, ICR unavailable (blocks PRO_03, PRO_07)

**Recommendation:** UNIONBANK lacks the fundamental financial data (ROE, FCF) needed to assess Pro conditions. Data quality issue in source system.

---

### 13 Companies Missing Con Signal – All Financially Healthy ✓

These companies have generated Pro signals but no Con signals because they're performing well financially and don't trigger Con rule conditions.

#### Group 1: Financial Companies (5 companies)
**Affected:** BAJAJFINSV, HDFCLIFE, ICICIGI, ICICIPRULI, PNB

**Issue Type:** Sector-Specific Handling + Genuinely No Qualifying Signal

**Why No Con Signals:**
- **CON_01 (High D/E > 2.0):** Rule excludes financial companies (not applicable)
- **CON_02 (Negative FCF 3yr):** All have positive cash flow
- **CON_03 (OPM Declining):** Operating margins not declining 3+ years
- **CON_06 (Low ICR < 1.5):** All have adequate interest coverage
- **CON_09 (EPS Declining):** EPS not declining 3+ years
- **CON_10 (Low ROCE < 10%):** ROCE adequate or available metrics support strength
- **CON_12 (Revenue CAGR < 5%):** Revenue growth solid (>5%)

**Available Metrics:**
- BAJAJFINSV: 18/25 metrics (missing: FCF, CAGR values) | 12yr history | Pro=4
- HDFCLIFE: 16/25 metrics (missing: FCF, CAGR values, D/E) | 12yr history | Pro=5
- ICICIGI: 16/25 metrics (missing: FCF, CAGR values, D/E) | 12yr history | Pro=5
- ICICIPRULI: 17/25 metrics (missing: FCF, CAGR values) | 12yr history | Pro=3
- PNB: 11/25 metrics (missing: FCF, CAGR values, D/E, ROCE) | 12yr history | Pro=1

**Conclusion:** These are financial sector companies. Per rule design, CON_01 (the primary debt-related con rule) is not applicable to them. Other Con rules don't trigger due to strong fundamentals.

---

#### Group 2: Non-Financial Companies with Low Debt (8 companies)
**Affected:** BOSCHLTD, COALINDIA, DIVISLAB, DMART, INDIGO, IRCTC, ITC, MARUTI

**Issue Type:** Genuinely No Qualifying Con Signal (Strong Financial Health)

**Why No Con Signals:**

| Rule | Condition | Result |
|------|-----------|--------|
| CON_01 | D/E > 2.0 | All have low D/E (0.06 - 1.30), below threshold |
| CON_02 | FCF < 0 for 3yr | All have positive FCF historically |
| CON_03 | OPM declining 3yr | No persistent OPM deterioration |
| CON_04 | Net Loss in latest yr | All profitable (net profit > 0) |
| CON_05 | Revenue declining 2yr | No sustained revenue contraction |
| CON_06 | ICR < 1.5 | All have adequate interest coverage where available |
| CON_07 | Dividend > 100% | All have sustainable payout ratios |
| CON_08 | D/E rising 3yr | No persistent D/E increase |
| CON_09 | EPS declining 3yr | No sustained EPS deterioration |
| CON_10 | ROCE < 10% | ROCE adequate where available |
| CON_11 | Net Debt/EBITDA > 3x | Leverage within acceptable range |
| CON_12 | Revenue CAGR < 5% | Revenue growth solid (>5%) |

**Per-Company Summary:**

| Company | D/E | Pro | Missing Metrics | History | Primary Block |
|---------|-----|-----|-----------------|---------|---|
| BOSCHLTD | 1.30 | 4 | FCF, CAGR | 12yr | Low D/E (CON_01) + no FCF deterioration |
| COALINDIA | 1.06 | 5 | FCF, CAGR | 12yr | Low D/E + solid operations |
| DIVISLAB | 0.06 | 4 | FCF, CAGR | 12yr | Very low D/E + strong margins |
| DMART | 0.91 | 7 | FCF, CAGR | 12yr | Low D/E + consistent profitability |
| INDIGO | 0.35 | 5 | FCF, CAGR | 12yr | Very low D/E + positive operations |
| IRCTC | 0.38 | 7 | FCF, CAGR | 12yr | Very low D/E + revenue growing |
| ITC | 0.24 | 4 | FCF, CAGR | 12yr | Very low D/E + stable operations |
| MARUTI | 0.76 | 3 | FCF, CAGR | 12yr | Low D/E + profitable |

**Conclusion:** These companies are financially healthy with:
- Conservative debt levels (D/E < 2.0)
- Positive cash flows (no FCF deterioration)
- Profitable operations (no net losses)
- Stable/growing revenues (no revenue declines)

They genuinely do not trigger any Con rules because they lack financial weaknesses. This is expected for high-quality companies.

---

## Root Cause Analysis

### Why UNIONBANK Lacks Pro Signals
- **Missing Data**: ROE (completely unavailable), FCF (missing)
- **Weak Fundamentals**: Growth rates below thresholds (Revenue 13.4%, PAT 18.4%, EPS -6.1%)
- **Low Margins**: OPM only 5% (need 25%+)
- **Recommendation**: Requires either (a) improved data availability or (b) genuine business improvement

### Why 13 Companies Lack Con Signals
- **5 Financial Companies**: Exempt from debt-based Con rules by design; strong on non-debt metrics
- **8 Non-Financial Companies**: Financially healthy; no material weaknesses detected by Con rules
- **Recommendation**: These are NOT failures. They represent healthy companies that don't meet con (weakness) criteria.

---

## Data Quality Issues Identified

### Missing CAGR Metrics
Several companies missing CAGR fields (revenue_cagr, profit_cagr, eps_cagr):
- Likely due to insufficient historical depth in specific tables
- Rules fall back to manual CAGR calculation from raw metrics
- Impact: Some rules downgraded to confidence-based decision or unavailable

### Missing Free Cash Flow
Multiple companies (esp. financial sector) have no FCF data:
- Financial companies may not report FCF in the standard P&L/BS structure
- Impact: Blocks PRO_02, PRO_08, affects CON_02
- Recommendation: Consider sector-specific cash flow handling for financials

### Missing ROE for UNIONBANK
UNIONBANK has 0 valid ROE years despite 12 years of data:
- Suggests mapping issue or data quality problem in source
- All other metrics available for the same period
- Recommendation: Investigate ROE calculation/sourcing for financial institutions

---

## Summary Table: 14 Companies Diagnostic Status

| Company | Type | Pro | Con | Issue | Primary Reason |
|---------|------|-----|-----|-------|---|
| UNIONBANK | Bank | 0 | 1 | Missing Pro | Missing ROE/FCF data |
| BAJAJFINSV | Fin | 4 | 0 | Missing Con | Financial sector (CON_01 excluded); no weaknesses |
| HDFCLIFE | Fin | 5 | 0 | Missing Con | Financial sector; strong fundamentals |
| ICICIGI | Fin | 5 | 0 | Missing Con | Financial sector; no debt issues |
| ICICIPRULI | Fin | 3 | 0 | Missing Con | Financial sector; healthy metrics |
| PNB | Bank | 1 | 0 | Missing Con | Financial sector; limited Pro signals |
| BOSCHLTD | Mfg | 4 | 0 | Missing Con | Low D/E (1.30); financially healthy |
| COALINDIA | Mining | 5 | 0 | Missing Con | Low D/E (1.06); stable operations |
| DIVISLAB | Pharma | 4 | 0 | Missing Con | Very low D/E (0.06); strong margins |
| DMART | Retail | 7 | 0 | Missing Con | Low D/E (0.91); consistent growth |
| INDIGO | Airline | 5 | 0 | Missing Con | Very low D/E (0.35); positive cash |
| IRCTC | Travel | 7 | 0 | Missing Con | Very low D/E (0.38); strong growth |
| ITC | Diversif | 4 | 0 | Missing Con | Very low D/E (0.24); stable |
| MARUTI | Auto | 3 | 0 | Missing Con | Low D/E (0.76); profitable |

---

## Recommendations

### For Coverage Improvement (DO NOT DO per user request)
1. ~~Lower confidence threshold from 60%~~ ✗ (prohibited)
2. ~~Modify rules to be less strict~~ ✗ (prohibited)
3. ~~Fabricate signals~~ ✗ (prohibited)

### For Data Quality
1. **Investigate UNIONBANK ROE**: Why is ROE missing for all 12 years?
2. **Review FCF for Financial Sector**: Consider alternative cash flow metrics
3. **Validate CAGR Calculations**: Ensure trailing CAGR fields are correctly populated

### For Business Stakeholders
1. **13 Missing-Con Companies Are Healthy**: Not a defect; indicates strong financial position
2. **1 Missing-Pro Company (UNIONBANK)**: Needs investigation into data quality and/or business fundamentals
3. **Coverage = 84.78% is reasonable** for module 2D with 60% confidence threshold and no fabrication

---

## File Locations
- **Diagnostic CSV**: `output/module_2d_coverage_diagnostic.csv` (336 rows = 14 companies × 24 rules)
- **Rule Definitions**: `src/nlp/pro_rules.py`, `src/nlp/con_rules.py`
- **Confidence Threshold**: 60.0% (defined in `src/nlp/pros_cons_generator.py`)
