"""
Integration test for Peer Percentile Engine with real database data
"""
import pandas as pd
from src.analytics.peer import (
    load_peer_groups,
    assign_peer_groups,
    calculate_all_percentiles,
    save_peer_percentiles,
    export_percentiles,
    get_peer_summary,
    validate_peer_data,
    run_peer_percentile_engine,
    SUPPORTED_METRICS,
    SUPPORTED_PEER_GROUPS,
)
from src.database.connection import get_connection

print("=" * 80)
print("PEER PERCENTILE ENGINE - INTEGRATION TEST")
print("=" * 80)

# Step 1: Load financial data from database
print("\n[1] Loading financial data from database...")
conn = get_connection()

# Get available periods
cursor = conn.execute("SELECT DISTINCT period FROM financial_ratios ORDER BY period DESC LIMIT 5")
available_periods = [row[0] for row in cursor.fetchall()]
print(f"Available periods: {available_periods}")

# Use the most recent period that has data
target_period = available_periods[0] if available_periods else 'Sep 2024'
print(f"Using period: {target_period}")

# Query for ALL companies in the period
query = f"""
    SELECT 
        fr.company_id,
        fr.period,
        fr.roe,
        fr.roa,
        fr.debt_to_equity,
        fr.pe_ratio,
        fr.pb_ratio,
        c.company_name
    FROM financial_ratios fr
    LEFT JOIN companies c ON fr.company_id = c.company_id
    WHERE fr.period = ?
    LIMIT 50
"""

df = pd.read_sql_query(query, conn, params=[target_period])
print(f"Loaded {len(df)} companies for period {target_period}")
print(f"Columns: {list(df.columns)}")

# Add some synthetic metrics for demonstration
import numpy as np
np.random.seed(42)
df['roce'] = df['roe'] * np.random.uniform(0.8, 1.2, len(df))
df['net_profit_margin'] = df['roe'] * np.random.uniform(0.5, 0.8, len(df))
df['interest_coverage'] = np.random.uniform(2, 15, len(df))
df['asset_turnover'] = np.random.uniform(0.5, 2.0, len(df))
df['free_cash_flow'] = np.random.uniform(1000, 10000, len(df))
df['revenue_cagr_5yr'] = np.random.uniform(5, 20, len(df))
df['pat_cagr_5yr'] = np.random.uniform(3, 18, len(df))
df['eps_cagr_5yr'] = np.random.uniform(4, 19, len(df))

# Step 2: Load peer groups
print("\n[2] Loading peer groups...")
peer_groups = load_peer_groups(source="database")
print(f"Loaded {len(peer_groups)} peer group assignments")
print(f"Unique peer groups: {peer_groups['peer_group_name'].unique()}")

# Step 3: Run the complete pipeline
print("\n[3] Running peer percentile engine...")
stats = run_peer_percentile_engine(df, target_period, export=True)

print(f"\nPipeline Statistics:")
print(f"  Status: {stats['status']}")
print(f"  Companies Processed: {stats['companies_processed']}")
print(f"  Companies with Peer Group: {stats['companies_with_peer_group']}")
print(f"  Companies without Peer Group: {stats['companies_without_peer_group']}")
print(f"  Metrics Processed: {stats['metrics_processed']}")
print(f"  Rows Inserted: {stats['rows_inserted']}")
print(f"  Rows Skipped: {stats['rows_skipped']}")

# Step 4: Validate results
print("\n[4] Validating results...")
if 'summary' in stats:
    summary = stats['summary']
    print(f"Peer Groups Found: {list(summary.get('peer_groups', {}).keys())}")
    print(f"Metrics Calculated: {list(summary.get('metrics_summary', {}).keys())}")

# Step 5: Check database
print("\n[5] Checking database...")
cursor = conn.execute("SELECT COUNT(*) FROM peer_percentiles")
total_records = cursor.fetchone()[0]
print(f"Total records in peer_percentiles table: {total_records}")

cursor = conn.execute("""
    SELECT peer_group_name, COUNT(*) as count 
    FROM peer_percentiles 
    GROUP BY peer_group_name
    ORDER BY count DESC
    LIMIT 10
""")
print("\nRecords by peer group:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}")

cursor = conn.execute("""
    SELECT metric, COUNT(*) as count 
    FROM peer_percentiles 
    GROUP BY metric
    ORDER BY count DESC
""")
print("\nRecords by metric:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}")

# Step 6: Verify CSV export
print("\n[6] Checking CSV export...")
import os
csv_path = "output/peer_percentiles.csv"
if os.path.exists(csv_path):
    export_df = pd.read_csv(csv_path)
    print(f"CSV file exists: {csv_path}")
    print(f"Total rows: {len(export_df)}")
    print(f"Columns: {list(export_df.columns)}")
    print(f"\nSample data:")
    print(export_df.head(10))
else:
    print(f"ERROR: CSV file not found at {csv_path}")

# Step 7: Verify Debt-to-Equity inversion
print("\n[7] Verifying Debt-to-Equity inversion...")
cursor = conn.execute(f"""
    SELECT company_id, peer_group_name, metric_value, percentile_rank
    FROM peer_percentiles
    WHERE metric = 'debt_to_equity'
    AND period = '{target_period}'
    ORDER BY percentile_rank DESC
    LIMIT 5
""")
print("Top 5 companies by Debt-to-Equity percentile (lower debt = higher percentile):")
for row in cursor.fetchall():
    print(f"  {row[0]} ({row[1]}): D/E={row[2]}, Percentile={row[3]:.4f}")

conn.close()

print("\n" + "=" * 80)
print("INTEGRATION TEST COMPLETE")
print("=" * 80)