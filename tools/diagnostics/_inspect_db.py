#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('data/database/n100.db')

companies = [
    'UNIONBANK',
    'BAJAJFINSV',
    'BOSCHLTD',
    'COALINDIA',
    'DIVISLAB',
    'DMART',
    'HDFCLIFE',
    'ICICIGI',
    'ICICIPRULI',
    'INDIGO',
    'IRCTC',
    'ITC',
    'MARUTI',
    'PNB',
]

for cid in companies:
    print(f"\n{'='*60}")
    print(f"COMPANY: {cid}")
    print(f"{'='*60}")
    
    # Check financial_kpis
    print(f"\n--- financial_kpis ---")
    cursor = conn.execute(
        'SELECT period, roe, roce, operating_margin, debt_to_equity, interest_coverage, free_cash_flow, dividend_yield, revenue_cagr, profit_cagr, eps_cagr FROM financial_kpis WHERE company_id = ? ORDER BY period',
        (cid,)
    )
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            print(row)
    else:
        print("NO DATA")
    
    # Check cash_flow
    print(f"\n--- cash_flow ---")
    cursor = conn.execute(
        'SELECT period, cash_from_operating_activity, cash_from_financing_activity, free_cash_flow, net_cash_flow FROM cash_flow WHERE company_id = ? ORDER BY period',
        (cid,)
    )
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            print(row)
    else:
        print("NO DATA")
    
    # Check balance_sheet
    print(f"\n--- balance_sheet ---")
    cursor = conn.execute(
        'SELECT period, borrowings, reserves, equity_capital, share_capital, investments, total_assets FROM balance_sheet WHERE company_id = ? ORDER BY period',
        (cid,)
    )
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            print(row)
    else:
        print("NO DATA")
    
    # Check profit_loss
    print(f"\n--- profit_loss ---")
    cursor = conn.execute(
        'SELECT period, sales, operating_profit, net_profit, opm_percentage, eps, dividend_payout, depreciation, interest FROM profit_loss WHERE company_id = ? ORDER BY period',
        (cid,)
    )
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            print(row)
    else:
        print("NO DATA")
    
    # Check market_cap
    print(f"\n--- market_cap ---")
    cursor = conn.execute(
        'SELECT period, dividend_yield FROM market_cap WHERE company_id = ? ORDER BY period',
        (cid,)
    )
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            print(row)
    else:
        print("NO DATA")

conn.close()
