#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('data/database/n100.db')

companies = [
    'UNIONBANK', 'BAJAJFINSV', 'BOSCHLTD', 'COALINDIA', 'DIVISLAB', 'DMART',
    'HDFCLIFE', 'ICICIGI', 'ICICIPRULI', 'INDIGO', 'IRCTC', 'ITC', 'MARUTI', 'PNB'
]

print("=== COMPANIES TABLE ===")
cursor = conn.execute(
    'SELECT company_id, company_name, sector FROM companies WHERE company_id IN ({})'.format(
        ','.join(['?' for _ in companies])
    ),
    companies
)
for row in cursor.fetchall():
    print(row)

print("\n=== SECTORS TABLE ===")
cursor = conn.execute(
    'SELECT company_id, broad_sector, sub_sector FROM sectors WHERE company_id IN ({})'.format(
        ','.join(['?' for _ in companies])
    ),
    companies
)
for row in cursor.fetchall():
    print(row)

conn.close()
