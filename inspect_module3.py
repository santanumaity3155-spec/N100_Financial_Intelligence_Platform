import sqlite3
from src.database.connection import get_connection
from datetime import datetime

def parse_period(period_str):
    """Convert period string like 'Mar 2024' to datetime object for comparison."""
    try:
        return datetime.strptime(period_str, '%b %Y')
    except ValueError:
        # If parsing fails, return a very old date so it won't be selected as latest
        return datetime(1900, 1, 1)

def get_latest_period(conn, company_id):
    """Get the latest period for a company from cash_flow table."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT period FROM cash_flow
        WHERE company_id = ?
    """, (company_id,))
    rows = cursor.fetchall()
    if not rows:
        return None
    # Convert to datetime for comparison, keep the original string
    periods_with_date = [(parse_period(period[0]), period[0]) for period in rows]
    # Sort by datetime descending and return the latest period string
    periods_with_date.sort(key=lambda x: x[0], reverse=True)
    return periods_with_date[0][1]

def fetch_latest_data(conn, company_id, period):
    """Fetch latest cash flow, profit loss, and balance sheet data for a company and period."""
    cursor = conn.cursor()

    # Cash flow data
    cursor.execute("""
        SELECT * FROM cash_flow
        WHERE company_id = ? AND period = ?
    """, (company_id, period))
    cf_row = cursor.fetchone()
    if cf_row:
        # Get column names
        cursor.execute("PRAGMA table_info(cash_flow);")
        cf_columns = [desc[1] for desc in cursor.fetchall()]
        cf_data = dict(zip(cf_columns, cf_row))
    else:
        cf_data = {}

    # Profit loss data
    cursor.execute("""
        SELECT * FROM profit_loss
        WHERE company_id = ? AND period = ?
    """, (company_id, period))
    pl_row = cursor.fetchone()
    if pl_row:
        cursor.execute("PRAGMA table_info(profit_loss);")
        pl_columns = [desc[1] for desc in cursor.fetchall()]
        pl_data = dict(zip(pl_columns, pl_row))
    else:
        pl_data = {}

    # Balance sheet data
    cursor.execute("""
        SELECT * FROM balance_sheet
        WHERE company_id = ? AND period = ?
    """, (company_id, period))
    bs_row = cursor.fetchone()
    if bs_row:
        cursor.execute("PRAGMA table_info(balance_sheet);")
        bs_columns = [desc[1] for desc in cursor.fetchall()]
        bs_data = dict(zip(bs_columns, bs_row))
    else:
        bs_data = {}

    return cf_data, pl_data, bs_data

def get_cfo(cf_data):
    """Get cash from operating activity, trying cash_from_operating_activity first, then operating_activity."""
    # Try cash_from_operating_activity
    cfo = cf_data.get('cash_from_operating_activity')
    if cfo is not None and not (isinstance(cfo, float) and pd.isna(cfo)):
        return cfo
    # Fallback to operating_activity
    cfo = cf_data.get('operating_activity')
    if cfo is not None and not (isinstance(cfo, float) and pd.isna(cfo)):
        return cfo
    return None

def get_cfi(cf_data):
    """Get cash from investing activity."""
    cfi = cf_data.get('cash_from_investing_activity')
    if cfi is not None and not (isinstance(cfi, float) and pd.isna(cfi)):
        return cfi
    cfi = cf_data.get('investing_activity')
    if cfi is not None and not (isinstance(cfi, float) and pd.isna(cfi)):
        return cfi
    return None

def get_cff(cf_data):
    """Get cash from financing activity."""
    cff = cf_data.get('cash_from_financing_activity')
    if cff is not None and not (isinstance(cff, float) and pd.isna(cff)):
        return cff
    cff = cf_data.get('financing_activity')
    if cff is not None and not (isinstance(cff, float) and pd.isna(cff)):
        return cff
    return None

def get_sales(pl_data):
    """Get sales from profit loss."""
    return pl_data.get('sales')

def get_net_profit(pl_data):
    """Get net profit (PAT) from profit loss."""
    return pl_data.get('net_profit')

def get_borrowings(bs_data):
    """Get borrowings from balance sheet."""
    return bs_data.get('borrowings')

if __name__ == "__main__":
    import pandas as pd  # For checking NaN

    conn = get_connection()
    try:
        # Get all companies
        cursor = conn.cursor()
        cursor.execute("SELECT company_id, sector FROM companies")
        companies = cursor.fetchall()
        print(f"Total companies: {len(companies)}")

        # Check a few companies
        for i, (company_id, sector) in enumerate(companies[:5]):
            print(f"\n{company_id} ({sector}):")
            latest_period = get_latest_period(conn, company_id)
            print(f"  Latest period: {latest_period}")
            if latest_period:
                cf_data, pl_data, bs_data = fetch_latest_data(conn, company_id, latest_period)
                cfo = get_cfo(cf_data)
                cfi = get_cfi(cf_data)
                cff = get_cff(cf_data)
                sales = get_sales(pl_data)
                net_profit = get_net_profit(pl_data)
                borrowings = get_borrowings(bs_data)
                print(f"  CFO: {cfo}")
                print(f"  CFI: {cfi}")
                print(f"  CFF: {cff}")
                print(f"  Sales: {sales}")
                print(f"  Net Profit: {net_profit}")
                print(f"  Borrowings: {borrowings}")
    finally:
        pass