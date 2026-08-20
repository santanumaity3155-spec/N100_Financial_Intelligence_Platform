"""
populate_financial_kpis.py

Script to populate the financial_kpis table in SQLite database.

This script calculates KPIs for all companies and all available periods
and stores the results in the financial_kpis table for easy querying
and analysis.
"""

import logging
import sys
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd

from src.config.logging_config import get_logger
from src.config.constants import PROJECT_ROOT
from src.kpi_engine.calculator import KPIEngine

# Setup logging
logger = get_logger(__name__)


def populate_financial_kpis(db_path: str = None, batch_size: int = 10) -> Dict[str, Any]:
    """
    Populate the financial_kpis table with calculated KPIs for all companies.
    
    Parameters
    ----------
    db_path : str, optional
        Path to SQLite database. If None, uses default path.
    batch_size : int, default 10
        Number of companies to process in each batch for progress tracking.
        
    Returns
    -------
    Dict[str, Any]
        Summary statistics of the population process
    """
    logger.info("=" * 80)
    logger.info("POPULATING FINANCIAL KPIs TABLE")
    logger.info("=" * 80)
    
    # Initialize KPI Engine
    engine = KPIEngine(db_path)
    
    # Get all companies
    companies = engine.get_available_companies()
    logger.info(f"Found {len(companies)} companies to process")
    
    if not companies:
        logger.error("No companies found in database")
        return {"error": "No companies found"}
    
    # Statistics tracking
    stats = {
        "total_companies": len(companies),
        "processed_companies": 0,
        "total_kpis_calculated": 0,
        "total_records": 0,
        "errors": [],
        "companies_with_data": 0,
        "companies_without_data": 0
    }
    
    # Process companies in batches
    all_kpi_records = []
    
    for i, company_id in enumerate(companies, 1):
        try:
            # Get available periods for this company
            periods = engine.get_available_periods(company_id)
            
            if not periods:
                logger.warning(f"No periods found for {company_id}, skipping")
                stats["companies_without_data"] += 1
                continue
            
            # Calculate KPIs for all periods
            kpi_results_list = engine.calculate_kpis_for_company(company_id, periods)
            
            if kpi_results_list:
                stats["companies_with_data"] += 1
                all_kpi_records.extend(kpi_results_list)
                
                # Count KPIs
                for result in kpi_results_list:
                    kpi_count = len([v for v in result.values() if v is not None])
                    stats["total_kpis_calculated"] += kpi_count
                
                stats["total_records"] += len(kpi_results_list)
            else:
                stats["companies_without_data"] += 1
            
            stats["processed_companies"] += 1
            
            # Progress logging
            if i % batch_size == 0 or i == len(companies):
                progress_pct = (i / len(companies)) * 100
                logger.info(
                    f"Progress: {i}/{len(companies)} companies ({progress_pct:.1f}%) | "
                    f"Records: {stats['total_records']} | "
                    f"KPIs: {stats['total_kpis_calculated']}"
                )
        
        except Exception as e:
            error_msg = f"Error processing {company_id}: {str(e)}"
            logger.error(error_msg)
            stats["errors"].append(error_msg)
            continue
    
    # Save to database
    if all_kpi_records:
        logger.info(f"Saving {len(all_kpi_records)} KPI records to database...")
        
        try:
            save_success = save_kpis_to_database(all_kpi_records, db_path)
            stats["database_save_success"] = save_success
            
            if save_success:
                logger.info("✓ Successfully saved KPIs to database")
            else:
                logger.error("✗ Failed to save KPIs to database")
        
        except Exception as e:
            error_msg = f"Error saving to database: {str(e)}"
            logger.error(error_msg)
            stats["errors"].append(error_msg)
            stats["database_save_success"] = False
    else:
        logger.warning("No KPI records to save")
        stats["database_save_success"] = False
    
    # Log summary
    logger.info("=" * 80)
    logger.info("POPULATION SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total Companies: {stats['total_companies']}")
    logger.info(f"Processed Companies: {stats['processed_companies']}")
    logger.info(f"Companies with Data: {stats['companies_with_data']}")
    logger.info(f"Companies without Data: {stats['companies_without_data']}")
    logger.info(f"Total Records Generated: {stats['total_records']}")
    logger.info(f"Total KPIs Calculated: {stats['total_kpis_calculated']}")
    logger.info(f"Database Save: {'✓ Success' if stats.get('database_save_success') else '✗ Failed'}")
    
    if stats["errors"]:
        logger.warning(f"Errors encountered: {len(stats['errors'])}")
        for error in stats["errors"][:5]:  # Show first 5 errors
            logger.warning(f"  - {error}")
    
    logger.info("=" * 80)
    
    return stats


def save_kpis_to_database(kpi_records: List[Dict[str, Any]], db_path: str = None) -> bool:
    """
    Save KPI records to the financial_kpis table in SQLite.
    
    Parameters
    ----------
    kpi_records : List[Dict[str, Any]]
        List of KPI result dictionaries
    db_path : str, optional
        Path to SQLite database
        
    Returns
    -------
    bool
        True if save was successful, False otherwise
    """
    try:
        import sqlite3
        from src.database.connection import get_connection
        
        logger.info(f"Preparing to save {len(kpi_records)} records to financial_kpis table")
        
        # Convert to DataFrame for easier handling
        df = pd.DataFrame(kpi_records)
        
        # Get database connection
        conn = get_connection()
        
        # Create table if it doesn't exist
        create_table_query = """
        CREATE TABLE IF NOT EXISTS financial_kpis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id TEXT NOT NULL,
            period TEXT NOT NULL,
            
            -- Profitability KPIs
            roe REAL,
            roce REAL,
            roa REAL,
            net_profit_margin REAL,
            operating_margin REAL,
            ebit_margin REAL,
            gross_margin REAL,
            
            -- Liquidity KPIs
            current_ratio REAL,
            quick_ratio REAL,
            cash_ratio REAL,
            
            -- Leverage KPIs
            debt_to_equity REAL,
            debt_ratio REAL,
            interest_coverage REAL,
            financial_leverage REAL,
            
            -- Efficiency KPIs
            asset_turnover REAL,
            inventory_turnover REAL,
            receivable_turnover REAL,
            working_capital_turnover REAL,
            
            -- Cash Flow KPIs
            operating_cash_flow REAL,
            free_cash_flow REAL,
            cash_conversion_ratio REAL,
            
            -- Valuation KPIs
            eps REAL,
            pe_ratio REAL,
            pb_ratio REAL,
            ev_ebitda REAL,
            dividend_yield REAL,
            
            -- Growth KPIs
            revenue_cagr REAL,
            profit_cagr REAL,
            eps_cagr REAL,
            margin_expansion REAL,
            
            -- Metadata
            calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- Unique constraint
            UNIQUE(company_id, period)
        )
        """
        
        conn.execute(create_table_query)
        
        # Create indexes for common queries
        index_queries = [
            "CREATE INDEX IF NOT EXISTS idx_financial_kpis_company ON financial_kpis(company_id)",
            "CREATE INDEX IF NOT EXISTS idx_financial_kpis_period ON financial_kpis(period)",
            "CREATE INDEX IF NOT EXISTS idx_financial_kpis_company_period ON financial_kpis(company_id, period)",
        ]
        
        for index_query in index_queries:
            conn.execute(index_query)
        
        # Insert or replace records
        insert_query = """
        INSERT OR REPLACE INTO financial_kpis (
            company_id, period,
            roe, roce, roa, net_profit_margin, operating_margin, ebit_margin, gross_margin,
            current_ratio, quick_ratio, cash_ratio,
            debt_to_equity, debt_ratio, interest_coverage, financial_leverage,
            asset_turnover, inventory_turnover, receivable_turnover, working_capital_turnover,
            operating_cash_flow, free_cash_flow, cash_conversion_ratio,
            eps, pe_ratio, pb_ratio, ev_ebitda, dividend_yield,
            revenue_cagr, profit_cagr, eps_cagr, margin_expansion
        ) VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
        """
        
        # Prepare data for insertion
        kpi_columns = [
            'company_id', 'period',
            'roe', 'roce', 'roa', 'net_profit_margin', 'operating_margin', 'ebit_margin', 'gross_margin',
            'current_ratio', 'quick_ratio', 'cash_ratio',
            'debt_to_equity', 'debt_ratio', 'interest_coverage', 'financial_leverage',
            'asset_turnover', 'inventory_turnover', 'receivable_turnover', 'working_capital_turnover',
            'operating_cash_flow', 'free_cash_flow', 'cash_conversion_ratio',
            'eps', 'pe_ratio', 'pb_ratio', 'ev_ebitda', 'dividend_yield',
            'revenue_cagr', 'profit_cagr', 'eps_cagr', 'margin_expansion'
        ]
        
        # Insert records
        records_inserted = 0
        for _, row in df.iterrows():
            try:
                values = tuple(row.get(col) for col in kpi_columns)
                conn.execute(insert_query, values)
                records_inserted += 1
            except Exception as e:
                logger.debug(f"Failed to insert record for {row.get('company_id')}, {row.get('period')}: {str(e)}")
                continue
        
        # Commit transaction
        conn.commit()
        
        # Verify insertion
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM financial_kpis")
        total_records = cursor.fetchone()[0]
        
        logger.info(f"✓ Inserted {records_inserted} records into financial_kpis table")
        logger.info(f"✓ Total records in financial_kpis table: {total_records}")
        
        # Don't close connection - it's a singleton shared across the application
        # The connection will be closed when the application exits
        
        return True
    
    except Exception as e:
        logger.error(f"Failed to save KPIs to database: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def verify_financial_kpis_table(db_path: str = None) -> Dict[str, Any]:
    """
    Verify the financial_kpis table and return statistics.
    
    Parameters
    ----------
    db_path : str, optional
        Path to SQLite database
        
    Returns
    -------
    Dict[str, Any]
        Table statistics
    """
    try:
        import sqlite3
        from src.database.connection import get_connection
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get total records
        cursor.execute("SELECT COUNT(*) FROM financial_kpis")
        total_records = cursor.fetchone()[0]
        
        # Get unique companies
        cursor.execute("SELECT COUNT(DISTINCT company_id) FROM financial_kpis")
        unique_companies = cursor.fetchone()[0]
        
        # Get unique periods
        cursor.execute("SELECT COUNT(DISTINCT period) FROM financial_kpis")
        unique_periods = cursor.fetchone()[0]
        
        # Get sample data
        cursor.execute("SELECT * FROM financial_kpis LIMIT 5")
        sample_data = cursor.fetchall()
        
        # Get column names
        cursor.execute("PRAGMA table_info(financial_kpis)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        stats = {
            "total_records": total_records,
            "unique_companies": unique_companies,
            "unique_periods": unique_periods,
            "columns": column_names,
            "sample_data": sample_data
        }
        
        logger.info("=" * 80)
        logger.info("FINANCIAL KPIs TABLE VERIFICATION")
        logger.info("=" * 80)
        logger.info(f"Total Records: {total_records}")
        logger.info(f"Unique Companies: {unique_companies}")
        logger.info(f"Unique Periods: {unique_periods}")
        logger.info(f"Columns: {len(column_names)}")
        logger.info("=" * 80)
        
        return stats
    
    except Exception as e:
        logger.error(f"Failed to verify financial_kpis table: {str(e)}")
        return {"error": str(e)}


def main():
    """Main execution function."""
    logger.info("Starting Financial KPIs Population Script")
    
    # Populate financial_kpis table
    stats = populate_financial_kpis()
    
    if stats.get("database_save_success"):
        # Verify the table
        verification = verify_financial_kpis_table()
        
        if "error" not in verification:
            logger.info("✓ Financial KPIs table populated and verified successfully")
            return 0
        else:
            logger.error("✗ Verification failed")
            return 1
    else:
        logger.error("✗ Failed to populate financial_kpis table")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"Script failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)