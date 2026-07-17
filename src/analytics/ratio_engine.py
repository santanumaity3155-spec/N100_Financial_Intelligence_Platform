"""
ratio_engine.py

Ratio Engine Pipeline for the N100 Financial Intelligence Platform.

This module orchestrates the calculation and loading of all financial ratios,
CAGR metrics, and cash flow KPIs into the SQLite database.

Responsibilities:
1. Read cleaned financial statements (P&L, Balance Sheet, Cash Flow, Market Data)
2. Call Module 1 (ratios), Module 2 (CAGR), Module 3 (cashflow KPIs)
3. Combine all KPIs into unified records
4. Validate output data
5. Insert results into SQLite with transaction management
6. Create load summary CSV
7. Generate audit logs

This is Module 4 - ONLY responsible for orchestration and storage.
DO NOT modify analytics calculations.
"""

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import sqlite3

from src.config.logging_config import get_logger
from src.database.connection import get_connection, commit, rollback
from src.database.schema import get_table_schema
from src.analytics.ratios import calculate_all_ratios
from src.analytics.cagr import calculate_all_cagr
from src.analytics.cashflow_kpis import calculate_all_cashflow_kpis

logger = get_logger(__name__)


# =============================================================================
# CONSTANTS
# =============================================================================

OUTPUT_DIR = Path("output")
RATIO_LOAD_SUMMARY_CSV = OUTPUT_DIR / "ratio_load_summary.csv"
RATIO_ENGINE_LOG = OUTPUT_DIR / "ratio_engine.log"

# Validation thresholds
MAX_PROCESSING_TIME_MS = 5000  # 5 seconds target


# =============================================================================
# DATA VALIDATION
# =============================================================================

class ValidationError:
    """Represents a validation error."""
    
    def __init__(self, company_id: str, period: str, error_type: str, message: str):
        """
        Initialize validation error.
        
        Parameters
        ----------
        company_id : str
            Company identifier
        period : str
            Financial period
        error_type : str
            Type of validation error
        message : str
            Error message
        """
        self.company_id = company_id
        self.period = period
        self.error_type = error_type
        self.message = message
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary."""
        return {
            "company_id": self.company_id,
            "period": self.period,
            "error_type": self.error_type,
            "message": self.message
        }


def validate_company_period(
    company_id: Any,
    period: Any,
    ratios_data: Dict[str, Any],
    cagr_data: Dict[str, Any],
    cashflow_data: Dict[str, Any]
) -> List[ValidationError]:
    """
    Validate company-period record before insertion.
    
    Parameters
    ----------
    company_id : Any
        Company identifier
    period : Any
        Financial period
    ratios_data : Dict[str, Any]
        Calculated ratios
    cagr_data : Dict[str, Any]
        Calculated CAGR metrics
    cashflow_data : Dict[str, Any]
        Calculated cash flow KPIs
    
    Returns
    -------
    List[ValidationError]
        List of validation errors (empty if valid)
    """
    errors = []
    
    # Check missing company_id
    if company_id is None or (isinstance(company_id, str) and not company_id.strip()):
        errors.append(ValidationError(
            str(company_id), str(period), "MISSING_COMPANY_ID",
            "Company ID is missing or empty"
        ))
    
    # Check missing period
    if period is None or (isinstance(period, str) and not period.strip()):
        errors.append(ValidationError(
            str(company_id), str(period), "MISSING_PERIOD",
            "Period is missing or empty"
        ))
    
    # Check for NaN values in critical fields
    critical_fields = [
        "net_profit_margin", "roe", "roa", "debt_to_equity",
        "revenue_cagr_3yr", "free_cash_flow"
    ]
    
    all_data = {**ratios_data, **cagr_data, **cashflow_data}
    
    for field in critical_fields:
        value = all_data.get(field)
        if value is not None and isinstance(value, dict):
            value = value.get("value")
        
        if value is not None and (pd.isna(value) or (isinstance(value, float) and (value != value))):
            errors.append(ValidationError(
                str(company_id), str(period), "NaN_VALUE",
                f"Field '{field}' contains NaN"
            ))
    
    # Check for infinite values
    for field, value in all_data.items():
        if isinstance(value, (int, float)) and (value == float('inf') or value == float('-inf')):
            errors.append(ValidationError(
                str(company_id), str(period), "INFINITE_VALUE",
                f"Field '{field}' contains infinite value"
            ))
    
    # Check negative assets (if total_assets is available)
    if "total_assets" in all_data:
        total_assets = all_data["total_assets"]
        if total_assets is not None and total_assets < 0:
            errors.append(ValidationError(
                str(company_id), str(period), "NEGATIVE_ASSETS",
                f"Total assets is negative: {total_assets}"
            ))
    
    # Check invalid equity
    if "equity" in all_data:
        equity = all_data["equity"]
        if equity is not None and equity <= 0:
            errors.append(ValidationError(
                str(company_id), str(period), "INVALID_EQUITY",
                f"Equity is zero or negative: {equity}"
            ))
    
    return errors


def validate_financial_data_availability(
    company_id: str,
    period: str,
    pl_data: pd.DataFrame,
    bs_data: pd.DataFrame,
    cf_data: pd.DataFrame
) -> List[ValidationError]:
    """
    Validate that required financial data is available.
    
    Parameters
    ----------
    company_id : str
        Company identifier
    period : str
        Financial period
    pl_data : pd.DataFrame
        Profit & Loss data
    bs_data : pd.DataFrame
        Balance Sheet data
    cf_data : pd.DataFrame
        Cash Flow data
    
    Returns
    -------
    List[ValidationError]
        List of validation errors
    """
    errors = []
    
    if pl_data.empty:
        errors.append(ValidationError(
            company_id, period, "MISSING_PL",
            "Profit & Loss data is missing"
        ))
    
    if bs_data.empty:
        errors.append(ValidationError(
            company_id, period, "MISSING_BS",
            "Balance Sheet data is missing"
        ))
    
    if cf_data.empty:
        errors.append(ValidationError(
            company_id, period, "MISSING_CF",
            "Cash Flow data is missing"
        ))
    
    return errors


# =============================================================================
# DATABASE OPERATIONS
# =============================================================================

def insert_financial_ratios(record: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Insert or update a financial ratios record in the database.
    
    Uses INSERT OR REPLACE to handle duplicates and support reruns.
    
    Parameters
    ----------
    record : Dict[str, Any]
        Financial ratios record to insert
    
    Returns
    -------
    Tuple[bool, Optional[str]]
        (success, error_message)
    """
    try:
        conn = get_connection()
        
        # Prepare column names and placeholders
        columns = list(record.keys())
        placeholders = ", ".join(["?"] * len(columns))
        column_names = ", ".join(columns)
        
        # Prepare values
        values = tuple(record.values())
        
        # Use INSERT OR REPLACE to handle duplicates
        sql = f"""
            INSERT OR REPLACE INTO financial_ratios ({column_names})
            VALUES ({placeholders})
        """
        
        conn.execute(sql, values)
        return True, None
        
    except sqlite3.Error as e:
        error_msg = f"Database error: {str(e)}"
        logger.error(f"Failed to insert record for {record.get('company_id')}, {record.get('period')}: {error_msg}")
        return False, error_msg
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(f"Failed to insert record for {record.get('company_id')}, {record.get('period')}: {error_msg}")
        return False, error_msg


def check_duplicate_period(company_id: str, period: str) -> bool:
    """
    Check if a company-period combination already exists.
    
    Parameters
    ----------
    company_id : str
        Company identifier
    period : str
        Financial period
    
    Returns
    -------
    bool
        True if duplicate exists, False otherwise
    """
    try:
        conn = get_connection()
        cursor = conn.execute(
            "SELECT COUNT(*) FROM financial_ratios WHERE company_id = ? AND period = ?",
            (company_id, period)
        )
        count = cursor.fetchone()[0]
        return count > 0
    except Exception as e:
        logger.error(f"Failed to check duplicate for {company_id}, {period}: {str(e)}")
        return False


# =============================================================================
# DATA MERGING
# =============================================================================

def merge_kpi_data(
    company_id: str,
    period: str,
    company_name: Optional[str],
    industry: Optional[str],
    sector: Optional[str],
    ratios_data: Dict[str, Any],
    cagr_data: Dict[str, Any],
    cashflow_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Merge all KPI data into a single record.
    
    Parameters
    ----------
    company_id : str
        Company identifier
    period : str
        Financial period
    company_name : Optional[str]
        Company name
    industry : Optional[str]
        Industry classification
    sector : Optional[str]
        Sector classification
    ratios_data : Dict[str, Any]
        Calculated ratios
    cagr_data : Dict[str, Any]
        Calculated CAGR metrics
    cashflow_data : Dict[str, Any]
        Calculated cash flow KPIs
    
    Returns
    -------
    Dict[str, Any]
        Merged record
    """
    # Start with base information
    record = {
        "company_id": company_id,
        "period": period,
        "company_name": company_name,
        "industry": industry,
        "sector": sector,
    }
    
    # Merge ratios data
    for key, value in ratios_data.items():
        if key not in ["company_id", "period"]:
            record[key] = value
    
    # Merge CAGR data
    for key, value in cagr_data.items():
        if key not in ["company_id", "period"]:
            # CAGR data comes as {"value": X, "flag": Y}
            if isinstance(value, dict):
                record[key] = value.get("value")
                record[f"{key}_flag"] = value.get("flag")
            else:
                record[key] = value
    
    # Merge cashflow data
    for key, value in cashflow_data.items():
        if key not in ["company_id", "period"]:
            if isinstance(value, dict):
                record[key] = value.get("value")
            else:
                record[key] = value
    
    # Add timestamps
    record["created_at"] = datetime.now().isoformat()
    record["updated_at"] = datetime.now().isoformat()
    
    return record


# =============================================================================
# COMPANY PROCESSING
# =============================================================================

def process_company(
    company_id: str,
    company_data: Dict[str, Any],
    pl_df: pd.DataFrame,
    bs_df: pd.DataFrame,
    cf_df: pd.DataFrame,
    market_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Process a single company and calculate all KPIs.
    
    Parameters
    ----------
    company_id : str
        Company identifier
    company_data : Dict[str, Any]
        Company metadata (name, industry, sector)
    pl_df : pd.DataFrame
        Profit & Loss data for all periods
    bs_df : pd.DataFrame
        Balance Sheet data for all periods
    cf_df : pd.DataFrame
        Cash Flow data for all periods
    market_data : Optional[Dict[str, Any]]
        Market data (optional)
    
    Returns
    -------
    Dict[str, Any]
        Processing result with status, errors, and record data
    """
    start_time = time.time()
    result = {
        "company_id": company_id,
        "status": "success",
        "validation_errors": [],
        "record": None,
        "processing_time_ms": 0
    }
    
    try:
        logger.info(f"Processing company: {company_id}")
        
        # Get company metadata
        company_name = company_data.get("company_name")
        industry = company_data.get("industry")
        sector = company_data.get("sector")
        
        # Get unique periods (use P&L as primary source)
        if pl_df.empty:
            result["status"] = "failed"
            result["validation_errors"].append({
                "error_type": "NO_DATA",
                "message": "No P&L data available"
            })
            return result
        
        periods = pl_df["period"].unique() if "period" in pl_df.columns else []
        
        if len(periods) == 0:
            result["status"] = "failed"
            result["validation_errors"].append({
                "error_type": "NO_PERIODS",
                "message": "No periods found in P&L data"
            })
            return result
        
        # Process each period
        for period in periods:
            try:
                # Filter data for this period
                pl_period = pl_df[pl_df["period"] == period] if "period" in pl_df.columns else pl_df
                bs_period = bs_df[bs_df["period"] == period] if "period" in bs_df.columns else bs_df
                cf_period = cf_df[cf_df["period"] == period] if "period" in cf_df.columns else cf_df
                
                # Validate data availability
                validation_errors = validate_financial_data_availability(
                    company_id, period, pl_period, bs_period, cf_period
                )
                
                if validation_errors:
                    result["validation_errors"].extend([e.to_dict() for e in validation_errors])
                    logger.warning(f"Validation errors for {company_id}, {period}: {len(validation_errors)} errors")
                    continue
                
                # Calculate all ratios (Module 1)
                ratios_data = calculate_all_ratios(company_id, period)
                
                # Calculate all CAGR (Module 2)
                cagr_data = calculate_all_cagr(pl_df, company_id, period)
                
                # Calculate all cash flow KPIs (Module 3)
                cashflow_data = calculate_all_cashflow_kpis(cf_period, pl_period, bs_period, company_id, period)
                
                # Merge all data
                record = merge_kpi_data(
                    company_id, period, company_name, industry, sector,
                    ratios_data, cagr_data, cashflow_data
                )
                
                # Validate merged record
                record_errors = validate_company_period(
                    company_id, period, ratios_data, cagr_data, cashflow_data
                )
                
                if record_errors:
                    result["validation_errors"].extend([e.to_dict() for e in record_errors])
                    logger.warning(f"Record validation errors for {company_id}, {period}: {len(record_errors)} errors")
                    continue
                
                # Store record for insertion
                if result["record"] is None:
                    result["record"] = record
                else:
                    # Multiple periods - store as list
                    if not isinstance(result["record"], list):
                        result["record"] = [result["record"]]
                    result["record"].append(record)
                
            except Exception as e:
                logger.error(f"Error processing period {period} for {company_id}: {str(e)}")
                result["validation_errors"].append({
                    "error_type": "PROCESSING_ERROR",
                    "message": str(e)
                })
        
        # Update status based on results
        if result["record"] is None:
            result["status"] = "failed"
        elif result["validation_errors"]:
            result["status"] = "partial_success"
        
    except Exception as e:
        logger.error(f"Failed to process company {company_id}: {str(e)}")
        result["status"] = "failed"
        result["validation_errors"].append({
            "error_type": "FATAL_ERROR",
            "message": str(e)
        })
    
    finally:
        # Calculate processing time
        end_time = time.time()
        result["processing_time_ms"] = int((end_time - start_time) * 1000)
    
    return result


# =============================================================================
# PIPELINE ORCHESTRATION
# =============================================================================

class RatioEnginePipeline:
    """
    Main pipeline orchestrator for the Ratio Engine.
    
    Coordinates the calculation and loading of all financial KPIs.
    """
    
    def __init__(self, output_dir: Path = OUTPUT_DIR):
        """
        Initialize pipeline.
        
        Parameters
        ----------
        output_dir : Path, optional
            Output directory for logs and summaries, by default OUTPUT_DIR
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.pipeline_stats = {
            "start_time": None,
            "end_time": None,
            "status": "not_started",
            "companies_processed": 0,
            "companies_failed": 0,
            "rows_inserted": 0,
            "rows_skipped": 0,
            "validation_failures": 0,
            "total_processing_time_ms": 0,
            "errors": []
        }
        
        self.load_summary = []
    
    def run(self, companies_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the complete ratio engine pipeline.
        
        Parameters
        ----------
        companies_data : Dict[str, Any]
            Dictionary mapping company_id to company data including
            P&L, Balance Sheet, Cash Flow, and Market Data
        
        Returns
        -------
        Dict[str, Any]
            Pipeline statistics and results
        """
        self.pipeline_stats["start_time"] = datetime.now().isoformat()
        
        logger.info("=" * 80)
        logger.info("STARTING RATIO ENGINE PIPELINE")
        logger.info("=" * 80)
        logger.info(f"Processing {len(companies_data)} companies")
        
        try:
            # Process each company
            for company_id, company_data in companies_data.items():
                try:
                    self._process_single_company(company_id, company_data)
                except Exception as e:
                    logger.error(f"Failed to process company {company_id}: {str(e)}")
                    self.pipeline_stats["companies_failed"] += 1
                    self.pipeline_stats["errors"].append({
                        "company_id": company_id,
                        "error": str(e)
                    })
            
            # Generate outputs
            self._generate_load_summary()
            self._log_pipeline_summary()
            
            self.pipeline_stats["status"] = "completed"
            
        except Exception as e:
            self.pipeline_stats["status"] = "failed"
            self.pipeline_stats["errors"].append(str(e))
            logger.error(f"Pipeline failed: {str(e)}")
        
        finally:
            self.pipeline_stats["end_time"] = datetime.now().isoformat()
        
        logger.info("=" * 80)
        logger.info("RATIO ENGINE PIPELINE COMPLETED")
        logger.info("=" * 80)
        
        return self.pipeline_stats
    
    def _process_single_company(self, company_id: str, company_data: Dict[str, Any]) -> None:
        """
        Process a single company.
        
        Parameters
        ----------
        company_id : str
            Company identifier
        company_data : Dict[str, Any]
            Company data including financial statements
        """
        logger.info(f"Processing company: {company_id}")
        
        # Extract financial data
        pl_df = company_data.get("profit_loss", pd.DataFrame())
        bs_df = company_data.get("balance_sheet", pd.DataFrame())
        cf_df = company_data.get("cash_flow", pd.DataFrame())
        market_data = company_data.get("market_data", {})
        
        # Process company
        result = process_company(
            company_id, company_data, pl_df, bs_df, cf_df, market_data
        )
        
        # Update statistics
        self.pipeline_stats["companies_processed"] += 1
        self.pipeline_stats["total_processing_time_ms"] += result["processing_time_ms"]
        
        # Handle validation errors
        if result["validation_errors"]:
            self.pipeline_stats["validation_failures"] += len(result["validation_errors"])
        
        # Insert into database
        if result["status"] in ["success", "partial_success"] and result["record"]:
            records = result["record"] if isinstance(result["record"], list) else [result["record"]]
            
            for record in records:
                try:
                    # Begin transaction
                    conn = get_connection()
                    
                    # Insert record
                    success, error_msg = insert_financial_ratios(record)
                    
                    if success:
                        conn.commit()
                        self.pipeline_stats["rows_inserted"] += 1
                        logger.info(f"Successfully inserted {company_id}, {record['period']}")
                    else:
                        conn.rollback()
                        self.pipeline_stats["rows_skipped"] += 1
                        logger.error(f"Failed to insert {company_id}, {record['period']}: {error_msg}")
                
                except Exception as e:
                    try:
                        rollback()
                    except:
                        pass
                    self.pipeline_stats["rows_skipped"] += 1
                    logger.error(f"Transaction failed for {company_id}: {str(e)}")
        else:
            self.pipeline_stats["rows_skipped"] += 1
            logger.warning(f"Skipping {company_id} - no valid records")
        
        # Add to load summary
        self.load_summary.append({
            "company_id": company_id,
            "period": company_data.get("period", "multiple"),
            "status": result["status"],
            "inserted": result["record"] is not None,
            "validation_errors": len(result["validation_errors"]),
            "processing_time_ms": result["processing_time_ms"]
        })
    
    def _generate_load_summary(self) -> None:
        """Generate load summary CSV file."""
        try:
            df = pd.DataFrame(self.load_summary)
            df.to_csv(RATIO_LOAD_SUMMARY_CSV, index=False)
            logger.info(f"Load summary generated: {RATIO_LOAD_SUMMARY_CSV}")
        except Exception as e:
            logger.error(f"Failed to generate load summary: {str(e)}")
    
    def _log_pipeline_summary(self) -> None:
        """Log pipeline summary statistics."""
        stats = self.pipeline_stats
        
        avg_time = 0
        if stats["companies_processed"] > 0:
            avg_time = stats["total_processing_time_ms"] / stats["companies_processed"]
        
        summary = f"""
Pipeline Summary
================
Companies Processed: {stats['companies_processed']}
Companies Failed: {stats['companies_failed']}
Rows Inserted: {stats['rows_inserted']}
Rows Skipped: {stats['rows_skipped']}
Validation Failures: {stats['validation_failures']}
Average Processing Time: {avg_time:.2f} ms
Total Runtime: {stats['total_processing_time_ms']} ms
Status: {stats.get('status', 'unknown')}
        """
        
        logger.info(summary)
        
        # Also write to dedicated log file
        try:
            with open(RATIO_ENGINE_LOG, 'w') as f:
                f.write(f"Ratio Engine Pipeline Log\n")
                f.write(f"Generated: {datetime.now().isoformat()}\n")
                f.write("=" * 80 + "\n")
                f.write(summary)
                f.write("\n")
                
                if stats["errors"]:
                    f.write("\nErrors:\n")
                    f.write("-" * 80 + "\n")
                    for error in stats["errors"]:
                        f.write(f"{error}\n")
            
            logger.info(f"Pipeline log generated: {RATIO_ENGINE_LOG}")
        except Exception as e:
            logger.error(f"Failed to write pipeline log: {str(e)}")


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def run_ratio_engine_pipeline(companies_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point for the Ratio Engine Pipeline.
    
    Parameters
    ----------
    companies_data : Dict[str, Any]
        Dictionary mapping company_id to company data including
        P&L, Balance Sheet, Cash Flow, and Market Data
    
    Returns
    -------
    Dict[str, Any]
        Pipeline statistics and results
    
    Example
    -------
    >>> companies_data = {
    ...     "RELIANCE": {
    ...         "company_name": "Reliance Industries",
    ...         "industry": "Refineries",
    ...         "sector": "Energy",
    ...         "profit_loss": pl_df,
    ...         "balance_sheet": bs_df,
    ...         "cash_flow": cf_df
    ...     }
    ... }
    >>> stats = run_ratio_engine_pipeline(companies_data)
    """
    pipeline = RatioEnginePipeline()
    return pipeline.run(companies_data)


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_pipeline_statistics() -> Dict[str, Any]:
    """
    Get current pipeline statistics from the database.
    
    Returns
    -------
    Dict[str, Any]
        Database statistics
    """
    try:
        conn = get_connection()
        
        # Total records
        cursor = conn.execute("SELECT COUNT(*) FROM financial_ratios")
        total_records = cursor.fetchone()[0]
        
        # Records by sector
        cursor = conn.execute("""
            SELECT sector, COUNT(*) as count 
            FROM financial_ratios 
            WHERE sector IS NOT NULL 
            GROUP BY sector
        """)
        by_sector = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Records by period
        cursor = conn.execute("""
            SELECT period, COUNT(*) as count 
            FROM financial_ratios 
            GROUP BY period 
            ORDER BY period DESC 
            LIMIT 10
        """)
        by_period = {row[0]: row[1] for row in cursor.fetchall()}
        
        return {
            "total_records": total_records,
            "by_sector": by_sector,
            "by_period": by_period
        }
    
    except Exception as e:
        logger.error(f"Failed to get pipeline statistics: {str(e)}")
        return {}


def validate_database_integrity() -> Dict[str, Any]:
    """
    Validate database integrity for financial_ratios table.
    
    Returns
    -------
    Dict[str, Any]
        Validation results
    """
    try:
        conn = get_connection()
        
        results = {
            "valid": True,
            "checks": []
        }
        
        # Check for duplicates
        cursor = conn.execute("""
            SELECT company_id, period, COUNT(*) as count
            FROM financial_ratios
            GROUP BY company_id, period
            HAVING count > 1
        """)
        duplicates = cursor.fetchall()
        
        if duplicates:
            results["valid"] = False
            results["checks"].append({
                "check": "duplicates",
                "status": "failed",
                "count": len(duplicates)
            })
        else:
            results["checks"].append({
                "check": "duplicates",
                "status": "passed"
            })
        
        # Check for missing company_id
        cursor = conn.execute("""
            SELECT COUNT(*) FROM financial_ratios WHERE company_id IS NULL
        """)
        missing_company_id = cursor.fetchone()[0]
        
        if missing_company_id > 0:
            results["valid"] = False
            results["checks"].append({
                "check": "missing_company_id",
                "status": "failed",
                "count": missing_company_id
            })
        else:
            results["checks"].append({
                "check": "missing_company_id",
                "status": "passed"
            })
        
        # Check for missing period
        cursor = conn.execute("""
            SELECT COUNT(*) FROM financial_ratios WHERE period IS NULL
        """)
        missing_period = cursor.fetchone()[0]
        
        if missing_period > 0:
            results["valid"] = False
            results["checks"].append({
                "check": "missing_period",
                "status": "failed",
                "count": missing_period
            })
        else:
            results["checks"].append({
                "check": "missing_period",
                "status": "passed"
            })
        
        return results
    
    except Exception as e:
        logger.error(f"Failed to validate database integrity: {str(e)}")
        return {"valid": False, "error": str(e)}