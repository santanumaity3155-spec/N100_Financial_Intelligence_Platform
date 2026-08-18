import sqlite3
conn = sqlite3.connect(r'D:\New Project\Bluestock_Projects\Nifty 100\N100 Financial Intelligence Platform\N100_Financial_Intelligence_Platform\data\database\n100.db')
cursor = conn.cursor()

cursor.execute('PRAGMA table_info(profit_loss)')
cols = cursor.fetchall()
print('profit_loss columns:', [c[1] for c in cols])

cursor.execute("SELECT * FROM profit_loss WHERE company_id='RELIANCE' LIMIT 3")
rows = cursor.fetchall()
print('Sample RELIANCE profit_loss rows:')
for row in rows:
    print(row)

cursor.execute('PRAGMA table_info(balance_sheet)')
cols = cursor.fetchall()
print('balance_sheet columns:', [c[1] for c in cols])

cursor.execute("SELECT * FROM balance_sheet WHERE company_id='RELIANCE' LIMIT 3")
rows = cursor.fetchall()
print('Sample RELIANCE balance_sheet rows:')
for row in rows:
    print(row)

conn.close()
