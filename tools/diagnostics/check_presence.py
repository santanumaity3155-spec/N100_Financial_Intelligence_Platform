import pandas as pd
from src.database.connection import get_connection
from src.nlp.pros_cons_generator import load_companies, load_profit_loss, load_balance_sheet, load_cashflow_data, load_ratio_data, load_market_cap, load_analysis_data

def check_table_for_company(table_loader, company_id, table_name):
    conn = get_connection()
    df = table_loader(conn)
    conn.close()
    if df.empty:
        print(f"{table_name}: No data at all")
        return False
    match = df[df["company_id"] == company_id.upper()]
    if match.empty:
        print(f"{table_name}: No data for {company_id}")
        return False
    else:
        print(f"{table_name}: {len(match)} rows for {company_id}")
        if "period" in match.columns:
            print(f"  Periods: {match['period'].tolist()[:5]}")
        return True

def main():
    company_ids = ["UNIONBANK", "SBIN", "ULTRACEMCO", "BAJAJFINSV"]
    loaders = [
        ("companies", load_companies),
        ("profit_loss", load_profit_loss),
        ("balance_sheet", load_balance_sheet),
        ("cash_flow", load_cashflow_data),
        ("ratios", load_ratio_data),
        ("market_cap", load_market_cap),
        ("analysis", load_analysis_data),
    ]
    for cid in company_ids:
        print(f"\n=== {cid} ===")
        for table_name, loader in loaders:
            check_table_for_company(loader, cid, table_name)

if __name__ == "__main__":
    main()