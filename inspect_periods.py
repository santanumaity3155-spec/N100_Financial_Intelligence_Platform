import sqlite3
import pandas as pd

conn = sqlite3.connect('data/database/n100.db')
conn.row_factory = sqlite3.Row

# Completeness per key annual period in financial_kpis
for p in ['Mar 2024','Sep 2024','Dec 2023','TTM']:
    cnt = conn.execute("SELECT COUNT(*) FROM financial_kpis WHERE period=?", (p,)).fetchone()[0]
    cnt_roe = conn.execute("SELECT COUNT(*) FROM financial_kpis WHERE period=? AND roe IS NOT NULL", (p,)).fetchone()[0]
    cnt_full = conn.execute("SELECT COUNT(*) FROM financial_kpis WHERE period=? AND roe IS NOT NULL AND roce IS NOT NULL AND pe_ratio IS NOT NULL AND free_cash_flow IS NOT NULL AND interest_coverage IS NOT NULL", (p,)).fetchone()[0]
    print(f"{p}: total={cnt}, roe_nn={cnt_roe}, fully_populated={cnt_full}")

# overall_score completeness per period in fhs
for p in ['Mar 2024','Sep 2024','Dec 2023']:
    cnt = conn.execute("SELECT COUNT(*) FROM financial_health_scores WHERE period=?", (p,)).fetchone()[0]
    cnt_nn = conn.execute("SELECT COUNT(*) FROM financial_health_scores WHERE period=? AND overall_score IS NOT NULL", (p,)).fetchone()[0]
    print(f"fhs {p}: total={cnt}, overall_nn={cnt_nn}")

# Per-company latest period with non-null roe
q = """
SELECT company_id, period, roe, roce, net_profit_margin, operating_margin,
       debt_to_equity, interest_coverage, free_cash_flow, pe_ratio, pb_ratio,
       dividend_yield, revenue_cagr, profit_cagr, eps_cagr
FROM financial_kpis
WHERE roe IS NOT NULL
ORDER BY company_id, period DESC
"""
df = pd.read_sql_query(q, conn)
latest = df.drop_duplicates('company_id', keep='first')
print("\ncompanies with non-null roe (latest period):", len(latest))
print("periods distribution for latest:", latest['period'].value_counts().to_dict())

# overall_score per company latest
fhs = pd.read_sql_query("SELECT company_id, overall_score FROM financial_health_scores ORDER BY company_id, period DESC", conn)
fhs_latest = fhs.drop_duplicates('company_id', keep='first')
print("fhs latest per company overall_score non-null:", fhs_latest['overall_score'].notna().sum())

merged = latest.merge(fhs_latest[['company_id','overall_score']], on='company_id', how='left')
print("merged with overall_score non-null:", merged['overall_score'].notna().sum(), "of", len(merged))

# Sample a couple companies full kpi rows
for cid in ['TCS','HDFCBANK','INFY','RELIANCE','HINDUNILVR']:
    r = conn.execute("SELECT period, roe, roce, debt_to_equity, pe_ratio, free_cash_flow, revenue_cagr, profit_cagr, operating_margin, interest_coverage, net_profit_margin, pb_ratio, dividend_yield FROM financial_kpis WHERE company_id=? AND roe IS NOT NULL ORDER BY period DESC LIMIT 3", (cid,)).fetchall()
    print(f"\n{cid}:")
    for row in r: print("  ", dict(row))
conn.close()
