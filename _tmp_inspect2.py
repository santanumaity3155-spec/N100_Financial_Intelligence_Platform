import sys
sys.path.insert(0, ".")
from src.database.connection import get_connection
import pandas as pd
import io

conn = get_connection()
buf = io.StringIO()

# Period format
buf.write("=== PERIOD FORMATS ===\n")
pl = pd.read_sql("SELECT DISTINCT period FROM profit_loss", conn)
buf.write(str(sorted(pl['period'].tolist())) + "\n")

# cash_flow free_cash_flow
buf.write("\n=== CASH FLOW: free_cash_flow ===\n")
cf_all = pd.read_sql("SELECT free_cash_flow FROM cash_flow", conn)
buf.write("Non-null free_cash_flow: %d / %d\n" % (cf_all['free_cash_flow'].notna().sum(), len(cf_all)))
cf_tcs = pd.read_sql("SELECT period, free_cash_flow FROM cash_flow WHERE company_id='TCS' ORDER BY period", conn)
buf.write("TCS FCF:\n" + cf_tcs.to_string()[:500] + "\n")

# balance_sheet: borrowings, investments, net_debt for TCS and AXISBANK
buf.write("\n=== BALANCE SHEET: borrowings, investments for TCS ===\n")
bs = pd.read_sql("SELECT period, borrowings, investments, total_assets FROM balance_sheet WHERE company_id='TCS' ORDER BY period", conn)
buf.write(bs.to_string()[:600] + "\n")

buf.write("\n=== BALANCE SHEET: borrowings, investments for AXISBANK ===\n")
bs2 = pd.read_sql("SELECT period, borrowings, investments, total_assets FROM balance_sheet WHERE company_id='AXISBANK' ORDER BY period", conn)
buf.write(bs2.to_string()[:600] + "\n")

# financial_kpis: roce, interest_coverage, debt_to_equity for TCS
buf.write("\n=== financial_kpis: roce, icr, d/e for TCS ===\n")
kpi_tcs = pd.read_sql("SELECT period, roce, interest_coverage, debt_to_equity FROM financial_kpis WHERE company_id='TCS' ORDER BY period", conn)
buf.write(kpi_tcs.to_string()[:600] + "\n")

# ROCE scale
buf.write("\n=== ROCE scale (all non-null) ===\n")
roce_vals = pd.read_sql("SELECT roce FROM financial_kpis WHERE roce IS NOT NULL AND roce != 0", conn)
buf.write("min: %s max: %s mean: %s count: %d\n" % (roce_vals['roce'].min(), roce_vals['roce'].max(), roce_vals['roce'].mean(), len(roce_vals)))

# revenue_cagr scale
buf.write("\n=== revenue_cagr scale ===\n")
rc = pd.read_sql("SELECT revenue_cagr FROM financial_kpis WHERE revenue_cagr IS NOT NULL", conn)
buf.write("min: %s max: %s count: %d\n" % (rc['revenue_cagr'].min(), rc['revenue_cagr'].max(), len(rc)))

# profit_loss: opm, net_profit, sales, dividend_payout, eps for TCS
buf.write("\n=== profit_loss: sales, opm, net_profit, dividend_payout, eps for TCS ===\n")
pl2 = pd.read_sql("SELECT period, sales, opm_percentage, net_profit, dividend_payout, eps FROM profit_loss WHERE company_id='TCS' ORDER BY period", conn)
buf.write(pl2.to_string()[:1200] + "\n")

# dividend_payout non-null count
buf.write("\n=== dividend_payout non-null count ===\n")
dp_all = pd.read_sql("SELECT COUNT(*) as total, SUM(CASE WHEN dividend_payout IS NOT NULL THEN 1 ELSE 0 END) as nonnull FROM profit_loss", conn)
buf.write("Total PL rows: %d, Non-null dividend_payout: %d\n" % (dp_all['total'][0], dp_all['nonnull'][0]))

# Companies table schema
buf.write("\n=== companies table: roce_percentage, roe_percentage ===\n")
comp = pd.read_sql("SELECT company_id, roce_percentage, roe_percentage, sector FROM companies LIMIT 5", conn)
buf.write(comp.to_string() + "\n")

# Rows per company
buf.write("\n=== ROW COUNTS per company ===\n")
for cid in ["TCS", "AXISBANK", "HDFCBANK"]:
    cnt = pd.read_sql("SELECT COUNT(*) as c FROM financial_kpis WHERE company_id='%s'" % cid, conn)['c'][0]
    cnt2 = pd.read_sql("SELECT COUNT(*) as c FROM profit_loss WHERE company_id='%s'" % cid, conn)['c'][0]
    cnt3 = pd.read_sql("SELECT COUNT(*) as c FROM balance_sheet WHERE company_id='%s'" % cid, conn)['c'][0]
    cnt4 = pd.read_sql("SELECT COUNT(*) as c FROM cash_flow WHERE company_id='%s'" % cid, conn)['c'][0]
    buf.write("%s: kpi=%d, pl=%d, bs=%d, cf=%d\n" % (cid, cnt, cnt2, cnt3, cnt4))

conn.close()
out = open("inspect_result.txt", "w")
out.write(buf.getvalue())
out.close()
print("Done")
