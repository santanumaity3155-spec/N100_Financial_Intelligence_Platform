"""
formatter.py

KPI result formatting and output utilities for the N100 Financial Intelligence Platform.

This module provides functions to format, export, and display KPI calculation results
in various formats including JSON, CSV, and DataFrames.
"""

import logging
from typing import Dict, Any, List, Optional
import pandas as pd
import json
from datetime import datetime

from src.config.logging_config import get_logger

logger = get_logger(__name__)


class KPIFormatter:
    """
    Formats and exports KPI calculation results.
    
    This class provides methods to convert KPI results into various formats
    for reporting, storage, and visualization.
    """

    def __init__(self):
        """Initialize the KPIFormatter."""
        logger.info("KPIFormatter initialized")

    def format_kpi_results(self, kpi_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format KPI results for output.
        
        Parameters
        ----------
        kpi_results : Dict[str, Any]
            Raw KPI calculation results
            
        Returns
        -------
        Dict[str, Any]
            Formatted KPI results
        """
        formatted = {
            "company_id": kpi_results.get("company_id"),
            "period": kpi_results.get("period"),
            "calculated_at": datetime.now().isoformat(),
            "kpis": {}
        }
        
        # Format each KPI
        for kpi_name, value in kpi_results.items():
            if kpi_name in ["company_id", "period", "periods"]:
                continue
            
            formatted["kpis"][kpi_name] = {
                "value": value,
                "formatted_value": self._format_kpi_value(kpi_name, value),
                "is_calculated": value is not None
            }
        
        logger.debug(f"Formatted KPI results for {formatted['company_id']}")
        return formatted

    def _format_kpi_value(self, kpi_name: str, value: Optional[float]) -> Optional[str]:
        """
        Format a single KPI value for display.
        
        Parameters
        ----------
        kpi_name : str
            Name of the KPI
        value : Optional[float]
            KPI value to format
            
        Returns
        -------
        Optional[str]
            Formatted string representation of the value
        """
        if value is None:
            return "N/A"
        
        # Format based on KPI type
        if kpi_name in ["roe", "roce", "roa", "net_profit_margin", "operating_margin", 
                        "ebit_margin", "gross_margin", "dividend_yield"]:
            return f"{value:.2f}%"
        elif kpi_name in ["current_ratio", "quick_ratio", "cash_ratio", "pe_ratio", 
                          "pb_ratio", "ev_ebitda", "debt_to_equity", "debt_ratio",
                          "interest_coverage", "financial_leverage"]:
            return f"{value:.2f}x"
        elif kpi_name in ["eps", "operating_cash_flow", "free_cash_flow"]:
            return f"{value:.2f}"
        elif kpi_name in ["asset_turnover", "inventory_turnover", "receivable_turnover",
                          "working_capital_turnover"]:
            return f"{value:.2f}x"
        elif kpi_name in ["revenue_cagr", "profit_cagr", "eps_cagr"]:
            return f"{value:.2f}%"
        elif kpi_name == "margin_expansion":
            return f"{value:+.2f}pp"  # + or - sign, percentage points
        else:
            return f"{value:.2f}"

    def kpi_results_to_dataframe(self, kpi_batch: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Convert a batch of KPI results to a pandas DataFrame.
        
        Parameters
        ----------
        kpi_batch : List[Dict[str, Any]]
            List of KPI result dictionaries
            
        Returns
        -------
        pd.DataFrame
            DataFrame with KPI results
        """
        if not kpi_batch:
            logger.warning("Empty KPI batch provided")
            return pd.DataFrame()
        
        # Flatten KPI results
        rows = []
        for kpi_results in kpi_batch:
            row = {
                "company_id": kpi_results.get("company_id"),
                "period": kpi_results.get("period"),
            }
            
            # Add all KPI values
            for kpi_name, value in kpi_results.items():
                if kpi_name not in ["company_id", "period", "periods"]:
                    row[kpi_name] = value
            
            rows.append(row)
        
        df = pd.DataFrame(rows)
        logger.info(f"Converted {len(rows)} KPI results to DataFrame")
        return df

    def kpi_results_to_json(self, kpi_batch: List[Dict[str, Any]], indent: int = 2) -> str:
        """
        Convert KPI results to JSON string.
        
        Parameters
        ----------
        kpi_batch : List[Dict[str, Any]]
            List of KPI result dictionaries
        indent : int, default 2
            JSON indentation level
            
        Returns
        -------
        str
            JSON string representation of KPI results
        """
        formatted_results = [self.format_kpi_results(kpi) for kpi in kpi_batch]
        json_str = json.dumps(formatted_results, indent=indent, default=str)
        logger.info(f"Converted {len(formatted_results)} KPI results to JSON")
        return json_str

    def kpi_results_to_csv(self, kpi_batch: List[Dict[str, Any]]) -> str:
        """
        Convert KPI results to CSV string.
        
        Parameters
        ----------
        kpi_batch : List[Dict[str, Any]]
            List of KPI result dictionaries
            
        Returns
        -------
        str
            CSV string representation of KPI results
        """
        df = self.kpi_results_to_dataframe(kpi_batch)
        csv_str = df.to_csv(index=False)
        logger.info(f"Converted {len(kpi_batch)} KPI results to CSV")
        return csv_str

    def save_kpi_results_to_json(self, kpi_batch: List[Dict[str, Any]], file_path: str) -> bool:
        """
        Save KPI results to a JSON file.
        
        Parameters
        ----------
        kpi_batch : List[Dict[str, Any]]
            List of KPI result dictionaries
        file_path : str
            Path to save the JSON file
            
        Returns
        -------
        bool
            True if save was successful
        """
        try:
            json_str = self.kpi_results_to_json(kpi_batch)
            with open(file_path, 'w') as f:
                f.write(json_str)
            logger.info(f"Saved KPI results to JSON file: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save KPI results to JSON: {str(e)}")
            return False

    def save_kpi_results_to_csv(self, kpi_batch: List[Dict[str, Any]], file_path: str) -> bool:
        """
        Save KPI results to a CSV file.
        
        Parameters
        ----------
        kpi_batch : List[Dict[str, Any]]
            List of KPI result dictionaries
        file_path : str
            Path to save the CSV file
            
        Returns
        -------
        bool
            True if save was successful
        """
        try:
            csv_str = self.kpi_results_to_csv(kpi_batch)
            with open(file_path, 'w') as f:
                f.write(csv_str)
            logger.info(f"Saved KPI results to CSV file: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save KPI results to CSV: {str(e)}")
            return False

    def generate_kpi_summary_report(self, kpi_batch: List[Dict[str, Any]]) -> str:
        """
        Generate a human-readable summary report of KPI results.
        
        Parameters
        ----------
        kpi_batch : List[Dict[str, Any]]
            List of KPI result dictionaries
            
        Returns
        -------
        str
            Formatted summary report
        """
        if not kpi_batch:
            return "No KPI results to report"
        
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("KPI CALCULATION SUMMARY REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Total Companies: {len(kpi_batch)}")
        report_lines.append("")
        
        for kpi_results in kpi_batch:
            company_id = kpi_results.get("company_id", "Unknown")
            period = kpi_results.get("period", "Unknown")
            
            report_lines.append("-" * 80)
            report_lines.append(f"Company: {company_id} | Period: {period}")
            report_lines.append("-" * 80)
            
            # Group KPIs by category
            categories = self._group_kpis_by_category(kpi_results)
            
            for category, kpis in categories.items():
                report_lines.append(f"\n{category}:")
                for kpi_name, value in kpis.items():
                    formatted_value = self._format_kpi_value(kpi_name, value)
                    report_lines.append(f"  {kpi_name:.<30} {formatted_value}")
            
            report_lines.append("")
        
        report_lines.append("=" * 80)
        
        report = "\n".join(report_lines)
        logger.info(f"Generated KPI summary report for {len(kpi_batch)} companies")
        return report

    def _group_kpis_by_category(self, kpi_results: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Group KPIs by category for reporting.
        
        Parameters
        ----------
        kpi_results : Dict[str, Any]
            KPI results dictionary
            
        Returns
        -------
        Dict[str, Dict[str, Any]]
            KPIs grouped by category
        """
        categories = {
            "Profitability": ["roe", "roce", "roa", "net_profit_margin", "operating_margin", 
                            "ebit_margin", "gross_margin"],
            "Liquidity": ["current_ratio", "quick_ratio", "cash_ratio"],
            "Leverage": ["debt_to_equity", "debt_ratio", "interest_coverage", "financial_leverage"],
            "Efficiency": ["asset_turnover", "inventory_turnover", "receivable_turnover",
                          "working_capital_turnover"],
            "Cash Flow": ["operating_cash_flow", "free_cash_flow", "cash_conversion_ratio"],
            "Valuation": ["eps", "pe_ratio", "pb_ratio", "ev_ebitda", "dividend_yield"],
            "Growth": ["revenue_cagr", "profit_cagr", "eps_cagr", "margin_expansion"]
        }
        
        grouped = {}
        for category, kpi_list in categories.items():
            category_kpis = {}
            for kpi_name in kpi_list:
                if kpi_name in kpi_results:
                    category_kpis[kpi_name] = kpi_results[kpi_name]
            
            if category_kpis:
                grouped[category] = category_kpis
        
        return grouped

    def print_kpi_results(self, kpi_results: Dict[str, Any]):
        """
        Print KPI results to console in a formatted manner.
        
        Parameters
        ----------
        kpi_results : Dict[str, Any]
            KPI results dictionary
        """
        report = self.generate_kpi_summary_report([kpi_results])
        print(report)

    def get_kpi_statistics(self, kpi_batch: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate statistics across a batch of KPI results.
        
        Parameters
        ----------
        kpi_batch : List[Dict[str, Any]]
            List of KPI result dictionaries
            
        Returns
        -------
        Dict[str, Any]
            Statistical summary of KPI values
        """
        if not kpi_batch:
            return {}
        
        # Convert to DataFrame for easier statistics
        df = self.kpi_results_to_dataframe(kpi_batch)
        
        stats = {
            "total_companies": len(df),
            "kpi_statistics": {}
        }
        
        # Calculate statistics for each KPI column
        for column in df.columns:
            if column in ["company_id", "period", "periods"]:
                continue
            
            values = pd.to_numeric(df[column], errors='coerce')
            valid_values = values.dropna()
            
            if len(valid_values) > 0:
                stats["kpi_statistics"][column] = {
                    "count": len(valid_values),
                    "mean": round(valid_values.mean(), 2),
                    "median": round(valid_values.median(), 2),
                    "std": round(valid_values.std(), 2),
                    "min": round(valid_values.min(), 2),
                    "max": round(valid_values.max(), 2),
                }
        
        logger.info(f"Calculated statistics for {len(stats['kpi_statistics'])} KPIs")
        return stats