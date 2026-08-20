from src.database.connection import get_connection

def main():
    conn = get_connection()
    if conn is None:
        print("No connection")
        return
    company_id = "UNIONBANK"
    # Get column names
    try:
        cols = conn.execute(f"PRAGMA table_info('balance_sheet')").fetchall()
        col_names = [c[1] for c in cols]
        print("balance_sheet columns:", col_names)
    except Exception as e:
        print(f"Error getting columns: {e}")
    # Fetch rows for company
    try:
        rows = conn.execute(f"SELECT * FROM balance_sheet WHERE company_id = ?", (company_id.upper(),)).fetchall()
        print(f"Number of rows: {len(rows)}")
        if rows:
            print("First row as dict:")
            row_dict = dict(zip(col_names, rows[0]))
            for k, v in row_dict.items():
                print(f"  {k}: {v}")
    except Exception as e:
        print(f"Error fetching rows: {e}")
    conn.close()

if __name__ == "__main__":
    main()