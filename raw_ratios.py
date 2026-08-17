from src.database.connection import get_connection

def check_table(table_name, company_id):
    conn = get_connection()
    if conn is None:
        print("No connection")
        return
    try:
        cnt = conn.execute(f"SELECT COUNT(*) FROM {table_name} WHERE company_id = ?", (company_id.upper(),)).fetchone()[0]
        print(f"{table_name}: {cnt} rows for {company_id}")
        if cnt > 0:
            # Show columns
            cols = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
            col_names = [c[1] for c in cols]
            print(f"  Columns: {col_names}")
            # Fetch first row
            row = conn.execute(f"SELECT * FROM {table_name} WHERE company_id = ? LIMIT 1", (company_id.upper(),)).fetchone()
            if row:
                print("  First row:")
                for col, val in zip(col_names, row):
                    print(f"    {col}: {val}")
    except Exception as e:
        print(f"Error checking {table_name}: {e}")
    finally:
        conn.close()

def main():
    company_id = "UNIONBANK"
    check_table("financial_kpis", company_id)
    print()
    check_table("financial_ratios", company_id)
    print()
    # Also check companies table for roe_percentage column
    conn = get_connection()
    try:
        cols = conn.execute("PRAGMA table_info(companies)").fetchall()
        col_names = [c[1] for c in cols]
        print("companies columns:", col_names)
        # Check if roe_percentage exists and has value for UNIONBANK
        if 'roe_percentage' in col_names:
            row = conn.execute("SELECT roe_percentage FROM companies WHERE company_id = ?", (company_id.upper(),)).fetchone()
            if row:
                print(f"roe_percentage for {company_id}: {row[0]}")
    except Exception as e:
        print(f"Error checking companies: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()