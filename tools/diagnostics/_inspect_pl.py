"""Inspect profit_loss, balance_sheet rows for TCS + financial_kpis table."""
import sqlite3

DB = "data/database/n100.db"
conn = sqlite3.connect(DB)
cur = conn.cursor()

print("=" * 90)
print("PROFIT_LOSS: TCS rows")
print("=" * 90)
cur.execute(
    "SELECT id, period, sales, net_profit, eps FROM profit_loss WHERE company_id='TCS' ORDER BY id"
)
for r in cur.fetchall():
    print("  ", r)

print()
print("=" * 90)
print("BALANCE_SHEET: TCS rows")
print("=" * 90)
cur.execute(
    "SELECT id, period, borrowings, total_assets FROM balance_sheet WHERE company_id='TCS' ORDER BY id"
)
for r in cur.fetchall():
    print("  ", r)

print()
print("=" * 90)
print("PROFIT_LOSS: odd periods (which companies have them)")
print("=" * 90)
cur.execute("""
    SELECT period, company_id FROM profit_loss
    WHERE period NOT GLOB '[A-Z][a-z][a-z] [0-9][0-9][0-9][0-9]'
    ORDER BY period
""")
for r in cur.fetchall():
    print("  ", r)

print()
print("=" * 90)
print("PROFIT_LOSS: distinct period per company (min/max)")
print("=" * 90)
cur.execute("""
    SELECT company_id, COUNT(*), MIN(period), MAX(period) FROM profit_loss
    GROUP BY company_id ORDER BY company_id LIMIT 20
""")
for r in cur.fetchall():
    print("  ", r)

print()
print("=" * 90)
print("FINANCIAL_KPIS: schema")
print("=" * 90)
cur.execute("PRAGMA table_info(financial_kpis)")
for r in cur.fetchall():
    print("  ", r)
cur.execute("SELECT COUNT(*) FROM financial_kpis")
print("  row count =", cur.fetchone()[0])
cur.execute("SELECT * FROM financial_kpis LIMIT 5")
cols = [d[0] for d in cur.description]
print("  columns:", cols)
for r in cur.fetchall():
    print("  ", r)

print()
print("=" * 90)
print("FINANCIAL_KPIS: distinct period formats")
print("=" * 90)
cur.execute("SELECT DISTINCT period FROM financial_kpis ORDER BY period LIMIT 30")
for r in cur.fetchall():
    print("  ", r)

conn.close()