"""
radar.py

Radar Chart Engine for the N100 Financial Intelligence Platform.

This module generates professional radar charts comparing a company against
its peer-group benchmark using percentile rankings from Module 7.

Responsibilities:
1. Load percentile data from database
2. Calculate peer group benchmarks (mean percentile)
3. Prepare radar chart data for 10 financial metrics
4. Generate professional matplotlib radar charts
5. Save PNG images to output/radar_charts/
6. Handle missing values and edge cases gracefully
7. Validate all inputs before chart generation
8. Log all operations and errors

Metrics Displayed:
- ROE (Return on Equity)
- ROCE (Return on Capital Employed)
- Net Profit Margin
- Debt to Equity (already inverted percentile)
- Free Cash Flow
- Revenue CAGR 5 Year
- PAT CAGR 5 Year
- EPS CAGR 5 Year
- Interest Coverage
- Asset Turnover
"""

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend for headless environments
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import sqlite3

from src.config.constants import OUTPUT_DIR
from src.config.logging_config import get_logger
from src.database.connection import get_connection
from src.analytics.peer import (
    SUPPORTED_METRICS,
    SUPPORTED_PEER_GROUPS,
    PeerAnalysisError,
)

logger = get_logger(__name__)

# =============================================================================
# CONSTANTS
# =============================================================================

# Output paths
RADAR_CHARTS_DIR = OUTPUT_DIR / "radar_charts"
RADAR_CHART_LOG = OUTPUT_DIR / "radar_chart.log"

# Chart configuration
CHART_DPI = 300
CHART_FIGSIZE = (10, 10)
CHART_DPI_HIGH_RES = 300

# Metric display names for chart labels
METRIC_DISPLAY_NAMES = {
    "roe": "ROE",
    "roce": "ROCE",
    "net_profit_margin": "Net Profit Margin",
    "debt_to_equity": "Debt to Equity",
    "free_cash_flow": "Free Cash Flow",
    "revenue_cagr_5yr": "Revenue CAGR 5Y",
    "pat_cagr_5yr": "PAT CAGR 5Y",
    "eps_cagr_5yr": "EPS CAGR 5Y",
    "interest_coverage": "Interest Coverage",
    "asset_turnover": "Asset Turnover",
}

# Color scheme
COLOR_COMPANY = "#2E86AB"  # Blue
COLOR_BENCHMARK = "#A23B72"  # Purple
COLOR_GRID = "#E0E0E0"  # Light gray
COLOR_FILL_COMPANY = "#2E86AB"
COLOR_FILL_BENCHMARK = "#A23B72"


# =============================================================================
# CUSTOM EXCEPTIONS
# =============================================================================

class RadarChartError(Exception):
    """Base exception for radar chart errors."""
    pass


class CompanyNotFoundError(RadarChartError):
    """Raised when company is not found."""
    pass


class PeerGroupNotFoundError(RadarChartError):
    """Raised when peer group is not found."""
    pass


class MetricValidationError(RadarChartError):
    """Raised when metrics validation fails."""
    pass


class ChartGenerationError(RadarChartError):
    """Raised when chart generation fails."""
    pass


# =============================================================================
# DATA LOADING
# =============================================================================

def load_percentile_data(
    company_id: Optional[str] = None,
    peer_group: Optional[str] = None,
    period: Optional[str] = None
) -> pd.DataFrame:
    """
    Load percentile data from database.
    
    Parameters
    ----------
    company_id : Optional[str], optional
        Filter by company ID, by default None (all companies)
    peer_group : Optional[str], optional
        Filter by peer group, by default None (all peer groups)
    period : Optional[str], optional
        Filter by period, by default None (all periods)
    
    Returns
    -------
    pd.DataFrame
        DataFrame with columns: company_id, peer_group_name, metric,
        metric_value, percentile_rank, period
    
    Raises
    ------
    sqlite3.Error
        If database query fails
    """
    logger.info(f"Loading percentile data: company={company_id}, peer_group={peer_group}, period={period}")
    
    try:
        conn = get_connection()
        
        # Build query with filters
        query = """
            SELECT 
                company_id,
                peer_group_name,
                metric,
                metric_value,
                percentile_rank,
                period
            FROM peer_percentiles
            WHERE 1=1
        """
        params = []
        
        if company_id:
            query += " AND company_id = ?"
            params.append(company_id)
        
        if peer_group:
            query += " AND peer_group_name = ?"
            params.append(peer_group)
        
        if period:
            query += " AND period = ?"
            params.append(period)
        
        query += " ORDER BY company_id, metric"
        
        df = pd.read_sql_query(query, conn, params=params)
        
        logger.info(f"Loaded {len(df)} percentile records")
        return df
        
    except sqlite3.Error as e:
        logger.error(f"Failed to load percentile data: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error loading percentile data: {str(e)}")
        raise RadarChartError(f"Failed to load percentile data: {str(e)}")


def load_company_data(company_id: str) -> Dict[str, Any]:
    """
    Load company information from database.
    
    Parameters
    ----------
    company_id : str
        Company identifier
    
    Returns
    -------
    Dict[str, Any]
        Company information
    
    Raises
    ------
    CompanyNotFoundError
        If company is not found
    """
    logger.info(f"Loading company data: {company_id}")
    
    try:
        conn = get_connection()
        cursor = conn.execute(
            "SELECT company_id, company_name, sector, industry FROM companies WHERE company_id = ?",
            (company_id,)
        )
        row = cursor.fetchone()
        
        if not row:
            raise CompanyNotFoundError(f"Company not found: {company_id}")
        
        company_data = {
            "company_id": row[0],
            "company_name": row[1],
            "sector": row[2],
            "industry": row[3],
        }
        
        logger.info(f"Loaded company data: {company_data['company_name']}")
        return company_data
        
    except CompanyNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Failed to load company data: {str(e)}")
        raise RadarChartError(f"Failed to load company data: {str(e)}")


# =============================================================================
# BENCHMARK CALCULATION
# =============================================================================

def calculate_peer_benchmark(df: pd.DataFrame, peer_group: str) -> Dict[str, float]:
    """
    Calculate peer group benchmark using mean percentile of all companies
    in the same peer group.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing percentile data
    peer_group : str
        Peer group name
    
    Returns
    -------
    Dict[str, float]
        Dictionary mapping metric to mean percentile
    
    Raises
    ------
    PeerGroupNotFoundError
        If peer group has no data or is not a valid peer group
    """
    logger.info(f"Calculating peer benchmark for: {peer_group}")
    
    try:
        # Validate peer group is in supported list
        if peer_group not in SUPPORTED_PEER_GROUPS:
            raise PeerGroupNotFoundError(f"Invalid peer group: {peer_group}")
        
        # Filter by peer group
        peer_df = df[df["peer_group_name"] == peer_group].copy()
        
        if peer_df.empty:
            raise PeerGroupNotFoundError(f"No data found for peer group: {peer_group}")
        
        # Calculate mean percentile for each metric
        benchmark = {}
        
        for metric in SUPPORTED_METRICS:
            metric_data = peer_df[peer_df["metric"] == metric]["percentile_rank"]
            
            if metric_data.empty:
                logger.warning(f"No data for metric {metric} in peer group {peer_group}")
                benchmark[metric] = 0.5  # Default to median
            else:
                # Use mean percentile, handling NaN values
                benchmark[metric] = metric_data.mean()
        
        logger.info(f"Benchmark calculated for {len(benchmark)} metrics")
        return benchmark
        
    except PeerGroupNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Failed to calculate peer benchmark: {str(e)}")
        raise RadarChartError(f"Failed to calculate peer benchmark: {str(e)}")


# =============================================================================
# RADAR DATA PREPARATION
# =============================================================================

def prepare_radar_data(
    company_id: str,
    period: Optional[str] = None
) -> Dict[str, Any]:
    """
    Prepare radar chart data for a company.
    
    Parameters
    ----------
    company_id : str
        Company identifier
    period : Optional[str], optional
        Financial period, by default None (uses latest period)
    
    Returns
    -------
    Dict[str, Any]
        Dictionary containing:
        - company_data: Company information
        - company_percentiles: Company's percentile values
        - benchmark: Peer group benchmark
        - peer_group: Peer group name
        - metrics: List of metrics
    
    Raises
    ------
    CompanyNotFoundError
        If company is not found
    PeerGroupNotFoundError
        If peer group is not found
    MetricValidationError
        If metrics validation fails
    """
    logger.info(f"Preparing radar data for company: {company_id}")
    
    try:
        # Load company data
        company_data = load_company_data(company_id)
        
        # Load percentile data for this company
        df = load_percentile_data(company_id=company_id, period=period)
        
        if df.empty:
            raise MetricValidationError(f"No percentile data found for company: {company_id}")
        
        # Get peer group
        peer_group = df["peer_group_name"].iloc[0]
        
        if peer_group not in SUPPORTED_PEER_GROUPS:
            raise PeerGroupNotFoundError(f"Invalid peer group: {peer_group}")
        
        # Prepare company percentiles
        company_percentiles = {}
        for metric in SUPPORTED_METRICS:
            metric_data = df[df["metric"] == metric]["percentile_rank"]
            
            if metric_data.empty:
                logger.warning(f"Missing percentile for {metric}, using 0.5")
                company_percentiles[metric] = 0.5
            else:
                company_percentiles[metric] = metric_data.iloc[0]
        
        # Calculate peer benchmark
        # Load all companies in the same peer group
        all_peer_df = load_percentile_data(peer_group=peer_group, period=period)
        benchmark = calculate_peer_benchmark(all_peer_df, peer_group)
        
        # Validate metrics
        validate_chart_inputs(company_percentiles, benchmark, peer_group)
        
        result = {
            "company_data": company_data,
            "company_percentiles": company_percentiles,
            "benchmark": benchmark,
            "peer_group": peer_group,
            "metrics": SUPPORTED_METRICS,
        }
        
        logger.info(f"Radar data prepared successfully for {company_id}")
        return result
        
    except (CompanyNotFoundError, PeerGroupNotFoundError, MetricValidationError):
        raise
    except Exception as e:
        logger.error(f"Failed to prepare radar data: {str(e)}")
        raise RadarChartError(f"Failed to prepare radar data: {str(e)}")


# =============================================================================
# VALIDATION
# =============================================================================

def validate_chart_inputs(
    company_percentiles: Dict[str, float],
    benchmark: Dict[str, float],
    peer_group: str
) -> bool:
    """
    Validate radar chart inputs.
    
    Parameters
    ----------
    company_percentiles : Dict[str, float]
        Company's percentile values
    benchmark : Dict[str, float]
        Peer group benchmark
    peer_group : str
        Peer group name
    
    Returns
    -------
    bool
        True if validation passes
    
    Raises
    ------
    MetricValidationError
        If validation fails
    """
    logger.info("Validating chart inputs")
    
    errors = []
    
    # Check 1: Exactly 10 metrics
    if len(company_percentiles) != 10:
        errors.append(f"Expected 10 metrics, got {len(company_percentiles)}")
    
    if len(benchmark) != 10:
        errors.append(f"Expected 10 benchmark metrics, got {len(benchmark)}")
    
    # Check 2: No duplicate metrics
    if len(company_percentiles) != len(set(company_percentiles.keys())):
        errors.append("Duplicate metrics found in company percentiles")
    
    if len(benchmark) != len(set(benchmark.keys())):
        errors.append("Duplicate metrics found in benchmark")
    
    # Check 3: All metrics are valid
    invalid_metrics = [m for m in company_percentiles.keys() if m not in SUPPORTED_METRICS]
    if invalid_metrics:
        errors.append(f"Invalid metrics: {invalid_metrics}")
    
    # Check 4: Percentiles between 0 and 1
    for metric, percentile in company_percentiles.items():
        if not 0 <= percentile <= 1:
            errors.append(f"Company percentile out of range for {metric}: {percentile}")
    
    for metric, percentile in benchmark.items():
        if not 0 <= percentile <= 1:
            errors.append(f"Benchmark percentile out of range for {metric}: {percentile}")
    
    # Check 5: Peer group exists
    if peer_group not in SUPPORTED_PEER_GROUPS:
        errors.append(f"Invalid peer group: {peer_group}")
    
    # Check 6: Benchmark exists
    if not benchmark:
        errors.append("Benchmark is empty")
    
    if errors:
        error_msg = "Validation failed: " + "; ".join(errors)
        logger.error(error_msg)
        raise MetricValidationError(error_msg)
    
    logger.info("Chart inputs validated successfully")
    return True


# =============================================================================
# CHART GENERATION
# =============================================================================

def generate_radar_chart(
    company_id: str,
    company_percentiles: Dict[str, float],
    benchmark: Dict[str, float],
    peer_group: str,
    company_name: str,
    output_path: Optional[Path] = None
) -> Path:
    """
    Generate a professional radar chart comparing company vs peer benchmark.
    
    Parameters
    ----------
    company_id : str
        Company identifier
    company_percentiles : Dict[str, float]
        Company's percentile values for each metric
    benchmark : Dict[str, float]
        Peer group benchmark (mean percentiles)
    peer_group : str
        Peer group name
    company_name : str
        Company name for chart title
    output_path : Optional[Path], optional
        Output file path, by default None (auto-generates path)
    
    Returns
    -------
    Path
        Path to saved chart
    
    Raises
    ------
    ChartGenerationError
        If chart generation fails
    """
    logger.info(f"Generating radar chart for: {company_id}")
    
    try:
        # Set default output path
        if output_path is None:
            RADAR_CHARTS_DIR.mkdir(parents=True, exist_ok=True)
            output_path = RADAR_CHARTS_DIR / f"{company_id}.png"
        else:
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Prepare data
        metrics = SUPPORTED_METRICS
        n_metrics = len(metrics)
        
        # Calculate angles for each metric
        angles = np.linspace(0, 2 * np.pi, n_metrics, endpoint=False).tolist()
        
        # Close the radar chart by repeating first angle
        angles += angles[:1]
        
        # Prepare values
        company_values = [company_percentiles[m] for m in metrics]
        benchmark_values = [benchmark[m] for m in metrics]
        
        # Close the data by repeating first value
        company_values += company_values[:1]
        benchmark_values += benchmark_values[:1]
        
        # Create figure
        fig, ax = plt.subplots(figsize=CHART_FIGSIZE, subplot_kw=dict(projection='polar'))
        
        # Plot benchmark (fill first, so company line is on top)
        ax.fill(angles, benchmark_values, color=COLOR_FILL_BENCHMARK, alpha=0.15)
        ax.plot(angles, benchmark_values, color=COLOR_BENCHMARK, linewidth=2, linestyle='--', label='Peer Benchmark')
        
        # Plot company
        ax.fill(angles, company_values, color=COLOR_FILL_COMPANY, alpha=0.25)
        ax.plot(angles, company_values, color=COLOR_COMPANY, linewidth=2.5, label=company_name)
        
        # Add metric labels
        metric_labels = [METRIC_DISPLAY_NAMES.get(m, m) for m in metrics]
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(metric_labels, fontsize=11, fontweight='bold')
        
        # Set y-axis (percentile scale)
        ax.set_ylim(0, 1)
        ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
        ax.set_yticklabels(['0%', '25%', '50%', '75%', '100%'], fontsize=9)
        ax.grid(True, color=COLOR_GRID, linestyle='--', linewidth=0.5)
        
        # Add title
        title = f"{company_name}\nvs {peer_group} Peer Benchmark"
        ax.set_title(title, fontsize=16, fontweight='bold', pad=30)
        
        # Add legend
        legend_elements = [
            mpatches.Patch(color=COLOR_COMPANY, alpha=0.25, label=company_name),
            mpatches.Patch(color=COLOR_BENCHMARK, alpha=0.15, label='Peer Benchmark'),
        ]
        ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=10)
        
        # Add percentile values as text annotations
        for i, (angle, company_val, benchmark_val) in enumerate(
            zip(angles[:-1], company_values[:-1], benchmark_values[:-1])
        ):
            # Company value
            ax.text(
                angle, company_val + 0.05,
                f'{company_val:.2f}',
                ha='center', va='bottom',
                fontsize=8, color=COLOR_COMPANY, fontweight='bold'
            )
            
            # Benchmark value
            ax.text(
                angle, benchmark_val - 0.05,
                f'{benchmark_val:.2f}',
                ha='center', va='top',
                fontsize=8, color=COLOR_BENCHMARK
            )
        
        # Adjust layout
        plt.tight_layout()
        
        # Save chart
        plt.savefig(output_path, dpi=CHART_DPI_HIGH_RES, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        
        logger.info(f"Radar chart saved: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Failed to generate radar chart: {str(e)}")
        raise ChartGenerationError(f"Failed to generate radar chart: {str(e)}")


def save_chart(fig: plt.Figure, output_path: Path) -> Path:
    """
    Save matplotlib figure to PNG file.
    
    Parameters
    ----------
    fig : plt.Figure
        Matplotlib figure to save
    output_path : Path
        Output file path
    
    Returns
    -------
    Path
        Path to saved file
    
    Raises
    ------
    ChartGenerationError
        If save fails
    """
    logger.info(f"Saving chart to: {output_path}")
    
    try:
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save figure
        fig.savefig(output_path, dpi=CHART_DPI_HIGH_RES, bbox_inches='tight', facecolor='white')
        
        logger.info(f"Chart saved successfully: {output_path}")
        return output_path
        
    except PermissionError as e:
        logger.error(f"Permission error saving chart: {str(e)}")
        raise ChartGenerationError(f"Permission error: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to save chart: {str(e)}")
        raise ChartGenerationError(f"Failed to save chart: {str(e)}")


# =============================================================================
# BATCH PROCESSING
# =============================================================================

def generate_all_charts(
    period: Optional[str] = None,
    output_dir: Optional[Path] = None,
    batch_size: int = 50
) -> Dict[str, Any]:
    """
    Generate radar charts for all companies.
    
    Parameters
    ----------
    period : Optional[str], optional
        Financial period, by default None (all periods)
    output_dir : Optional[Path], optional
        Output directory, by default None (uses RADAR_CHARTS_DIR)
    batch_size : int, optional
        Number of charts to process per batch, by default 50
    
    Returns
    -------
    Dict[str, Any]
        Statistics dictionary with counts and errors
    """
    logger.info("=" * 80)
    logger.info("STARTING RADAR CHART GENERATION")
    logger.info("=" * 80)
    
    start_time = time.time()
    
    stats = {
        "total_companies": 0,
        "charts_generated": 0,
        "charts_failed": 0,
        "errors": [],
        "warnings": [],
    }
    
    try:
        # Set output directory
        if output_dir is None:
            output_dir = RADAR_CHARTS_DIR
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load all companies with percentile data
        conn = get_connection()
        cursor = conn.execute("""
            SELECT DISTINCT company_id, peer_group_name, period
            FROM peer_percentiles
            WHERE peer_group_name IS NOT NULL
            AND peer_group_name != 'No peer group assigned'
            ORDER BY company_id, period DESC
        """)
        
        companies = cursor.fetchall()
        stats["total_companies"] = len(companies)
        
        logger.info(f"Found {len(companies)} company-period combinations")
        
        # Process each company
        for idx, (company_id, peer_group, period_val) in enumerate(companies, 1):
            try:
                logger.info(f"Processing {idx}/{len(companies)}: {company_id}")
                
                # Prepare radar data
                radar_data = prepare_radar_data(company_id, period=period_val)
                
                # Generate chart
                output_path = output_dir / f"{company_id}.png"
                generate_radar_chart(
                    company_id=company_id,
                    company_percentiles=radar_data["company_percentiles"],
                    benchmark=radar_data["benchmark"],
                    peer_group=radar_data["peer_group"],
                    company_name=radar_data["company_data"]["company_name"],
                    output_path=output_path
                )
                
                stats["charts_generated"] += 1
                
                # Log progress
                if idx % batch_size == 0:
                    logger.info(f"Progress: {idx}/{len(companies)} charts generated")
                
            except Exception as e:
                error_msg = f"Failed to generate chart for {company_id}: {str(e)}"
                logger.error(error_msg)
                stats["charts_failed"] += 1
                stats["errors"].append(error_msg)
        
        # Calculate execution time
        elapsed_time = time.time() - start_time
        
        # Log summary
        summary = f"""
Radar Chart Generation Summary
==============================
Total Companies: {stats['total_companies']}
Charts Generated: {stats['charts_generated']}
Charts Failed: {stats['charts_failed']}
Execution Time: {elapsed_time:.2f}s
        """
        
        logger.info(summary)
        
        # Write log file
        try:
            with open(RADAR_CHART_LOG, 'w') as f:
                f.write(f"Radar Chart Generation Log\n")
                f.write(f"Generated: {datetime.now().isoformat()}\n")
                f.write("=" * 80 + "\n")
                f.write(summary)
                f.write("\n")
                
                if stats["errors"]:
                    f.write("\nErrors:\n")
                    f.write("-" * 80 + "\n")
                    for error in stats["errors"]:
                        f.write(f"{error}\n")
                
                if stats["warnings"]:
                    f.write("\nWarnings:\n")
                    f.write("-" * 80 + "\n")
                    for warning in stats["warnings"]:
                        f.write(f"{warning}\n")
            
            logger.info(f"Log file generated: {RADAR_CHART_LOG}")
        except Exception as e:
            logger.error(f"Failed to write log file: {str(e)}")
        
        return stats
        
    except Exception as e:
        logger.error(f"Radar chart generation failed: {str(e)}")
        stats["errors"].append(str(e))
        return stats


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_radar_chart_statistics(output_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Get statistics about generated radar charts.
    
    Parameters
    ----------
    output_dir : Optional[Path], optional
        Output directory, by default None (uses RADAR_CHARTS_DIR)
    
    Returns
    -------
    Dict[str, Any]
        Statistics dictionary
    """
    if output_dir is None:
        output_dir = RADAR_CHARTS_DIR
    
    try:
        if not output_dir.exists():
            return {"total_charts": 0, "directory_exists": False}
        
        chart_files = list(output_dir.glob("*.png"))
        
        stats = {
            "total_charts": len(chart_files),
            "directory_exists": True,
            "output_dir": str(output_dir),
            "charts": [f.name for f in chart_files],
        }
        
        logger.info(f"Radar chart statistics: {len(chart_files)} charts found")
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get radar chart statistics: {str(e)}")
        return {"total_charts": 0, "error": str(e)}


def validate_radar_chart_output(output_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Validate generated radar charts.
    
    Parameters
    ----------
    output_dir : Optional[Path], optional
        Output directory, by default None (uses RADAR_CHARTS_DIR)
    
    Returns
    -------
    Dict[str, Any]
        Validation results
    """
    if output_dir is None:
        output_dir = RADAR_CHARTS_DIR
    
    logger.info("Validating radar chart output")
    
    results = {
        "valid": True,
        "checks": [],
        "errors": [],
        "warnings": [],
    }
    
    try:
        # Check 1: Directory exists
        if not output_dir.exists():
            results["errors"].append("Output directory does not exist")
            results["valid"] = False
            results["checks"].append({"check": "directory_exists", "status": "failed"})
            return results
        
        results["checks"].append({"check": "directory_exists", "status": "passed"})
        
        # Check 2: At least one chart exists
        chart_files = list(output_dir.glob("*.png"))
        
        if not chart_files:
            results["warnings"].append("No radar charts found")
            results["checks"].append({"check": "charts_exist", "status": "warning"})
        else:
            results["checks"].append({
                "check": "charts_exist",
                "status": "passed",
                "count": len(chart_files)
            })
        
        # Check 3: Verify chart files are valid PNGs
        invalid_charts = []
        for chart_file in chart_files:
            try:
                with open(chart_file, 'rb') as f:
                    header = f.read(8)
                    if header[:8] != b'\x89PNG\r\n\x1a\n':
                        invalid_charts.append(chart_file.name)
            except Exception as e:
                invalid_charts.append(f"{chart_file.name} (error: {str(e)})")
        
        if invalid_charts:
            results["errors"].append({
                "error": "invalid_png_files",
                "files": invalid_charts
            })
            results["valid"] = False
            results["checks"].append({"check": "valid_png", "status": "failed"})
        else:
            results["checks"].append({"check": "valid_png", "status": "passed"})
        
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

class RadarChartEngine:
    """
    Main pipeline orchestrator for radar chart generation.
    
    Coordinates the generation of radar charts for all companies.
    """
    
    def __init__(
        self,
        output_dir: Path = RADAR_CHARTS_DIR,
        period: Optional[str] = None
    ):
        """
        Initialize pipeline.
        
        Parameters
        ----------
        output_dir : Path, optional
            Output directory for charts, by default RADAR_CHARTS_DIR
        period : Optional[str], optional
            Financial period, by default None (all periods)
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.period = period
        
        self.pipeline_stats = {
            "start_time": None,
            "end_time": None,
            "status": "not_started",
            "total_companies": 0,
            "charts_generated": 0,
            "charts_failed": 0,
            "total_processing_time_ms": 0,
            "errors": [],
            "warnings": [],
        }
    
    def run(self, batch_size: int = 50) -> Dict[str, Any]:
        """
        Run the complete radar chart generation pipeline.
        
        Parameters
        ----------
        batch_size : int, optional
            Number of charts per batch, by default 50
        
        Returns
        -------
        Dict[str, Any]
            Pipeline statistics and results
        """
        self.pipeline_stats["start_time"] = datetime.now().isoformat()
        
        logger.info("=" * 80)
        logger.info("STARTING RADAR CHART ENGINE")
        logger.info("=" * 80)
        
        try:
            # Generate all charts
            stats = generate_all_charts(
                period=self.period,
                output_dir=self.output_dir,
                batch_size=batch_size
            )
            
            # Update statistics
            self.pipeline_stats["total_companies"] = stats["total_companies"]
            self.pipeline_stats["charts_generated"] = stats["charts_generated"]
            self.pipeline_stats["charts_failed"] = stats["charts_failed"]
            self.pipeline_stats["errors"] = stats["errors"]
            self.pipeline_stats["warnings"] = stats["warnings"]
            self.pipeline_stats["status"] = "completed"
            
            # Log summary
            self._log_pipeline_summary()
            
        except Exception as e:
            self.pipeline_stats["status"] = "failed"
            self.pipeline_stats["errors"].append(str(e))
            logger.error(f"Pipeline failed: {str(e)}")
        
        finally:
            self.pipeline_stats["end_time"] = datetime.now().isoformat()
        
        logger.info("=" * 80)
        logger.info("RADAR CHART ENGINE COMPLETED")
        logger.info("=" * 80)
        
        return self.pipeline_stats
    
    def _log_pipeline_summary(self) -> None:
        """Log pipeline summary statistics."""
        stats = self.pipeline_stats
        
        summary = f"""
Radar Chart Engine Summary
==========================
Total Companies: {stats['total_companies']}
Charts Generated: {stats['charts_generated']}
Charts Failed: {stats['charts_failed']}
Status: {stats.get('status', 'unknown')}
        """
        
        logger.info(summary)


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def run_radar_chart_engine(
    period: Optional[str] = None,
    output_dir: Optional[Path] = None,
    batch_size: int = 50
) -> Dict[str, Any]:
    """
    Main entry point for the Radar Chart Engine.
    
    Parameters
    ----------
    period : Optional[str], optional
        Financial period, by default None (all periods)
    output_dir : Optional[Path], optional
        Output directory, by default None (uses RADAR_CHARTS_DIR)
    batch_size : int, optional
        Number of charts per batch, by default 50
    
    Returns
    -------
    Dict[str, Any]
        Pipeline statistics and results
    
    Example
    -------
    >>> stats = run_radar_chart_engine(period="FY2024")
    >>> print(f"Generated {stats['charts_generated']} charts")
    """
    engine = RadarChartEngine(output_dir=output_dir, period=period)
    return engine.run(batch_size=batch_size)