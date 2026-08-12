"""
validate_pro_rules.py

Sprint 5 - Module 2B: run the 12 Pro rules against the live N100 database and
emit an intermediate Pro-only result file (``output/pros_generated.csv``).

This is an *intermediate* Module 2B validation output (type = pro only). It is
NOT the final Sprint 5 ``pros_cons_generated.csv`` (that belongs to the
completed Module 2D).

Report includes, per the Module 2B spec:
  - total companies processed
  - companies with at least one Pro / with zero Pros
  - total Pro triggers and trigger count per rule (PRO_01 .. PRO_12)
  - confidence min / mean / max
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database.connection import get_connection  # noqa: E402
from src.nlp.pros_cons_generator import (  # noqa: E402
    OUTPUT_COLUMNS,
    TYPE_PRO,
    evaluate_rules_for_company,
    get_company_context,
    validate_output_schema,
)

OUTPUT_CSV = PROJECT_ROOT / "output" / "pros_generated.csv"


def load_company_ids() -> List[str]:
    """Return the canonical company universe from the master table."""
    conn = get_connection()
    rows = conn.execute("SELECT company_id FROM companies",).fetchall()
    return [str(r[0]).strip().upper() for r in rows if r[0]]


def run_validation() -> Dict[str, object]:
    company_ids = load_company_ids()
    triggered_rows: List[Dict[str, object]] = []
    per_rule = Counter()
    companies_with_pro: set = set()
    zero_pro_companies: List[str] = []
    confidences: List[float] = []

    for cid in company_ids:
        context = get_company_context(cid)
        results = evaluate_rules_for_company(context)
        pro_hits = [r for r in results
                    if r.triggered and r.rule_type == TYPE_PRO]
        if not pro_hits:
            zero_pro_companies.append(cid)
            continue
        companies_with_pro.add(cid)
        for r in pro_hits:
            triggered_rows.append(r.to_dict())
            per_rule[r.rule_id] += 1
            confidences.append(float(r.confidence_pct))

    df = pd.DataFrame(triggered_rows, columns=OUTPUT_COLUMNS)
    df = df.sort_values(["company_id", "rule_id"]).reset_index(drop=True)
    df.to_csv(OUTPUT_CSV, index=False)

    valid, issues = validate_output_schema(df)
    for rule_id in [f"PRO_{i:02d}" for i in range(1, 13)]:
        per_rule.setdefault(rule_id, 0)

    stats = {
        "total_companies": len(company_ids),
        "companies_with_pro": len(companies_with_pro),
        "companies_with_zero_pros": len(zero_pro_companies),
        "zero_pro_companies": sorted(zero_pro_companies),
        "total_pro_triggers": len(triggered_rows),
        "per_rule_counts": dict(sorted(per_rule.items())),
        "confidence_count": len(confidences),
        "confidence_min": round(min(confidences), 2) if confidences else None,
        "confidence_max": round(max(confidences), 2) if confidences else None,
        "confidence_mean": round(sum(confidences) / len(confidences), 2)
        if confidences else None,
        "output_path": str(OUTPUT_CSV),
        "output_rows": int(len(df)),
        "output_schema_valid": valid,
        "output_schema_issues": issues,
    }
    return stats


def print_report(stats: Dict[str, object]) -> None:
    print("\n================ MODULE 2B REAL-DATA VALIDATION ================")
    print(f"Total companies processed        : {stats['total_companies']}")
    print(f"Companies with at least one Pro  : {stats['companies_with_pro']}")
    print(f"Companies with zero Pros         : {stats['companies_with_zero_pros']}")
    print(f"Total Pro rule triggers          : {stats['total_pro_triggers']}")
    print("--- Trigger count per rule ---")
    for rule_id, count in stats["per_rule_counts"].items():
        print(f"  {rule_id}: {count}")
    print("--- Confidence statistics (triggered only) ---")
    print(f"  count = {stats['confidence_count']}")
    print(f"  min   = {stats['confidence_min']}")
    print(f"  max   = {stats['confidence_max']}")
    print(f"  mean  = {stats['confidence_mean']}")
    print(f"Output rows                      : {stats['output_rows']}")
    print(f"Output schema valid              : {stats['output_schema_valid']}")
    if not stats["output_schema_valid"]:
        for i in stats["output_schema_issues"]:
            print("   -", i)
    print("--- Companies with zero Pros ---")
    print("  " + (", ".join(stats["zero_pro_companies"]) or "(none)"))
    print("================================================================\n")


if __name__ == "__main__":
    stats = run_validation()
    print_report(stats)