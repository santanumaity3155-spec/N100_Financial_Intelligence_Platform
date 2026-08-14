#!/usr/bin/env python3
"""Analyze diagnostic output to identify why Con signals are failing."""

import pandas as pd

df = pd.read_csv('output/module_2d_coverage_diagnostic.csv')

print('='*80)
print('DIAGNOSTIC INSIGHT: WHY 13 COMPANIES HAVE NO VALID CON SIGNALS')
print('='*80)
print()

# Get only Con rules that triggered
con_triggered = df[(df['rule_type']=='con') & (df['triggered']==True)]
print(f'Total Con rules triggered (any confidence): {len(con_triggered)}')
print(f'Total Con rules eligible (>60 confidence): {len(df[(df["rule_type"]=="con") & (df["final_output_eligible"]==True)])}')
print()

# Show which Con rules triggered but have low confidence
con_triggered_low = con_triggered[con_triggered['confidence_pct'] <= 60.0]
print(f'Con rules that triggered but have confidence <=60: {len(con_triggered_low)}')
if len(con_triggered_low) > 0:
    print()
    print(con_triggered_low[['company_id', 'rule_id', 'confidence_pct', 'reason']].to_string())

print()
print('='*80)
print('PRO RULES: Summary')
print('='*80)
pro_df = df[df['rule_type']=='pro']
pro_summary = pro_df.groupby('company_id').agg({
    'triggered': 'sum', 
    'final_output_eligible': 'sum',
    'confidence_pct': 'max'
}).rename(columns={
    'triggered': 'triggered_count',
    'final_output_eligible': 'eligible_count',
    'confidence_pct': 'max_confidence'
})
print(pro_summary)

print()
print('='*80)
print('KEY FINDINGS: Why coverage fails')
print('='*80)

for company in df['company_id'].unique():
    company_df = df[df['company_id'] == company]
    con_eligible = len(company_df[(company_df['rule_type']=='con') & (company_df['final_output_eligible']==True)])
    pro_eligible = len(company_df[(company_df['rule_type']=='pro') & (company_df['final_output_eligible']==True)])
    
    if con_eligible == 0 or pro_eligible == 0:
        reason = 'No Con >60' if con_eligible == 0 else 'No Pro >60'
        
        # Show which Con rules don't trigger
        if con_eligible == 0:
            con_rules = company_df[company_df['rule_type']=='con'].sort_values('rule_id')
            con_not_triggered = con_rules[~con_rules['triggered']]
            print(f"\n{company}: {reason}")
            print(f"  Pro: {pro_eligible} eligible, Con: {con_eligible} eligible")
            print("  Con rules NOT triggered (top reasons):")
            for _, rule in con_not_triggered.head(3).iterrows():
                print(f"    {rule['rule_id']}: {rule['reason']}")
