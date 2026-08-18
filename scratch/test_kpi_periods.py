import sqlite3
from pathlib import Path

db_path = Path("data/database/n100.db")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("""
    SELECT id, period, roe, roce, net_profit_margin, operating_margin, pe_ratio, pb_ratio
    FROM financial_kpis
    WHERE company_id = 'TCS'
    ORDER BY id DESC
""")
print("TCS financial_kpis (descending by id):")
for r in cursor.fetchall():
    print(dict(r))

print("\nTCS financial_ratios (descending by id):")
cursor.execute("""
    SELECT id, period, roe, debt_to_equity, current_ratio, pe_ratio, pb_ratio
    FROM financial_ratios
    WHERE company_id = 'TCS'
    ORDER BY id DESC
""")
for r in cursor.fetchall():
    print(dict(r))

conn.close()
