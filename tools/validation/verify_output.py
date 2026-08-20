#!/usr/bin/env python3
"""Quick verification script for Module 1 outputs."""

import pandas as pd
from pathlib import Path

def main():
    print("=" * 80)
    print("MODULE 1 - OUTPUT VERIFICATION")
    print("=" * 80)
    
    # Check files exist
    parsed_path = Path("output/analysis_parsed.csv")
    failures_path = Path("output/parse_failures.csv")
    
    print(f"\n✓ analysis_parsed.csv exists: {parsed_path.exists()}")
    print(f"✓ parse_failures.csv exists: {failures_path.exists()}")
    
    if not parsed_path.exists() or not failures_path.exists():
        print("\n❌ Output files missing!")
        return
    
    # Load data
    parsed_df = pd.read_csv(parsed_path)
    failures_df = pd.read_csv(failures_path)
    
    print(f"\n{'=' * 80}")
    print("ANALYSIS_PARSED.CSV STATISTICS")
    print("=" * 80)
    print(f"Total rows: {len(parsed_df)}")
    print(f"Companies: {parsed_df['company_id'].nunique()}")
    print(f"Metrics: {list(parsed_df['metric_type'].unique())}")
    print(f"Manual review flagged: {parsed_df['manual_review'].sum()}")
    
    print(f"\nPeriod distribution:")
    print(parsed_df['period_years'].value_counts().sort_index())
    
    print(f"\nManual review details (difference > 5%):")
    manual_review = parsed_df[parsed_df['manual_review'] == True]
    if not manual_review.empty:
        print(manual_review[['company_id', 'metric_type', 'value_pct', 'difference_pct']].to_string(index=False))
    else:
        print("  None")
    
    print(f"\n{'=' * 80}")
    print("PARSE_FAILURES.CSV STATISTICS")
    print("=" * 80)
    print(f"Total failures: {len(failures_df)}")
    print(f"\nFailure reasons:")
    print(failures_df['failure_reason'].value_counts())
    
    print(f"\n{'=' * 80}")
    print("SAMPLE DATA (First 5 rows)")
    print("=" * 80)
    print(parsed_df.head().to_string(index=False))
    
    print(f"\n{'=' * 80}")
    print("✅ VERIFICATION COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
