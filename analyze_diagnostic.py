import pandas as pd
import sys
from pathlib import Path

# Paths
OUTPUT_DIR = Path(__file__).parent / "output"
DIAGNOSTIC_CSV = OUTPUT_DIR / "module_2d_coverage_diagnostic.csv"
EXISTING_CSV = OUTPUT_DIR / "pros_cons_generated.csv"
COMPANIES_CSV = Path(__file__).parent / "data" / "companies.csv"  # Adjust if needed

def main():
    # Load diagnostic data
    df_diag = pd.read_csv(DIAGNOSTIC_CSV)

    # Load existing generated CSV to see what signals exist
    try:
        df_existing = pd.read_csv(EXISTING_CSV)
        existing_pro = set(df_existing[df_existing["type"] == "pro"]["company_id"])
        existing_con = set(df_existing[df_existing["type"] == "con"]["company_id"])
    except Exception as e:
        print(f"Could not read existing CSV: {e}")
        existing_pro = set()
        existing_con = set()

    # Load all companies from the companies table (if available) or from diagnostic
    try:
        companies_df = pd.read_csv(COMPANIES_CSV)
        all_company_ids = set(companies_df["company_id"].astype(str).str.strip().str.upper())
    except Exception:
        # Fallback to unique company_ids in diagnostic
        all_company_ids = set(df_diag["company_id"].unique())

    missing_pro = all_company_ids - existing_pro
    missing_con = all_company_ids - existing_con

    print(f"Total companies: {len(all_company_ids)}")
    print(f"Missing Pro companies ({len(missing_pro)}): {sorted(missing_pro)}")
    print(f"Missing Con companies ({len(missing_con)}): {sorted(missing_con)}")

    # Focus on companies missing either Pro or Con
    target_companies = missing_pro | missing_con

    print("\n" + "="*80)
    print("ANALYSIS PER MISSING COMPANY")
    print("="*80)

    for cid in sorted(target_companies):
        print(f"\nCompany: {cid}")
        sub = df_diag[df_diag["company_id"] == cid]

        # Pro analysis
        pro_sub = sub[sub["type"] == "pro"]
        pro_eligible = pro_sub[pro_sub["eligible_after_threshold"] == True]
        pro_triggered_not_eligible = pro_sub[(pro_sub["triggered"] == True) & (pro_sub["eligible_after_threshold"] == False)]
        pro_not_triggered = pro_sub[pro_sub["triggered"] == False]

        print(f"  PRO: Eligible triggers: {len(pro_eligible)}")
        if len(pro_eligible) > 0:
            print(f"    Rule IDs: {list(pro_eligible['rule_id'].unique())}")
        print(f"  PRO: Triggered but not eligible (confidence <=60): {len(pro_triggered_not_eligible)}")
        if len(pro_triggered_not_eligible) > 0:
            for _, row in pro_triggered_not_eligible.iterrows():
                print(f"    {row['rule_id']}: confidence={row['confidence_pct']}, reason='{row['reason']}'")
        print(f"  PRO: Not triggered: {len(pro_not_triggered)}")
        if len(pro_not_triggered) > 0 and len(pro_not_triggered) <= 5:  # Show first few reasons
            for _, row in pro_not_triggered.head().iterrows():
                print(f"    {row['rule_id']}: reason='{row['reason']}'")
        elif len(pro_not_triggered) > 5:
            print(f"    (showing first 5)")
            for _, row in pro_not_triggered.head().iterrows():
                print(f"    {row['rule_id']}: reason='{row['reason']}'")

        # Con analysis
        con_sub = sub[sub["type"] == "con"]
        con_eligible = con_sub[con_sub["eligible_after_threshold"] == True]
        con_triggered_not_eligible = con_sub[(con_sub["triggered"] == True) & (con_sub["eligible_after_threshold"] == False)]
        con_not_triggered = con_sub[con_sub["triggered"] == False]

        print(f"  CON: Eligible triggers: {len(con_eligible)}")
        if len(con_eligible) > 0:
            print(f"    Rule IDs: {list(con_eligible['rule_id'].unique())}")
        print(f"  CON: Triggered but not eligible (confidence <=60): {len(con_triggered_not_eligible)}")
        if len(con_triggered_not_eligible) > 0:
            for _, row in con_triggered_not_eligible.iterrows():
                print(f"    {row['rule_id']}: confidence={row['confidence_pct']}, reason='{row['reason']}'")
        print(f"  CON: Not triggered: {len(con_not_triggered)}")
        if len(con_not_triggered) > 0 and len(con_not_triggered) <= 5:
            for _, row in con_not_triggered.head().iterrows():
                print(f"    {row['rule_id']}: reason='{row['reason']}'")
        elif len(con_not_triggered) > 5:
            print(f"    (showing first 5)")
            for _, row in con_not_triggered.head().iterrows():
                print(f"    {row['rule_id']}: reason='{row['reason']}'")

        # Summary for this company
        print(f"  >>> SUMMARY: Pro eligible: {len(pro_eligible)}, Con eligible: {len(con_eligible)}")
        if len(pro_eligible) == 0 and len(con_eligible) == 0:
            print(f"      >>> NO ELIGIBLE SIGNALS FOR EITHER TYPE <<<")
        elif len(pro_eligible) == 0:
            print(f"      >>> MISSING PRO SIGNAL ONLY <<<")
        elif len(con_eligible) == 0:
            print(f"      >>> MISSING CON SIGNAL ONLY <<<")

    print("\n" + "="*80)
    print("OVERALL SUMMARY")
    print("="*80)
    print(f"Companies missing Pro but have Con: {len(missing_pro - missing_con)}")
    print(f"Companies missing Con but have Pro: {len(missing_con - missing_pro)}")
    print(f"Companies missing both Pro and Con: {len(missing_pro & missing_con)}")

    # List companies missing both
    both_missing = missing_pro & missing_con
    if both_missing:
        print(f"\nCompanies missing both Pro and Con ({len(both_missing)}): {sorted(both_missing)}")

    # List companies missing only Pro
    only_pro_missing = missing_pro - missing_con
    if only_pro_missing:
        print(f"\nCompanies missing only Pro ({len(only_pro_missing)}): {sorted(only_pro_missing)}")

    # List companies missing only Con
    only_con_missing = missing_con - missing_pro
    if only_con_missing:
        print(f"\nCompanies missing only Con ({len(only_con_missing)}): {sorted(only_con_missing)}")

if __name__ == "__main__":
    main()