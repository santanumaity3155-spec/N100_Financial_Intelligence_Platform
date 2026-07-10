"""
Script to check header rows across all Excel files.
"""
import pandas as pd
from pathlib import Path

raw_dir = Path("data/raw")
excel_files = list(raw_dir.glob("*.xlsx"))

for file_path in excel_files[:5]:  # Check first 5 files
    print(f"\n{'='*80}")
    print(f"FILE: {file_path.name}")
    print(f"{'='*80}")
    
    # Read first 3 rows without header
    df_raw = pd.read_excel(file_path, header=None, nrows=3)
    print("\nFirst 3 rows (no header):")
    for idx, row in df_raw.iterrows():
        print(f"Row {idx}: {row.tolist()}")
    
    # Try header=1
    try:
        df = pd.read_excel(file_path, header=1, nrows=2)
        print(f"\nWith header=1:")
        print(f"Columns: {list(df.columns)}")
    except Exception as e:
        print(f"Error with header=1: {e}")