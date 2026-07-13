"""
Inspect actual Excel structure with different header rows
"""

import pandas as pd
from pathlib import Path

raw_data_dir = Path("data/raw")

# Check a few key files with different header settings
files_to_check = [
    "profitandloss.xlsx",
    "balancesheet.xlsx",
    "market_cap.xlsx",
]

for filename in files_to_check:
    file_path = raw_data_dir / filename
    if file_path.exists():
        print(f"\n{'='*80}")
        print(f"File: {filename}")
        print('='*80)
        
        # Read with header=0 (first row)
        df_header0 = pd.read_excel(file_path, header=0, nrows=3)
        print(f"\nWith header=0:")
        print(f"  Columns: {list(df_header0.columns)}")
        print(f"  First row: {df_header0.iloc[0].to_dict()}")
        
        # Read with header=1 (second row)
        df_header1 = pd.read_excel(file_path, header=1, nrows=3)
        print(f"\nWith header=1:")
        print(f"  Columns: {list(df_header1.columns)}")
        print(f"  First row: {df_header1.iloc[0].to_dict()}")