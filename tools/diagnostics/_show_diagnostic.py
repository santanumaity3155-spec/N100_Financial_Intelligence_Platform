import pandas as pd

df = pd.read_csv('output/module_2d_coverage_diagnostic.csv')

print('=' * 100)
print('MODULE 2D COVERAGE DIAGNOSTIC - CSV SAMPLE')
print('=' * 100)
print(f'\nTotal rows: {len(df)} (14 companies x 24 rules)')

print('\n' + '=' * 100)
print('SAMPLE: UNIONBANK (Missing Pro) - All Pro Rules')
print('=' * 100)
unionbank_pro = df[(df['company_id'] == 'UNIONBANK') & (df['type'] == 'pro')]
for idx, row in unionbank_pro.iterrows():
    print(f"\n{row['rule_id']} (PRO):")
    print(f"  Triggered: {row['triggered']}")
    print(f"  Confidence: {row['confidence_pct']:.1f}% | Passes (>60%): {row['eligible_after_threshold']}")
    print(f"  Reason: {row['reason'][:90]}")

print('\n' + '=' * 100)
print('SAMPLE: DMART (Missing Con) - All Con Rules')
print('=' * 100)
dmart_con = df[(df['company_id'] == 'DMART') & (df['type'] == 'con')]
for idx, row in dmart_con.iterrows():
    print(f"\n{row['rule_id']} (CON):")
    print(f"  Triggered: {row['triggered']}")
    print(f"  Confidence: {row['confidence_pct']:.1f}% | Passes (>60%): {row['eligible_after_threshold']}")
    print(f"  Reason: {row['reason'][:90]}")

print('\n' + '=' * 100)
print('COVERAGE SUMMARY')
print('=' * 100)
by_company = df.groupby('company_id').apply(
    lambda x: {
        'pro_pass': len(x[(x['type'] == 'pro') & x['eligible_after_threshold']]),
        'con_pass': len(x[(x['type'] == 'con') & x['eligible_after_threshold']]),
    }
)

for cid, stats in sorted(by_company.items()):
    status = ""
    if stats['pro_pass'] == 0:
        status += "NO PRO"
    if stats['con_pass'] == 0:
        if status:
            status += " | "
        status += "NO CON"
    
    print(f"{cid}: Pro={stats['pro_pass']}, Con={stats['con_pass']}  [{status}]")
