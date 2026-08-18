import sqlite3
from pathlib import Path
import json

db_path = Path("data/database/n100.db")
if not db_path.exists():
    print("Database path does not exist:", db_path.absolute())
    exit(1)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Get all table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row[0] for row in cursor.fetchall()]
print("Tables:", tables)

for table in tables:
    cursor.execute(f"PRAGMA table_info({table});")
    cols = [(col["name"], col["type"]) for col in cursor.fetchall()]
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f"\nTable: {table} (Count: {count})")
    print("Columns:", cols)

# Check companies sample row
cursor.execute("SELECT * FROM companies LIMIT 2")
sample_comp = [dict(r) for r in cursor.fetchall()]
print("\nCompanies sample:", json.dumps(sample_comp, indent=2))

conn.close()
