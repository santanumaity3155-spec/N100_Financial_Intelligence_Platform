"""
exporter.py

CSV export functionality for the Investment Screener Engine (Module 6).
"""

import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.config.logging_config import get_logger
from src.screener.constants import SCREENER_CSV_PATH

logger = get_logger(__name__)


# =============================================================================
# SCREENER EXPORTER
# =============================================================================

class ScreenerExporter:
    """
    Exports screener results to CSV files.
    """

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize the ScreenerExporter.

        Parameters
        ----------
        output_dir : Path, optional
            Output directory for CSV files, by default uses SCREENER_CSV_PATH
        """
        self.output_dir = output_dir or SCREENER_CSV_PATH.parent
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_results(
        self,
        results: List[Dict[str, Any]],
        filename: Optional[str] = None,
        columns: Optional[List[str]] = None,
        include_rank: bool = True,
    ) -> Optional[Path]:
        """
        Export screener results to CSV.

        Parameters
        ----------
        results : List[Dict[str, Any]]
            List of screener result records
        filename : str, optional
            Custom filename (without extension), by default uses timestamp
        columns : List[str], optional
            List of columns to export, by default exports all available columns
        include_rank : bool, optional
            Whether to include rank column, by default True

        Returns
        -------
        Optional[Path]
            Path to the generated CSV file, or None if export failed
        """
        if not results:
            logger.warning("No results to export")
            return None

        # Generate filename with timestamp
        if filename:
            csv_filename = f"{filename}.csv"
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_filename = f"screener_results_{timestamp}.csv"

        csv_path = self.output_dir / csv_filename

        try:
            # Determine columns to export
            if columns:
                # Use specified columns, but ensure they exist in results
                available_cols = set(results[0].keys())
                export_cols = [col for col in columns if col in available_cols]
            else:
                # Export all columns from first record
                export_cols = list(results[0].keys())

            # Add rank column if requested and not already present
            if include_rank and "rank" not in export_cols:
                export_cols.insert(0, "rank")

            # Write CSV
            with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(
                    csvfile,
                    fieldnames=export_cols,
                    extrasaction="ignore",
                    restval="",
                )
                writer.writeheader()

                for idx, record in enumerate(results, start=1):
                    row = {k: record.get(k, "") for k in export_cols}
                    if include_rank and "rank" not in record:
                        row["rank"] = idx
                    writer.writerow(row)

            logger.info(
                f"Exported {len(results)} records to {csv_path} "
                f"({len(export_cols)} columns)"
            )
            return csv_path

        except Exception as e:
            logger.error(f"Failed to export CSV: {str(e)}")
            return None

    def export_to_csv(
        self,
        results: List[Dict[str, Any]],
        output_path: Optional[Path] = None,
    ) -> Optional[Path]:
        """
        Export screener results to CSV (convenience method).

        Parameters
        ----------
        results : List[Dict[str, Any]]
            List of screener result records
        output_path : Path, optional
            Custom output path, by default uses SCREENER_CSV_PATH

        Returns
        -------
        Optional[Path]
            Path to the generated CSV file, or None if export failed
        """
        if not results:
            logger.warning("No results to export")
            return None

        csv_path = output_path or SCREENER_CSV_PATH

        try:
            # Get all columns from results
            if results:
                fieldnames = list(results[0].keys())
            else:
                fieldnames = []

            with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(
                    csvfile,
                    fieldnames=fieldnames,
                    extrasaction="ignore",
                    restval="",
                )
                writer.writeheader()

                for record in results:
                    row = {k: record.get(k, "") for k in fieldnames}
                    writer.writerow(row)

            logger.info(
                f"Exported {len(results)} records to {csv_path} "
                f"({len(fieldnames)} columns)"
            )
            return csv_path

        except Exception as e:
            logger.error(f"Failed to export CSV: {str(e)}")
            return None

    def export_filtered_results(
        self,
        results: List[Dict[str, Any]],
        filters: List[Dict[str, Any]],
    ) -> Optional[Path]:
        """
        Export filtered results with filter metadata.

        Parameters
        ----------
        results : List[Dict[str, Any]]
            List of screener result records
        filters : List[Dict[str, Any]]
            List of filter conditions applied

        Returns
        -------
        Optional[Path]
            Path to the generated CSV file, or None if export failed
        """
        if not results:
            logger.warning("No results to export")
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"screener_filtered_{timestamp}.csv"
        csv_path = self.output_dir / csv_filename

        try:
            fieldnames = list(results[0].keys())

            with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(
                    csvfile,
                    fieldnames=fieldnames,
                    extrasaction="ignore",
                    restval="",
                )
                writer.writeheader()

                # Write metadata as comments
                csvfile.write(f"# Filtered Results Export\n")
                csvfile.write(f"# Generated: {datetime.now().isoformat()}\n")
                csvfile.write(f"# Records: {len(results)}\n")
                csvfile.write(f"# Filters Applied: {len(filters)}\n")
                for i, filt in enumerate(filters, 1):
                    field = filt.get("field", "unknown")
                    operator = filt.get("operator", "unknown")
                    value = filt.get("value", "")
                    csvfile.write(f"# Filter {i}: {field} {operator} {value}\n")
                csvfile.write(f"#\n")

                # Write data
                for record in results:
                    row = {k: record.get(k, "") for k in fieldnames}
                    writer.writerow(row)

            logger.info(
                f"Exported {len(results)} filtered results to {csv_path}"
            )
            return csv_path

        except Exception as e:
            logger.error(f"Failed to export filtered results: {str(e)}")
            return None

    def export_ranked_results(
        self,
        results: List[Dict[str, Any]],
        rank_field: str,
    ) -> Optional[Path]:
        """
        Export ranked results with ranking metadata.

        Parameters
        ----------
        results : List[Dict[str, Any]]
            List of screener result records (should include 'rank' field)
        rank_field : str
            Field used for ranking

        Returns
        -------
        Optional[Path]
            Path to the generated CSV file, or None if export failed
        """
        if not results:
            logger.warning("No results to export")
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"screener_ranked_{timestamp}.csv"
        csv_path = self.output_dir / csv_filename

        try:
            fieldnames = list(results[0].keys())

            with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(
                    csvfile,
                    fieldnames=fieldnames,
                    extrasaction="ignore",
                    restval="",
                )
                writer.writeheader()

                # Write metadata
                csvfile.write(f"# Ranked Results Export\n")
                csvfile.write(f"# Generated: {datetime.now().isoformat()}\n")
                csvfile.write(f"# Records: {len(results)}\n")
                csvfile.write(f"# Ranked By: {rank_field}\n")
                csvfile.write(f"#\n")

                # Write data
                for record in results:
                    row = {k: record.get(k, "") for k in fieldnames}
                    writer.writerow(row)

            logger.info(
                f"Exported {len(results)} ranked results to {csv_path} "
                f"(ranked by {rank_field})"
            )
            return csv_path

        except Exception as e:
            logger.error(f"Failed to export ranked results: {str(e)}")
            return None