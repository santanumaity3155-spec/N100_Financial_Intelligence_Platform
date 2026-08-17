from src.database.connection import get_connection

def main():
    conn = get_connection()
    if conn is None:
        print("No connection")
        return
    company_id = "UNIONBANK"
    cid = company_id.upper()
    # Get balance_sheet rows for UNIONBANK ordered by period
    rows = conn.execute("""
        SELECT period, share_capital, reserves, borrowings, total_assets, equity_capital, investments
        FROM balance_sheet
        WHERE company_id = ?
        ORDER BY
          CASE
            WHEN substr(period, -4) GLOB '[0-9][0-9][0-9][0-9]' THEN substr(period, -4)
            ELSE 0
          END,
          period
    """, (cid,)).fetchall()
    print(f"Balance Sheet rows for {company_id} (chronological):")
    for r in rows:
        period, share_cap, reserves, borrowings, total_assets, equity_cap, investments = r
        equity = None
        if equity_cap is not None:
            equity = equity_cap
        elif share_cap is not None and reserves is not None:
            equity = share_cap + reserves
        print(f"  Period: {period}")
        print(f"    Share Capital: {share_cap}")
        print(f"    Reserves: {reserves}")
        print(f"    Borrowings: {borrowings}")
        print(f"    Total Assets: {total_assets}")
        print(f"    Equity Capital: {equity_cap}")
        print(f"    Computed Equity (share_cap+reserves): {equity}")
        print(f"    Investments: {investments}")
    conn.close()

if __name__ == "__main__":
    main()