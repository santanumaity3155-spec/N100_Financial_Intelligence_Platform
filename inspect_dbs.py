import sqlite3
import os
import glob

for db_path in glob.glob('**/*.db', recursive=True):
    size = os.path.getsize(db_path)
    print(f'DB: {db_path} | Size: {size} bytes')
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f'  Tables: {tables}')
        for table in tables:
            cursor.execute(f'SELECT COUNT(*) FROM {table}')
            count = cursor.fetchone()[0]
            print(f'    {table}: {count} rows')
            cursor.execute(f'PRAGMA table_info({table})')
            cols = [row[1] for row in cursor.fetchall()]
            print(f'    Columns: {cols}')
        conn.close()
    except Exception as e:
        print(f'  Error: {e}')
    print()
