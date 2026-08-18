"""Diagnostic: inspect the canonical database for Module 3."""
import sqlite3
import sys
from pathlib import Path

DB = Path("data/database/n100.db")
print("DB exists:", DB.exists(), "size:", DB.stat().st_size if DB.exists() else "N/A")

conn = sqlite3.connect(str(DB))
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
print("TABLES:", [r[0] for r in cur.fetchall()])
print()

for t in ["companies", "cash_flow", "profit_loss", "balance_sheet", "financial_ratios"]:
    try:
        cur.execute(f'SELECT COUNT(*) FROM "{t}"')
        c = cur.fetchone()[0]
        cur.execute(f'PRAGMA table_info("{t}")')
        cols = [r[1] for r in cur.fetchall()]
        print(f"TABLE {t}: rows={c}")
        print(f"  cols={cols}")
    except Exception as e:
        print(f"TABLE {t}: ERROR {e}")
    print()

conn.close()
