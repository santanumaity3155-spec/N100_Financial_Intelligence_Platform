"""Diagnostic: run the analytics cashflow_intelligence engine on real data."""
import sys
from pathlib import Path

import pandas as pd

from src.database.connection import get_connection
from src.analytics.cashflow_intelligence import (
    compute_cfo_quality,
    compute_capex_intensity,
    compute_fcf_cagr_5yr,
    compute_fcf_conversion,
    compute_distress_flag,
    compute_deleveraging_flag,
    compute_capital_allocation_label,
)

conn = get_connection()
for cid in ["TCS", "AXISBANK", "HDFCBANK", "ATGL", "SBIN", "RELIANCE"]:
    print("=" * 70)
    cf = pd.read_sql_query("SELECT period, operating_activity, investing_activity, financing_activity FROM cash_flow WHERE company_id=? ORDER BY period", conn, params=(cid,))
    pl = pd.read_sql_query("SELECT period, sales, net_profit FROM profit_loss WHERE company_id=? ORDER BY period", conn, params=(cid,))
    bs = pd.read_sql_query("SELECT period, borrowings FROM balance_sheet WHERE company_id=? ORDER BY period", conn, params=(cid,))
    print(cid, "cf rows:", len(cf), "pl rows:", len(pl), "bs rows:", len(bs))
    print("cf periods sample:", cf["period"].tolist()[:4], "...", cf["period"].tolist()[-3:])
    try:
        print("  cfo_quality:", compute_cfo_quality(cf, pl))
        print("  capex_intensity:", compute_capex_intensity(cf, pl))
        print("  fcf_cagr_5yr:", compute_fcf_cagr_5yr(cf))
        print("  fcf_conversion:", compute_fcf_conversion(cf, pl))
        print("  distress:", compute_distress_flag(cf))
        print("  deleveraging:", compute_deleveraging_flag(cf, bs))
        print("  capital_allocation:", compute_capital_allocation_label(cf, pl))
    except Exception as e:
        import traceback
        traceback.print_exc()

conn.close()
