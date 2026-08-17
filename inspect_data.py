import pandas as pd
from src.database.connection import get_connection
from src.nlp.pros_cons_generator import (
    load_companies, load_profit_loss, load_balance_sheet, load_cashflow_data,
    load_ratio_data, load_market_cap, load_analysis_data, load_sectors,
    METRIC_SOURCES, _DERIVED_METRICS, parse_period, get_company_context
)

def inspect_company(company_id):
    print(f"\n{'='*60}")
    print(f"Inspecting company: {company_id}")
    print('='*60)

    conn = get_connection()
    if conn is None:
        print("ERROR: No database connection")
        return

    # Load all data
    data = {
        "companies": load_companies(conn),
        "sectors": load_sectors(conn),
        "profit_loss": load_profit_loss(conn),
        "balance_sheet": load_balance_sheet(conn),
        "cash_flow": load_cashflow_data(conn),
        "ratios": load_ratio_data(conn),
        "market_cap": load_market_cap(conn),
        "analysis": load_analysis_data(conn),
    }

    # Check companies table
    companies_df = data["companies"]
    if not companies_df.empty:
        match = companies_df[companies_df["company_id"] == company_id.upper()]
        if not match.empty:
            print("\nCompanies table row:")
            print(match.to_string())
        else:
            print("\nCompany not found in companies table")

    # Check sectors
    sectors_df = data["sectors"]
    if not sectors_df.empty:
        match = sectors_df[sectors_df["company_id"] == company_id.upper()]
        if not match.empty:
            print("\nSectors table row:")
            print(match[["company_id", "broad_sector", "sub_sector"]].to_string())

    # Check each period-based table for data
    for table_name in ["profit_loss", "balance_sheet", "cash_flow", "ratios", "market_cap", "analysis"]:
        df = data[table_name]
        if df.empty:
            print(f"\n{table_name}: No data")
            continue
        match = df[df["company_id"] == company_id.upper()]
        if match.empty:
            print(f"\n{table_name}: No data for company")
        else:
            print(f"\n{table_name}: {len(match)} rows")
            # Show periods and a few columns
            if "period" in match.columns:
                periods = match["period"].tolist()
                print(f"  Periods: {periods[:10]}{'...' if len(periods)>10 else ''}")
            # Show some key columns if they exist
            key_cols = []
            if table_name == "profit_loss":
                key_cols = ["sales", "net_profit", "operating_profit", "opm_percentage", "eps"]
            elif table_name == "balance_sheet":
                key_cols = ["borrowings", "total_assets", "net_debt"]
            elif table_name == "cash_flow":
                key_cols = ["free_cash_flow", "cash_from_operating_activity"]
            elif table_name == "ratios":
                key_cols = ["roe", "roce", "debt_to_equity", "interest_coverage", "free_cash_flow"]
            elif table_name == "market_cap":
                key_cols = ["dividend_yield"]
            elif table_name == "analysis":
                key_cols = ["compounded_sales_growth", "compounded_profit_growth", "roe"]

            # Filter to existing columns
            existing_key_cols = [c for c in key_cols if c in match.columns]
            if existing_key_cols:
                # Show first row values
                row = match.iloc[0]
                vals = {c: row[c] for c in existing_key_cols}
                print(f"  Sample values (first row): {vals}")

    # Build company context and show latest and history
    print("\n--- CompanyContext ---")
    context = get_company_context(company_id, conn=conn, data=data)
    print(f"Company ID: {context.company_id}")
    print(f"Company Name: {context.company_name}")
    print(f"Sector: {context.sector}")
    print(f"Is Financial: {context.is_financial}")
    print(f"Latest Year: {context.latest_year}")
    print(f"History Years: {context.history_years}")
    print(f"Latest Metrics: {context.latest}")
    print(f"Trailing Metrics: {context.trailing}")
    # Show history lengths
    for metric in ["roe", "roce", "debt_to_equity", "interest_coverage", "free_cash_flow", "revenue", "net_profit"]:
        if metric in context.history:
            print(f"  History {metric}: {len(context.history[metric])} values -> {context.history[metric]}")

    conn.close()

if __name__ == "__main__":
    # List of companies to inspect
    companies_to_inspect = [
        "UNIONBANK",   # missing Pro
        "SBIN",        # missing both
        "ULTRACEMCO",  # missing both
        "BAJAJFINSV",  # missing Con only
        "RELIANCE",    # a company that should have signals (spot check)
    ]

    for cid in companies_to_inspect:
        inspect_company(cid)