import sqlite3
from pathlib import Path
import json

db_path = Path("data/database/n100.db")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("--- TCS in companies table ---")
cursor.execute("SELECT * FROM companies WHERE company_id = 'TCS'")
r = cursor.fetchone()
print(dict(r) if r else "Not found")

print("\n--- TCS in sectors table ---")
cursor.execute("SELECT * FROM sectors WHERE company_id = 'TCS'")
r = cursor.fetchone()
print(dict(r) if r else "Not found")

print("\n--- TCS P&L rows (first 5) ---")
cursor.execute("SELECT * FROM profit_loss WHERE company_id = 'TCS' LIMIT 5")
print([dict(x) for x in cursor.fetchall()])

print("\n--- TCS Balance Sheet rows (first 5) ---")
cursor.execute("SELECT * FROM balance_sheet WHERE company_id = 'TCS' LIMIT 5")
print([dict(x) for x in cursor.fetchall()])

print("\n--- TCS Cash Flow rows (first 5) ---")
cursor.execute("SELECT * FROM cash_flow WHERE company_id = 'TCS' LIMIT 5")
print([dict(x) for x in cursor.fetchall()])

print("\n--- TCS Financial KPIs rows (first 5) ---")
cursor.execute("SELECT * FROM financial_kpis WHERE company_id = 'TCS' LIMIT 5")
print([dict(x) for x in cursor.fetchall()])

print("\n--- TCS Financial Ratios rows (first 5) ---")
cursor.execute("SELECT * FROM financial_ratios WHERE company_id = 'TCS' LIMIT 5")
print([dict(x) for x in cursor.fetchall()])

conn.close()
