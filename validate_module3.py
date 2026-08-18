"""
validate_module3.py

Sprint 5 - Module 3 (Cash Flow Intelligence) output validation.

Verifies:
  1. output/cashflow_intelligence.xlsx exists
  2. output/distress_alerts.csv exists
  3. Excel is readable
  4. CSV is readable
  5. required columns exist
  6. company coverage is correct (against the authoritative companies table)
  7. duplicate company rows == 0
  8. CFO quality labels are valid
  9. CapEx labels are valid
 10. distress flags are valid
 11. deleveraging flags are valid
 12. capital allocation labels are valid
 13. distress CSV contains only valid distress companies

Run from the project root:

    python validate_module3.py
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.module3_cashflow_intelligence import (  # noqa: E402
    OUTPUT_COLUMNS,
    DISTRESS_CSV_COLUMNS,
    EXCEL_OUTPUT_FILENAME,
    DISTRESS_CSV_FILENAME,
)
from src.config.constants import OUTPUT_DIR  # noqa: E402
from src.database.connection import get_connection  # noqa: E402

# Valid label / flag values (produced by the Sprint 5 engine)
VALID_CFO_QUALITY_LABELS = {"High Quality", "Moderate", "Accrual Risk", "Insufficient Data"}
VALID_CAPEX_LABELS = {"Asset Light", "Moderate", "Capital Intensive", "Insufficient Data"}
VALID_CAPITAL_ALLOCATION_LABELS = {
    "EXCELLENT", "GOOD", "MODERATE", "WEAK", "DISTRESSED", "Insufficient Data",
}


def _check(ok: bool, *details: Any) -> bool:
    """Return ok; print a human readable detail line when it is False."""
    if not ok:
        print("    " + " ".join(str(d) for d in details))
    return ok


def get_authoritative_company_ids() -> List[str]:
    """Company ids from the authoritative ``companies`` table."""
    conn = get_connection()
    try:
        rows = pd.read_sql_query("SELECT company_id FROM companies ORDER BY company_id", conn)
        return rows["company_id"].tolist()
    finally:
        conn.close()


def validate() -> Dict[str, bool]:
    """Run every Module 3 check and return a {label: passed} mapping."""
    checks: Dict[str, bool] = {}

    excel_path = OUTPUT_DIR / EXCEL_OUTPUT_FILENAME
    csv_path = OUTPUT_DIR / DISTRESS_CSV_FILENAME

    # ------------------------------------------------------------------
    # 1. Files exist
    # ------------------------------------------------------------------
    excel_exists = excel_path.exists()
    csv_exists = csv_path.exists()
    checks["excel_file_exists"] = excel_exists
    checks["csv_file_exists"] = csv_exists

    excel_size = excel_path.stat().st_size if excel_exists else 0
    csv_size = csv_path.stat().st_size if csv_exists else 0
    checks["excel_nonempty"] = excel_exists and excel_size > 0
    checks["csv_nonempty_or_valid_empty"] = csv_exists and csv_size >= 0

    excel_df: Optional[pd.DataFrame] = None
    csv_df: Optional[pd.DataFrame] = None

    # ------------------------------------------------------------------
    # 3/5/7. Excel readable + required columns + duplicates
    # ------------------------------------------------------------------
    excel_ok = False
    if excel_exists and excel_size > 0:
        try:
            excel_df = pd.read_excel(excel_path)
            excel_ok = True
        except Exception as exc:  # noqa: BLE001
            print(f"    Excel read error: {exc!r}")
    checks["excel_readable"] = excel_ok

    if excel_df is not None:
        missing = [c for c in OUTPUT_COLUMNS if c not in excel_df.columns]
        checks["required_columns"] = _check(not missing, f"missing columns: {missing}")
        checks["duplicate_rows"] = _check(
            int(excel_df["company_id"].duplicated().sum()) == 0,
            f"duplicate company rows: {int(excel_df['company_id'].duplicated().sum())}",
        )
    else:
        checks["required_columns"] = False
        checks["duplicate_rows"] = False

    # ------------------------------------------------------------------
    # 2/4. CSV readable + required columns
    # ------------------------------------------------------------------
    csv_ok = False
    if csv_exists and csv_size > 0:
        try:
            csv_df = pd.read_csv(csv_path)
            csv_ok = True
        except Exception as exc:  # noqa: BLE001
            print(f"    CSV read error: {exc!r}")
    elif csv_exists and csv_size == 0:
        # A zero-row CSV is a legitimate outcome (no distress companies).
        try:
            csv_df = pd.read_csv(csv_path)
            csv_ok = True
        except Exception as exc:  # noqa: BLE001
            print(f"    CSV read error: {exc!r}")
    checks["csv_readable"] = csv_ok

    if csv_df is not None:
        missing = [c for c in DISTRESS_CSV_COLUMNS if c not in csv_df.columns]
        checks["csv_required_columns"] = _check(
            not missing, f"missing csv columns: {missing}"
        )
    else:
        checks["csv_required_columns"] = False

    # ------------------------------------------------------------------
    # 6. Company coverage
    # ------------------------------------------------------------------
    authoritative = get_authoritative_company_ids()
    expected_count = len(authoritative)
    if excel_df is not None:
        actual_ids = set(excel_df["company_id"].astype(str).str.strip())
        expected = set(authoritative)
        coverage_ok = _check(
            len(excel_df) == expected_count,
            f"row count {len(excel_df)} != companies count {expected_count}",
        )
        coverage_ok = _check(
            expected == actual_ids,
            f"missing ids: {sorted(expected - actual_ids)[:10]}",
        ) and coverage_ok
        checks["company_coverage"] = coverage_ok
    else:
        checks["company_coverage"] = False

    # ------------------------------------------------------------------
    # 8-12. Metric / flag validity
    # ------------------------------------------------------------------
    checks["cfo_quality"] = False
    checks["capex_intensity"] = False
    checks["fcf_cagr"] = False
    checks["fcf_conversion"] = False
    checks["distress_detection"] = False
    checks["deleveraging"] = False
    checks["capital_allocation"] = False

    if excel_df is not None:
        # CFO quality
        labels = set(excel_df["cfo_quality_label"].dropna().astype(str))
        checks["cfo_quality"] = _check(
            labels.issubset(VALID_CFO_QUALITY_LABELS),
            f"invalid cfo labels: {labels - VALID_CFO_QUALITY_LABELS}",
        )
        # CapEx intensity
        labels = set(excel_df["capex_label"].dropna().astype(str))
        checks["capex_intensity"] = _check(
            labels.issubset(VALID_CAPEX_LABELS),
            f"invalid capex labels: {labels - VALID_CAPEX_LABELS}",
        )
        # FCF CAGR (missing values are legitimate; non-null must be numeric)
        cagr_notna = excel_df["fcf_cagr_5yr"].notna()
        numeric = pd.to_numeric(excel_df["fcf_cagr_5yr"], errors="coerce")
        checks["fcf_cagr"] = _check(
            bool(numeric[cagr_notna].notna().all()),
            "fcf_cagr_5yr contains non-numeric values",
        )
        # FCF conversion (missing values are legitimate; non-null must be numeric)
        conv_notna = excel_df["fcf_conversion_pct"].notna()
        numeric = pd.to_numeric(excel_df["fcf_conversion_pct"], errors="coerce")
        checks["fcf_conversion"] = _check(
            bool(numeric[conv_notna].notna().all()),
            "fcf_conversion_pct contains non-numeric values",
        )
        # Distress flags are boolean-ish
        distress_vals = excel_df["distress_flag"].dropna()
        checks["distress_detection"] = _check(
            distress_vals.map(lambda v: isinstance(v, (bool,)) or v in (0, 1)).all(),
            "distress_flag contains non-boolean values",
        )
        # Deleveraging flags are boolean-ish
        deleveraging_vals = excel_df["deleveraging_flag"].dropna()
        checks["deleveraging"] = _check(
            deleveraging_vals.map(lambda v: isinstance(v, (bool,)) or v in (0, 1)).all(),
            "deleveraging_flag contains non-boolean values",
        )
        # Capital allocation labels
        labels = set(excel_df["capital_allocation_label"].dropna().astype(str))
        checks["capital_allocation"] = _check(
            labels.issubset(VALID_CAPITAL_ALLOCATION_LABELS),
            f"invalid capital allocation labels: {labels - VALID_CAPITAL_ALLOCATION_LABELS}",
        )

    # ------------------------------------------------------------------
    # 13. Distress CSV contains only valid distress companies
    # ------------------------------------------------------------------
    checks["distress_csv_valid"] = False
    if csv_df is not None and not csv_df.empty:
        valid_rows = (csv_df["CFO"] < 0) & (csv_df["CFF"] > 0)
        checks["distress_csv_valid"] = _check(
            bool(valid_rows.all()),
            "CSV contains rows that do not satisfy CFO<0 AND CFF>0",
        )
        if excel_df is not None:
            excel_distress_ids = set(
                excel_df.loc[
                    excel_df["distress_flag"].fillna(False).astype(bool), "company_id"
                ]
            )
            csv_ids = set(csv_df["company_id"].astype(str).str.strip())
            checks["distress_csv_valid"] = _check(
                csv_ids == excel_distress_ids,
                f"csv ids differ from excel distress ids: "
                f"extra={sorted(csv_ids - excel_distress_ids)[:10]} "
                f"missing={sorted(excel_distress_ids - csv_ids)[:10]}",
            ) and checks["distress_csv_valid"]
    elif csv_df is not None and csv_df.empty:
        # Zero distress rows is a legitimate outcome.
        checks["distress_csv_valid"] = _check(
            True, "no distress companies (valid zero-row CSV)"
        )

    return checks


def main() -> int:
    """Run validation and print the standard Module 3 report."""
    checks = validate()

    results = {
        "Excel output": (
            checks["excel_file_exists"]
            and checks["excel_nonempty"]
            and checks["excel_readable"]
        ),
        "Distress CSV": checks["csv_file_exists"] and checks["csv_readable"],
        "Required columns": (
            checks.get("required_columns", False)
            and checks.get("csv_required_columns", False)
        ),
        "Company coverage": checks.get("company_coverage", False),
        "Duplicate rows": checks.get("duplicate_rows", False),
        "CFO Quality": checks.get("cfo_quality", False),
        "CapEx Intensity": checks.get("capex_intensity", False),
        "FCF CAGR": checks.get("fcf_cagr", False),
        "FCF Conversion": checks.get("fcf_conversion", False),
        "Distress Detection": checks.get("distress_detection", False),
        "Deleveraging": checks.get("deleveraging", False),
        "Capital Allocation": checks.get("capital_allocation", False),
    }

    final_pass = all(results.values())

    print("=" * 60)
    print("MODULE 3 VALIDATION")
    print("=" * 60)
    for label, passed in results.items():
        print(f"{label}: {'PASS' if passed else 'FAIL'}")
    print()
    print(f"FINAL STATUS: {'PASS' if final_pass else 'FAIL'}")
    print("=" * 60)

    return 0 if final_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())



