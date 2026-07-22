import sqlite3

conn = sqlite3.connect('data/database/n100.db')

# Check what companies are in financial_ratios
cursor = conn.execute("""
    SELECT DISTINCT fr.company_id, c.company_name, fr.period
    FROM financial_ratios fr
    LEFT JOIN companies c ON fr.company_id = c.company_id
    WHERE fr.period = 'Sep 2024'
    LIMIT 20
""")
print("Companies in financial_ratios for Sep 2024:")
for row in cursor.fetchall():
    print(f"  {row[0]} - {row[1]} ({row[2]})")

# Check what companies are in peer_groups
cursor = conn.execute("""
    SELECT DISTINCT company_id, peer_group_name
    FROM peer_groups
    ORDER BY peer_group_name, company_id
""")
print("\nCompanies in peer_groups:")
for row in cursor.fetchall():
    print(f"  {row[0]} - {row[1]}")

conn.close()