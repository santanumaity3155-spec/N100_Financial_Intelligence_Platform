import sqlite3
conn = sqlite3.connect(r"d:\New Project\Bluestock_Projects\Nifty 100\N100 Financial Intelligence Platform\N100_Financial_Intelligence_Platform\data\database\n100.db")
cur = conn.cursor()
print("---financial_kpis rows with non-null revenue_cagr---")
cur.execute("SELECT company_id, period, revenue_cagr, profit_cagr, eps_cagr, roe FROM financial_kpis WHERE revenue_cagr IS NOT NULL LIMIT 20")
for r in cur.fetchall():
    print(r)
print("---count non null---")
cur.execute("SELECT COUNT(*) FROM financial_kpis WHERE revenue_cagr IS NOT NULL")
print(cur.fetchone())
print("---HDFCBANK all periods roe/revenue_cagr---")
cur.execute("SELECT company_id, period, roe, revenue_cagr, profit_cagr FROM financial_kpis WHERE company_id='HDFCBANK' ORDER BY period")
for r in cur.fetchall():
    print(r)
