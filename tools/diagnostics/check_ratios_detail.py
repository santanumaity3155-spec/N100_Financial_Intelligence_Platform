from src.database.connection import get_connection

def main():
    conn = get_connection()
    if conn is None:
        print("No connection")
        return
    company_id = "UNIONBANK"
    cid = company_id.upper()

    # Check exact match
    cnt = conn.execute("SELECT COUNT(*) FROM financial_ratios WHERE company_id = ?", (cid,)).fetchone()[0]
    print(f"Exact match '{cid}': {cnt} rows")
    # Check like
    cnt_like = conn.execute("SELECT COUNT(*) FROM financial_ratios WHERE company_id LIKE ?", (f"%{cid}%",)).fetchone()[0]
    print(f"Like '%{cid}%': {cnt_like} rows")
    # List distinct company_ids that contain unionbank
    rows = conn.execute("SELECT DISTINCT company_id FROM financial_ratios WHERE company_id LIKE '%UNION%'").fetchall()
    print("Distinct company_ids containing UNION:", rows)
    # If our exact not found, show what's there
    if cnt == 0:
        rows = conn.execute("SELECT company_id FROM financial_ratios LIMIT 10").fetchall()
        print("First 10 company_ids in financial_ratios:", [r[0] for r in rows])
    # Show periods for our company if any
    if cnt > 0:
        periods = conn.execute("SELECT period FROM financial_ratios WHERE company_id = ? ORDER BY period", (cid,)).fetchall()
        print(f"Periods for {cid}:", [p[0] for p in periods])
    else:
        # Try to find any row that might be ours with different formatting
        rows = conn.execute("SELECT company_id, period FROM financial_ratios WHERE company_id LIKE '%UNIONBANK%'").fetchall()
        if rows:
            print("Rows with LIKE '%UNIONBANK%':")
            for r in rows:
                print(f"  company_id='{r[0]}', period='{r[1]}'")
        else:
            print("No rows with LIKE '%UNIONBANK%'")
    conn.close()

if __name__ == "__main__":
    main()