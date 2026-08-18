import sqlite3
from pathlib import Path

db_path = Path("data/database/n100.db")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("SELECT * FROM market_cap WHERE company_id = 'TCS'")
for r in cursor.fetchall():
    print(dict(r))

conn.close()
