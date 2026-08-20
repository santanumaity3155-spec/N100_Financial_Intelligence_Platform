import sqlite3

for db_path in ['data/database/n100.db', 'data/database/financial_data.db']:
    print(f"\n=== {db_path} ===")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print("Tables:", tables)
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        cols = cursor.fetchall()
        print(f"  {table}: {[c[1] for c in cols]}")
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        print(f"    count: {cursor.fetchone()[0]}")
    conn.close()
