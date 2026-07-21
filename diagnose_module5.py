"""
Diagnostic script for Module 5 production issues.
"""

import sqlite3
import pandas as pd
from pathlib import Path

DATABASE_PATH = Path("data/database/n100.db")

def main():
    print("=" * 80)
    print("MODULE 5 DIAGNOSTIC REPORT")
    print("=" * 80)
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Issue 1: Foreign Key Investigation
    print("\n" + "=" * 80)
    print("ISSUE 1: FOREIGN KEY CONSTRAINT INVESTIGATION")
    print("=" * 80)
    
    # Check if companies table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='companies'")
    companies_table = cursor.fetchone()
    print(f"\nCompanies table exists: {companies_table is not None}")
    
    if companies_table:
        cursor.execute("SELECT COUNT(*) FROM companies")
        total_companies = cursor.fetchone()[0]
        print(f"Total companies in companies table: {total_companies}")
        
        cursor.execute("SELECT company_id FROM companies LIMIT 10")
        sample_companies = [row[0] for row in cursor.fetchall()]
        print(f"Sample company IDs: {sample_companies[:5]}")
    
    # Check financial_ratios table
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='financial_ratios'")
    ratios_table = cursor.fetchone()
    print(f"\nFinancial ratios table exists: {ratios_table is not None}")
    
    if ratios_table:
        cursor.execute("SELECT COUNT(*) FROM financial_ratios")
        total_ratios = cursor.fetchone()[0]
        print(f"Total records in financial_ratios: {total_ratios}")
        
        cursor.execute("SELECT DISTINCT company_id FROM financial_ratios LIMIT 10")
        ratio_companies = [row[0] for row in cursor.fetchall()]
        print(f"Sample company IDs in financial_ratios: {ratio_companies}")
    
    # Check financial_health_scores table
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='financial_health_scores'")
    health_table = cursor.fetchone()
    print(f"\nFinancial health scores table exists: {health_table is not None}")
    
    if health_table:
        cursor.execute("SELECT COUNT(*) FROM financial_health_scores")
        total_health = cursor.fetchone()[0]
        print(f"Total records in financial_health_scores: {total_health}")
    
    # Check for FK violations
    print("\n" + "-" * 80)
    print("Checking for FK violations...")
    cursor.execute("""
        SELECT DISTINCT fr.company_id 
        FROM financial_ratios fr
        LEFT JOIN companies c ON fr.company_id = c.company_id
        WHERE c.company_id IS NULL
    """)
    missing_companies = [row[0] for row in cursor.fetchall()]
    print(f"Companies in financial_ratios but NOT in companies table: {len(missing_companies)}")
    if missing_companies:
        print(f"Sample missing companies: {missing_companies[:10]}")
    
    # Issue 2: Growth Score Investigation
    print("\n" + "=" * 80)
    print("ISSUE 2: GROWTH SCORE ALWAYS ZERO")
    print("=" * 80)
    
    if ratios_table:
        # Check CAGR columns
        cursor.execute("PRAGMA table_info(financial_ratios)")
        columns = [row[1] for row in cursor.fetchall()]
        
        cagr_cols = [col for col in columns if 'cagr' in col.lower()]
        print(f"\nCAGR columns found: {cagr_cols}")
        
        # Check for non-null CAGR values
        for col in ['revenue_cagr_3yr', 'pat_cagr_3yr', 'eps_cagr_3yr']:
            if col in columns:
                cursor.execute(f"""
                    SELECT 
                        COUNT(*) as total,
                        COUNT({col}) as not_null,
                        MIN({col}) as min_val,
                        MAX({col}) as max_val,
                        AVG({col}) as avg_val
                    FROM financial_ratios
                """)
                stats = cursor.fetchone()
                print(f"\n{col}:")
                print(f"  Total records: {stats[0]}")
                print(f"  Non-null count: {stats[1]}")
                print(f"  Min: {stats[2]}, Max: {stats[3]}, Avg: {stats[4]}")
    
    # Issue 3: Cash Flow Score Investigation
    print("\n" + "=" * 80)
    print("ISSUE 3: CASH FLOW SCORE ALWAYS ZERO")
    print("=" * 80)
    
    if ratios_table:
        cf_cols = ['free_cash_flow', 'fcf_margin', 'cash_conversion', 'cash_return_on_assets', 'capital_allocation_rating']
        for col in cf_cols:
            if col in columns:
                cursor.execute(f"""
                    SELECT 
                        COUNT(*) as total,
                        COUNT({col}) as not_null,
                        MIN({col}) as min_val,
                        MAX({col}) as max_val
                    FROM financial_ratios
                """)
                stats = cursor.fetchone()
                print(f"\n{col}:")
                print(f"  Total: {stats[0]}, Non-null: {stats[1]}")
                print(f"  Min: {stats[2]}, Max: {stats[3]}")
    
    # Issue 4: Efficiency Score Investigation
    print("\n" + "=" * 80)
    print("ISSUE 4: EFFICIENCY SCORE ALWAYS ZERO")
    print("=" * 80)
    
    if ratios_table:
        if 'asset_turnover' in columns:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(asset_turnover) as not_null,
                    MIN(asset_turnover) as min_val,
                    MAX(asset_turnover) as max_val,
                    AVG(asset_turnover) as avg_val
                FROM financial_ratios
            """)
            stats = cursor.fetchone()
            print(f"\nAsset Turnover:")
            print(f"  Total: {stats[0]}, Non-null: {stats[1]}")
            print(f"  Min: {stats[2]}, Max: {stats[3]}, Avg: {stats[4]}")
    
    # Issue 6: Database Content Verification
    print("\n" + "=" * 80)
    print("ISSUE 6: DATABASE CONTENT VERIFICATION")
    print("=" * 80)
    
    if health_table:
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(DISTINCT company_id) as unique_companies,
                COUNT(DISTINCT period) as unique_periods,
                MIN(period) as earliest_period,
                MAX(period) as latest_period
            FROM financial_health_scores
        """)
        stats = cursor.fetchone()
        print(f"\nFinancial Health Scores:")
        print(f"  Total records: {stats[0]}")
        print(f"  Unique companies: {stats[1]}")
        print(f"  Unique periods: {stats[2]}")
        print(f"  Period range: {stats[3]} to {stats[4]}")
        
        # Check for duplicates
        cursor.execute("""
            SELECT company_id, period, COUNT(*) as cnt
            FROM financial_health_scores
            GROUP BY company_id, period
            HAVING cnt > 1
        """)
        duplicates = cursor.fetchall()
        print(f"  Duplicate records: {len(duplicates)}")
        if duplicates:
            print(f"  Sample duplicates: {duplicates[:5]}")
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()