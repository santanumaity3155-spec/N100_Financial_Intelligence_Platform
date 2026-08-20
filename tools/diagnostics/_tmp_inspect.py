import sys
sys.path.insert(0, ".")
from src.database.connection import get_connection
import pandas as pd
import numpy as np

conn = get_connection()

# Period format
print("=== PERIOD FORMATS ===")
pl = pd.read_sql("SELECT DISTINCT period FROM profit_loss LIMIT 30", conn)
print(pl['period'].tolist())

# cash_flow free_cash_flow
print("\n=== CASH FLOW: free_cash_flow ===")
cf = pd.read_sql("SELECT company_id, period, free_cash_flow FROM cash_flow WHERE company_id='AXISBANK' ORDER BY period", conn)
print(cf.to_string()[:500])
cf_all = pd.read_sql("SELECT free_cash_flow FROM cash_flow", conn)
print("Non-null free_cash_flow:", cf_all['free_cash_flow'].notna().sum(), "/", len(cf_all))

# balance_sheet: borrowings, investments (for net_debt derivation)
print("\n=== BALANCE SHEET: borrowings, investments, net_debt for TCS ===")
bs = pd.read_sql("SELECT company_id, period, borrowings, investments, total_assets, reserves FROM balance_sheet WHERE company_id='TCS' ORDER BY period", conn)
print(bs.to_string()[:800])

# financial_kpis: roce, interest_coverage, debt_to_equity for TCS and a financial co
print("\n=== financial_kpis: roce, icr, d/e for TCS ===")
kpi = pd.read_sql("SELECT period, roce, interest_coverage, debt_to_equity, roe FROM financial_kpis WHERE company_id='TCS' ORDER BY period", conn)
print(kpi.to_string()[:800])

print("\n=== financial_kpis: roce, icr, d/e for AXISBANK (financial) ===")
kpi2 = pd.read_sql("SELECT period, roce, interest_coverage, debt_to_equity, roe FROM financial_kpis WHERE company_id='AXISBANK' ORDER BY period", conn)
print(kpi2.to_string()[:800])

# profit_loss: opm, net_profit, sales, dividend_payout for TCS
print("\n=== profit_loss: sales, opm, net_profit, dividend_payout for TCS ===")
pl2 = pd.read_sql("SELECT period, sales, opm_percentage, net_profit, dividend_payout, eps, depreciation, operating_profit FROM profit_loss WHERE company_id='TCS' ORDER BY period", conn)
print(pl2.to_string()[:1200])

# financial_kpis roce scale - check ranges
print("\n=== ROCE scale (all non-null) ===")
roce_vals = pd.read_sql("SELECT roce FROM financial_kpis WHERE roce IS NOT NULL", conn)
print("min:", roce_vals['roce'].min(), "max:", roce_vals['roce'].max(), "mean:", roce_vals['roce'].mean())

# revenue_cagr scale
print("\n=== revenue_cagr scale ===")
rc = pd.read_sql("SELECT revenue_cagr FROM financial_kpis WHERE revenue_cagr IS NOT NULL", conn)
print("min:", rc['revenue_cagr'].min(), "max:", rc['revenue_cagr'].max(), "count:", len(rc))

# dividend_payout in profit_loss
print("\n=== dividend_payout in profit_loss ===")
dp = pd.read_sql("SELECT dividend_payout FROM profit_loss WHERE dividend_payout IS NOT NULL LIMIT 20", conn)
print(dp.to_string()[:500])
dp_all = pd.read_sql("SELECT COUNT(*) as total, SUM(CASE WHEN dividend_payout IS NOT NULL THEN 1 ELSE 0 END) as nonnull FROM profit_loss", conn)
print("Total PL rows:", dp_all['total'][0], "Non-null dividend_payout:", dp_all['nonnull'][0])

conn.close()





import sqlite3
import pandas as pd
import json

conn = sqlite3.connect('NIFTY_SMALL_100.db')

# List all tables
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
print("=== TABLES ===")
for t in tables:
    name = t[0]
    cols = conn.execute(f"PRAGMA table_info('{name}')").fetchall()
    col_names = [c[1] for c in cols]
    print(f"\n--- TABLE: {name} ---")
    print(f"Columns: {col_names}")
    # Show row count
    count = conn.execute(f"SELECT COUNT(*) FROM '{name}'").fetchone()[0]
    print(f"Row count: {count}")

conn.close()
