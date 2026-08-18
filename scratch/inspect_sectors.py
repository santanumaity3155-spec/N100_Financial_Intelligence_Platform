import sqlite3
from pathlib import Path

db_path = Path("data/database/n100.db")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("SELECT DISTINCT broad_sector FROM sectors")
print("Sectors table broad_sector:", [r[0] for r in cursor.fetchall()])

cursor.execute("SELECT DISTINCT sub_sector FROM sectors")
print("\nSectors table sub_sector:", [r[0] for r in cursor.fetchall()])

cursor.execute("SELECT DISTINCT sector FROM companies")
print("\nCompanies table sector:", [r[0] for r in cursor.fetchall()])

cursor.execute("SELECT DISTINCT industry FROM companies")
print("\nCompanies table industry:", [r[0] for r in cursor.fetchall()])

conn.close()
