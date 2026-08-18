"""Comprehensive data profile for Module 3 implementation."""
import sqlite3
import re

DB = "data/database/n100.db"
conn = sqlite3.connect(DB)
cur = conn.cursor()

def canonical_year(p):
    """Extract a sortable period key from various period formats."""
    p = str(p).strip()
    m = re.match(r"([A-Za-z]{3})[\s-](\d{4})", p)
    if m:
        months = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
                  "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}
        mon = months.get(m.group(1).lower(), 0)
        return (int(m.group(2)), mon)
    m = re.match(r"(\d{4})(?:\.5)?$", p)
    if m:
        return (int(m.group(1)), 12)
    return (0, 0)


print("=" * 90)
print("CASH_FLOW: latest period per company (sorted chronologically)")
print("=" * 90)
cur.execute("SELECT company_id, period FROM cash_flow")
rows = cur.fetchall()
by_co = {}
for cid, p in rows:
    by_co.setdefault(cid, []).append(p)
for cid in sorted(by_co):
    ps = sorted(by_co[cid], key=canonical_year)
    print(f"  {cid}: n={len(ps)} latest={ps[-1] if ps else None} earliest={ps[0] if ps else None}")

print()
print("=" * 90)
print("PROFIT_LOSS: stub periods and TTM - check surrounding rows for HCLTECH, SHREECEM, AMBUJACEM")
print("=" * 90)
for cid in ["HCLTECH", "SHREECEM", "AMBUJACEM"]:
    cur.execute(
        "SELECT period, sales, net_profit FROM profit_loss WHERE company_id=? ORDER BY id",
        (cid,),
    )
    print(f"  --- {cid} ---")
    for r in cur.fetchall():
        print("   ", r)

print()
print("=" * 90)
print("BALANCE_SHEET: distinct periods per company (first 20 companies)")
print("=" * 90)
cur.execute("SELECT company_id, period FROM balance_sheet")
rows = cur.fetchall()
by_co = {}
for cid, p in rows:
    by_co.setdefault(cid, []).append(p)
for cid in sorted(by_co)[:20]:
    ps = sorted(set(by_co[cid]), key=canonical_year)
    print(f"  {cid}: {ps}")

print()
print("=" * 90)
print("BALANCE_SHEET: companies using year-only or odd periods")
print("=" * 90)
odd = {}
for cid, ps in by_co.items():
    for p in ps:
        if not re.match(r"[A-Za-z]{3} \d{4}$", str(p).strip()):
            odd.setdefault(cid, set()).add(p)
for cid in sorted(odd):
    print(f"  {cid}: {sorted(odd[cid], key=canonical_year)}")

print()
print("=" * 90)
print("CASH_FLOW: companies missing cash_flow rows entirely?")
print("=" * 90)
cur.execute("SELECT DISTINCT company_id FROM cash_flow")
with_cf = {r[0] for r in cur.fetchall()}
cur.execute("SELECT company_id FROM companies")
all_co = [r[0] for r in cur.fetchall()]
missing_cf = [c for c in all_co if c not in with_cf]
print("  companies without cash_flow rows:", missing_cf)
cur.execute("SELECT COUNT(DISTINCT company_id) FROM cash_flow")
print("  distinct companies in cash_flow:", cur.fetchone()[0])

print()
print("=" * 90)
print("CASH_FLOW: sign convention check - investing_activity sign")
print("=" * 90)
cur.execute("""
    SELECT SUM(CASE WHEN investing_activity < 0 THEN 1 ELSE 0 END) neg,
           SUM(CASE WHEN investing_activity > 0 THEN 1 ELSE 0 END) pos,
           SUM(CASE WHEN investing_activity = 0 THEN 1 ELSE 0 END) zero,
           SUM(CASE WHEN investing_activity IS NULL THEN 1 ELSE 0 END) nullv
    FROM cash_flow
""")
print("  investing_activity: neg=%s pos=%s zero=%s null=%s" % cur.fetchone())
cur.execute("""
    SELECT SUM(CASE WHEN operating_activity < 0 THEN 1 ELSE 0 END) neg,
           SUM(CASE WHEN operating_activity > 0 THEN 1 ELSE 0 END) pos,
           SUM(CASE WHEN operating_activity IS NULL THEN 1 ELSE 0 END) nullv
    FROM cash_flow
""")
print("  operating_activity: neg=%s pos=%s null=%s" % cur.fetchone())
cur.execute("""
    SELECT SUM(CASE WHEN financing_activity < 0 THEN 1 ELSE 0 END) neg,
           SUM(CASE WHEN financing_activity > 0 THEN 1 ELSE 0 END) pos,
           SUM(CASE WHEN financing_activity IS NULL THEN 1 ELSE 0 END) nullv
    FROM cash_flow
""")
print("  financing_activity: neg=%s pos=%s null=%s" % cur.fetchone())

print()
print("=" * 90)
print("CASH_FLOW: net_cash_flow vs sum of components (TCS)")
print("=" * 90)
cur.execute(
    "SELECT period, operating_activity, investing_activity, financing_activity, net_cash_flow "
    "FROM cash_flow WHERE company_id='TCS' AND period LIKE 'Mar 201%' ORDER BY period"
)
for r in cur.fetchall():
    comp = (r[1] or 0) + (r[2] or 0) + (r[3] or 0)
    print(f"  {r[0]}: sum={comp} net={r[4]} match={abs(comp - r[4]) < 1}")

print()
print("=" * 90)
print("PROFIT_LOSS: sales/net_profit null counts")
print("=" * 90)
cur.execute(
    "SELECT SUM(CASE WHEN sales IS NULL THEN 1 ELSE 0 END), "
    "SUM(CASE WHEN net_profit IS NULL THEN 1 ELSE 0 END), COUNT(*) FROM profit_loss"
)
print("  null sales, null net_profit, total =", cur.fetchone())

print()
print("=" * 90)
print("SECTORS table: coverage")
print("=" * 90)
cur.execute("SELECT COUNT(*) FROM sectors")
print("  sectors rows =", cur.fetchone()[0])
cur.execute("SELECT COUNT(DISTINCT company_id) FROM sectors")
print("  distinct companies in sectors =", cur.fetchone()[0])
cur.execute("SELECT company_id FROM companies EXCEPT SELECT company_id FROM sectors")
print("  companies missing from sectors:", [r[0] for r in cur.fetchall()])

conn.close()