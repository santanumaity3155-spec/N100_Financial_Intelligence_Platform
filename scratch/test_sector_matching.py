import sqlite3
from pathlib import Path

db_path = Path("data/database/n100.db")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

def test_sector_filter(sec):
    sec_clean = sec.strip()
    like_pattern = f"%{sec_clean}%"
    prefix_pattern = f"{sec_clean}%"
    cursor.execute("""
        SELECT c.company_id, c.company_name, s.sub_sector
        FROM companies c
        LEFT JOIN sectors s ON c.company_id = s.company_id
        WHERE LOWER(s.sub_sector) = LOWER(?)
           OR LOWER(s.sub_sector) LIKE LOWER(?)
           OR LOWER(s.broad_sector) LIKE LOWER(?)
    """, (sec_clean, like_pattern, like_pattern))
    rows = cursor.fetchall()
    print(f"Filter sector='{sec}' matched {len(rows)} companies:")
    for r in rows:
        print(" ", r["company_id"], "->", r["sub_sector"])

test_sector_filter("IT")
test_sector_filter("Healthcare")
test_sector_filter("Private Banks")

conn.close()
