"""
validate_module4c.py

Module 4C Validation Script: Year-over-Year Capital Allocation Pattern Changes
N100 Financial Intelligence Platform (Sprint 5)

This script validates the output and integrity of Module 4C.
"""

import sys
import pandas as pd
from pathlib import Path

from src.database.connection import get_connection
from src.config.constants import OUTPUT_DIR
from src.analytics.capital_allocation_distribution import SUPPORTED_PATTERNS
from src.analytics.capital_allocation_pattern_changes import run_module4c_pipeline


def validate_module4c():
    print("=" * 60)
    print("MODULE 4C VALIDATION")
    print("=" * 60)

    # Ensure output exists
    pattern_changes_path = OUTPUT_DIR / "pattern_changes.csv"
    if not pattern_changes_path.exists():
        print("Running Module 4C pipeline to generate output...")
        run_module4c_pipeline()

    if not pattern_changes_path.exists():
        print("FAIL: pattern_changes.csv does not exist")
        return False

    df = pd.read_csv(pattern_changes_path)
    print(f"Loaded {len(df)} rows from {pattern_changes_path.name}")

    checks = {}

    # Check 1: Required Columns
    required_cols = [
        'company_id', 'company_name', 'sector',
        'previous_year', 'previous_pattern',
        'latest_year', 'latest_pattern', 'changed'
    ]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"Missing columns: {missing_cols}")
        checks['Required Columns'] = False
    else:
        checks['Required Columns'] = True
        print("Required Columns              PASS")

    # Connect to DB for authoritative company validation
    conn = get_connection()
    try:
        auth_companies = set(pd.read_sql("SELECT company_id FROM companies", conn)['company_id'])
    finally:
        conn.close()

    # Check 2: Valid Company IDs
    if not df.empty:
        invalid_companies = set(df['company_id']) - auth_companies
        if invalid_companies:
            print(f"Invalid company IDs: {invalid_companies}")
            checks['Company IDs'] = False
        else:
            checks['Company IDs'] = True
            print(f"Company IDs ({len(df['company_id'].unique())} valid) PASS")
    else:
        checks['Company IDs'] = True
        print("Company IDs                   PASS (empty dataset)")

    # Check 3: Pattern Validity
    if not df.empty:
        invalid_prev = set(df['previous_pattern']) - set(SUPPORTED_PATTERNS)
        invalid_latest = set(df['latest_pattern']) - set(SUPPORTED_PATTERNS)
        if invalid_prev or invalid_latest:
            print(f"Invalid patterns found. Prev: {invalid_prev}, Latest: {invalid_latest}")
            checks['Pattern Validity'] = False
        else:
            checks['Pattern Validity'] = True
            print("Pattern Validity              PASS")
    else:
        checks['Pattern Validity'] = True
        print("Pattern Validity              PASS")

    # Check 4: Year Ordering (previous_year < latest_year)
    if not df.empty:
        invalid_years = df[df['previous_year'] >= df['latest_year']]
        if not invalid_years.empty:
            print(f"Invalid year ordering in {len(invalid_years)} rows")
            checks['Year Ordering'] = False
        else:
            checks['Year Ordering'] = True
            print("Year Ordering (prev < latest) PASS")
    else:
        checks['Year Ordering'] = True
        print("Year Ordering                 PASS")

    # Check 5: Pattern Change Logic (previous_pattern != latest_pattern)
    if not df.empty:
        false_changes = df[df['previous_pattern'] == df['latest_pattern']]
        invalid_change_records = len(false_changes)
        if invalid_change_records > 0:
            print(f"Invalid change records (previous == latest): {invalid_change_records}")
            checks['Pattern Change Logic'] = False
        else:
            checks['Pattern Change Logic'] = True
            print(f"Pattern Change Logic (0 invalid) PASS")
    else:
        checks['Pattern Change Logic'] = True
        print("Pattern Change Logic          PASS")

    # Check 6: Duplicate Check
    if not df.empty:
        dups = df[df.duplicated(subset=['company_id'], keep=False)]
        if not dups.empty:
            print(f"Duplicate companies found in change output: {dups['company_id'].tolist()}")
            checks['Duplicate Check'] = False
        else:
            checks['Duplicate Check'] = True
            print("Duplicate Check (0 duplicates) PASS")
    else:
        checks['Duplicate Check'] = True
        print("Duplicate Check               PASS")

    # Check 7: Output Readability & Integrity
    file_size = pattern_changes_path.stat().st_size
    if file_size > 0:
        checks['Output Readability'] = True
        print(f"Output Readability ({file_size} bytes) PASS")
    else:
        checks['Output Readability'] = False
        print("Output Readability            FAIL (0 bytes)")

    print("=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    all_passed = all(checks.values())
    for name, status in checks.items():
        print(f"{name:<30}: {'PASS' if status else 'FAIL'}")

    print("=" * 60)
    print(f"FINAL STATUS: {'PASS' if all_passed else 'FAIL'}")
    print("=" * 60)

    return all_passed


if __name__ == "__main__":
    success = validate_module4c()
    sys.exit(0 if success else 1)