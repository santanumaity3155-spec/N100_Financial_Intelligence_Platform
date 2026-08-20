from src.database.connection import get_connection
from src.nlp.pros_cons_generator import load_profit_loss, load_balance_sheet, load_cashflow_data, load_ratio_data

def debug_table(loader, name):
    conn = get_connection()
    df = loader(conn)
    conn.close()
    if df.empty:
        print(f"{name}: empty table")
        return
    print(f"{name}: {len(df)} rows")
    print(f"Columns: {df.columns.tolist()}")
    # Get unique company_ids
    if 'company_id' in df.columns:
        unique_ids = df['company_id'].dropna().unique()
        print(f"Unique company_ids count: {len(unique_ids)}")
        # Show first 10
        print(f"First 10: {sorted(unique_ids)[:10]}")
        # Check for our targets
        targets = ['UNIONBANK', 'SBIN', 'ULTRACEMCO', 'BAJAJFINSV']
        for t in targets:
            match = df[df['company_id'] == t.upper()]
            print(f"  {t}: {len(match)} rows")
    else:
        print("No company_id column")

def main():
    debug_table(load_profit_loss, "profit_loss")
    debug_table(load_balance_sheet, "balance_sheet")
    debug_table(load_cashflow_data, "cash_flow")
    debug_table(load_ratio_data, "ratios")

if __name__ == "__main__":
    main()