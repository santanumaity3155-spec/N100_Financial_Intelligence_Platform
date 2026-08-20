from src.database.connection import get_connection

def main():
    conn = get_connection()
    if conn is None:
        print("No connection")
        return
    company_id = "UNIONBANK"
    cid = company_id.upper()
    # Get all profit_loss rows ordered by period
    rows = conn.execute("""
        SELECT period, sales, net_profit, operating_profit, opm_percentage, eps, dividend_payout, depreciation, interest
        FROM profit_loss
        WHERE company_id = ?
        ORDER BY
          CASE
            WHEN substr(period, -4) GLOB '[0-9][0-9][0-9][0-9]' THEN substr(period, -4)
            ELSE 0
          END,
          period
    """, (cid,)).fetchall()
    print(f"Profit/Loss rows for {company_id} (chronological):")
    for r in rows:
        print(f"  Period: {r[0]}, Sales: {r[1]}, Net Profit: {r[2]}, Op%: {r[4]}, EPS: {r[5]}, Div%: {r[6]}, Dep: {r[7]}, Int: {r[8]}")
    conn.close()

if __name__ == "__main__":
    main()