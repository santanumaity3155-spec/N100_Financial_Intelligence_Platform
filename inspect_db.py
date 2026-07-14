import sqlite3

conn = sqlite3.connect('data/database/n100.db')
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [t[0] for t in cursor.fetchall()]
print('Tables:', tables)

# Check balance_sheet columns
cursor.execute('PRAGMA table_info(balance_sheet)')
bs_cols = [c[1] for c in cursor.fetchall()]
print('\nBalance Sheet columns:', bs_cols)

# Check cash_flow columns
cursor.execute('PRAGMA table_info(cash_flow)')
cf_cols = [c[1] for c in cursor.fetchall()]
print('\nCash Flow columns:', cf_cols)

# Check market_cap columns
cursor.execute('PRAGMA table_info(market_cap)')
mc_cols = [c[1] for c in cursor.fetchall()]
print('\nMarket Cap columns:', mc_cols)

# Check profit_loss columns
cursor.execute('PRAGMA table_info(profit_loss)')
pl_cols = [c[1] for c in cursor.fetchall()]
print('\nProfit Loss columns:', pl_cols)

# Check companies columns
cursor.execute('PRAGMA table_info(companies)')
comp_cols = [c[1] for c in cursor.fetchall()]
print('\nCompanies columns:', comp_cols)

# Sample data from balance_sheet
cursor.execute('SELECT * FROM balance_sheet LIMIT 3')
rows = cursor.fetchall()
print('\nSample balance_sheet data:')
for row in rows:
    print(row)

# Sample data from cash_flow
cursor.execute('SELECT * FROM cash_flow LIMIT 3')
rows = cursor.fetchall()
print('\nSample cash_flow data:')
for row in rows:
    print(row)

conn.close()