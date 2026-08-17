from src.database.connection import get_connection
from src.nlp.pros_cons_generator import load_ratio_data

def main():
    conn = get_connection()
    if conn is None:
        print("No connection")
        return
    # Load ratios data
    df = load_ratio_data(conn)
    print(f"Loaded ratios data shape: {df.shape}")
    if df.empty:
        print("Ratios data is empty")
    else:
        print(f"Columns: {df.columns.tolist()}")
        # Check for UNIONBANK
        df['company_id'] = df['company_id'].astype(str).str.strip().str.upper()
        match = df[df['company_id'] == 'UNIONBANK']
        print(f"Rows for UNIONBANK: {len(match)}")
        if not match.empty:
            print("First UNIONBANK row:")
            print(match.iloc[0])
        else:
            print("No UNIONBANK rows in ratios data")
            # Show some company_ids present
            ids = df['company_id'].dropna().unique()[:10]
            print(f"First 10 company_ids in ratios data: {ids.tolist()}")
    conn.close()

if __name__ == "__main__":
    main()