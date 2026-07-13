"""
Quick script to inspect Excel file column names
"""

import pandas as pd
from pathlib import Path

raw_data_dir = Path("data/raw")
datasets = {
    "companies": "companies.xlsx",
    "profit_loss": "profitandloss.xlsx",
    "balance_sheet": "balancesheet.xlsx",
    "cash_flow": "cashflow.xlsx",
    "analysis": "analysis.xlsx",
    "documents": "documents.xlsx",
    "pros_cons": "prosandcons.xlsx",
    "sectors": "sectors.xlsx",
    "stock_prices": "stock_prices.xlsx",
    "market_cap": "market_cap.xlsx",
    "financial_ratios": "financial_ratios.xlsx",
    "peer_groups": "peer_groups.xlsx",
}

for dataset_name, filename in datasets.items():
    file_path = raw_data_dir / filename
    if file_path.exists():
        df = pd.read_excel(file_path, nrows=0)  # Just read headers
        print(f"\n{dataset_name}:")
        print(f"  Columns: {list(df.columns)}")
    else:
        print(f"\n{dataset_name}: FILE NOT FOUND")