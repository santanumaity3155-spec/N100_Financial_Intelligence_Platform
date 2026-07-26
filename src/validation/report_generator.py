"""
report_generator.py

Report Generator for the N100 Financial Intelligence Platform.

This module provides utilities for generating various types of reports
including validation reports, summary reports, and export functionality.

Responsibilities:
1. Generate Markdown reports
2. Generate HTML reports
3. Export data to CSV
4. Create summary statistics
5. Format validation results
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from src.config.constants import OUTPUT_DIR
from src.config.logging_config import get_logger

logger = get_logger(__name__)


# =============================================================================
# MARKDOWN REPORT GENERATOR
# =============================================================================

class MarkdownReportGenerator:
    """
    Generates Markdown formatted reports.
    """
    
    def __init__(self, output_dir: Path = OUTPUT_DIR):
        """
        Initialize report generator.
        
        Parameters
        ----------
        output_dir : Path, optional
            Output directory for reports, by default OUTPUT_DIR
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_header(self, title: str, subtitle: str = "") -> str:
        """
        Generate report header.
        
        Parameters
        ----------
        title : str
            Report title
        subtitle : str, optional
            Report subtitle, by default ""
        
        Returns
        -------
        str
            Markdown formatted header
        """
        lines = [
            f"# {title}",
            "",
        ]
        
        if subtitle:
            lines.append(f"**{subtitle}**")
            lines.append("")
        
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        return "\n".join(lines)
    
    def generate_table(self, headers: List[str], rows: List[List[Any]], 
                       alignments: Optional[List[str]] = None) -> str:
        """
        Generate Markdown table.
        
        Parameters
        ----------
        headers : List[str]
            Table headers
        rows : List[List[Any]]
            Table rows
        alignments : Optional[List[str]], optional
            Column alignments ('left', 'center', 'right'), by default None
        
        Returns
        -------
        str
            Markdown formatted table
        """
        if not headers or not rows:
            return ""
        
        # Default alignment
        if alignments is None:
            alignments = ["left"] * len(headers)
        
        # Build header
        header = "| " + " | ".join(str(h) for h in headers) + " |"
        
        # Build separator
        separator = "| "
        for align in alignments:
            if align == "center":
                separator += ":-: | "
            elif align == "right":
                separator += "-: | "
            else:
                separator += "- | "
        
        # Build rows
        row_lines = []
        for row in rows:
            row_str = "| " + " | ".join(str(cell) for cell in row) + " |"
            row_lines.append(row_str)
        
        return "\n".join([header, separator] + row_lines)
    
    def generate_summary_section(self, title: str, statistics: Dict[str, Any]) -> str:
        """
        Generate summary statistics section.
        
        Parameters
        ----------
        title : str
            Section title
        statistics : Dict[str, Any]
            Statistics dictionary
        
        Returns
        -------
        str
            Markdown formatted section
        """
        lines = [
            f"## {title}",
            "",
        ]
        
        for key, value in statistics.items():
            # Format key for display
            display_key = key.replace("_", " ").title()
            lines.append(f"- **{display_key}:** {value}")
        
        lines.append("")
        return "\n".join(lines)
    
    def generate_status_badge(self, status: str) -> str:
        """
        Generate status badge.
        
        Parameters
        ----------
        status : str
            Status string ("PASS", "FAIL", "WARNING")
        
        Returns
        -------
        str
            Emoji badge
        """
        if status.upper() == "PASS":
            return "✅ PASS"
        elif status.upper() == "FAIL":
            return "❌ FAIL"
        elif status.upper() == "WARNING":
            return "⚠️ WARNING"
        else:
            return status
    
    def save_report(self, content: str, filename: str) -> Path:
        """
        Save report to file.
        
        Parameters
        ----------
        content : str
            Report content
        filename : str
            Output filename
        
        Returns
        -------
        Path
            Path to saved report
        """
        report_path = self.output_dir / filename
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Report saved: {report_path}")
            return report_path
        
        except Exception as e:
            logger.error(f"Failed to save report: {str(e)}")
            raise


# =============================================================================
# HTML REPORT GENERATOR
# =============================================================================

class HTMLReportGenerator:
    """
    Generates HTML formatted reports.
    """
    
    def __init__(self, output_dir: Path = OUTPUT_DIR):
        """
        Initialize HTML report generator.
        
        Parameters
        ----------
        output_dir : Path, optional
            Output directory for reports, by default OUTPUT_DIR
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_html_header(self, title: str) -> str:
        """
        Generate HTML header with styling.
        
        Parameters
        ----------
        title : str
            Report title
        
        Returns
        -------
        str
            HTML header
        """
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
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
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #2E86AB;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #2E86AB;
            margin-top: 30px;
        }}
        h3 {{
            color: #555;
        }}
        .pass {{
            color: #28a745;
            font-weight: bold;
        }}
        .fail {{
            color: #dc3545;
            font-weight: bold;
        }}
        .warning {{
            color: #ffc107;
            font-weight: bold;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #2E86AB;
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        .summary-box {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .timestamp {{
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
"""
    
    def generate_html_footer(self) -> str:
        """
        Generate HTML footer.
        
        Returns
        -------
        str
            HTML footer
        """
        return """
    </div>
</body>
</html>
"""
    
    def markdown_to_html(self, markdown: str) -> str:
        """
        Convert simple Markdown to HTML.
        
        Parameters
        ----------
        markdown : str
            Markdown content
        
        Returns
        -------
        str
            HTML content
        """
        html = markdown
        
        # Headers
        html = html.replace("# ", "<h1>").replace("\n", "</h1>\n", 1)
        html = html.replace("## ", "<h2>").replace("\n", "</h2>\n")
        html = html.replace("### ", "<h3>").replace("\n", "</h3>\n")
        
        # Bold
        import re
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
        
        # Tables (simple conversion)
        lines = html.split('\n')
        in_table = False
        table_lines = []
        result_lines = []
        
        for line in lines:
            if '|' in line and not in_table:
                in_table = True
                table_lines = [line]
            elif '|' in line and in_table:
                table_lines.append(line)
            else:
                if in_table:
                    # Process table
                    result_lines.append(self._markdown_table_to_html(table_lines))
                    in_table = False
                    table_lines = []
                result_lines.append(line)
        
        if in_table:
            result_lines.append(self._markdown_table_to_html(table_lines))
        
        html = '\n'.join(result_lines)
        
        # Lists
        html = html.replace("- ", "<li>").replace("\n<li>", "</li>\n<li>")
        
        return html
    
    def _markdown_table_to_html(self, lines: List[str]) -> str:
        """
        Convert Markdown table to HTML.
        
        Parameters
        ----------
        lines : List[str]
            Markdown table lines
        
        Returns
        -------
        str
            HTML table
        """
        if len(lines) < 2:
            return ""
        
        # Skip separator line
        data_lines = [line for line in lines if not line.strip().startswith('| -')]
        
        html = ['<table>']
        
        for i, line in enumerate(data_lines):
            cells = [cell.strip() for cell in line.split('|') if cell.strip()]
            
            if i == 0:
                # Header
                html.append('<thead><tr>')
                for cell in cells:
                    html.append(f'<th>{cell}</th>')
                html.append('</tr></thead><tbody>')
            else:
                # Data row
                html.append('<tr>')
                for cell in cells:
                    html.append(f'<td>{cell}</td>')
                html.append('</tr>')
        
        html.append('</tbody></table>')
        return '\n'.join(html)
    
    def save_html_report(self, content: str, filename: str) -> Path:
        """
        Save HTML report to file.
        
        Parameters
        ----------
        content : str
            Report content (Markdown or HTML)
        filename : str
            Output filename
        
        Returns
        -------
        Path
            Path to saved report
        """
        report_path = self.output_dir / filename
        
        try:
            # Convert Markdown to HTML if needed
            if not content.strip().startswith('<!DOCTYPE'):
                html_content = self.markdown_to_html(content)
                full_html = self.generate_html_header("Report") + html_content + self.generate_html_footer()
            else:
                full_html = content
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(full_html)
            
            logger.info(f"HTML report saved: {report_path}")
            return report_path
        
        except Exception as e:
            logger.error(f"Failed to save HTML report: {str(e)}")
            raise


# =============================================================================
# DATA EXPORTER
# =============================================================================

class DataExporter:
    """
    Exports data to various formats.
    """
    
    def __init__(self, output_dir: Path = OUTPUT_DIR):
        """
        Initialize data exporter.
        
        Parameters
        ----------
        output_dir : Path, optional
            Output directory, by default OUTPUT_DIR
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export_to_csv(self, df: pd.DataFrame, filename: str, 
                      index: bool = False) -> Path:
        """
        Export DataFrame to CSV.
        
        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to export
        filename : str
            Output filename
        index : bool, optional
            Whether to include index, by default False
        
        Returns
        -------
        Path
            Path to exported file
        """
        output_path = self.output_dir / filename
        
        try:
            df.to_csv(output_path, index=index)
            logger.info(f"Data exported to CSV: {output_path}")
            return output_path
        
        except Exception as e:
            logger.error(f"Failed to export CSV: {str(e)}")
            raise
    
    def export_to_json(self, data: Dict[str, Any], filename: str) -> Path:
        """
        Export data to JSON.
        
        Parameters
        ----------
        data : Dict[str, Any]
            Data to export
        filename : str
            Output filename
        
        Returns
        -------
        Path
            Path to exported file
        """
        output_path = self.output_dir / filename
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.info(f"Data exported to JSON: {output_path}")
            return output_path
        
        except Exception as e:
            logger.error(f"Failed to export JSON: {str(e)}")
            raise
    
    def export_to_excel(self, df: pd.DataFrame, filename: str,
                        sheet_name: str = "Sheet1") -> Path:
        """
        Export DataFrame to Excel.
        
        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to export
        filename : str
            Output filename
        sheet_name : str, optional
            Excel sheet name, by default "Sheet1"
        
        Returns
        -------
        Path
            Path to exported file
        """
        output_path = self.output_dir / filename
        
        try:
            df.to_excel(output_path, sheet_name=sheet_name, index=False)
            logger.info(f"Data exported to Excel: {output_path}")
            return output_path
        
        except Exception as e:
            logger.error(f"Failed to export Excel: {str(e)}")
            raise


# =============================================================================
# SUMMARY GENERATOR
# =============================================================================

def generate_execution_summary(statistics: Dict[str, Any]) -> str:
    """
    Generate execution summary in Markdown format.
    
    Parameters
    ----------
    statistics : Dict[str, Any]
        Execution statistics
    
    Returns
    -------
    str
        Markdown formatted summary
    """
    lines = [
        "# Execution Summary",
        "",
    ]
    
    for key, value in statistics.items():
        display_key = key.replace("_", " ").title()
        lines.append(f"- **{display_key}:** {value}")
    
    lines.append("")
    return "\n".join(lines)


def generate_validation_summary_table(results: Dict[str, Any]) -> str:
    """
    Generate validation summary table.
    
    Parameters
    ----------
    results : Dict[str, Any]
        Validation results
    
    Returns
    -------
    str
        Markdown formatted table
    """
    headers = ["Module", "Status", "Checks Passed", "Checks Failed", "Warnings"]
    rows = []
    
    for module_name, result in results.items():
        if isinstance(result, dict):
            status = result.get("passed", False)
            status_str = "✅ PASS" if status else "❌ FAIL"
            
            checks = result.get("checks", [])
            passed = len([c for c in checks if c.get("status") == "PASS"])
            failed = len([c for c in checks if c.get("status") == "FAIL"])
            warnings = len([c for c in checks if c.get("status") == "WARNING"])
            
            rows.append([module_name, status_str, passed, failed, warnings])
    
    # Create Markdown table
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    
    for row in rows:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    
    lines.append("")
    return "\n".join(lines)


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def format_number(value: Any, decimals: int = 2) -> str:
    """
    Format number for display.
    
    Parameters
    ----------
    value : Any
        Value to format
    decimals : int, optional
        Number of decimal places, by default 2
    
    Returns
    -------
    str
        Formatted number
    """
    if value is None:
        return "N/A"
    
    try:
        return f"{float(value):.{decimals}f}"
    except (ValueError, TypeError):
        return str(value)


def format_percentage(value: Any, decimals: int = 2) -> str:
    """
    Format percentage for display.
    
    Parameters
    ----------
    value : Any
        Value to format (0-1 or 0-100)
    decimals : int, optional
        Number of decimal places, by default 2
    
    Returns
    -------
    str
        Formatted percentage
    """
    if value is None:
        return "N/A"
    
    try:
        val = float(value)
        # If value is in 0-1 range, convert to percentage
        if val <= 1.0:
            val = val * 100
        return f"{val:.{decimals}f}%"
    except (ValueError, TypeError):
        return str(value)


def format_timestamp(timestamp: str) -> str:
    """
    Format timestamp for display.
    
    Parameters
    ----------
    timestamp : str
        ISO format timestamp
    
    Returns
    -------
    str
        Formatted timestamp
    """
    try:
        dt = datetime.fromisoformat(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return timestamp