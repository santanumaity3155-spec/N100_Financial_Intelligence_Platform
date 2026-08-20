#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('data/database/n100.db')

# Check PNB profit_loss
cursor = conn.execute('SELECT * FROM profit_loss WHERE company_id = "PNB" AND period = "Mar 2024"')
row = cursor.fetchone()
print('PNB columns:', len(row) if row else 0)
print('PNB row:', row)
print()

# Check COALINDIA profit_loss
cursor = conn.execute('SELECT * FROM profit_loss WHERE company_id = "COALINDIA" AND period = "Mar 2024"')
row = cursor.fetchone()
print('COALINDIA columns:', len(row) if row else 0)
print('COALINDIA row:', row)
print()

# Check HDFCLIFE profit_loss
cursor = conn.execute('SELECT * FROM profit_loss WHERE company_id = "HDFCLIFE" AND period = "Mar 2024"')
row = cursor.fetchone()
print('HDFCLIFE columns:', len(row) if row else 0)
print('HDFCLIFE row:', row)
print()

# Check ICICIGI profit_loss
cursor = conn.execute('SELECT * FROM profit_loss WHERE company_id = "ICICIGI" AND period = "Mar 2024"')
row = cursor.fetchone()
print('ICICIGI columns:', len(row) if row else 0)
print('ICICIGI row:', row)

conn.close()
