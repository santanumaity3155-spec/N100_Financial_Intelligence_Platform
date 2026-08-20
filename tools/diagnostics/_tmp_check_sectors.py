import sqlite3
conn = sqlite3.connect('data/database/n100.db')
c = conn.cursor()

c.execute('SELECT DISTINCT sub_sector FROM sectors WHERE sub_sector IS NOT NULL ORDER BY sub_sector')
print('All sub_sectors:', [r[0] for r in c.fetchall()])
print()

c.execute("SELECT company_id, sub_sector FROM sectors WHERE LOWER(sub_sector) LIKE '%bank%' OR LOWER(sub_sector) LIKE '%financial%' OR LOWER(sub_sector) LIKE '%insurance%' ORDER BY sub_sector")
print('Financial sub_sectors:', c.fetchall())
print()

c.execute('SELECT sector, COUNT(*) FROM companies GROUP BY sector')
print('companies.sector distribution:', c.fetchall())
print()

# Check broad_sector
c.execute('SELECT DISTINCT broad_sector FROM sectors WHERE broad_sector IS NOT NULL ORDER BY broad_sector')
print('broad_sectors:', [r[0] for r in c.fetchall()])

conn.close()
