import sqlite3
from pathlib import Path

db_path = Path("data/database/n100.db")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

for table in ["profit_loss", "balance_sheet", "cash_flow", "financial_kpis", "financial_ratios"]:
    cursor.execute(f"SELECT DISTINCT period FROM {table} ORDER BY period")
    periods = [r[0] for r in cursor.fetchall()]
    print(f"\nTable {table} periods ({len(periods)} distinct):")
    print(periods[:20])

conn.close()
