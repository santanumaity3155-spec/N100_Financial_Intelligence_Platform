"""Compare child vs parent n100.db."""
import sqlite3
from pathlib import Path

for label, db in [
    ("CHILD", Path("data/database/n100.db")),
    ("PARENT", Path("../data/database/n100.db")),
]:
    conn = sqlite3.connect(str(db))
    cur = conn.cursor()
    def q(sql):
        cur.execute(sql)
        return cur.fetchone()[0]
    print(f"=== {label}: {db} size={db.stat().st_size} ===")
    for t in ["companies", "cash_flow", "profit_loss", "balance_sheet"]:
        try:
            print(f"  {t}: {q(f'SELECT COUNT(*) FROM {t}')}")
        except Exception as e:
            print(f"  {t}: ERROR {e}")
    cur.execute("SELECT COUNT(*) FROM cash_flow WHERE operating_activity IS NOT NULL")
    print("  cash_flow with operating_activity:", cur.fetchone()[0])
    cur.execute("SELECT COUNT(*) FROM cash_flow WHERE cash_from_operating_activity IS NOT NULL")
    print("  cash_flow with cash_from_operating_activity:", cur.fetchone()[0])
    cur.execute("SELECT COUNT(*) FROM companies c LEFT JOIN sectors s ON s.company_id=c.company_id WHERE s.company_id IS NULL")
    print("  companies missing sector:", cur.fetchone()[0])
    conn.close()
    print()
