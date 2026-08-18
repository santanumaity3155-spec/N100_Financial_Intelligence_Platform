import sqlite3
from pathlib import Path

db_path = Path("data/database/n100.db")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

def test_refined_sector_filter(sec):
    sec_clean = sec.strip()
    sec_lower = sec_clean.lower()
    
    if sec_lower == "it":
        query = """
            SELECT c.company_id, c.company_name, s.sub_sector
            FROM companies c
            LEFT JOIN sectors s ON c.company_id = s.company_id
            WHERE LOWER(s.sub_sector) = 'it'
               OR LOWER(s.sub_sector) LIKE 'it %'
               OR LOWER(s.sub_sector) LIKE '% it%'
               OR LOWER(s.sub_sector) LIKE '%information technology%'
        """
        cursor.execute(query)
    else:
        pattern = f"%{sec_clean}%"
        query = """
            SELECT c.company_id, c.company_name, s.sub_sector
            FROM companies c
            LEFT JOIN sectors s ON c.company_id = s.company_id
            WHERE LOWER(s.sub_sector) = LOWER(?)
               OR LOWER(s.broad_sector) = LOWER(?)
               OR LOWER(c.sector) = LOWER(?)
               OR LOWER(c.industry) = LOWER(?)
               OR LOWER(s.sub_sector) LIKE LOWER(?)
        """
        cursor.execute(query, (sec_clean, sec_clean, sec_clean, sec_clean, pattern))
        
    rows = cursor.fetchall()
    print(f"\nRefined sector='{sec}' matched {len(rows)} companies:")
    for r in rows:
        print(" ", r["company_id"], "->", r["sub_sector"])

test_refined_sector_filter("IT")
test_refined_sector_filter("IT Services")
test_refined_sector_filter("Healthcare")
test_refined_sector_filter("Private Banks")

conn.close()
