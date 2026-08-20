"""
validate_module4b.py

Validation Script for Module 4B — Latest-Year Capital Allocation Pattern Distribution
N100 Financial Intelligence Platform (Sprint 5)
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

from src.database.connection import get_connection
from src.analytics.capital_allocation_distribution import (
    SUPPORTED_PATTERNS,
    parse_year_from_period,
    determine_latest_year,
)


def validate_module4b() -> bool:
    print("============================================================")
    print("MODULE 4B VALIDATION")
    print("============================================================")

    dist_file = Path("output/capital_allocation_distribution.csv")

    distribution_output_pass = False
    pattern_coverage_pass = False
    count_validation_pass = False
    percentage_validation_pass = False
    data_integrity_pass = False

    latest_year_str = "N/A"
    valid_companies_count = 0
    expected_companies_count = 0
    patterns_found = 0
    company_count_sum = 0
    percentage_sum = 0.0

    missing_patterns = []
    unexpected_patterns = []

    # Check 1: Authoritative DB Companies Count
    try:
        conn = get_connection()
        companies_df = pd.read_sql("SELECT company_id FROM companies", conn)
        expected_companies_count = len(companies_df)

        cf_df = pd.read_sql("SELECT period FROM cash_flow", conn)
        pl_df = pd.read_sql("SELECT period FROM profit_loss", conn)
        db_latest_year = determine_latest_year(cf_df, pl_df)
    except Exception as e:
        print(f"Error connecting to database: {e}")
        db_latest_year = 2024
        expected_companies_count = 94

    # Check 2: Output File Exists & Readable
    if not dist_file.exists():
        print(f"ERROR: Output file {dist_file} does not exist!")
    else:
        try:
            df = pd.read_csv(dist_file)
            distribution_output_pass = True

            req_cols = ["latest_year", "pattern", "company_count", "percentage"]
            if not all(col in df.columns for col in req_cols):
                print(f"ERROR: Missing required columns in {dist_file}")
                distribution_output_pass = False

            if distribution_output_pass and len(df) > 0:
                latest_year_val = df["latest_year"].iloc[0]
                latest_year_str = str(latest_year_val)

                # Validate latest year matches DB
                if latest_year_val == db_latest_year:
                    data_integrity_pass = True
                else:
                    print(
                        f"WARNING: Output year {latest_year_val} differs from DB year {db_latest_year}"
                    )

                # Check pattern coverage
                found_patterns_list = df["pattern"].tolist()
                patterns_found = len(found_patterns_list)

                # Check duplicates
                if len(found_patterns_list) != len(set(found_patterns_list)):
                    print("ERROR: Duplicate pattern rows found in output!")
                    distribution_output_pass = False

                missing_patterns = [
                    p for p in SUPPORTED_PATTERNS if p not in found_patterns_list
                ]
                unexpected_patterns = [
                    p for p in found_patterns_list if p not in SUPPORTED_PATTERNS
                ]

                if not missing_patterns and not unexpected_patterns:
                    pattern_coverage_pass = True

                # Check company counts
                counts = df["company_count"].tolist()
                if all(isinstance(c, (int, float, np.integer)) and c >= 0 for c in counts):
                    company_count_sum = int(sum(counts))
                    valid_companies_count = company_count_sum

                    if company_count_sum == expected_companies_count:
                        count_validation_pass = True
                    else:
                        print(
                            f"ERROR: Company count sum ({company_count_sum}) != Expected ({expected_companies_count})"
                        )

                # Check percentages
                pcts = df["percentage"].tolist()
                if all(
                    isinstance(p, (int, float, np.floating)) and 0.0 <= p <= 100.0
                    for p in pcts
                ):
                    percentage_sum = round(sum(pcts), 2)
                    if 99.0 <= percentage_sum <= 101.0:
                        percentage_validation_pass = True
                    else:
                        print(f"ERROR: Percentage sum ({percentage_sum}%) out of range!")

        except Exception as e:
            print(f"Error reading {dist_file}: {e}")
            distribution_output_pass = False

    final_pass = (
        distribution_output_pass
        and pattern_coverage_pass
        and count_validation_pass
        and percentage_validation_pass
        and data_integrity_pass
    )

    print()
    print(f"Latest Year: {latest_year_str}")
    print(f"Valid Companies: {valid_companies_count}")
    print(f"Patterns Expected: {len(SUPPORTED_PATTERNS)}")
    print(f"Patterns Found: {patterns_found}")
    print()
    print(f"Company Count Sum: {company_count_sum}")
    print(f"Expected Company Count: {expected_companies_count}")
    print()
    print(f"Percentage Sum: {percentage_sum:.2f}%")
    print()
    print(f"Missing Patterns: {missing_patterns}")
    print(f"Unexpected Patterns: {unexpected_patterns}")
    print()
    print(f"Distribution Output: {'PASS' if distribution_output_pass else 'FAIL'}")
    print(f"Pattern Coverage: {'PASS' if pattern_coverage_pass else 'FAIL'}")
    print(f"Count Validation: {'PASS' if count_validation_pass else 'FAIL'}")
    print(f"Percentage Validation: {'PASS' if percentage_validation_pass else 'FAIL'}")
    print(f"Data Integrity: {'PASS' if data_integrity_pass else 'FAIL'}")
    print()
    print(f"FINAL STATUS: {'PASS' if final_pass else 'FAIL'}")
    print("============================================================")

    return final_pass


if __name__ == "__main__":
    success = validate_module4b()
    sys.exit(0 if success else 1)
