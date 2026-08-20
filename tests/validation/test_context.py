from src.database.connection import get_connection
from src.nlp.pros_cons_generator import get_company_context

def main():
    conn = get_connection()
    if conn is None:
        print("No connection")
        return
    company_id = "UNIONBANK"
    context = get_company_context(company_id, conn=conn)
    print(f"Context for {company_id}:")
    print(f"  Company ID: {context.company_id}")
    print(f"  Latest Year: {context.latest_year}")
    print(f"  History Years: {len(context.history_years)}")
    print(f"  Latest Metrics:")
    for metric in ["roe", "roce", "debt_to_equity", "interest_coverage", "revenue", "net_profit", "opm", "eps"]:
        val = context.latest.get(metric)
        print(f"    {metric}: {val}")
    # Also compute expected ROE from PL and BS
    print("\n  Expected ROE from PL/BS:")
    # Fetch latest PL and BS
    pl = conn.execute("""
        SELECT net_profit FROM profit_loss
        WHERE company_id = ?
        ORDER BY
          CASE
            WHEN substr(period, -4) GLOB '[0-9][0-9][0-9][0-9]' THEN substr(period, -4)
            ELSE 0
          END DESC, period
        LIMIT 1
    """, (company_id.upper(),)).fetchone()
    bs = conn.execute("""
        SELECT share_capital, reserves FROM balance_sheet
        WHERE company_id = ?
        ORDER BY
          CASE
            WHEN substr(period, -4) GLOB '[0-9][0-9][0-9][0-9]' THEN substr(period, -4)
            ELSE 0
          END DESC, period
        LIMIT 1
    """, (company_id.upper(),)).fetchone()
    if pl and bs:
        net_profit = pl[0]
        share_cap, reserves = bs[0], bs[1]
        equity = None
        if share_cap is not None and reserves is not None:
            equity = share_cap + reserves
        if equity is not None and equity != 0:
            roe = net_profit / equity
            print(f"    Net Profit: {net_profit}")
            print(f"    Equity: {equity}")
            print(f"    ROE: {roe:.4f} ({roe*100:.2f}%)")
        else:
            print("    Could not compute equity")
    else:
        print("    Missing PL or BS data")
    conn.close()

if __name__ == "__main__":
    main()