import sys
sys.path.insert(0, '.')

from src.database.connection import get_connection

def test_connection():
    conn = get_connection()
    print("Connection:", conn)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM companies")
    count = cursor.fetchone()[0]
    print(f"Number of companies: {count}")
    cursor.execute("SELECT company_id FROM companies LIMIT 5")
    companies = cursor.fetchall()
    print("First 5 companies:", [c[0] for c in companies])
    conn.close()

if __name__ == "__main__":
    test_connection()