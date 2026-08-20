import pandas as pd
import sqlite3
conn = sqlite3.connect('data/database/n100.db')
df = pd.read_sql_query('SELECT period, operating_activity, investing_activity, financing_activity FROM cash_flow WHERE company_id = "ABB" ORDER BY period', conn)
print('=== ABB cash_flow ===')
print(df)
df2 = pd.read_sql_query('SELECT period, sales, net_profit FROM profit_loss WHERE company_id = "ABB" ORDER BY period', conn)
print('\n=== ABB profit_loss ===')
print(df2)
conn.close()
