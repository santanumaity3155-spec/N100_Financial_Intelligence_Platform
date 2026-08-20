"""Check SIEMENS + HCLTECH + SHREECEM + AMBUJACEM data details and TCS legacy rows."""
import sqlite3

DB = "data/database/n100.db"
conn = sqlite3.connect(DB)
cur = conn.cursor()

print("SIEMENS cash_flow periods:")
cur.execute("SELECT period, operating_activity, investing_activity, financing_activity FROM cash_flow WHERE company_id='SIEMENS' ORDER BY id")
for r in cur.fetchall():
    print("  ", r)

print()
print("SIEMENS profit_loss periods:")
cur.execute("SELECT period, sales, net_profit FROM profit_loss WHERE company_id='SIEMENS' ORDER BY id")
for r in cur.fetchall():
    print("  ", r)

print()
print("HCLTECH profit_loss periods:")
cur.execute("SELECT period, sales, net_profit FROM profit_loss WHERE company_id='HCLTECH' ORDER BY id")
for r in cur.fetchall():
    print("  ", r)

print()
print("SHREECEM profit_loss periods:")
cur.execute("SELECT period, sales, net_profit FROM profit_loss WHERE company_id='SHREECEM' ORDER BY id")
for r in cur.fetchall():
    print("  ", r)

print()
print("AMBUJACEM profit_loss periods:")
cur.execute("SELECT period, sales, net_profit FROM profit_loss WHERE company_id='AMBUJACEM' ORDER BY id")
for r in cur.fetchall():
    print("  ", r)

print()
print("Which companies have legacy 'Mar-YY' cash_flow periods:")
cur.execute("SELECT DISTINCT company_id FROM cash_flow WHERE period LIKE 'Mar-%'")
print("  ", [r[0] for r in cur.fetchall()])

print()
print("NESTLEIND cash_flow periods:")
cur.execute("SELECT period, operating_activity FROM cash_flow WHERE company_id='NESTLEIND' ORDER BY id")
for r in cur.fetchall():
    print("  ", r)

conn.close()