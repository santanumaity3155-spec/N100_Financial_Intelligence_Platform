"""
Demo script for Module 5 - Financial Health Score Engine

This script demonstrates the Health Score Engine by:
1. Loading financial ratios from the database
2. Calculating health scores for all companies
3. Saving results to the database
4. Exporting to CSV
5. Displaying summary statistics
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from src.health_score.engine import run_health_score_pipeline, get_health_score_statistics
from src.config.logging_config import get_logger

def main():
    """Run the Financial Health Score Engine demo."""
    print("=" * 80)
    print("MODULE 5 - FINANCIAL HEALTH SCORE ENGINE")
    print("N100 Financial Intelligence Platform")
    print("=" * 80)
    print()
    
    # Setup logging
    logger = get_logger(__name__)
    
    print("Step 1: Running Health Score Pipeline...")
    print("-" * 80)
    
    # Run the pipeline
    stats = run_health_score_pipeline()
    
    print()
    print("Step 2: Pipeline Statistics")
    print("-" * 80)
    print(f"Status: {stats['status']}")
    print(f"Total Records Processed: {stats['companies_processed']}")
    print(f"Records Skipped: {stats['companies_skipped']}")
    print(f"Records Failed: {stats['companies_failed']}")
    print(f"Rows Inserted in DB: {stats['rows_inserted']}")
    print(f"Rows Skipped in DB: {stats['rows_skipped']}")
    print(f"Duplicates Found: {stats['duplicates_found']}")
    print(f"Warnings: {len(stats['warnings'])}")
    print(f"Errors: {len(stats['errors'])}")
    
    if stats['errors']:
        print("\nErrors encountered:")
        for error in stats['errors'][:5]:  # Show first 5 errors
            print(f"  - {error}")
    
    print()
    print("Step 3: Database Statistics")
    print("-" * 80)
    
    # Get statistics from database
    db_stats = get_health_score_statistics()
    
    if db_stats:
        print(f"Total Records in DB: {db_stats.get('total_records', 0)}")
        
        if 'rating_distribution' in db_stats:
            print("\nRating Distribution:")
            for rating, count in sorted(db_stats['rating_distribution'].items()):
                print(f"  {rating:15s}: {count:4d} companies")
        
        if 'averages' in db_stats:
            print("\nAverage Scores:")
            avgs = db_stats['averages']
            print(f"  Profitability: {avgs.get('profitability', 0) or 0:.2f}")
            print(f"  Growth:        {avgs.get('growth', 0) or 0:.2f}")
            print(f"  Cash Flow:     {avgs.get('cashflow', 0) or 0:.2f}")
            print(f"  Leverage:      {avgs.get('leverage', 0) or 0:.2f}")
            print(f"  Efficiency:    {avgs.get('efficiency', 0) or 0:.2f}")
            print(f"  Overall:       {avgs.get('overall', 0) or 0:.2f}")
        
        if 'top_performers' in db_stats and db_stats['top_performers']:
            print("\nTop 10 Performers:")
            for i, company in enumerate(db_stats['top_performers'], 1):
                print(f"  {i:2d}. {company['company_id']:15s} - "
                      f"Score: {company['overall_score']:6.2f} "
                      f"({company['rating']})")
    else:
        print("No statistics available (database may be empty)")
    
    print()
    print("=" * 80)
    print("Module 5 execution completed successfully!")
    print("=" * 80)
    
    return 0 if stats['status'] == 'completed' else 1

if __name__ == "__main__":
    sys.exit(main())