import sqlite3
import re
from pathlib import Path
import json

db_path = Path("data/database/n100.db")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

def parse_period_year(period_str):
    """Extract 4-digit year from period string like 'Mar 2024', '2024', 'Dec 2019', 'Mar-20'."""
    if not period_str:
        return None
    # Look for 4 digit year
    m = re.search(r'\b(19\d\d|20\d\d)\b', str(period_str))
    if m:
        return int(m.group(1))
    # Look for 2 digit year with prefix Mar-20 -> 2020
    m2 = re.search(r'-(1\d|2\d)\b', str(period_str))
    if m2:
        return 2000 + int(m2.group(1))
    return None

def parse_year_param(val):
    """Parse query param like '2019-03', '2019', 2019 into integer year or date tuple (year, month)."""
    if not val:
        return None
    val_str = str(val).strip()
    # Format YYYY-MM
    m_full = re.match(r'^(\d{4})-(0[1-9]|1[0-2])$', val_str)
    if m_full:
        return int(m_full.group(1)), int(m_full.group(2))
    # Format YYYY
    m_year = re.match(r'^\d{4}$', val_str)
    if m_year:
        return int(m_year.group(0)), None
    raise ValueError(f"Invalid year format: {val_str}")

print("Testing period parser:")
sample_periods = ['Dec 2012', '2013', '2024.5', 'Mar-13', 'Mar-24', 'Sep 2024', 'Jun 2015']
for p in sample_periods:
    print(f"  '{p}' -> {parse_period_year(p)}")

print("\nTesting year param parser:")
for y in ['2019-03', '2024-03', '2024']:
    print(f"  '{y}' -> {parse_year_param(y)}")

# Test invalid year param
try:
    parse_year_param("invalid")
except ValueError as e:
    print("  'invalid' -> caught expected ValueError:", e)

# Test query for /api/v1/companies
cursor.execute("""
    SELECT 
        c.company_id,
        c.company_name,
        COALESCE(s.broad_sector, c.sector) AS broad_sector,
        COALESCE(s.sub_sector, c.industry) AS sub_sector,
        s.market_cap_category,
        c.roe_percentage AS roe_pct,
        c.roce_percentage AS roce_pct
    FROM companies c
    LEFT JOIN sectors s ON c.company_id = s.company_id
    ORDER BY c.company_id
""")
rows = [dict(r) for r in cursor.fetchall()]
print(f"\nCompanies endpoint count: {len(rows)}")
print("Sample first company:", json.dumps(rows[0], indent=2))

# Test company profile query for TCS
cursor.execute("""
    SELECT 
        c.*,
        s.broad_sector,
        s.sub_sector,
        s.market_cap_category,
        s.index_weight_pct
    FROM companies c
    LEFT JOIN sectors s ON c.company_id = s.company_id
    WHERE UPPER(TRIM(c.company_id)) = UPPER(TRIM(?))
""", ('TCS',))
prof = cursor.fetchone()
print("\nProfile for TCS:", dict(prof) if prof else "Not found")

# Test latest KPI query for TCS
cursor.execute("""
    SELECT *
    FROM financial_kpis
    WHERE company_id = 'TCS'
    ORDER BY period DESC
    LIMIT 1
""")
kpi = cursor.fetchone()
print("\nLatest KPI for TCS:", dict(kpi) if kpi else "Not found")

conn.close()
