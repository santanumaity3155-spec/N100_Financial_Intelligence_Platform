"""
peer.py

Peer Percentile Ranking Engine for the N100 Financial Intelligence Platform.

This module computes percentile rankings of companies within their peer groups
across multiple financial metrics.

Responsibilities:
1. Load peer groups from database or Excel
2. Assign companies to peer groups
3. Calculate percentile rankings for 10 financial metrics
4. Handle Debt-to-Equity inversion (lower is better)
5. Store results in SQLite with UPSERT support
6. Export clean CSV outputs
7. Validate data integrity
8. Handle missing peer groups safely

Metrics Ranked:
- ROE (Return on Equity)
- ROCE (Return on Capital Employed)
- Net Profit Margin
- Debt to Equity (inverted - lower is better)
- Free Cash Flow
- Revenue CAGR 5 Year
- PAT CAGR 5 Year
- EPS CAGR 5 Year
- Interest Coverage Ratio
- Asset Turnover
"""

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import sqlite3

from src.config.constants import (
    PROJECT_ROOT,
    RAW_DATA_DIR,
    OUTPUT_DIR,
    DATABASE_DIR,
)
from src.config.logging_config import get_logger
from src.database.connection import get_connection, commit, rollback
from src.database.schema import get_table_schema

logger = get_logger(__name__)

# =============================================================================
# CONSTANTS
# =============================================================================

# Output paths
PEER_PERCENTILES_CSV = OUTPUT_DIR / "peer_percentiles.csv"
PEER_ANALYSIS_LOG = OUTPUT_DIR / "peer_analysis.log"

# Supported metrics for percentile ranking
SUPPORTED_METRICS = [
    "roe",
    "roce",
    "net_profit_margin",
    "debt_to_equity",
    "free_cash_flow",
    "revenue_cagr_5yr",
    "pat_cagr_5yr",
    "eps_cagr_5yr",
    "interest_coverage",
    "asset_turnover",
]

# Metrics where lower is better (need inversion)
INVERTED_METRICS = ["debt_to_equity"]

# All 11 peer groups supported by the platform
SUPPORTED_PEER_GROUPS = [
    "IT Services",
    "Banks",
    "Financial Services",
    "FMCG",
    "Pharmaceuticals",
    "Automobiles",
    "Metals",
    "Energy",
    "Infrastructure",
    "Cement",
    "Consumer Goods",
]

# Column mappings from various source tables to standardized metrics
METRIC_COLUMN_MAPPING = {
    # From financial_ratios table
    "roe": "roe",
    "roce": "roce",
    "net_profit_margin": "net_profit_margin",
    "debt_to_equity": "debt_to_equity",
    "free_cash_flow": "free_cash_flow",
    "revenue_cagr_5yr": "revenue_cagr_5yr",
    "pat_cagr_5yr": "pat_cagr_5yr",
    "eps_cagr_5yr": "eps_cagr_5yr",
    "interest_coverage": "interest_coverage",
    "asset_turnover": "asset_turnover",
}


# =============================================================================
# CUSTOM EXCEPTIONS
# =============================================================================

class PeerAnalysisError(Exception):
    """Base exception for peer analysis errors."""
    pass


class PeerGroupNotFoundError(PeerAnalysisError):
    """Raised when peer group is not found."""
    pass


class MetricNotFoundError(PeerAnalysisError):
    """Raised when metric is not found."""
    pass


class ValidationError:
    """Represents a validation error."""
    
    def __init__(self, company_id: str, peer_group: str, error_type: str, message: str):
        """
        Initialize validation error.
        
        Parameters
        ----------
        company_id : str
            Company identifier
        peer_group : str
            Peer group name
        error_type : str
            Type of validation error
        message : str
            Error message
        """
        self.company_id = company_id
        self.peer_group = peer_group
        self.error_type = error_type
        self.message = message
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary."""
        return {
            "company_id": self.company_id,
            "peer_group": self.peer_group,
            "error_type": self.error_type,
            "message": self.message
        }


# =============================================================================
# PEER GROUP LOADING
# =============================================================================

def load_peer_groups(source: str = "database") -> pd.DataFrame:
    """
    Load peer groups from database or Excel file.
    
    Parameters
    ----------
    source : str, optional
        Source of peer groups: "database" or "excel", by default "database"
    
    Returns
    -------
    pd.DataFrame
        DataFrame with columns: company_id, peer_group_name, is_benchmark
    
    Raises
    ------
    FileNotFoundError
        If Excel file is not found when source="excel"
    sqlite3.Error
        If database query fails
    """
    logger.info(f"Loading peer groups from {source}")
    
    try:
        if source == "excel":
            # Load from Excel file
            excel_path = RAW_DATA_DIR / "peer_groups.xlsx"
            
            if not excel_path.exists():
                raise FileNotFoundError(f"Peer groups Excel file not found: {excel_path}")
            
            df = pd.read_excel(excel_path)
            logger.info(f"Loaded {len(df)} peer group records from Excel")
            
        elif source == "database":
            # Load from database
            conn = get_connection()
            query = """
                SELECT 
                    company_id,
                    peer_group_name,
                    is_benchmark
                FROM peer_groups
                WHERE peer_group_name IS NOT NULL
            """
            df = pd.read_sql_query(query, conn)
            logger.info(f"Loaded {len(df)} peer group records from database")
            
        else:
            raise ValueError(f"Invalid source: {source}. Must be 'database' or 'excel'")
        
        # Validate required columns
        required_cols = ["company_id", "peer_group_name"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            raise PeerAnalysisError(
                f"Missing required columns in peer groups data: {missing_cols}"
            )
        
        # Add is_benchmark column if missing (default to 0)
        if "is_benchmark" not in df.columns:
            df["is_benchmark"] = 0
        
        logger.info(f"Successfully loaded {len(df)} peer group assignments")
        return df
        
    except Exception as e:
        logger.error(f"Failed to load peer groups: {str(e)}")
        raise


def assign_peer_groups(df: pd.DataFrame, company_id_col: str = "company_id") -> pd.DataFrame:
    """
    Assign peer groups to companies in a DataFrame.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing company data
    company_id_col : str, optional
        Name of company_id column, by default "company_id"
    
    Returns
    -------
    pd.DataFrame
        DataFrame with added peer_group_name column
    """
    logger.info("Assigning peer groups to companies")
    
    try:
        # Load peer groups
        peer_groups_df = load_peer_groups(source="database")
        
        # Create mapping dictionary
        peer_group_map = dict(zip(
            peer_groups_df["company_id"],
            peer_groups_df["peer_group_name"]
        ))
        
        # Map peer groups to companies
        df["peer_group_name"] = df[company_id_col].map(peer_group_map)
        
        # Fill missing peer groups with "No peer group assigned"
        df["peer_group_name"] = df["peer_group_name"].fillna("No peer group assigned")
        
        # Log statistics
        assigned_count = (df["peer_group_name"] != "No peer group assigned").sum()
        unassigned_count = (df["peer_group_name"] == "No peer group assigned").sum()
        
        logger.info(
            f"Peer group assignment complete: {assigned_count} assigned, "
            f"{unassigned_count} unassigned"
        )
        
        return df
        
    except Exception as e:
        logger.error(f"Failed to assign peer groups: {str(e)}")
        raise


# =============================================================================
# PERCENTILE CALCULATION
# =============================================================================

def calculate_percentile_rank(series: pd.Series, invert: bool = False) -> pd.Series:
    """
    Calculate percentile rank for a series of values.
    
    Uses PERCENT_RANK style: (rank - 1) / (n - 1)
    
    Parameters
    ----------
    series : pd.Series
        Series of numeric values
    invert : bool, optional
        If True, invert the percentile (1 - percentile), by default False
        Used for metrics where lower is better (e.g., Debt to Equity)
    
    Returns
    -------
    pd.Series
        Series of percentile ranks between 0 and 1
    """
    # Remove NaN values for calculation
    valid_mask = series.notna()
    
    # Initialize result with NaN
    result = pd.Series(index=series.index, dtype=float)
    
    if valid_mask.sum() == 0:
        return result
    
    valid_values = series[valid_mask]
    n = len(valid_values)
    
    if n == 1:
        # Single value gets percentile 0.5
        result[valid_mask] = 0.5
    else:
        # Calculate percentile rank using pandas rank
        # method='min' gives the minimum rank for ties
        ranks = valid_values.rank(method='min', ascending=True)
        percentiles = (ranks - 1) / (n - 1)
        
        # Clip to [0, 1] range
        percentiles = percentiles.clip(0, 1)
        
        # Invert if needed (for metrics where lower is better)
        if invert:
            percentiles = 1 - percentiles
        
        result[valid_mask] = percentiles
    
    return result


def calculate_metric_percentiles(
    df: pd.DataFrame,
    metric: str,
    group_by: str = "peer_group_name",
    invert: bool = False
) -> pd.DataFrame:
    """
    Calculate percentile rankings for a specific metric within peer groups.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing metric values and peer group assignments
    metric : str
        Name of the metric column to rank
    group_by : str, optional
        Column to group by (typically peer_group_name), by default "peer_group_name"
    invert : bool, optional
        If True, invert the percentile ranking, by default False
    
    Returns
    -------
    pd.DataFrame
        DataFrame with added percentile_rank column for the metric
    
    Raises
    ------
    KeyError
        If metric column is not found in DataFrame
    """
    logger.info(f"Calculating percentiles for metric: {metric}")
    
    if metric not in df.columns:
        raise KeyError(f"Metric column '{metric}' not found in DataFrame")
    
    # Create a copy to avoid modifying original
    result_df = df.copy()
    
    # Calculate percentiles within each peer group
    result_df[f"{metric}_percentile"] = result_df.groupby(group_by)[metric].transform(
        lambda x: calculate_percentile_rank(x, invert=invert)
    )
    
    # Log statistics
    valid_percentiles = result_df[f"{metric}_percentile"].notna().sum()
    logger.info(
        f"Calculated percentiles for {valid_percentiles} companies "
        f"(invert={invert})"
    )
    
    return result_df


def calculate_all_percentiles(
    df: pd.DataFrame,
    metrics: Optional[List[str]] = None,
    group_by: str = "peer_group_name"
) -> pd.DataFrame:
    """
    Calculate percentile rankings for all specified metrics within peer groups.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing metric values and peer group assignments
    metrics : Optional[List[str]], optional
        List of metrics to rank, by default None (uses SUPPORTED_METRICS)
    group_by : str, optional
        Column to group by, by default "peer_group_name"
    
    Returns
    -------
    pd.DataFrame
        DataFrame with added percentile columns for all metrics
    """
    logger.info("Calculating percentiles for all metrics")
    
    if metrics is None:
        metrics = SUPPORTED_METRICS
    
    result_df = df.copy()
    
    for metric in metrics:
        # Check if metric exists in DataFrame
        if metric not in result_df.columns:
            logger.warning(f"Metric '{metric}' not found in DataFrame, skipping")
            continue
        
        # Determine if metric needs inversion
        invert = metric in INVERTED_METRICS
        
        # Calculate percentiles
        result_df = calculate_metric_percentiles(
            result_df, metric, group_by=group_by, invert=invert
        )
    
    logger.info(f"Completed percentile calculation for {len(metrics)} metrics")
    return result_df


# =============================================================================
# DATABASE OPERATIONS
# =============================================================================

def save_peer_percentiles(
    df: pd.DataFrame,
    period: str,
    metrics: Optional[List[str]] = None,
    batch_size: int = 1000
) -> Dict[str, Any]:
    """
    Save peer percentile rankings to SQLite database.
    
    Uses UPSERT (INSERT OR REPLACE) to handle duplicates.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing percentile rankings
    period : str
        Financial period (e.g., "FY2024")
    metrics : Optional[List[str]], optional
        List of metrics to save, by default None (uses SUPPORTED_METRICS)
    batch_size : int, optional
        Number of records to insert per batch, by default 1000
    
    Returns
    -------
    Dict[str, Any]
        Dictionary with insertion statistics
    
    Raises
    ------
    sqlite3.Error
        If database operation fails
    """
    logger.info(f"Saving peer percentiles to database for period: {period}")
    
    if metrics is None:
        metrics = SUPPORTED_METRICS
    
    start_time = time.time()
    stats = {
        "total_records": 0,
        "successful_inserts": 0,
        "failed_inserts": 0,
        "skipped_records": 0,
    }
    
    try:
        # Ensure table exists
        conn = get_connection()
        conn.execute(get_table_schema("peer_percentiles"))
        
        # Prepare records for insertion
        records = []
        
        for _, row in df.iterrows():
            company_id = row.get("company_id")
            peer_group = row.get("peer_group_name", "No peer group assigned")
            
            # Skip companies without peer groups
            if peer_group == "No peer group assigned":
                stats["skipped_records"] += 1
                continue
            
            # Create a record for each metric
            for metric in metrics:
                percentile_col = f"{metric}_percentile"
                
                # Skip if percentile column doesn't exist
                if percentile_col not in row:
                    stats["skipped_records"] += 1
                    continue
                
                metric_value = row.get(metric)
                percentile_rank = row.get(percentile_col)
                
                # Skip if percentile is NaN
                if pd.isna(percentile_rank):
                    stats["skipped_records"] += 1
                    continue
                
                # Create record
                record = {
                    "company_id": company_id,
                    "peer_group_name": peer_group,
                    "metric": metric,
                    "metric_value": metric_value if not pd.isna(metric_value) else None,
                    "percentile_rank": float(percentile_rank),
                    "period": period,
                    "created_at": datetime.now().isoformat(),
                }
                
                records.append(record)
                stats["total_records"] += 1
        
        # Batch insert records
        if records:
            # Use INSERT OR REPLACE for UPSERT support
            sql = """
                INSERT OR REPLACE INTO peer_percentiles 
                (company_id, peer_group_name, metric, metric_value, percentile_rank, period, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            
            batch_count = 0
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                
                try:
                    conn.executemany(sql, [
                        (
                            r["company_id"],
                            r["peer_group_name"],
                            r["metric"],
                            r["metric_value"],
                            r["percentile_rank"],
                            r["period"],
                            r["created_at"],
                        )
                        for r in batch
                    ])
                    conn.commit()
                    stats["successful_inserts"] += len(batch)
                    batch_count += 1
                    
                except sqlite3.Error as e:
                    conn.rollback()
                    logger.error(f"Failed to insert batch {batch_count}: {str(e)}")
                    stats["failed_inserts"] += len(batch)
        
        elapsed_time = time.time() - start_time
        logger.info(
            f"Database save complete: {stats['successful_inserts']} inserted, "
            f"{stats['failed_inserts']} failed, {stats['skipped_records']} skipped "
            f"in {elapsed_time:.2f}s"
        )
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to save peer percentiles: {str(e)}")
        raise


# =============================================================================
# EXPORT FUNCTIONS
# =============================================================================

def export_percentiles(
    df: pd.DataFrame,
    output_path: Optional[Path] = None,
    period: Optional[str] = None
) -> Path:
    """
    Export peer percentiles to CSV.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing percentile rankings
    output_path : Optional[Path], optional
        Output file path, by default None (uses PEER_PERCENTILES_CSV)
    period : Optional[str], optional
        Financial period to filter by, by default None (exports all)
    
    Returns
    -------
    Path
        Path to exported CSV file
    
    Raises
    ------
    IOError
        If file cannot be written
    """
    logger.info("Exporting peer percentiles to CSV")
    
    if output_path is None:
        output_path = PEER_PERCENTILES_CSV
    
    try:
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Prepare export DataFrame
        export_df = df.copy()
        
        # Filter by period if specified
        if period and "period" in export_df.columns:
            export_df = export_df[export_df["period"] == period]
        
        # Melt percentile columns to long format
        percentile_cols = [f"{m}_percentile" for m in SUPPORTED_METRICS if f"{m}_percentile" in export_df.columns]
        
        if not percentile_cols:
            logger.warning("No percentile columns found for export")
            export_df.to_csv(output_path, index=False)
            return output_path
        
        # Create long format DataFrame
        export_records = []
        
        for _, row in export_df.iterrows():
            company_id = row.get("company_id")
            company_name = row.get("company_name", "")
            peer_group = row.get("peer_group_name", "No peer group assigned")
            period_val = row.get("period", period or "")
            
            for metric in SUPPORTED_METRICS:
                percentile_col = f"{metric}_percentile"
                
                if percentile_col not in row:
                    continue
                
                percentile_rank = row.get(percentile_col)
                metric_value = row.get(metric)
                
                # Skip if percentile is NaN
                if pd.isna(percentile_rank):
                    continue
                
                export_records.append({
                    "company_id": company_id,
                    "company_name": company_name,
                    "peer_group": peer_group,
                    "metric": metric,
                    "metric_value": metric_value if not pd.isna(metric_value) else None,
                    "percentile_rank": round(float(percentile_rank), 4),
                    "period": period_val,
                })
        
        export_df_final = pd.DataFrame(export_records)
        
        # Sort by peer group, metric, and percentile rank
        export_df_final = export_df_final.sort_values(
            ["peer_group", "metric", "percentile_rank"],
            ascending=[True, True, False]
        )
        
        # Write to CSV
        export_df_final.to_csv(output_path, index=False)
        
        logger.info(
            f"Exported {len(export_df_final)} percentile records to {output_path}"
        )
        
        return output_path
        
    except Exception as e:
        logger.error(f"Failed to export percentiles: {str(e)}")
        raise IOError(f"Failed to export percentiles: {str(e)}")


# =============================================================================
# SUMMARY AND VALIDATION
# =============================================================================

def get_peer_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate summary statistics for peer percentile analysis.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing percentile rankings
    
    Returns
    -------
    Dict[str, Any]
        Summary statistics
    """
    logger.info("Generating peer percentile summary")
    
    summary = {
        "total_companies": len(df),
        "companies_with_peer_group": 0,
        "companies_without_peer_group": 0,
        "peer_groups": {},
        "metrics_summary": {},
        "periods": [],
    }
    
    try:
        # Count companies with/without peer groups
        if "peer_group_name" in df.columns:
            with_peer = (df["peer_group_name"] != "No peer group assigned").sum()
            without_peer = (df["peer_group_name"] == "No peer group assigned").sum()
            
            summary["companies_with_peer_group"] = int(with_peer)
            summary["companies_without_peer_group"] = int(without_peer)
            
            # Count by peer group
            peer_group_counts = df["peer_group_name"].value_counts()
            summary["peer_groups"] = peer_group_counts.to_dict()
        
        # Get unique periods
        if "period" in df.columns:
            summary["periods"] = df["period"].unique().tolist()
        
        # Calculate metrics summary
        for metric in SUPPORTED_METRICS:
            percentile_col = f"{metric}_percentile"
            
            if percentile_col not in df.columns:
                continue
            
            valid_percentiles = df[percentile_col].dropna()
            
            if len(valid_percentiles) == 0:
                continue
            
            summary["metrics_summary"][metric] = {
                "count": len(valid_percentiles),
                "mean": round(valid_percentiles.mean(), 4),
                "median": round(valid_percentiles.median(), 4),
                "min": round(valid_percentiles.min(), 4),
                "max": round(valid_percentiles.max(), 4),
                "std": round(valid_percentiles.std(), 4) if len(valid_percentiles) > 1 else 0,
            }
        
        logger.info(f"Summary generated: {summary['total_companies']} companies processed")
        return summary
        
    except Exception as e:
        logger.error(f"Failed to generate summary: {str(e)}")
        return summary


def validate_peer_data(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate peer percentile data.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing percentile rankings
    
    Returns
    -------
    Dict[str, Any]
        Validation results
    """
    logger.info("Validating peer percentile data")
    
    results = {
        "valid": True,
        "checks": [],
        "warnings": [],
        "errors": [],
    }
    
    try:
        # Check 1: Verify all companies are processed
        if "company_id" in df.columns:
            total_companies = len(df)
            results["checks"].append({
                "check": "total_companies",
                "status": "passed",
                "count": total_companies,
            })
        
        # Check 2: Verify peer groups exist
        if "peer_group_name" in df.columns:
            peer_groups = df["peer_group_name"].unique()
            invalid_groups = [g for g in peer_groups if g not in SUPPORTED_PEER_GROUPS and g != "No peer group assigned"]
            
            if invalid_groups:
                results["warnings"].append({
                    "warning": "invalid_peer_groups",
                    "groups": invalid_groups,
                })
            
            results["checks"].append({
                "check": "peer_groups",
                "status": "passed",
                "unique_groups": len([g for g in peer_groups if g != "No peer group assigned"]),
            })
        
        # Check 3: Verify metrics exist
        percentile_cols = [f"{m}_percentile" for m in SUPPORTED_METRICS if f"{m}_percentile" in df.columns]
        
        if len(percentile_cols) != len(SUPPORTED_METRICS):
            missing_metrics = [m for m in SUPPORTED_METRICS if f"{m}_percentile" not in df.columns]
            results["warnings"].append({
                "warning": "missing_metrics",
                "metrics": missing_metrics,
            })
        
        results["checks"].append({
            "check": "metrics",
            "status": "passed",
            "metrics_calculated": len(percentile_cols),
        })
        
        # Check 4: Verify percentiles are within [0, 1]
        for col in percentile_cols:
            valid_values = df[col].dropna()
            
            if len(valid_values) == 0:
                continue
            
            out_of_range = ((valid_values < 0) | (valid_values > 1)).sum()
            
            if out_of_range > 0:
                results["errors"].append({
                    "error": "percentiles_out_of_range",
                    "metric": col,
                    "count": int(out_of_range),
                })
                results["valid"] = False
        
        results["checks"].append({
            "check": "percentile_range",
            "status": "passed" if results["valid"] else "failed",
        })
        
        # Check 5: Verify no duplicate company IDs
        if "company_id" in df.columns:
            duplicates = df["company_id"].duplicated().sum()
            
            if duplicates > 0:
                results["errors"].append({
                    "error": "duplicate_company_ids",
                    "count": int(duplicates),
                })
                results["valid"] = False
            
            results["checks"].append({
                "check": "no_duplicates",
                "status": "passed" if duplicates == 0 else "failed",
            })
        
        # Check 6: Verify required columns exist
        required_cols = ["company_id", "peer_group_name"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            results["errors"].append({
                "error": "missing_required_columns",
                "columns": missing_cols,
            })
            results["valid"] = False
        
        results["checks"].append({
            "check": "required_columns",
            "status": "passed" if not missing_cols else "failed",
        })
        
        logger.info(f"Validation complete: valid={results['valid']}")
        return results
        
    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        results["valid"] = False
        results["errors"].append({"error": "validation_exception", "message": str(e)})
        return results


# =============================================================================
# MAIN PIPELINE
# =============================================================================

class PeerPercentileEngine:
    """
    Main pipeline orchestrator for peer percentile ranking.
    
    Coordinates the calculation and storage of peer percentile rankings.
    """
    
    def __init__(
        self,
        output_dir: Path = OUTPUT_DIR,
        source: str = "database"
    ):
        """
        Initialize pipeline.
        
        Parameters
        ----------
        output_dir : Path, optional
            Output directory for logs and exports, by default OUTPUT_DIR
        source : str, optional
            Source of peer groups: "database" or "excel", by default "database"
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.source = source
        
        self.pipeline_stats = {
            "start_time": None,
            "end_time": None,
            "status": "not_started",
            "companies_processed": 0,
            "companies_with_peer_group": 0,
            "companies_without_peer_group": 0,
            "metrics_processed": 0,
            "rows_inserted": 0,
            "rows_skipped": 0,
            "validation_errors": 0,
            "total_processing_time_ms": 0,
            "errors": [],
        }
    
    def run(
        self,
        df: pd.DataFrame,
        period: str,
        metrics: Optional[List[str]] = None,
        export: bool = True
    ) -> Dict[str, Any]:
        """
        Run the complete peer percentile pipeline.
        
        Parameters
        ----------
        df : pd.DataFrame
            DataFrame containing financial metrics for companies
        period : str
            Financial period (e.g., "FY2024")
        metrics : Optional[List[str]], optional
            List of metrics to rank, by default None (uses SUPPORTED_METRICS)
        export : bool, optional
            Whether to export to CSV, by default True
        
        Returns
        -------
        Dict[str, Any]
            Pipeline statistics and results
        """
        self.pipeline_stats["start_time"] = datetime.now().isoformat()
        
        logger.info("=" * 80)
        logger.info("STARTING PEER PERCENTILE ENGINE")
        logger.info("=" * 80)
        logger.info(f"Processing {len(df)} companies for period: {period}")
        
        try:
            # Step 1: Assign peer groups
            logger.info("Step 1: Assigning peer groups")
            df = assign_peer_groups(df)
            
            # Step 2: Calculate percentiles
            logger.info("Step 2: Calculating percentiles")
            df = calculate_all_percentiles(df, metrics=metrics)
            
            # Step 3: Validate data
            logger.info("Step 3: Validating data")
            validation_results = validate_peer_data(df)
            
            if not validation_results["valid"]:
                logger.warning(f"Validation warnings/errors: {validation_results}")
                self.pipeline_stats["validation_errors"] = len(validation_results["errors"])
            
            # Step 4: Save to database
            logger.info("Step 4: Saving to database")
            db_stats = save_peer_percentiles(df, period, metrics=metrics)
            
            # Step 5: Export to CSV
            if export:
                logger.info("Step 5: Exporting to CSV")
                export_percentiles(df, period=period)
            
            # Update statistics
            self.pipeline_stats["companies_processed"] = len(df)
            self.pipeline_stats["companies_with_peer_group"] = (
                df["peer_group_name"] != "No peer group assigned"
            ).sum() if "peer_group_name" in df.columns else 0
            self.pipeline_stats["companies_without_peer_group"] = (
                df["peer_group_name"] == "No peer group assigned"
            ).sum() if "peer_group_name" in df.columns else 0
            self.pipeline_stats["metrics_processed"] = len(metrics) if metrics else len(SUPPORTED_METRICS)
            self.pipeline_stats["rows_inserted"] = db_stats["successful_inserts"]
            self.pipeline_stats["rows_skipped"] = db_stats["skipped_records"]
            self.pipeline_stats["status"] = "completed"
            
            # Generate summary
            summary = get_peer_summary(df)
            self.pipeline_stats["summary"] = summary
            
            # Log summary
            self._log_pipeline_summary()
            
        except Exception as e:
            self.pipeline_stats["status"] = "failed"
            self.pipeline_stats["errors"].append(str(e))
            logger.error(f"Pipeline failed: {str(e)}")
        
        finally:
            self.pipeline_stats["end_time"] = datetime.now().isoformat()
        
        logger.info("=" * 80)
        logger.info("PEER PERCENTILE ENGINE COMPLETED")
        logger.info("=" * 80)
        
        return self.pipeline_stats
    
    def _log_pipeline_summary(self) -> None:
        """Log pipeline summary statistics."""
        stats = self.pipeline_stats
        
        summary = f"""
Peer Percentile Engine Summary
==============================
Companies Processed: {stats['companies_processed']}
Companies with Peer Group: {stats['companies_with_peer_group']}
Companies without Peer Group: {stats['companies_without_peer_group']}
Metrics Processed: {stats['metrics_processed']}
Rows Inserted: {stats['rows_inserted']}
Rows Skipped: {stats['rows_skipped']}
Validation Errors: {stats['validation_errors']}
Status: {stats.get('status', 'unknown')}
        """
        
        logger.info(summary)
        
        # Write to log file
        try:
            with open(PEER_ANALYSIS_LOG, 'w') as f:
                f.write(f"Peer Percentile Engine Log\n")
                f.write(f"Generated: {datetime.now().isoformat()}\n")
                f.write("=" * 80 + "\n")
                f.write(summary)
                f.write("\n")
                
                if stats["errors"]:
                    f.write("\nErrors:\n")
                    f.write("-" * 80 + "\n")
                    for error in stats["errors"]:
                        f.write(f"{error}\n")
            
            logger.info(f"Pipeline log generated: {PEER_ANALYSIS_LOG}")
        except Exception as e:
            logger.error(f"Failed to write pipeline log: {str(e)}")


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def run_peer_percentile_engine(
    df: pd.DataFrame,
    period: str,
    metrics: Optional[List[str]] = None,
    export: bool = True,
    source: str = "database"
) -> Dict[str, Any]:
    """
    Main entry point for the Peer Percentile Engine.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing financial metrics for companies
    period : str
        Financial period (e.g., "FY2024")
    metrics : Optional[List[str]], optional
        List of metrics to rank, by default None (uses SUPPORTED_METRICS)
    export : bool, optional
        Whether to export to CSV, by default True
    source : str, optional
        Source of peer groups: "database" or "excel", by default "database"
    
    Returns
    -------
    Dict[str, Any]
        Pipeline statistics and results
    
    Example
    -------
    >>> df = pd.DataFrame({
    ...     "company_id": ["RELIANCE", "TCS", "INFY"],
    ...     "company_name": ["Reliance Industries", "TCS", "Infosys"],
    ...     "roe": [15.0, 20.0, 18.0],
    ...     "roce": [12.0, 18.0, 16.0]
    ... })
    >>> stats = run_peer_percentile_engine(df, "FY2024")
    """
    engine = PeerPercentileEngine(source=source)
    return engine.run(df, period, metrics=metrics, export=export)


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_peer_percentile_statistics() -> Dict[str, Any]:
    """
    Get statistics from the peer_percentiles table.
    
    Returns
    -------
    Dict[str, Any]
        Database statistics
    """
    try:
        conn = get_connection()
        
        # Total records
        cursor = conn.execute("SELECT COUNT(*) FROM peer_percentiles")
        total_records = cursor.fetchone()[0]
        
        # Records by peer group
        cursor = conn.execute("""
            SELECT peer_group_name, COUNT(*) as count 
            FROM peer_percentiles 
            GROUP BY peer_group_name
            ORDER BY count DESC
        """)
        by_peer_group = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Records by metric
        cursor = conn.execute("""
            SELECT metric, COUNT(*) as count 
            FROM peer_percentiles 
            GROUP BY metric
            ORDER BY count DESC
        """)
        by_metric = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Records by period
        cursor = conn.execute("""
            SELECT period, COUNT(*) as count 
            FROM peer_percentiles 
            GROUP BY period 
            ORDER BY period DESC
        """)
        by_period = {row[0]: row[1] for row in cursor.fetchall()}
        
        return {
            "total_records": total_records,
            "by_peer_group": by_peer_group,
            "by_metric": by_metric,
            "by_period": by_period,
        }
    
    except Exception as e:
        logger.error(f"Failed to get peer percentile statistics: {str(e)}")
        return {}


def validate_database_integrity() -> Dict[str, Any]:
    """
    Validate database integrity for peer_percentiles table.
    
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
            SELECT company_id, peer_group_name, metric, period, COUNT(*) as count
            FROM peer_percentiles
            GROUP BY company_id, peer_group_name, metric, period
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
            SELECT COUNT(*) FROM peer_percentiles WHERE company_id IS NULL
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
        
        # Check for missing peer_group_name
        cursor = conn.execute("""
            SELECT COUNT(*) FROM peer_percentiles WHERE peer_group_name IS NULL
        """)
        missing_peer_group = cursor.fetchone()[0]
        
        if missing_peer_group > 0:
            results["valid"] = False
            results["checks"].append({
                "check": "missing_peer_group",
                "status": "failed",
                "count": missing_peer_group
            })
        else:
            results["checks"].append({
                "check": "missing_peer_group",
                "status": "passed"
            })
        
        # Check for invalid percentile values
        cursor = conn.execute("""
            SELECT COUNT(*) FROM peer_percentiles 
            WHERE percentile_rank < 0 OR percentile_rank > 1
        """)
        invalid_percentiles = cursor.fetchone()[0]
        
        if invalid_percentiles > 0:
            results["valid"] = False
            results["checks"].append({
                "check": "invalid_percentiles",
                "status": "failed",
                "count": invalid_percentiles
            })
        else:
            results["checks"].append({
                "check": "invalid_percentiles",
                "status": "passed"
            })
        
        return results
    
    except Exception as e:
        logger.error(f"Failed to validate database integrity: {str(e)}")
        return {"valid": False, "error": str(e)}