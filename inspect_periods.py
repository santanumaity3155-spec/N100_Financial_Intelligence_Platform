import sqlite3
conn = sqlite3.connect('data/database/n100.db')
c = conn.cursor()
c.execute('SELECT DISTINCT period FROM cash_flow WHERE company_id = "ABB" ORDER BY period')
print('ABB cash_flow periods:', [r[0] for r in c.fetchall()])
c.execute('SELECT DISTINCT period FROM profit_loss WHERE company_id = "ABB" ORDER BY period')
print('ABB profit_loss periods:', [r[0] for r in c.fetchall()])
conn.close()
