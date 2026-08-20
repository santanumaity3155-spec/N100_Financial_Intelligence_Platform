from src.database.connection import get_connection

def main():
    conn = get_connection()
    if conn is None:
        print("No connection")
        return
    company_id = "UNIONBANK"
    cid = company_id.upper()

    print(f"=== Data for {company_id} ===")

    # 1. Profit and Loss
    print("\n1. Profit and Loss (latest year):")
    pl = conn.execute("""
        SELECT period, sales, operating_profit, net_profit, opm_percentage, eps, dividend_payout, depreciation, interest
        FROM profit_loss
        WHERE company_id = ?
        ORDER BY period DESC
        LIMIT 1
    """, (cid,)).fetchone()
    if pl:
        period, sales, op, net, opm, eps, div, dep, int_ = pl
        print(f"  Period: {period}")
        print(f"  Sales: {sales}")
        print(f"  Operating Profit: {op}")
        print(f"  Net Profit: {net}")
        print(f"  OPM%: {opm}")
        print(f"  EPS: {eps}")
        print(f"  Dividend Payout%: {div}")
        print(f"  Depreciation: {dep}")
        print(f"  Interest: {int_}")
    else:
        print("  No data")

    # 2. Balance Sheet (latest year)
    print("\n2. Balance Sheet (latest year):")
    bs = conn.execute("""
        SELECT period, share_capital, reserves, borrowings, total_assets, equity_capital, investments
        FROM balance_sheet
        WHERE company_id = ?
        ORDER BY period DESC
        LIMIT 1
    """, (cid,)).fetchone()
    if bs:
        period, share_cap, reserves, borrowings, total_assets, equity_cap, investments = bs
        print(f"  Period: {period}")
        print(f"  Share Capital: {share_cap}")
        print(f"  Reserves: {reserves}")
        print(f"  Borrowings: {borrowings}")
        print(f"  Total Assets: {total_assets}")
        print(f"  Equity Capital: {equity_cap}")
        print(f"  Investments: {investments}")
        # Compute equity if equity_capital is None
        if equity_cap is None and share_cap is not None and reserves is not None:
            equity = share_cap + reserves
            print(f"  Computed Equity (share_cap + reserves): {equity}")
        else:
            equity = equity_cap
    else:
        print("  No data")
        equity = None

    # 3. Cash Flow (latest year)
    print("\n3. Cash Flow (latest year):")
    cf = conn.execute("""
        SELECT period, free_cash_flow, cash_from_operating_activity
        FROM cash_flow
        WHERE company_id = ?
        ORDER BY period DESC
        LIMIT 1
    """, (cid,)).fetchone()
    if cf:
        period, fcf, cfo = cf
        print(f"  Period: {period}")
        print(f"  Free Cash Flow: {fcf}")
        print(f"  Cash from Operations: {cfo}")
    else:
        print("  No data")

    # 4. Ratios / KPIs (latest year)
    print("\n4. Financial KPIs (latest year):")
    kpi = conn.execute("""
        SELECT period, roce, roe, debt_to_equity, interest_coverage
        FROM financial_kpis
        WHERE company_id = ?
        ORDER BY period DESC
        LIMIT 1
    """, (cid,)).fetchone()
    if kpi:
        period, roce, roe, de, icr = kpi
        print(f"  Period: {period}")
        print(f"  ROCE: {roce}")
        print(f"  ROE: {roe}")
        print(f"  Debt/Equity: {de}")
        print(f"  Interest Coverage: {icr}")
    else:
        print("  No data in financial_kpis")
        # Try financial_ratios as fallback
        rat = conn.execute("""
            SELECT period, roe, roa, debt_to_equity, dividend_yield
            FROM financial_ratios
            WHERE company_id = ?
            ORDER BY period DESC
            LIMIT 1
        """, (cid,)).fetchone()
        if rat:
            period, roe, roa, de, dy = rat
            print(f"  Financial Ratios - Period: {period}")
            print(f"  ROE: {roe}")
            print(f"  ROA: {roa}")
            print(f"  Debt/Equity: {de}")
            print(f"  Dividend Yield: {dy}")
        else:
            print("  No data in financial_ratios either")

    # 5. Compute ROE from PL and BS if possible
    print("\n5. Computed ROE (Net Profit / Equity):")
    if pl and bs:
        net_profit = pl[3]  # net_profit
        equity = None
        if bs[6] is not None:  # equity_capital
            equity = bs[6]
        elif bs[1] is not None and bs[2] is not None:  # share_capital + reserves
            equity = bs[1] + bs[2]
        if equity is not None and equity != 0:
            computed_roe = net_profit / equity
            print(f"  Net Profit: {net_profit}")
            print(f"  Equity: {equity}")
            print(f"  Computed ROE: {computed_roe:.4f} ({computed_roe*100:.2f}%)")
        else:
            print("  Could not compute equity")
    else:
        print("  Missing PL or BS data")

    # 6. Compute ROCE approximation: EBIT / (Total Assets - Current Liabilities)
    # We don't have current liabilities, so we'll approximate using total_assets - total_liabilities + current_liabilities? Not possible.
    # Instead, we can compute ROCE as EBIT / (Shareholders' Equity + Long-term Debt)
    # We have borrowings as total debt? We'll assume borrowings is long-term debt for simplicity.
    print("\n6. Approximate ROCE (EBIT / (Equity + Long-term Debt)):")
    if pl and bs:
        ebit = pl[2]  # operating_profit
        equity = None
        if bs[6] is not None:
            equity = bs[6]
        elif bs[1] is not None and bs[2] is not None:
            equity = bs[1] + bs[2]
        long_term_debt = bs[4]  # borrowings column
        if equity is not None and long_term_debt is not None:
            denominator = equity + long_term_debt
            if denominator != 0:
                computed_roce = ebit / denominator
                print(f"  EBIT: {ebit}")
                print(f"  Equity: {equity}")
                print(f"  Long-term Debt (borrowings): {long_term_debt}")
                print(f"  Denominator (Equity + LTD): {denominator}")
                print(f"  Computed ROCE: {computed_roce:.4f} ({computed_roce*100:.2f}%)")
            else:
                print("  Denominator zero")
        else:
            print("  Missing equity or debt")
    else:
        print("  Missing PL or BS")

    conn.close()

if __name__ == "__main__":
    main()