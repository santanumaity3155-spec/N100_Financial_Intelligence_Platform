"""Inspect cash flow sign conventions, free_cash_flow, periods per company."""
import sqlite3

DB = "data/database/n100.db"
conn = sqlite3.connect(DB)
cur = conn.cursor()

print("=" * 90)
print("CASH_FLOW: TCS sample (ordered by id)")
print("=" * 90)
cur.execute(
    "SELECT period, cash_from_operating_activity, cash_from_investing_activity, "
    "cash_from_financing_activity, free_cash_flow, net_cash_flow, operating_activity, "
    "investing_activity, financing_activity FROM cash_flow WHERE company_id='TCS' ORDER BY id"
)
for r in cur.fetchall():
    print("  ", r)

print()
print("=" * 90)
print("free_cash_flow column: how many rows populated?")
print("=" * 90)
cur.execute(
    "SELECT COUNT(*), SUM(CASE WHEN free_cash_flow IS NOT NULL THEN 1 ELSE 0 END), "
    "SUM(CASE WHEN cash_from_operating_activity IS NOT NULL THEN 1 ELSE 0 END), "
    "SUM(CASE WHEN cash_from_investing_activity IS NOT NULL THEN 1 ELSE 0 END), "
    "SUM(CASE WHEN cash_from_financing_activity IS NOT NULL THEN 1 ELSE 0 END) FROM cash_flow"
)
r = cur.fetchone()
print(f"  total rows={r[0]}, free_cash_flow populated={r[1]}, cfo populated={r[2]}, cfi populated={r[3]}, cff populated={r[4]}")

print()
print("=" * 90)
print("Mixed-month companies: count companies having >1 distinct month in cash_flow periods")
print("=" * 90)
cur.execute("""
    SELECT COUNT(*) FROM (
        SELECT company_id FROM cash_flow
        GROUP BY company_id
        HAVING COUNT(DISTINCT substr(period, 1, 3)) > 1
    )
""")
print("  companies with mixed months =", cur.fetchone()[0])

cur.execute("""
    SELECT company_id, GROUP_CONCAT(DISTINCT substr(period,1,3)) FROM cash_flow
    GROUP BY company_id
    HAVING COUNT(DISTINCT substr(period, 1, 3)) > 1
    LIMIT 20
""")
for r in cur.fetchall():
    print("  ", r)

print()
print("=" * 90)
print("Legacy period formats (non '%b %Y')")
print("=" * 90)
cur.execute("""
    SELECT DISTINCT period FROM cash_flow
    WHERE period NOT GLOB '[A-Z][a-z][a-z] [0-9][0-9][0-9][0-9]'
    ORDER BY period
""")
for r in cur.fetchall():
    print("  ", r)

print()
print("=" * 90)
print("Profit_loss: distinct period formats")
print("=" * 90)
cur.execute("""
    SELECT DISTINCT period FROM profit_loss
    WHERE period NOT GLOB '[A-Z][a-z][a-z] [0-9][0-9][0-9][0-9]'
    ORDER BY period LIMIT 20
""")
for r in cur.fetchall():
    print("  ", r)

print()
print("=" * 90)
print("Balance_sheet: distinct period formats")
print("=" * 90)
cur.execute("""
    SELECT DISTINCT period FROM balance_sheet
    WHERE period NOT GLOB '[A-Z][a-z][a-z] [0-9][0-9][0-9][0-9]'
    ORDER BY period LIMIT 20
""")
for r in cur.fetchall():
    print("  ", r)

print()
print("=" * 90)
print("Missing value counts per company in cash_flow")
print("=" * 90)
cur.execute("""
    SELECT company_id, COUNT(*) total,
           SUM(CASE WHEN cash_from_operating_activity IS NULL THEN 1 ELSE 0 END) null_ocf,
           SUM(CASE WHEN cash_from_investing_activity IS NULL THEN 1 ELSE 0 END) null_cfi,
           SUM(CASE WHEN cash_from_financing_activity IS NULL THEN 1 ELSE 0 END) null_cff
    FROM cash_flow GROUP BY company_id
    HAVING null_ocf > 0 OR null_cfi > 0 OR null_cff > 0
    ORDER BY company_id
""")
for r in cur.fetchall():
    print("  ", r)

print()
print("=" * 90)
print("Companies with 0 borrowings (all zeros) vs null borrowings")
print("=" * 90)
cur.execute("""
    SELECT company_id,
           SUM(CASE WHEN borrowings IS NULL THEN 1 ELSE 0 END) null_borr,
           SUM(CASE WHEN borrowings = 0 THEN 1 ELSE 0 END) zero_borr,
           COUNT(*) total
    FROM balance_sheet GROUP BY company_id
    HAVING null_borr > 0 OR zero_borr > 0
    ORDER BY company_id LIMIT 40
""")
for r in cur.fetchall():
    print("  ", r)

conn.close()