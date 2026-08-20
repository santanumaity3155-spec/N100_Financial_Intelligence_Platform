import sqlite3

conn = sqlite3.connect('data/database/n100.db')
c = conn.cursor()

print("=== RELIANCE cash_flow ===")
c.execute('SELECT company_id, period, operating_activity, investing_activity, financing_activity FROM cash_flow WHERE company_id = ? ORDER BY period DESC LIMIT 5', ('RELIANCE',))
for row in c.fetchall():
    print(row)

print("=== RELIANCE profit_loss ===")
c.execute('SELECT company_id, period, sales, net_profit FROM profit_loss WHERE company_id = ? ORDER BY period DESC LIMIT 5', ('RELIANCE',))
for row in c.fetchall():
    print(row)

print("=== RELIANCE balance_sheet ===")
c.execute('SELECT company_id, period, borrowings FROM balance_sheet WHERE company_id = ? ORDER BY period DESC LIMIT 5', ('RELIANCE',))
for row in c.fetchall():
    print(row)

print("\n=== Companies with cash_flow data ===")
c.execute('SELECT COUNT(DISTINCT company_id) FROM cash_flow')
print("Distinct companies in cash_flow:", c.fetchone()[0])

c.execute('SELECT COUNT(DISTINCT company_id) FROM profit_loss')
print("Distinct companies in profit_loss:", c.fetchone()[0])

c.execute('SELECT COUNT(DISTINCT company_id) FROM balance_sheet')
print("Distinct companies in balance_sheet:", c.fetchone()[0])

conn.close()
