import sqlite3
from pathlib import Path

DB = Path("data/database/n100.db")
conn = sqlite3.connect(str(DB))
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [r[0] for r in cur.fetchall()]
print("=== TABLES ===")
for t in tables:
    print(f"  - {t}")
    cur.execute(f"PRAGMA table_info({t})")
    cols = cur.fetchall()
    for c in cols:
        print(f"      {c['name']:35s} {c['type']}")
    cur.execute(f"SELECT COUNT(*) FROM {t}")
    cnt = cur.fetchone()[0]
    print(f"      [rows: {cnt}]")

print("\n=== SCHEMA SAMPLES ===")
for t in ["companies", "financial_ratios", "peer_groups"]:
    if t in tables:
        print(f"\n--- {t} (first 2 rows) ---")
        cur.execute(f"SELECT * FROM {t} LIMIT 2")
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        print("Columns:", cols)
        for r in rows:
            print(dict(r))

conn.close()
