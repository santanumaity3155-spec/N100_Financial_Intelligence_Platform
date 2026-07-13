"""
data_quality.py

Data quality reporting module for the N100 Financial Intelligence Platform.
Generates comprehensive data quality reports in JSON and HTML formats.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.config.constants import REPORTS_DIR
from src.config.logging_config import get_logger

logger = get_logger(__name__)


class DataQualityReporter:
    """
    Generates data quality reports.
    
    Responsibilities:
    1. Compile validation results
    2. Generate JSON reports
    3. Generate HTML reports
    4. Track data quality metrics
    """

    def __init__(self, reports_dir: Optional[Path] = None):
        """
        Initialize the DataQualityReporter.
        
        Parameters
        ----------
        reports_dir : Path, optional
            Directory to save reports. Defaults to REPORTS_DIR from constants.
        """
        self.reports_dir = reports_dir or REPORTS_DIR
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        self.validation_results = {}
        self.normalization_log = []
        self.transformation_log = []
        self.load_stats = {}

    def set_validation_results(self, results: Dict[str, Any]):
        """
        Set validation results.
        
        Parameters
        ----------
        results : Dict[str, Any]
            Validation results from DataValidator
        """
        self.validation_results = results
        logger.info("Validation results set for reporting")

    def set_normalization_log(self, log: List[Dict[str, Any]]):
        """
        Set normalization log.
        
        Parameters
        ----------
        log : List[Dict[str, Any]]
            Normalization log from DataNormalizer
        """
        self.normalization_log = log
        logger.info(f"Normalization log set: {len(log)} operations")

    def set_transformation_log(self, log: List[Dict[str, Any]]):
        """
        Set transformation log.
        
        Parameters
        ----------
        log : List[Dict[str, Any]]
            Transformation log from DataTransformer
        """
        self.transformation_log = log
        logger.info(f"Transformation log set: {len(log)} operations")

    def set_load_stats(self, stats: Dict[str, Any]):
        """
        Set load statistics.
        
        Parameters
        ----------
        stats : Dict[str, Any]
            Load statistics from DataLoader
        """
        self.load_stats = stats
        logger.info("Load statistics set for reporting")

    def generate_summary_report(self) -> Dict[str, Any]:
        """
        Generate summary data quality report.
        
        Returns
        -------
        Dict[str, Any]
            Summary report
        """
        report = {
            "report_title": "N100 Financial Intelligence Platform - Data Quality Report",
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_datasets": 0,
                "validation_passed": 0,
                "validation_failed": 0,
                "total_rows_loaded": 0,
                "total_errors": 0,
                "total_warnings": 0
            },
            "validation_summary": {},
            "normalization_summary": {},
            "transformation_summary": {},
            "load_summary": {},
            "recommendations": []
        }

        # Validation summary
        if self.validation_results:
            # pipeline may pass either the summary directly or a nested structure
            val_summary = self.validation_results.get("summary", self.validation_results)
            report["summary"]["total_datasets"] = val_summary.get("total_datasets", 0)
            report["summary"]["validation_passed"] = val_summary.get("passed", 0)
            report["summary"]["validation_failed"] = val_summary.get("failed", 0)
            report["validation_summary"] = val_summary
        else:
            # No validation results available
            report["summary"]["total_datasets"] = 0
            report["summary"]["validation_passed"] = 0
            report["summary"]["validation_failed"] = 0
            report["validation_summary"] = {
                "message": "Validation was not performed or no results available"
            }

        # Normalization summary
        if self.normalization_log:
            report["normalization_summary"] = {
                "total_operations": len(self.normalization_log),
                "operations": self.normalization_log
            }

        # Transformation summary
        if self.transformation_log:
            report["transformation_summary"] = {
                "total_operations": len(self.transformation_log),
                "operations": self.transformation_log
            }

        # Load summary
        if self.load_stats:
            report["load_summary"] = self.load_stats
            report["summary"]["total_rows_loaded"] = self.load_stats.get("total_rows_loaded", 0)

        # Generate recommendations
        report["recommendations"] = self._generate_recommendations(report)

        return report

    def _generate_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """
        Generate recommendations based on data quality issues.
        
        Parameters
        ----------
        report : Dict[str, Any]
            Summary report
            
        Returns
        -------
        List[str]
            List of recommendations
        """
        recommendations = []

        # Check validation failures
        failed_datasets = report["validation_summary"].get("failed", 0)
        if failed_datasets > 0:
            recommendations.append(
                f"Review {failed_datasets} failed dataset validations"
            )

        # Check for missing values
        if self.validation_results:
            datasets = self.validation_results.get("datasets", self.validation_results.get("datasets", {}))
            if not datasets:
                datasets = self.validation_results.get("datasets", {})
            for dataset_name, dataset_info in datasets.items():
                failed_checks = dataset_info.get("failed_checks", [])
                if "missing_values" in failed_checks:
                    recommendations.append(
                        f"Address missing values in {dataset_name}"
                    )

        # Check load errors
        if self.load_stats:
            failed_loads = self.load_stats.get("failed_loads", [])
            if failed_loads:
                recommendations.append(
                    f"Retry failed loads: {failed_loads}"
                )

        if not recommendations:
            recommendations.append("Data quality looks good. No immediate actions required.")

        return recommendations

    def save_json_report(self, filename: Optional[str] = None) -> Path:
        """
        Save data quality report as JSON.
        
        Parameters
        ----------
        filename : str, optional
            Report filename. Defaults to timestamped name.
            
        Returns
        -------
        Path
            Path to saved report
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data_quality_report_{timestamp}.json"

        report_path = self.reports_dir / filename
        
        report = self.generate_summary_report()
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"JSON report saved: {report_path}")
            return report_path
            
        except Exception as e:
            logger.error(f"Failed to save JSON report: {str(e)}")
            raise

    def save_html_report(self, filename: Optional[str] = None) -> Path:
        """
        Save data quality report as HTML.
        
        Parameters
        ----------
        filename : str, optional
            Report filename. Defaults to timestamped name.
            
        Returns
        -------
        Path
            Path to saved report
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data_quality_report_{timestamp}.html"

        report_path = self.reports_dir / filename
        
        report = self.generate_summary_report()
        
        try:
            html_content = self._generate_html_report(report)
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"HTML report saved: {report_path}")
            return report_path
            
        except Exception as e:
            logger.error(f"Failed to save HTML report: {str(e)}")
            raise

    def _generate_html_report(self, report: Dict[str, Any]) -> str:
        """
        Generate HTML content for the report.
        
        Parameters
        ----------
        report : Dict[str, Any]
            Summary report
            
        Returns
        -------
        str
            HTML content
        """
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{report['report_title']}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #007bff;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #555;
            margin-top: 30px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .metric {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #007bff;
        }}
        .metric-label {{
            font-size: 14px;
            color: #666;
            margin-bottom: 5px;
        }}
        .metric-value {{
            font-size: 24px;
            font-weight: bold;
            color: #333;
        }}
        .passed {{
            border-left-color: #28a745;
        }}
        .failed {{
            border-left-color: #dc3545;
        }}
        .recommendations {{
            background-color: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 5px;
            padding: 15px;
            margin: 20px 0;
        }}
        .recommendations ul {{
            margin: 10px 0;
            padding-left: 20px;
        }}
        .recommendations li {{
            margin: 5px 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 10px;
            text-align: left;
        }}
        th {{
            background-color: #007bff;
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        .timestamp {{
            color: #666;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{report['report_title']}</h1>
        <p class="timestamp">Generated: {report['generated_at']}</p>
        
        <h2>Summary</h2>
        <div class="summary">
            <div class="metric">
                <div class="metric-label">Total Datasets</div>
                <div class="metric-value">{report['summary']['total_datasets']}</div>
            </div>
            <div class="metric passed">
                <div class="metric-label">Validations Passed</div>
                <div class="metric-value">{report['summary']['validation_passed']}</div>
            </div>
            <div class="metric failed">
                <div class="metric-label">Validations Failed</div>
                <div class="metric-value">{report['summary']['validation_failed']}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Total Rows Loaded</div>
                <div class="metric-value">{report['summary']['total_rows_loaded']:,}</div>
            </div>
        </div>
        
        <h2>Recommendations</h2>
        <div class="recommendations">
            <ul>
                {"".join(f"<li>{rec}</li>" for rec in report['recommendations'])}
            </ul>
        </div>
        
        <h2>Load Summary</h2>
        <table>
            <tr>
                <th>Table</th>
                <th>Rows Loaded</th>
                <th>Status</th>
            </tr>
"""
        
        # Add load summary rows
        if report.get("load_summary"):
            for table, stats in report["load_summary"].get("tables", {}).items():
                status = "✓ Success" if stats.get("success") else "✗ Failed"
                rows = stats.get("rows_loaded", 0)
                html += f"            <tr><td>{table}</td><td>{rows:,}</td><td>{status}</td></tr>\n"

        html += """        </table>
    </div>
</body>
</html>
"""
        
        return html

    def print_summary(self):
        """Print data quality summary to console."""
        report = self.generate_summary_report()
        
        print("\n" + "="*80)
        print("DATA QUALITY REPORT SUMMARY")
        print("="*80)
        print(f"Generated: {report['generated_at']}")
        print(f"Total Datasets: {report['summary']['total_datasets']}")
        print(f"Validations Passed: {report['summary']['validation_passed']}")
        print(f"Validations Failed: {report['summary']['validation_failed']}")
