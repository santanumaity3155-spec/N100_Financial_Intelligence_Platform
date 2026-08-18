"""Diagnostic: inspect data population of key columns and sample records."""
import sqlite3
from pathlib import Path

DB = Path("data/database/n100.db")
conn = sqlite3.connect(str(DB))
cur = conn.cursor()

print("=== cash_flow sample ===")
cur.execute("SELECT id, company_id, period, cash_from_operating_activity, cash_from_investing_activity, cash_from_financing_activity, operating_activity, investing_activity, financing_activity FROM cash_flow LIMIT 6")
for r in cur.fetchall():
    print(r)

print("\n=== cash_flow column population stats ===")
cur.execute("""
SELECT
  COUNT(*) AS total,
  SUM(CASE WHEN cash_from_operating_activity IS NOT NULL THEN 1 ELSE 0 END) AS cf_oper,
  SUM(CASE WHEN cash_from_investing_activity IS NOT NULL THEN 1 ELSE 0 END) AS cf_inv,
  SUM(CASE WHEN cash_from_financing_activity IS NOT NULL THEN 1 ELSE 0 END) AS cf_fin,
  SUM(CASE WHEN operating_activity IS NOT NULL THEN 1 ELSE 0 END) AS oper,
  SUM(CASE WHEN investing_activity IS NOT NULL THEN 1 ELSE 0 END) AS inv,
  SUM(CASE WHEN financing_activity IS NOT NULL THEN 1 ELSE 0 END) AS fin
FROM cash_flow
""")
print(cur.fetchone())

print("\n=== profit_loss sample ===")
cur.execute("SELECT id, company_id, period, sales, net_profit FROM profit_loss LIMIT 6")
for r in cur.fetchall():
    print(r)

print("\n=== profit_loss population stats ===")
cur.execute("SELECT COUNT(*), SUM(CASE WHEN sales IS NOT NULL THEN 1 ELSE 0 END), SUM(CASE WHEN net_profit IS NOT NULL THEN 1 ELSE 0 END) FROM profit_loss")
print(cur.fetchone())

print("\n=== balance_sheet sample ===")
cur.execute("SELECT id, company_id, period, borrowings, total_assets FROM balance_sheet LIMIT 6")
for r in cur.fetchall():
    print(r)

print("\n=== balance_sheet population stats ===")
cur.execute("SELECT COUNT(*), SUM(CASE WHEN borrowings IS NOT NULL THEN 1 ELSE 0 END), SUM(CASE WHEN total_assets IS NOT NULL THEN 1 ELSE 0 END) FROM balance_sheet")
print(cur.fetchone())

print("\n=== companies sample ===")
cur.execute("SELECT company_id, company_name, sector FROM companies LIMIT 6")
for r in cur.fetchall():
    print(r)

print("\n=== companies sector counts ===")
cur.execute("SELECT COUNT(DISTINCT sector) FROM companies")
print("distinct sectors:", cur.fetchone()[0])

print("\n=== companies without any cash_flow row ===")
cur.execute("""
SELECT c.company_id FROM companies c
LEFT JOIN cash_flow cf ON cf.company_id = c.company_id
WHERE cf.company_id IS NULL
""")
missing_cf = [r[0] for r in cur.fetchall()]
print("missing cash_flow:", len(missing_cf), missing_cf[:20])

cur.execute("""
SELECT c.company_id FROM companies c
LEFT JOIN profit_loss pl ON pl.company_id = c.company_id
WHERE pl.company_id IS NULL
""")
missing_pl = [r[0] for r in cur.fetchall()]
print("missing profit_loss:", len(missing_pl), missing_pl[:20])

cur.execute("""
SELECT c.company_id FROM companies c
LEFT JOIN balance_sheet bs ON bs.company_id = c.company_id
WHERE bs.company_id IS NULL
""")
missing_bs = [r[0] for r in cur.fetchall()]
print("missing balance_sheet:", len(missing_bs), missing_bs[:20])

conn.close()
