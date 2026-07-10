import pandas as pd

files = ['stock_prices', 'market_cap', 'financial_ratios', 'peer_groups', 'analysis', 'sectors']

for f in files:
    try:
        # Read with no header to see raw structure
        df_raw = pd.read_excel(f'data/raw/{f}.xlsx', header=None)
        print(f'\n{f}:')
        print(f'  Row 0 (first 3): {list(df_raw.iloc[0])[:3]}')
        print(f'  Row 1 (first 3): {list(df_raw.iloc[1])[:3]}')
        print(f'  Row 2 (first 3): {list(df_raw.iloc[2])[:3]}')
    except Exception as e:
        print(f'{f}: Error - {e}')