import sqlite3
from pathlib import Path

db_path = Path("data/database/n100.db")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("SELECT DISTINCT period FROM cash_flow")
print("Cash flow periods:", [r[0] for r in cursor.fetchall()])

conn.close()
