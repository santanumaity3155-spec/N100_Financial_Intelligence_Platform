import pandas as pd
from src.database.connection import get_connection
from src.nlp.pros_cons_generator import load_companies, load_profit_loss, load_balance_sheet, load_cashflow_data, load_ratio_data, load_market_cap, load_analysis_data

def examine_table(loader, name, company_id):
    conn = get_connection()
    df = loader(conn)
    conn.close()
    if df.empty:
        print(f"{name}: No data")
        return
    match = df[df["company_id"] == company_id.upper()]
    if match.empty:
        print(f"{name}: No data for {company_id}")
        return
    print(f"{name}: {len(match)} rows")
    print(f"Columns: {match.columns.tolist()}")
    # Show first row values
    if not match.empty:
        row = match.iloc[0]
        print("First row:")
        for col in match.columns:
            print(f"  {col}: {row[col]}")
    # Show unique periods
    if "period" in match.columns:
        periods = match["period"].tolist()
        print(f"Periods: {periods}")

def main():
    company_id = "UNIONBANK"
    print(f"=== Examining {company_id} ===")
    examine_table(load_profit_loss, "profit_loss", company_id)
    print()
    examine_table(load_balance_sheet, "balance_sheet", company_id)
    print()
    examine_table(load_cashflow_data, "cash_flow", company_id)
    print()
    examine_table(load_ratio_data, "ratios", company_id)
    print()
    examine_table(load_market_cap, "market_cap", company_id)
    print()
    examine_table(load_analysis_data, "analysis", company_id)

if __name__ == "__main__":
    main()