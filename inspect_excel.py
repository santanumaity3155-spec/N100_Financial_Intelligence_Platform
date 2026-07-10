"""
Script to inspect Excel file structure for debugging header issues.
"""
import pandas as pd
from pathlib import Path

# Read first few rows of companies.xlsx to see structure
file_path = Path("data/raw/companies.xlsx")
print(f"\n{'='*80}")
print(f"INSPECTING: {file_path.name}")
print(f"{'='*80}")

# Read without header to see raw structure
df_raw = pd.read_excel(file_path, header=None, nrows=10)
print("\nFirst 10 rows (no header):")
print(df_raw)
print(f"\nShape: {df_raw.shape}")

# Try different header rows
for header_row in [0, 1, 2, 3]:
    try:
        df = pd.read_excel(file_path, header=header_row, nrows=5)
        print(f"\n--- Header row {header_row} ---")
        print(f"Columns: {list(df.columns)}")
        print(f"First row: {df.iloc[0].to_dict()}")
    except Exception as e:
        print(f"Error with header={header_row}: {e}")