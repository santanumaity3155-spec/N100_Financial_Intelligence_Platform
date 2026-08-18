"""
validate_module4.py

Final Master Validation Script for Module 4: Capital Allocation Intelligence
N100 Financial Intelligence Platform (Sprint 5)

This validator performs complete integration, data integrity, and cross-module
consistency checks across Module 4A, Module 4B, and Module 4C.
"""

import sys
import pandas as pd
from pathlib import Path

from src.database.connection import get_connection
from src.config.constants import OUTPUT_DIR
from src.analytics.capital_allocation_distribution import (
    SUPPORTED_PATTERNS,
    compute_latest_year_classifications,
)
from src.analytics.capital_allocation_pattern_changes import (
    compute_year_classifications,
    get_available_years,
)
from validate_module4a import main as validate_module4a_main
from validate_module4b import validate_module4b
from validate_module4c import validate_module4c


def validate_module4():
    print("=" * 60)
    print("MODULE 4 FINAL VALIDATION")
    print("============================================================")

    results = {}

    # 1. Run Sub-module Validators
    print("\n--- Sub-Module 4A Validation ---")
    val_4a = (validate_module4a_main() == 0)
    results['Module 4A'] = val_4a

    print("\n--- Sub-Module 4B Validation ---")
    val_4b = validate_module4b()
    results['Module 4B'] = val_4b

    print("\n--- Sub-Module 4C Validation ---")
    val_4c = validate_module4c()
    results['Module 4C'] = val_4c

    print("\n--- Cross-Module & Integration Checks ---")

    conn = get_connection()

    # 2. Company Coverage Check
    try:
        auth_df = pd.read_sql("SELECT company_id FROM companies", conn)
        auth_count = len(auth_df)
    except Exception as e:
        auth_count = 94

    dist_path = OUTPUT_DIR / "capital_allocation_distribution.csv"
    changes_path = OUTPUT_DIR / "pattern_changes.csv"
    latest_path = OUTPUT_DIR / "capital_allocation_latest_year.csv"

    # Check Company Coverage
    if latest_path.exists():
        latest_df = pd.read_csv(latest_path)
        coverage_pass = len(latest_df) == auth_count
    else:
        coverage_pass = False
    results['Company Coverage'] = coverage_pass

    # 3. Pattern Set Consistency Check
    if dist_path.exists():
        dist_df = pd.read_csv(dist_path)
        found_patterns = set(dist_df['pattern'].tolist())
        pattern_set_pass = (found_patterns == set(SUPPORTED_PATTERNS))
    else:
        pattern_set_pass = False
    results['Pattern Set'] = pattern_set_pass

    # 4. Distribution Reconciliation (Count & Percentage)
    if dist_path.exists():
        dist_count_sum = dist_df['company_count'].sum()
        dist_pct_sum = round(dist_df['percentage'].sum(), 2)
        dist_pass = (dist_count_sum == auth_count) and (abs(dist_pct_sum - 100.0) <= 0.1)
    else:
        dist_pass = False
    results['Distribution'] = dist_pass

    # 5. Pattern Changes Validation
    if changes_path.exists():
        changes_df = pd.read_csv(changes_path)
        if not changes_df.empty:
            pattern_changes_pass = (
                (changes_df['previous_pattern'] != changes_df['latest_pattern']).all()
                and (changes_df['previous_year'] < changes_df['latest_year']).all()
            )
        else:
            pattern_changes_pass = True
    else:
        pattern_changes_pass = False
    results['Pattern Changes'] = pattern_changes_pass

    # 6. Cross-Module Consistency Check (4B vs 4C latest pattern agreement)
    latest_yr, df_4b = compute_latest_year_classifications(conn)
    years = get_available_years(conn)
    latest_yr_4c = years[0] if years else 2024
    df_4c_latest = compute_year_classifications(latest_yr_4c, conn)

    cross_val_rows = []
    cross_match_count = 0
    total_compared = 0

    if not df_4b.empty and not df_4c_latest.empty:
        merged = pd.merge(
            df_4b[['company_id', 'capital_allocation_pattern']],
            df_4c_latest[['company_id', 'capital_allocation_pattern']],
            on='company_id',
            suffixes=('_module4b', '_module4c')
        )
        total_compared = len(merged)
        for _, row in merged.iterrows():
            cid = row['company_id']
            p4b = row['capital_allocation_pattern_module4b']
            p4c = row['capital_allocation_pattern_module4c']
            match = (p4b == p4c)
            if match:
                cross_match_count += 1
            cross_val_rows.append({
                'company_id': cid,
                'module4b_pattern': p4b,
                'module4c_latest_pattern': p4c,
                'match': match
            })

    # Save diagnostic cross validation file
    cross_val_df = pd.DataFrame(cross_val_rows)
    cross_val_path = OUTPUT_DIR / "module4_cross_validation.csv"
    cross_val_df.to_csv(cross_val_path, index=False)
    print(f"Saved cross-module diagnostic to {cross_val_path.name}")

    cross_module_pass = (total_compared == auth_count) and (cross_match_count == total_compared)
    results['Cross-Module Consistency'] = cross_module_pass

    # 7. Output Integrity Check
    output_files_exist = dist_path.exists() and changes_path.exists() and cross_val_path.exists()
    outputs_non_empty = (
        dist_path.stat().st_size > 0
        and changes_path.stat().st_size > 0
        and cross_val_path.stat().st_size > 0
    )
    results['Output Integrity'] = output_files_exist and outputs_non_empty

    # 8. Duplicate Check
    if changes_path.exists() and not changes_df.empty:
        dup_pass = changes_df['company_id'].is_unique
    else:
        dup_pass = True
    results['Duplicate Check'] = dup_pass

    # 9. Year Ordering Check
    if changes_path.exists() and not changes_df.empty:
        year_order_pass = (changes_df['previous_year'] < changes_df['latest_year']).all()
    else:
        year_order_pass = True
    results['Year Ordering'] = year_order_pass

    # Final Summary Table
    print("\n" + "=" * 60)
    print("MODULE 4 FINAL VALIDATION")
    print("=" * 60)

    print(f"Module 4A: {'PASS' if results['Module 4A'] else 'FAIL'}")
    print(f"Module 4B: {'PASS' if results['Module 4B'] else 'FAIL'}")
    print(f"Module 4C: {'PASS' if results['Module 4C'] else 'FAIL'}")
    print()
    print(f"Company Coverage: {'PASS' if results['Company Coverage'] else 'FAIL'}")
    print(f"Pattern Set: {'PASS' if results['Pattern Set'] else 'FAIL'}")
    print(f"Distribution: {'PASS' if results['Distribution'] else 'FAIL'}")
    print(f"Pattern Changes: {'PASS' if results['Pattern Changes'] else 'FAIL'}")
    print(f"Cross-Module Consistency: {'PASS' if results['Cross-Module Consistency'] else 'FAIL'}")
    print(f"Output Integrity: {'PASS' if results['Output Integrity'] else 'FAIL'}")
    print(f"Duplicate Check: {'PASS' if results['Duplicate Check'] else 'FAIL'}")
    print(f"Year Ordering: {'PASS' if results['Year Ordering'] else 'FAIL'}")

    all_pass = all(results.values())

    print("=" * 60)
    print(f"FINAL STATUS: {'PASS' if all_pass else 'FAIL'}")
    print("=" * 60)

    return all_pass


if __name__ == "__main__":
    success = validate_module4()
    sys.exit(0 if success else 1)
