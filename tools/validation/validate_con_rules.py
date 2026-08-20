"""
validate_con_rules.py

Sprint 5 - Module 2C: Run the 12 Con rules against the live N100 database and
emit an intermediate Con-only result file (`output/cons_generated.csv`).
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database.connection import get_connection
from src.nlp.pros_cons_generator import (
    OUTPUT_COLUMNS,
    TYPE_CON,
    evaluate_rules_for_company,
    get_company_context,
    validate_output_schema,
)

OUTPUT_CSV = PROJECT_ROOT / "output" / "cons_generated.csv"


def load_company_ids() -> List[str]:
    """Return the canonical company universe from the master table."""
    conn = get_connection()
    rows = conn.execute("SELECT company_id FROM companies",).fetchall()
    return [str(r[0]).strip().upper() for r in rows if r[0]]


def run_validation() -> Dict[str, object]:
    company_ids = load_company_ids()
    triggered_rows: List[Dict[str, object]] = []
    per_rule = Counter()
    companies_with_con: set = set()
    zero_con_companies: List[str] = []
    confidences: List[float] = []

    for cid in company_ids:
        context = get_company_context(cid)
        results = evaluate_rules_for_company(context)
        con_hits = [r for r in results if r.triggered and r.rule_type == TYPE_CON]
        if not con_hits:
            zero_con_companies.append(cid)
            continue
        companies_with_con.add(cid)
        for r in con_hits:
            triggered_rows.append(r.to_dict())
            per_rule[r.rule_id] += 1
            confidences.append(float(r.confidence_pct))

    df = pd.DataFrame(triggered_rows, columns=OUTPUT_COLUMNS)
    if not df.empty:
        df = df.sort_values(["company_id", "rule_id"]).reset_index(drop=True)
    df.to_csv(OUTPUT_CSV, index=False)

    valid, issues = validate_output_schema(df)
    for rule_id in [f"CON_{i:02d}" for i in range(1, 13)]:
        per_rule.setdefault(rule_id, 0)

    stats = {
        "total_companies": len(company_ids),
        "companies_with_con": len(companies_with_con),
        "companies_with_zero_cons": len(zero_con_companies),
        "zero_con_companies": sorted(zero_con_companies),
        "total_con_triggers": len(triggered_rows),
        "per_rule_counts": dict(sorted(per_rule.items())),
        "confidence_count": len(confidences),
        "confidence_min": round(min(confidences), 2) if confidences else None,
        "confidence_max": round(max(confidences), 2) if confidences else None,
        "confidence_mean": round(sum(confidences) / len(confidences), 2) if confidences else None,
        "output_path": str(OUTPUT_CSV),
        "output_rows": int(len(df)),
        "output_schema_valid": valid,
        "output_schema_issues": issues,
    }
    return stats


def print_report(stats: Dict[str, object]) -> None:
    print("\n================ MODULE 2C REAL-DATA VALIDATION ================")
    print(f"Total companies processed        : {stats['total_companies']}")
    print(f"Companies with at least one Con  : {stats['companies_with_con']}")
    print(f"Companies with zero Cons         : {stats['companies_with_zero_cons']}")
    print(f"Total Con rule triggers          : {stats['total_con_triggers']}")
    print("--- Trigger count per rule ---")
    for rule_id, count in stats["per_rule_counts"].items():
        print(f"  {rule_id}: {count}")
    print("--- Confidence statistics (triggered only) ---")
    print(f"  min/mean/max = {stats['confidence_min']} / {stats['confidence_mean']} / {stats['confidence_max']}")
    print(f"Output schema valid              : {stats['output_schema_valid']}")
    print("================================================================\n")


if __name__ == "__main__":
    validation_stats = run_validation()
    print_report(validation_stats)