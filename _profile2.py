"""Focused data profiling for Module 3."""
import sqlite3
import re

DB = "data/database/n100.db"
conn = sqlite3.connect(DB)
cur = conn.cursor()

print("=" * 90)
print("Companies in cash_flow but NOT in companies table")
print("=" * 90)
cur.execute("SELECT DISTINCT company_id FROM cash_flow")
cf_ids = set(r[0] for r in cur.fetchall())
cur.execute("SELECT company_id FROM companies")
co_ids = set(r[0] for r in cur.fetchall())
print("  in cash_flow only:", sorted(cf_ids - co_ids))
print("  in companies only:", sorted(co_ids - cf_ids))

print()
print("=" * 90)
print("Companies with zero cash_flow rows OR only nulls")
print("=" * 90)
for cid in sorted(co_ids - cf_ids):
    print("  ", cid, "-> NO cash_flow rows")

print()
print("=" * 90)
print("Balance sheet periods per company (full list)")
print("=" * 90)
cur.execute("SELECT company_id, period FROM balance_sheet")
rows = cur.fetchall()
by_co = {}
for cid, p in rows:
    by_co.setdefault(cid, []).append(p)

def key(p):
    p = str(p).strip()
    m = re.match(r"([A-Za-z]{3})[\s-](\d{4})", p)
    if m:
        months = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
                  "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}
        return (int(m.group(2)), months.get(m.group(1).lower(), 0))
    m = re.match(r"(\d{4})(?:\.5)?$", p)
    if m:
        return (int(m.group(1)), 12)
    return (0, 0)

for cid in sorted(by_co):
    ps = sorted(set(by_co[cid]), key=key)
    # Is there a 'Mar YYYY' annual period? list annual (non-sep, non-.5)
    annual = [p for p in ps if re.match(r"[A-Za-z]{3} \d{4}$", p) and not p.startswith("Sep")]
    latest2 = ps[-2:]
    print(f"  {cid}: annual_latest2={annual[-2:] if len(annual) >= 2 else annual} all_latest2={latest2}")

print()
print("=" * 90)
print("profit_loss: does every company have Mar 2024 + TTM?")
print("=" * 90)
cur.execute("""
    SELECT company_id,
           SUM(CASE WHEN period='Mar 2024' THEN 1 ELSE 0 END) has_mar24,
           SUM(CASE WHEN period='TTM' THEN 1 ELSE 0 END) has_ttm,
           COUNT(*) total
    FROM profit_loss GROUP BY company_id ORDER BY company_id
""")
odd = 0
for r in cur.fetchall():
    if r[1] != 1 or r[2] != 1:
        odd += 1
        print("  ", r)
print("  companies not having exactly one Mar 2024 AND one TTM:", odd)

print()
print("=" * 90)
print("cash_flow: does every company have Mar 2024?")
print("=" * 90)
cur.execute("""
    SELECT company_id, COUNT(*) FROM cash_flow WHERE period='Mar 2024' GROUP BY company_id
""")
rows24 = set(r[0] for r in cur.fetchall())
missing24 = [c for c in sorted(co_ids & cf_ids) if c not in rows24]
print("  companies in both tables missing Mar 2024 cash_flow:", missing24)

print()
print("=" * 90)
print("Duplicated periods in cash_flow (TCS legacy + canonical)")
print("=" * 90)
cur.execute("""
    SELECT company_id, period, COUNT(*) c FROM cash_flow
    GROUP BY company_id, period HAVING COUNT(*) > 1
""")
dups = cur.fetchall()
print("  duplicate company-period rows:", len(dups))
for r in dups[:10]:
    print("   ", r)

print()
print("=" * 90)
print("Sample of ATGL data in companies vs sectors")
print("=" * 90)
cur.execute("SELECT company_id, company_name FROM companies WHERE company_id='ATGL'")
print("  ", cur.fetchall())
cur.execute("SELECT company_id, broad_sector, sub_sector FROM sectors WHERE company_id='ATGL'")
print("  ", cur.fetchall())

conn.close()