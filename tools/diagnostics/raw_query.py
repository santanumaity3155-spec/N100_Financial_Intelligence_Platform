from src.database.connection import get_connection

def query_table(conn, table_name, company_id=None):
    if company_id:
        sql = f"SELECT COUNT(*) as cnt FROM \"{table_name}\" WHERE company_id = ?"
        params = (company_id.upper(),)
    else:
        sql = f"SELECT COUNT(*) as cnt FROM \"{table_name}\""
        params = ()
    try:
        cursor = conn.execute(sql, params)
        row = cursor.fetchone()
        return row[0] if row else 0
    except Exception as e:
        return f"Error: {e}"

def main():
    conn = get_connection()
    if conn is None:
        print("No connection")
        return
    tables = ["companies", "profit_loss", "balance_sheet", "cash_flow", "financial_kpis", "financial_ratios", "market_cap", "analysis"]
    company_ids = ["UNIONBANK", "SBIN", "ULTRACEMCO", "BAJAJFINSV"]
    print("Row counts per table:")
    for t in tables:
        cnt = query_table(conn, t)
        print(f"  {t}: {cnt}")
    print("\nRow counts per company in profit_loss:")
    for cid in company_ids:
        cnt = query_table(conn, "profit_loss", cid)
        print(f"  {cid}: {cnt}")
    print("\nRow counts per company in balance_sheet:")
    for cid in company_ids:
        cnt = query_table(conn, "balance_sheet", cid)
        print(f"  {cid}: {cnt}")
    print("\nRow counts per company in cash_flow:")
    for cid in company_ids:
        cnt = query_table(conn, "cash_flow", cid)
        print(f"  {cid}: {cnt}")
    print("\nRow counts per company in financial_kpis:")
    for cid in company_ids:
        cnt = query_table(conn, "financial_kpis", cid)
        print(f"  {cid}: {cnt}")
    conn.close()

if __name__ == "__main__":
    main()