import sqlite3
conn = sqlite3.connect('data/database/n100.db')
c = conn.cursor()
c.execute('PRAGMA table_info(cash_flow)')
print('cash_flow columns:', [r[1] for r in c.fetchall()])
c.execute('SELECT * FROM cash_flow WHERE company_id = "ABB" LIMIT 5')
for r in c.fetchall(): print(r)
conn.close()
