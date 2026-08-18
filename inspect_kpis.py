import sqlite3
conn = sqlite3.connect('data/database/n100.db')
c = conn.cursor()
c.execute('PRAGMA table_info(financial_kpis)')
print('financial_kpis columns:', [r[1] for r in c.fetchall()])
c.execute('SELECT * FROM financial_kpis WHERE company_id = "ABB" LIMIT 3')
for r in c.fetchall(): print(r)
conn.close()
