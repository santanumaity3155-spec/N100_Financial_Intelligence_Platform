"""
validator.py

KPI validation and data quality checks for the N100 Financial Intelligence Platform.

This module provides validation functions to ensure KPI calculations are
accurate, complete, and meet quality standards.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd

from src.config.logging_config import get_logger

logger = get_logger(__name__)


class KPIValidator:
    """
    Validates KPI calculations and data quality.
    
    This class provides methods to validate calculated KPIs for accuracy,
    completeness, and reasonableness.
    """

    def __init__(self):
        """Initialize the KPIValidator."""
        self.validation_results = []
        logger.info("KPIValidator initialized")

    def validate_kpi_result(self, kpi_name: str, value: Any, expected_type: type = float) -> Tuple[bool, Optional[str]]:
        """
        Validate a single KPI result.
        
        Parameters
        ----------
        kpi_name : str
            Name of the KPI
        value : Any
            Calculated KPI value
        expected_type : type, default float
            Expected data type for the KPI
            
        Returns
        -------
        Tuple[bool, Optional[str]]
            (is_valid, error_message)
        """
        # Check for None
        if value is None:
            return False, f"{kpi_name}: Value is None"
        
        # Check type
        if not isinstance(value, (expected_type, int)):
            return False, f"{kpi_name}: Expected {expected_type.__name__}, got {type(value).__name__}"
        
        # Check for NaN
        if isinstance(value, float) and pd.isna(value):
            return False, f"{kpi_name}: Value is NaN"
        
        # Check for infinity
        if isinstance(value, float) and (value == float('inf') or value == float('-inf')):
            return False, f"{kpi_name}: Value is infinite"
        
        return True, None

    def validate_kpi_set(self, kpi_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a complete set of KPI results for a company/period.
        
        Parameters
        ----------
        kpi_results : Dict[str, Any]
            Dictionary of calculated KPIs
            
        Returns
        -------
        Dict[str, Any]
            Validation results including pass/fail status and errors
        """
        validation = {
            "company_id": kpi_results.get("company_id"),
            "period": kpi_results.get("period"),
            "total_kpis": 0,
            "valid_kpis": 0,
            "failed_kpis": 0,
            "errors": [],
            "is_valid": True
        }
        
        # Skip metadata fields
        metadata_fields = {"company_id", "period", "periods"}
        
        for kpi_name, value in kpi_results.items():
            if kpi_name in metadata_fields:
                continue
            
            validation["total_kpis"] += 1
            
            is_valid, error_msg = self.validate_kpi_result(kpi_name, value)
            
            if is_valid:
                validation["valid_kpis"] += 1
            else:
                validation["failed_kpis"] += 1
                validation["errors"].append(error_msg)
                validation["is_valid"] = False
        
        self.validation_results.append(validation)
        logger.info(
            f"Validated KPIs for {validation['company_id']}, period {validation['period']}: "
            f"{validation['valid_kpis']}/{validation['total_kpis']} valid"
        )
        
        return validation

    def validate_kpi_batch(self, kpi_batch: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate a batch of KPI results.
        
        Parameters
        ----------
        kpi_batch : List[Dict[str, Any]]
            List of KPI result dictionaries
            
        Returns
        -------
        Dict[str, Any]
            Batch validation summary
        """
        batch_validation = {
            "total_companies": len(kpi_batch),
            "total_kpis": 0,
            "valid_kpis": 0,
            "failed_kpis": 0,
            "company_validations": [],
            "is_valid": True
        }
        
        for kpi_results in kpi_batch:
            validation = self.validate_kpi_set(kpi_results)
            batch_validation["company_validations"].append(validation)
            batch_validation["total_kpis"] += validation["total_kpis"]
            batch_validation["valid_kpis"] += validation["valid_kpis"]
            batch_validation["failed_kpis"] += validation["failed_kpis"]
            
            if not validation["is_valid"]:
                batch_validation["is_valid"] = False
        
        logger.info(
            f"Batch validation complete: {batch_validation['valid_kpis']}/{batch_validation['total_kpis']} "
            f"KPIs valid across {batch_validation['total_companies']} companies"
        )
        
        return batch_validation

    def check_kpi_reasonableness(self, kpi_name: str, value: float, min_val: Optional[float] = None, max_val: Optional[float] = None) -> Tuple[bool, Optional[str]]:
        """
        Check if a KPI value is within reasonable bounds.
        
        Parameters
        ----------
        kpi_name : str
            Name of the KPI
        value : float
            KPI value to check
        min_val : float, optional
            Minimum acceptable value
        max_val : float, optional
            Maximum acceptable value
            
        Returns
        -------
        Tuple[bool, Optional[str]]
            (is_reasonable, warning_message)
        """
        if value is None or pd.isna(value):
            return True, None  # None values are handled by validate_kpi_result
        
        warnings = []
        
        # Define default ranges for common KPIs if not provided
        default_ranges = {
            "roe": (-100, 100),
            "roce": (-100, 100),
            "roa": (-100, 100),
            "net_profit_margin": (-100, 100),
            "operating_margin": (-100, 100),
            "ebit_margin": (-100, 100),
            "gross_margin": (-100, 100),
            "current_ratio": (0, 10),
            "quick_ratio": (0, 10),
            "debt_to_equity": (0, 10),
            "debt_ratio": (0, 1),
            "interest_coverage": (0, 100),
            "pe_ratio": (0, 1000),
            "pb_ratio": (0, 100),
            "dividend_yield": (0, 50),
        }
        
        # Use default ranges if custom ranges not provided
        if min_val is None or max_val is None:
            default_min, default_max = default_ranges.get(kpi_name, (None, None))
            min_val = min_val if min_val is not None else default_min
            max_val = max_val if max_val is not None else default_max
        
        # Check bounds
        if min_val is not None and value < min_val:
            warnings.append(f"{kpi_name}: Value {value:.2f} is below minimum {min_val}")
        
        if max_val is not None and value > max_val:
            warnings.append(f"{kpi_name}: Value {value:.2f} is above maximum {max_val}")
        
        is_reasonable = len(warnings) == 0
        warning_msg = "; ".join(warnings) if warnings else None
        
        if not is_reasonable:
            logger.warning(warning_msg)
        
        return is_reasonable, warning_msg

    def get_validation_summary(self) -> Dict[str, Any]:
        """
        Get summary of all validations performed.
        
        Returns
        -------
        Dict[str, Any]
            Validation summary statistics
        """
        if not self.validation_results:
            return {
                "total_validations": 0,
                "total_kpis": 0,
                "valid_kpis": 0,
                "failed_kpis": 0,
                "success_rate": 0.0
            }
        
        total_kpis = sum(v["total_kpis"] for v in self.validation_results)
        valid_kpis = sum(v["valid_kpis"] for v in self.validation_results)
        failed_kpis = sum(v["failed_kpis"] for v in self.validation_results)
        
        return {
            "total_validations": len(self.validation_results),
            "total_kpis": total_kpis,
            "valid_kpis": valid_kpis,
            "failed_kpis": failed_kpis,
            "success_rate": (valid_kpis / total_kpis * 100) if total_kpis > 0 else 0.0
        }

    def clear_validation_results(self):
        """Clear all validation results."""
        self.validation_results = []
        logger.debug("Validation results cleared")

    def get_failed_validations(self) -> List[Dict[str, Any]]:
        """
        Get list of all failed validations.
        
        Returns
        -------
        List[Dict[str, Any]]
            List of validation results that failed
        """
        return [v for v in self.validation_results if not v["is_valid"]]

    def validate_data_completeness(self, df: pd.DataFrame, required_columns: List[str]) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate that a DataFrame has all required columns with sufficient data.
        
        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to validate
        required_columns : List[str]
            List of required column names
            
        Returns
        -------
        Tuple[bool, Dict[str, Any]]
            (is_complete, validation_report)
        """
        report = {
            "total_columns": len(df.columns),
            "required_columns": required_columns,
            "missing_columns": [],
            "columns_with_nulls": [],
            "completeness_score": 0.0,
            "is_complete": True
        }
        
        # Check for missing columns
        for col in required_columns:
            if col not in df.columns:
                report["missing_columns"].append(col)
                report["is_complete"] = False
        
        # Check for null values
        for col in df.columns:
            null_count = df[col].isna().sum()
            null_pct = (null_count / len(df)) * 100 if len(df) > 0 else 0
            
            if null_pct > 20:  # More than 20% nulls
                report["columns_with_nulls"].append({
                    "column": col,
                    "null_count": int(null_count),
                    "null_percentage": round(null_pct, 2)
                })
        
        # Calculate completeness score
        if len(df.columns) > 0:
            total_cells = len(df) * len(df.columns)
            null_cells = df.isna().sum().sum()
            report["completeness_score"] = round(((total_cells - null_cells) / total_cells) * 100, 2)
        
        logger.debug(f"Data completeness validation: {report['completeness_score']}% complete")
        
        return report["is_complete"], report