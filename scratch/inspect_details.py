import sqlite3
from pathlib import Path

db_path = Path("data/database/n100.db")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Join companies and sectors
cursor.execute("""
    SELECT c.company_id, c.company_name, s.broad_sector, s.sub_sector, s.market_cap_category, c.roe_percentage, c.roce_percentage
    FROM companies c
    LEFT JOIN sectors s ON c.company_id = s.company_id
    LIMIT 10
""")
for row in cursor.fetchall():
    print(dict(row))

print("\n--- Period formats in P&L ---")
cursor.execute("SELECT DISTINCT period FROM profit_loss LIMIT 15")
print([r[0] for r in cursor.fetchall()])

print("\n--- Period formats in Balance Sheet ---")
cursor.execute("SELECT DISTINCT period FROM balance_sheet LIMIT 15")
print([r[0] for r in cursor.fetchall()])

print("\n--- Period formats in Cash Flow ---")
cursor.execute("SELECT DISTINCT period FROM cash_flow LIMIT 15")
print([r[0] for r in cursor.fetchall()])

print("\n--- Period formats in Financial KPIs ---")
cursor.execute("SELECT DISTINCT period FROM financial_kpis LIMIT 15")
print([r[0] for r in cursor.fetchall()])

print("\n--- Company count check ---")
cursor.execute("SELECT COUNT(*) FROM companies")
print("Companies count in companies table:", cursor.fetchone()[0])
cursor.execute("SELECT COUNT(*) FROM sectors")
print("Companies count in sectors table:", cursor.fetchone()[0])

conn.close()

print("\n--- Checking tearsheet PDFs location ---")
for p in Path(".").rglob("*.pdf"):
    print("Found PDF:", p)

