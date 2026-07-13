"""
validator.py

Data validation module for the N100 Financial Intelligence Platform.
Validates datasets for structure, completeness, and data quality.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

import pandas as pd

from src.config.logging_config import get_logger

logger = get_logger(__name__)


class DataValidator:
    """
    Validates DataFrames for data quality and structure.
    
    Responsibilities:
    1. Validate required columns exist
    2. Check for missing values
    3. Detect duplicate records
    4. Validate data types
    5. Generate validation reports
    """

    def __init__(self):
        """Initialize the DataValidator."""
        self.validation_results = {}

    def validate_required_columns(
        self,
        df: pd.DataFrame,
        required_columns: List[str],
        dataset_name: str
    ) -> Dict[str, Any]:
        """
        Validate that all required columns exist in the DataFrame.
        
        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to validate
        required_columns : List[str]
            List of required column names
        dataset_name : str
            Name of the dataset for logging
            
        Returns
        -------
        Dict[str, Any]
            Validation results
        """
        result = {
            "dataset": dataset_name,
            "check": "required_columns",
            "passed": True,
            "missing_columns": [],
            "extra_columns": [],
            "message": ""
        }

        df_columns = set(df.columns)
        
        # If no required columns specified, just report what we have
        if not required_columns:
            result["message"] = f"No required columns specified. Dataset has {len(df_columns)} columns."
            logger.info(f"{dataset_name}: No required columns specified, dataset has {len(df_columns)} columns")
            return result
        
        required_set = set(required_columns)
        
        missing = required_set - df_columns
        extra = df_columns - required_set

        if missing:
            result["passed"] = False
            result["missing_columns"] = list(missing)
            result["message"] = f"Missing required columns: {list(missing)}"
            logger.error(f"{dataset_name}: Missing columns {list(missing)}")
        else:
            logger.info(f"{dataset_name}: All required columns present")
            
        if extra:
            result["extra_columns"] = list(extra)
            logger.warning(f"{dataset_name}: Extra columns found {list(extra)}")

        return result

    def detect_missing_values(
        self,
        df: pd.DataFrame,
        dataset_name: str,
        threshold: float = 30.0,
        columns_to_check: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Detect and report missing values in the DataFrame.
        
        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to check
        dataset_name : str
            Name of the dataset for logging
        threshold : float, default 30.0
            Maximum allowed percentage of missing values per column
        columns_to_check : List[str], optional
            Specific columns to check for missing values. If None, checks all columns.
            
        Returns
        -------
        Dict[str, Any]
            Missing value analysis results
        """
        result = {
            "dataset": dataset_name,
            "check": "missing_values",
            "passed": True,
            "total_rows": len(df),
            "columns_with_missing": {},
            "columns_exceeding_threshold": [],
            "message": ""
        }

        # Determine which columns to check
        if columns_to_check:
            # Only check specified columns that exist in DataFrame
            columns_to_check = [col for col in columns_to_check if col in df.columns]
            if not columns_to_check:
                logger.info(f"{dataset_name}: No valid columns to check for missing values")
                return result
        else:
            # Check all columns
            columns_to_check = list(df.columns)

        # Calculate missing values per column
        missing_counts = df[columns_to_check].isnull().sum()
        missing_percentages = (missing_counts / len(df)) * 100

        # Find columns with missing values
        columns_with_missing = {}
        for col in columns_to_check:
            missing_count = missing_counts[col]
            missing_pct = missing_percentages[col]
            
            if missing_count > 0:
                columns_with_missing[col] = {
                    "count": int(missing_count),
                    "percentage": round(missing_pct, 2)
                }
                
                if missing_pct > threshold:
                    result["columns_exceeding_threshold"].append(col)

        result["columns_with_missing"] = columns_with_missing

        if result["columns_exceeding_threshold"]:
            result["passed"] = False
            result["message"] = (
                f"Columns exceeding {threshold}% missing values: "
                f"{result['columns_exceeding_threshold']}"
            )
            logger.warning(
                f"{dataset_name}: {len(result['columns_exceeding_threshold'])} "
                f"columns exceed {threshold}% missing values"
            )
        else:
            logger.info(f"{dataset_name}: Missing values within acceptable limits")

        return result

    def detect_duplicates(
        self,
        df: pd.DataFrame,
        dataset_name: str,
        subset: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Detect duplicate records in the DataFrame.
        
        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to check
        dataset_name : str
            Name of the dataset for logging
        subset : List[str], optional
            Columns to consider for identifying duplicates
            
        Returns
        -------
        Dict[str, Any]
            Duplicate detection results
        """
        result = {
            "dataset": dataset_name,
            "check": "duplicates",
            "passed": True,
            "total_rows": len(df),
            "duplicate_count": 0,
            "duplicate_percentage": 0.0,
            "message": ""
        }

        # Filter subset to only include columns that exist in DataFrame
        if subset:
            subset = [col for col in subset if col in df.columns]
            
        # Skip duplicate check if subset is empty or None
        if not subset:
            logger.info(f"{dataset_name}: Skipping duplicate check (no valid subset columns)")
            result["message"] = "Duplicate check skipped - no valid subset columns"
            return result

        try:
            duplicate_count = df.duplicated(subset=subset, keep=False).sum()
            duplicate_pct = (duplicate_count / len(df) * 100) if len(df) > 0 else 0.0

            result["duplicate_count"] = int(duplicate_count)
            result["duplicate_percentage"] = round(duplicate_pct, 2)

            if duplicate_count > 0:
                result["passed"] = False
                result["message"] = (
                    f"Found {duplicate_count} duplicate rows "
                    f"({duplicate_pct:.2f}%)"
                )
                logger.warning(
                    f"{dataset_name}: {duplicate_count} duplicate rows found"
                )
            else:
                logger.info(f"{dataset_name}: No duplicates found")

        except Exception as e:
            logger.warning(f"{dataset_name}: Could not check duplicates: {str(e)}")
            result["message"] = f"Duplicate check failed: {str(e)}"

        return result

    def validate_data_types(
        self,
        df: pd.DataFrame,
        expected_types: Dict[str, str],
        dataset_name: str
    ) -> Dict[str, Any]:
        """
        Validate data types of columns.
        
        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to validate
        expected_types : Dict[str, str]
            Dictionary mapping column names to expected data types
        dataset_name : str
            Name of the dataset for logging
            
        Returns
        -------
        Dict[str, Any]
            Data type validation results
        """
        result = {
            "dataset": dataset_name,
            "check": "data_types",
            "passed": True,
            "type_mismatches": [],
            "message": ""
        }

        for col, expected_type in expected_types.items():
            if col not in df.columns:
                result["type_mismatches"].append({
                    "column": col,
                    "issue": "Column not found"
                })
                continue

            actual_type = str(df[col].dtype)
            
            # Flexible type checking
            type_match = False
            if expected_type.lower() in ["int", "integer"] and "int" in actual_type:
                type_match = True
            elif expected_type.lower() in ["float", "numeric"] and "float" in actual_type:
                type_match = True
            elif expected_type.lower() in ["str", "string", "text"] and "object" in actual_type:
                type_match = True
            elif expected_type.lower() in ["date", "datetime"] and (
                "datetime" in actual_type or "object" in actual_type
            ):
                type_match = True

            if not type_match:
                result["type_mismatches"].append({
                    "column": col,
                    "expected": expected_type,
                    "actual": actual_type
                })

        if result["type_mismatches"]:
            result["passed"] = False
            result["message"] = f"Type mismatches found: {len(result['type_mismatches'])}"
            logger.warning(f"{dataset_name}: Data type mismatches detected")
        else:
            logger.info(f"{dataset_name}: Data types validated successfully")

        return result

    def validate_dataset(
        self,
        df: pd.DataFrame,
        dataset_name: str,
        required_columns: Optional[List[str]] = None,
        expected_types: Optional[Dict[str, str]] = None,
        missing_threshold: Optional[float] = None,
        duplicate_subset: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive validation on a dataset.
        
        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to validate
        dataset_name : str
            Name of the dataset
        required_columns : List[str], optional
            List of required columns
        expected_types : Dict[str, str], optional
            Expected data types for columns
        missing_threshold : float, optional
            Maximum allowed missing value percentage. If None, uses dataset-specific defaults
        duplicate_subset : List[str], optional
            Columns to check for duplicates
            
        Returns
        -------
        Dict[str, Any]
            Complete validation results
        """
        logger.info(f"Starting validation for dataset: {dataset_name}")

        # Use dataset-specific null limits if threshold not provided
        if missing_threshold is None:
            missing_threshold = self._get_null_limit(dataset_name)

        validation_result = {
            "dataset": dataset_name,
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "checks": [],
            "overall_passed": True
        }

        # Check required columns
        if required_columns:
            col_check = self.validate_required_columns(
                df, required_columns, dataset_name
            )
            validation_result["checks"].append(col_check)
            if not col_check["passed"]:
                validation_result["overall_passed"] = False

        # Check missing values (only for required columns to avoid false failures)
        # For datasets with high null tolerance (like pros_cons), only check required columns
        columns_to_check = required_columns if missing_threshold >= 50 else None
        missing_check = self.detect_missing_values(
            df, dataset_name, threshold=missing_threshold, columns_to_check=columns_to_check
        )
        validation_result["checks"].append(missing_check)
        if not missing_check["passed"]:
            validation_result["overall_passed"] = False

        # Check duplicates
        dup_check = self.detect_duplicates(
            df, dataset_name, subset=duplicate_subset
        )
        validation_result["checks"].append(dup_check)
        if not dup_check["passed"]:
            validation_result["overall_passed"] = False

        # Check data types
        if expected_types:
            type_check = self.validate_data_types(
                df, expected_types, dataset_name
            )
            validation_result["checks"].append(type_check)
            if not type_check["passed"]:
                validation_result["overall_passed"] = False

        # Store result
        self.validation_results[dataset_name] = validation_result

        status = "PASSED" if validation_result["overall_passed"] else "FAILED"
        logger.info(f"Validation {status} for {dataset_name}")

        return validation_result

    def get_validation_summary(self) -> Dict[str, Any]:
        """
        Get summary of all validation results.
        
        Returns
        -------
        Dict[str, Any]
            Summary of validation results
        """
        total_datasets = len(self.validation_results)
        passed = sum(1 for r in self.validation_results.values() if r["overall_passed"])
        failed = total_datasets - passed

        summary = {
            "total_datasets": total_datasets,
            "passed": passed,
            "failed": failed,
            "pass_rate": round((passed / total_datasets * 100) if total_datasets > 0 else 0, 2),
            "datasets": {}
        }

        for dataset_name, result in self.validation_results.items():
            summary["datasets"][dataset_name] = {
                "overall_passed": result["overall_passed"],
                "total_rows": result["total_rows"],
                "total_columns": result["total_columns"],
                "failed_checks": [
                    check["check"] for check in result["checks"] if not check["passed"]
                ]
            }

        return summary

    def _get_null_limit(self, dataset_name: str) -> float:
        """
        Get dataset-specific null value limit.
        
        Parameters
        ----------
        dataset_name : str
            Name of the dataset
            
        Returns
        -------
        float
            Maximum allowed missing value percentage for this dataset
        """
        # Dataset-specific null limits (Fix for Issue #1)
        NULL_LIMITS = {
            "companies": 5,
            "profit_loss": 5,
            "balance_sheet": 5,
            "cash_flow": 5,
            "pros_cons": 80,  # pros_cons can have high null values (e.g., remarks column)
            "analysis": 5,
            "documents": 5,
            "stock_prices": 5,
            "market_cap": 5,
            "financial_ratios": 5,
            "peer_groups": 5
        }
        
        return NULL_LIMITS.get(dataset_name, 30.0)

    def clear_results(self):
        """Clear all validation results."""
        self.validation_results.clear()
        logger.info("Validation results cleared")


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def validate_dataset(
    df: pd.DataFrame,
    dataset_name: str,
    **kwargs
) -> Dict[str, Any]:
    """
    Convenience function to validate a single dataset.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to validate
    dataset_name : str
        Name of the dataset
    **kwargs
        Additional arguments for DataValidator.validate_dataset()
        
    Returns
    -------
    Dict[str, Any]
        Validation results
    """
    validator = DataValidator()
    return validator.validate_dataset(df, dataset_name, **kwargs)


# =============================================================================
# SCRIPT TEST
# =============================================================================

if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)
    
    # Create sample DataFrame
    df = pd.DataFrame({
        "id": [1, 2, 3, 4, 5],
        "name": ["A", "B", "C", "D", "E"],
        "value": [10.0, None, 30.0, 40.0, 50.0]
    })
    
    validator = DataValidator()
    result = validator.validate_dataset(
        df,
        "test_dataset",
        required_columns=["id", "name", "value"],
        expected_types={"id": "int", "name": "str", "value": "float"}
    )
    
    print("Validation Result:", result["overall_passed"])
    print("Summary:", validator.get_validation_summary())