import sqlite3

conn = sqlite3.connect('data/database/n100.db')
cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='peer_percentiles'")
result = cursor.fetchone()
print('peer_percentiles table exists:', result is not None)

if result:
    cursor = conn.execute('PRAGMA table_info(peer_percentiles)')
    cols = [row[1] for row in cursor.fetchall()]
    print('Columns:', cols)
    
    cursor = conn.execute('SELECT COUNT(*) FROM peer_percentiles')
    count = cursor.fetchone()[0]
    print('Total records:', count)

conn.close()