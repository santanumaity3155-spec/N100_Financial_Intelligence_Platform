"""Inspect the actual n100.db database schema and data coverage."""
import sqlite3

DB = "data/database/n100.db"
conn = sqlite3.connect(DB)
cur = conn.cursor()

print("=" * 90)
print("TABLES")
print("=" * 90)
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [r[0] for r in cur.fetchall()]
for t in tables:
    print(f"  {t}")

print()
print("=" * 90)
print("COMPANIES: row count")
print("=" * 90)
cur.execute("SELECT COUNT(*) FROM companies")
print("companies count =", cur.fetchone()[0])

for t in ["companies", "cash_flow", "profit_loss", "balance_sheet", "financial_ratios"]:
    print()
    print(f"--- {t} ---")
    cur.execute(f"PRAGMA table_info({t})")
    cols = [(r[1], r[2]) for r in cur.fetchall()]
    for c in cols:
        print("   ", c)
    try:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        print("    row count =", cur.fetchone()[0])
    except Exception as e:
        print("    count error:", e)

print()
print("=" * 90)
print("COMPANIES: sample rows (company_id, company_name, sector)")
print("=" * 90)
cur.execute("SELECT company_id, company_name, sector FROM companies LIMIT 15")
for r in cur.fetchall():
    print("  ", r)

print()
print("=" * 90)
print("DISTINCT SECTORS + count")
print("=" * 90)
cur.execute("SELECT sector, COUNT(*) FROM companies GROUP BY sector ORDER BY COUNT(*) DESC")
for r in cur.fetchall():
    print("  ", r)

print()
print("=" * 90)
print("CASH_FLOW: sample periods per company")
print("=" * 90)
cur.execute("SELECT company_id, COUNT(*), MIN(period), MAX(period) FROM cash_flow GROUP BY company_id ORDER BY company_id LIMIT 15")
for r in cur.fetchall():
    print("  ", r)

print()
print("=" * 90)
print("CASH_FLOW: distinct period formats")
print("=" * 90)
cur.execute("SELECT period, COUNT(*) FROM cash_flow GROUP BY period ORDER BY period LIMIT 30")
for r in cur.fetchall():
    print("  ", r)

conn.close()