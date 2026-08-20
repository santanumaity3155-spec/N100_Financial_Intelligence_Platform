from src.database.connection import get_connection

def main():
    conn = get_connection()
    if conn is None:
        print("No connection")
        return
    company_id = "UNIONBANK"
    cid = company_id.upper()
    # Get latest annual period from financial_ratios (excluding TTM)
    row = conn.execute("""
        SELECT period, roe, roa, debt_to_equity, dividend_yield
        FROM financial_ratios
        WHERE company_id = ?
        AND period <> 'TTM'
        ORDER BY
          CASE
            WHEN substr(period, -4) GLOB '[0-9][0-9][0-9][0-9]' THEN substr(period, -4)
            ELSE 0
          END DESC
        LIMIT 1
    """, (cid,)).fetchone()
    if row:
        period, roe, roa, de, dy = row
        print(f"Latest annual financial_ratios for {company_id}:")
        print(f"  Period: {period}")
        print(f"  ROE: {roe}")
        print(f"  ROA: {roa}")
        print(f"  Debt/Equity: {de}")
        print(f"  Dividend Yield: {dy}")
    else:
        print("No annual rows found")
    conn.close()

if __name__ == "__main__":
    main()