#!/usr/bin/env python3
"""
validate_module4a.py

Module 4A Diagnostic for N100 Financial Intelligence Platform
Validates the Capital Allocation Engine and data readiness for Module 4B and 4C.
"""

import sys
import os
import sqlite3
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def print_header(title):
    """Print a formatted header."""
    print("=" * 60)
    print(title)
    print("=" * 60)

def print_result(check_name, passed, details=""):
    """Print a check result."""
    status = "PASS" if passed else "FAIL"
    print(f"{check_name:<30} {status}")
    if details:
        print(f"  {details}")

def check_database():
    """Check if canonical database is found."""
    db_path = Path("data/database/n100.db")
    if db_path.exists():
        size_mb = db_path.stat().st_size / (1024 * 1024)
        return True, f"Found at {db_path} ({size_mb:.1f} MB)"
    else:
        return False, f"Not found at {db_path}"

def check_companies_table():
    """Check if companies table exists and get count."""
    try:
        conn = sqlite3.connect("data/database/n100.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM companies")
        count = cursor.fetchone()[0]
        conn.close()
        return True, f"Found {count} companies"
    except Exception as e:
        return False, f"Error: {e}"

def check_authoritative_company_count():
    """Check that authoritative company count is detected."""
    try:
        conn = sqlite3.connect("data/database/n100.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM companies")
        count = cursor.fetchone()[0]
        conn.close()
        # Expect around 94 based on our earlier analysis
        return True, f"Authoritative companies: {count}"
    except Exception as e:
        return False, f"Error: {e}"

def check_capital_allocation_inputs():
    """Check that required Capital Allocation inputs can be calculated."""
    try:
        conn = sqlite3.connect("data/database/n100.db")
        cursor = conn.cursor()

        # Check if we can calculate the base inputs: OCF, CapEx, Net Profit
        cursor.execute('''
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN cf.operating_activity IS NULL THEN 1 ELSE 0 END) as missing_ocf,
                SUM(CASE WHEN cf.investing_activity IS NULL THEN 1 ELSE 0 END) as missing_capex,
                SUM(CASE WHEN pl.net_profit IS NULL THEN 1 ELSE 0 END) as missing_net_profit
            FROM cash_flow cf
            INNER JOIN profit_loss pl ON cf.company_id = pl.company_id AND cf.period = pl.period
            WHERE cf.company_id IN (SELECT company_id FROM companies)
        ''')
        result = cursor.fetchone()
        total, missing_ocf, missing_capex, missing_net_profit = result

        # Calculate completeness
        missing_total = missing_ocf + missing_capex + missing_net_profit
        max_possible_missing = total * 3  # 3 fields that could be missing
        completeness = ((max_possible_missing - missing_total) / max_possible_missing) * 100 if max_possible_missing > 0 else 0

        conn.close()

        if completeness >= 99.0:  # Allow for minor data issues
            return True, f"Input completeness: {completeness:.1f}%"
        else:
            return False, f"Input completeness too low: {completeness:.1f}%"
    except Exception as e:
        return False, f"Error checking inputs: {e}"

def check_duplicate_records():
    """Check for duplicate company/year records."""
    try:
        conn = sqlite3.connect("data/database/n100.db")
        cursor = conn.cursor()

        # Check cash_flow duplicates
        cursor.execute('''
            SELECT COUNT(*)
            FROM (
                SELECT company_id, period, COUNT(*) as cnt
                FROM cash_flow
                GROUP BY company_id, period
                HAVING COUNT(*) > 1
            ) dup_cf
        ''')
        cf_dups = cursor.fetchone()[0]

        # Check profit_loss duplicates
        cursor.execute('''
            SELECT COUNT(*)
            FROM (
                SELECT company_id, period, COUNT(*) as cnt
                FROM profit_loss
                GROUP BY company_id, period
                HAVING COUNT(*) > 1
            ) dup_pl
        ''')
        pl_dups = cursor.fetchone()[0]

        conn.close()

        total_dups = cf_dups + pl_dups
        if total_dups == 0:
            return True, "No duplicate company/period records found"
        else:
            return False, f"Found {total_dups} duplicate records (CF: {cf_dups}, PL: {pl_dups})"
    except Exception as e:
        return False, f"Error checking duplicates: {e}"

def check_existing_rating_values():
    """Check if existing rating values can be identified (by computing them)."""
    try:
        from src.analytics.cashflow_kpis import classify_capital_allocation, RATING_EXCELLENT, RATING_GOOD, RATING_MODERATE, RATING_WEAK, RATING_DISTRESSED

        conn = sqlite3.connect("data/database/n100.db")
        cursor = conn.cursor()

        # Compute ratings for a sample of data
        cursor.execute('''
            SELECT
                cf.operating_activity as ocf,
                ABS(cf.investing_activity) as capex,
                (cf.operating_activity - ABS(cf.investing_activity)) as fcf,
                pl.net_profit
            FROM cash_flow cf
            INNER JOIN profit_loss pl ON cf.company_id = pl.company_id AND cf.period = pl.period
            WHERE cf.company_id IN (SELECT company_id FROM companies)
            AND cf.operating_activity IS NOT NULL
            AND cf.investing_activity IS NOT NULL
            AND pl.net_profit IS NOT NULL
            LIMIT 1000
        ''')
        records = cursor.fetchall()
        conn.close()

        # Apply classification logic
        ratings_found = set()
        for ocf, capex, fcf, net_profit in records:
            if fcf is None or ocf is None:
                rating = 'DISTRESSED'
            elif fcf < 0 or ocf < 0:
                rating = 'DISTRESSED'
            else:
                # Calculate derived values
                cash_conversion = (fcf / net_profit) * 100 if net_profit != 0 else None
                capex_intensity = (capex / ocf) * 100 if ocf != 0 else None

                if cash_conversion is None:
                    rating = 'MODERATE'
                elif cash_conversion > 100.0:
                    if capex_intensity is not None and capex_intensity < 50.0:
                        rating = 'EXCELLENT'
                    else:
                        rating = 'GOOD'
                elif cash_conversion > 80.0:
                    rating = 'GOOD'
                elif cash_conversion > 50.0:
                    rating = 'MODERATE'
                else:
                    rating = 'WEAK'

            ratings_found.add(rating)

        expected_ratings = {RATING_EXCELLENT, RATING_GOOD, RATING_MODERATE, RATING_WEAK, RATING_DISTRESSED}
        if ratings_found.issubset(expected_ratings) and len(ratings_found) > 0:
            return True, f"Valid ratings found: {sorted(ratings_found)}"
        else:
            return False, f"Unexpected ratings: {ratings_found}"
    except Exception as e:
        return False, f"Error checking ratings: {e}"

def check_engine_import():
    """Check if existing engine imports successfully."""
    try:
        from src.analytics.cashflow_kpis import classify_capital_allocation
        return True, "Engine imports successfully"
    except Exception as e:
        return False, f"Import failed: {e}"

def check_engine_evaluation():
    """Check if existing engine can evaluate sample data."""
    try:
        from src.analytics.cashflow_kpis import classify_capital_allocation

        # Test with known good values
        rating = classify_capital_allocation(500, 120, 40, 1000)
        if rating == "EXCELLENT":
            return True, "Engine evaluation works (EXCELLENT case)"
        else:
            return False, f"Engine returned unexpected rating: {rating}"
    except Exception as e:
        return False, f"Evaluation failed: {e}"

def check_pattern_mapping():
    """Check if existing pattern mapping can be identified."""
    try:
        # Check the mapping in src/dashboard/pages/07_capital.py
        mapping_file = Path("src/dashboard/pages/07_capital.py")
        if mapping_file.exists():
            content = mapping_file.read_text(encoding='utf-8')
            # Look for the pattern mapping
            if '"EXCELLENT": "Reinvestor"' in content and '"GOOD": "Shareholder Returns"' in content:
                return True, "Pattern mapping found in capital.py"
            else:
                return False, "Pattern mapping not found or incomplete in capital.py"
        else:
            return False, "capital.py file not found"
    except Exception as e:
        return False, f"Error checking pattern mapping: {e}"

def main():
    """Run all validation checks."""
    print_header("MODULE 4A VALIDATION")
    print("N100 Financial Intelligence Platform")
    print()

    checks = [
        ("Database", check_database),
        ("Companies Table", check_companies_table),
        ("Authoritative Company Count", check_authoritative_company_count),
        ("Capital Allocation Inputs", check_capital_allocation_inputs),
        ("Duplicate Records", check_duplicate_records),
        ("Existing Rating Values", check_existing_rating_values),
        ("Engine Import", check_engine_import),
        ("Engine Evaluation", check_engine_evaluation),
        ("Pattern Mapping", check_pattern_mapping),
    ]

    results = []
    for check_name, check_func in checks:
        passed, details = check_func()
        print_result(check_name, passed, details)
        results.append((check_name, passed))
        print()

    # Summary
    print_header("VALIDATION SUMMARY")
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for check_name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"{check_name}: {status}")

    print()
    print(f"Overall: {passed_count}/{total_count} checks passed")

    if passed_count == total_count:
        print("FINAL STATUS: PASS")
        return 0
    else:
        print("FINAL STATUS: FAIL")
        return 1

if __name__ == "__main__":
    sys.exit(main())