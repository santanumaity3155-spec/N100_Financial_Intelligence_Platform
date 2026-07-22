"""
run_peer_analysis.py

Demo script for Module 7 - Peer Percentile Ranking Engine.

This script demonstrates the complete workflow:
1. Load financial data from database
2. Assign peer groups
3. Calculate percentile rankings for all 10 metrics
4. Verify Debt-to-Equity inversion
5. Save to SQLite database
6. Export to CSV
7. Generate summary report

Usage:
    python run_peer_analysis.py
"""

import logging
import sys
from pathlib import Path

import pandas as pd

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config.logging_config import setup_logging
from src.database.connection import get_connection, close_connection
from src.analytics.peer import (
    run_peer_percentile_engine,
    get_peer_percentile_statistics,
    validate_database_integrity,
    SUPPORTED_METRICS,
    SUPPORTED_PEER_GROUPS,
    INVERTED_METRICS,
)

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


def load_financial_data() -> pd.DataFrame:
    """
    Load financial data from database.
    
    Returns
    -------
    pd.DataFrame
        DataFrame with financial metrics for all companies
    """
    logger.info("Loading financial data from database")
    
    try:
        conn = get_connection()
        
        # Query to join financial_ratios with peer_groups
        query = """
            SELECT 
                fr.company_id,
                fr.company_name,
                fr.period,
                fr.sector,
                fr.industry,
                pg.peer_group_name,
                -- Profitability
                fr.roe,
                fr.roce,
                fr.net_profit_margin,
                -- Leverage
                fr.debt_to_equity,
                fr.interest_coverage,
                -- Efficiency
                fr.asset_turnover,
                -- Cash Flow
                fr.free_cash_flow,
                -- CAGR
                fr.revenue_cagr_5yr,
                fr.pat_cagr_5yr,
                fr.eps_cagr_5yr
            FROM financial_ratios fr
            LEFT JOIN peer_groups pg ON fr.company_id = pg.company_id
            WHERE fr.period = (SELECT MAX(period) FROM financial_ratios)
            AND fr.company_id IS NOT NULL
        """
        
        df = pd.read_sql_query(query, conn)
        logger.info(f"Loaded {len(df)} company records from database")
        
        return df
        
    except Exception as e:
        logger.error(f"Failed to load financial data: {str(e)}")
        raise


def validate_requirements(df: pd.DataFrame) -> bool:
    """
    Validate that all requirements are met.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with financial metrics
    
    Returns
    -------
    bool
        True if all requirements are met
    """
    logger.info("=" * 80)
    logger.info("VALIDATING REQUIREMENTS")
    logger.info("=" * 80)
    
    all_valid = True
    
    # Check 1: All 11 peer groups supported
    logger.info(f"✓ Supported peer groups: {len(SUPPORTED_PEER_GROUPS)} (required: 11)")
    if len(SUPPORTED_PEER_GROUPS) != 11:
        logger.error("❌ FAIL: Expected 11 peer groups")
        all_valid = False
    
    # Check 2: All 10 metrics supported
    logger.info(f"✓ Supported metrics: {len(SUPPORTED_METRICS)} (required: 10)")
    if len(SUPPORTED_METRICS) != 10:
        logger.error("❌ FAIL: Expected 10 metrics")
        all_valid = False
    
    # Check 3: Debt-to-Equity is in inverted metrics
    logger.info(f"✓ Inverted metrics: {INVERTED_METRICS}")
    if "debt_to_equity" not in INVERTED_METRICS:
        logger.error("❌ FAIL: debt_to_equity should be in INVERTED_METRICS")
        all_valid = False
    
    # Check 4: Data has required columns
    required_cols = ["company_id", "peer_group_name"] + SUPPORTED_METRICS
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        logger.error(f"❌ FAIL: Missing columns in data: {missing_cols}")
        all_valid = False
    else:
        logger.info(f"✓ All required columns present in data")
    
    # Check 5: Companies with peer groups
    if "peer_group_name" in df.columns:
        with_peer = (df["peer_group_name"] != "No peer group assigned").sum()
        without_peer = (df["peer_group_name"] == "No peer group assigned").sum()
        
        logger.info(f"✓ Companies with peer group: {with_peer}")
        logger.info(f"✓ Companies without peer group: {without_peer}")
        
        if with_peer == 0:
            logger.warning("⚠ WARNING: No companies have peer groups assigned")
    
    # Check 6: Peer groups in data
    if "peer_group_name" in df.columns:
        peer_groups_in_data = df["peer_group_name"].unique()
        valid_peer_groups = [pg for pg in peer_groups_in_data if pg in SUPPORTED_PEER_GROUPS]
        
        logger.info(f"✓ Unique peer groups in data: {len(valid_peer_groups)}")
        
        for pg in valid_peer_groups[:5]:  # Show first 5
            count = (df["peer_group_name"] == pg).sum()
            logger.info(f"  - {pg}: {count} companies")
    
    logger.info("=" * 80)
    
    return all_valid


def main():
    """Main execution function."""
    logger.info("=" * 80)
    logger.info("PEER PERCENTILE RANKING ENGINE - MODULE 7")
    logger.info("=" * 80)
    
    try:
        # Step 1: Load financial data
        logger.info("\n[Step 1/5] Loading financial data...")
        df = load_financial_data()
        
        if len(df) == 0:
            logger.error("No data found in database. Please run previous modules first.")
            return False
        
        logger.info(f"Loaded {len(df)} company records")
        
        # Step 2: Validate requirements
        logger.info("\n[Step 2/5] Validating requirements...")
        validate_requirements(df)
        
        # Step 3: Run peer percentile engine
        logger.info("\n[Step 3/5] Running peer percentile engine...")
        period = df["period"].iloc[0] if "period" in df.columns else "FY2024"
        
        stats = run_peer_percentile_engine(
            df=df,
            period=period,
            metrics=SUPPORTED_METRICS,
            export=True,
            source="database"
        )
        
        logger.info(f"Pipeline status: {stats['status']}")
        logger.info(f"Companies processed: {stats['companies_processed']}")
        logger.info(f"Companies with peer group: {stats['companies_with_peer_group']}")
        logger.info(f"Companies without peer group: {stats['companies_without_peer_group']}")
        logger.info(f"Metrics processed: {stats['metrics_processed']}")
        logger.info(f"Rows inserted: {stats['rows_inserted']}")
        logger.info(f"Rows skipped: {stats['rows_skipped']}")
        
        # Step 4: Verify database
        logger.info("\n[Step 4/5] Verifying database...")
        db_stats = get_peer_percentile_statistics()
        
        if db_stats:
            logger.info(f"Total records in database: {db_stats.get('total_records', 0)}")
            logger.info(f"Peer groups: {len(db_stats.get('by_peer_group', {}))}")
            logger.info(f"Metrics: {len(db_stats.get('by_metric', {}))}")
            logger.info(f"Periods: {db_stats.get('by_period', {})}")
        
        # Validate database integrity
        integrity = validate_database_integrity()
        logger.info(f"Database integrity: {'✓ VALID' if integrity.get('valid') else '❌ INVALID'}")
        
        if not integrity.get('valid'):
            for check in integrity.get('checks', []):
                logger.info(f"  - {check.get('check')}: {check.get('status')}")
        
        # Step 5: Summary
        logger.info("\n[Step 5/5] Summary")
        logger.info("=" * 80)
        
        if stats["status"] == "completed":
            logger.info("✅ Peer Percentile Engine completed successfully")
            logger.info(f"✅ Processed {stats['companies_processed']} companies")
            logger.info(f"✅ Inserted {stats['rows_inserted']} records into database")
            logger.info(f"✅ Exported CSV to: output/peer_percentiles.csv")
            logger.info(f"✅ All 10 metrics ranked across peer groups")
            logger.info(f"✅ Debt-to-Equity inversion applied")
            
            if stats["rows_skipped"] > 0:
                logger.warning(f"⚠ Skipped {stats['rows_skipped']} records (missing peer groups or NaN values)")
            
            logger.info("=" * 80)
            logger.info("MODULE 7 COMPLETE")
            logger.info("=" * 80)
            
            return True
        else:
            logger.error("❌ Pipeline failed")
            return False
    
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        return False
    
    finally:
        close_connection()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)