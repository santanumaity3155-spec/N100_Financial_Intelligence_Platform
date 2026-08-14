import sys
sys.path.insert(0, ".")
from src.database.connection import get_connection
import pandas as pd
import io

conn = get_connection()
buf = io.StringIO()

# Check OPM for various companies
buf.write("=== OPM percentage sample ===\n")
for cid in ["TCS", "AXISBANK", "HDFCBANK", "INFY", "KOTAKBANK", "LT", "HINDUNILVR"]:
    df = pd.read_sql("SELECT period, opm_percentage FROM profit_loss WHERE company_id='%s'" % cid, conn)
    if not df.empty:
        opm_vals = df['opm_percentage'].dropna().tolist()
        buf.write("%s: %s\n" % (cid, opm_vals[:5]))

# Check cash flow columns
buf.write("\n=== Cash flow columns ===\n")
cf_cols = pd.read_sql("PRAGMA table_info(cash_flow)", conn)
buf.write(str(cf_cols[['name']].to_string()) + "\n")
cf_sample = pd.read_sql("SELECT * FROM cash_flow WHERE company_id='TCS' ORDER BY period LIMIT 2", conn)
buf.write("\nTCS cash_flow sample:\n")
buf.write(cf_sample.to_string()[:800] + "\n")

# Check financial_kpis columns
buf.write("\n=== financial_kpis columns check ===\n")
kpi_cols = pd.read_sql("PRAGMA table_info(financial_kpis)", conn)
names = kpi_cols['name'].tolist()
buf.write("Has net_debt: %s, Has ebitda: %s\n" % ("net_debt" in names, "ebitda" in names))
buf.write("Has dividend_payout: %s\n" % ("dividend_payout" in names))

# Companies with low ICR (non-financial)
buf.write("\n=== Companies with ICR < 2.0 (non-financial) ===\n")
bs_df = pd.read_sql("SELECT company_id, sub_sector FROM sectors", conn)
fin_subs = ["Private Banks","Public Sector Banks","Consumer Finance","Speciality Finance","Life Insurance","General Insurance","Diversified Financials","Financial Services","Asset Management","NBFC"]
fin_ids = set(bs_df[bs_df['sub_sector'].isin(fin_subs)]['company_id'])
kpi_low = pd.read_sql("SELECT company_id, interest_coverage FROM financial_kpis WHERE interest_coverage IS NOT NULL AND interest_coverage < 2.0 ORDER BY interest_coverage", conn)
non_fin_low = kpi_low[~kpi_low['company_id'].isin(fin_ids)]
buf.write("Non-financial with ICR < 2: %s\n" % non_fin_low['company_id'].tolist())

# Companies with dividend_payout > 100
buf.write("\n=== Companies with dividend_payout > 100 ===\n")
dp = pd.read_sql("SELECT DISTINCT company_id, MAX(dividend_payout) as max_dp FROM profit_loss WHERE dividend_payout IS NOT NULL AND dividend_payout > 100 GROUP BY company_id ORDER BY max_dp DESC", conn)
buf.write(dp.to_string()[:500] + "\n")

# Companies with negative net_profit in latest year
buf.write("\n=== Companies with negative net_profit (latest) ===\n")
np_df = pd.read_sql("SELECT company_id, net_profit FROM profit_loss WHERE net_profit IS NOT NULL AND net_profit < 0 ORDER BY net_profit LIMIT 20", conn)
buf.write("Count: %d\n" % len(np_df))
buf.write(np_df.to_string()[:800] + "\n")

conn.close()
out = open("data_detail.txt", "w")
out.write(buf.getvalue())
out.close()
print("Done")
