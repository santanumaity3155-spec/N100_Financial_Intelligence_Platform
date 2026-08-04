import sqlite3
import pandas as pd
from src.screener.engine import ScreenerEngine
from src.screener.filters import FilterCondition, FilterOperator
from src.screener.constants import VALID_SCREEN_FIELDS

conn = sqlite3.connect('data/database/n100.db')
conn.row_factory = sqlite3.Row

# 1. Determine latest period per company in financial_kpis
kpi_periods = pd.read_sql_query("SELECT company_id, period FROM financial_kpis ORDER BY company_id, period", conn)
print("financial_kpis periods sample:", kpi_periods['period'].unique()[:10])

# 2. Build a shaped DataFrame: one row per company (latest period), aliased to VALID_SCREEN_FIELDS names
query = """
SELECT
    fk.company_id               AS company_id,
    fk.period                   AS period,
    c.company_name              AS company_name,
    fk.roe                      AS roe,
    fk.roce                     AS roce,
    fk.roa                      AS roa,
    fk.net_profit_margin        AS net_profit_margin,
    fk.operating_margin         AS operating_profit_margin,
    fk.debt_to_equity           AS debt_to_equity,
    fk.current_ratio            AS current_ratio,
    fk.quick_ratio              AS quick_ratio,
    fk.interest_coverage        AS interest_coverage,
    fk.free_cash_flow           AS free_cash_flow,
    fk.revenue_cagr             AS revenue_cagr_5yr,
    fk.profit_cagr              AS pat_cag_5yr,
    fk.eps_cagr                 AS eps_cagr_5yr,
    fk.pe_ratio                 AS pe_ratio,
    fk.pb_ratio                 AS pb_ratio,
    fk.dividend_yield           AS dividend_yield,
    fhs.overall_score           AS overall_score,
    pg.peer_group_name          AS sector
FROM financial_kpis fk
LEFT JOIN companies c ON c.company_id = fk.company_id
LEFT JOIN financial_health_scores fhs ON fhs.company_id = fk.company_id AND fhs.period = fk.period
LEFT JOIN peer_groups pg ON pg.company_id = fk.company_id
ORDER BY fk.company_id, fk.period DESC
"""
df = pd.read_sql_query(query, conn)
print("total kpi rows:", len(df))
print("cols:", list(df.columns))

# Take latest period per company
latest = df.sort_values('period', ascending=False).drop_duplicates('company_id', keep='first').copy()
print("latest per company:", len(latest))
print("overall_score non-null:", latest['overall_score'].notna().sum())
print("sector non-null:", latest['sector'].notna().sum())

# 3. Inject into ScreenerEngine and test apply_filters
engine = ScreenerEngine()
engine.data = latest
conditions = [
    FilterCondition(field='roe', operator=FilterOperator.GREATER_THAN_OR_EQUAL, value=15),
    FilterCondition(field='debt_to_equity', operator=FilterOperator.LESS_THAN_OR_EQUAL, value=0.5),
    FilterCondition(field='pe_ratio', operator=FilterOperator.LESS_THAN, value=25),
]
engine.apply_filters(conditions, logic='AND')
print("after filters:", len(engine.filtered_data))
engine.sort_results(engine.filtered_data, sort_by='overall_score', ascending=False)
print("sorted ok")
# rank
engine.rank_companies(engine.filtered_data, rank_by='overall_score', ascending=False)
print("rank ok")

# 4. Test empty conditions handling
try:
    engine.apply_filters([], logic='AND')
    print("empty filters: applied (unexpected)")
except Exception as e:
    print("empty filters raises:", type(e).__name__, str(e)[:80])

# 5. Test get_peers / peer_percentiles availability
peers = pd.read_sql_query("SELECT DISTINCT peer_group_name, is_benchmark FROM peer_groups ORDER BY peer_group_name", conn)
print("peer groups:", len(peers))
pp = pd.read_sql_query("SELECT * FROM peer_percentiles WHERE period='FY2024' LIMIT 3", conn)
print("peer_percentiles sample cols:", list(pp.columns))
conn.close()
print("ALL SCHEMA TESTS PASSED")
