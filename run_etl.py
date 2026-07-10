#!/usr/bin/env python3
"""
run_etl.py

Main entry point for the N100 Financial Intelligence Platform ETL Pipeline.
This script orchestrates the complete ETL workflow from Excel files to SQLite database.

Usage:
    python run_etl.py

Output:
    - data/database/n100.db (SQLite database)
    - reports/ (Data quality reports in JSON and HTML)
    - logs/ (Application logs)
"""

import sys
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config.logging_config import get_logger
from src.etl.pipeline import run_etl_pipeline

logger = get_logger(__name__)


def main():
    """
    Main function to run the ETL pipeline.
    
    Returns
    -------
    int
        Exit code (0 for success, 1 for failure)
    """
    logger.info("="*80)
    logger.info("N100 FINANCIAL INTELLIGENCE PLATFORM - ETL PIPELINE")
    logger.info("="*80)
    logger.info(f"Project Root: {PROJECT_ROOT}")
    logger.info(f"Starting ETL Pipeline...")
    
    try:
        # Run the ETL pipeline
        results = run_etl_pipeline(
            validate=True,
            normalize=True,
            transform=True,
            load=True,
            generate_reports=True
        )
        
        # Print summary
        print("\n" + "="*80)
        print("ETL PIPELINE EXECUTION SUMMARY")
        print("="*80)
        
        # Pipeline stats
        pipeline_stats = results.get("pipeline_stats", {})
        print(f"Status: {pipeline_stats.get('status', 'unknown')}")
        print(f"Start Time: {pipeline_stats.get('start_time', 'N/A')}")
        print(f"End Time: {pipeline_stats.get('end_time', 'N/A')}")
        print(f"Datasets Processed: {pipeline_stats.get('datasets_processed', 0)}")
        
        # Load stats
        load_stats = results.get("load_stats", {})
        print(f"\nTotal Rows Loaded: {load_stats.get('total_rows_loaded', 0):,}")
        print(f"Successful Loads: {load_stats.get('successful_loads', 0)}")
        print(f"Failed Loads: {len(load_stats.get('failed_loads', []))}")
        
        # Validation summary
        validation_summary = results.get("validation_summary", {})
        print(f"\nValidation Results:")
        print(f"  - Total Datasets: {validation_summary.get('total_datasets', 0)}")
        print(f"  - Passed: {validation_summary.get('passed', 0)}")
        print(f"  - Failed: {validation_summary.get('failed', 0)}")
        
        # Output locations
        print("\nOutput Locations:")
        print(f"  - Database: {PROJECT_ROOT / 'data' / 'database' / 'n100.db'}")
        print(f"  - Reports: {PROJECT_ROOT / 'reports'}")
        print(f"  - Logs: {PROJECT_ROOT / 'logs' / 'application.log'}")
        
        print("="*80)
        
        # Check for errors
        if pipeline_stats.get("status") == "completed":
            logger.info("ETL Pipeline completed successfully!")
            return 0
        else:
            logger.error("ETL Pipeline did not complete successfully")
            return 1

    except KeyboardInterrupt:
        logger.warning("\nPipeline interrupted by user")
        return 1
    
    except Exception as e:
        logger.error(f"\nPipeline failed with error: {str(e)}", exc_info=True)
        print(f"\nERROR: {str(e)}")
        print("Check logs for details: logs/application.log")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)