"""
normalizer.py

Data normalization module for the N100 Financial Intelligence Platform.
Normalizes company IDs, dates, and column names across all datasets.
"""

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Any

import pandas as pd

from src.config.logging_config import get_logger

logger = get_logger(__name__)


class DataNormalizer:
    """
    Normalizes data across datasets for consistency.
    
    Responsibilities:
    1. Normalize company IDs to standard format
    2. Normalize date formats
    3. Clean and standardize column names
    4. Ensure data consistency across datasets
    """

    def __init__(self):
        """Initialize the DataNormalizer."""
        self.normalization_log = []

    def normalize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and standardize column names.
        
        Parameters
        ----------
        df : pd.DataFrame
            DataFrame with columns to normalize
            
        Returns
        -------
        pd.DataFrame
            DataFrame with normalized column names
        """
        df = df.copy()
        
        # Create mapping of old to new column names
        new_columns = {}
        for col in df.columns:
            # Convert to string
            col_str = str(col).strip()
            
            # Convert to lowercase
            col_lower = col_str.lower()
            
            # Replace spaces and special characters with underscores
            col_normalized = re.sub(r'[^a-z0-9]+', '_', col_lower)
            
            # Remove leading/trailing underscores
            col_normalized = col_normalized.strip('_')
            
            # Remove multiple consecutive underscores
            col_normalized = re.sub(r'_+', '_', col_normalized)
            
            new_columns[col] = col_normalized

        df.rename(columns=new_columns, inplace=True)
        
        logger.info(f"Normalized {len(new_columns)} column names")
        self.normalization_log.append({
            "operation": "normalize_column_names",
            "columns_normalized": len(new_columns)
        })
        
        return df

    def normalize_company_id(
        self,
        df: pd.DataFrame,
        company_id_column: str = "company_id"
    ) -> pd.DataFrame:
        """
        Normalize company IDs to standard format.
        
        Parameters
        ----------
        df : pd.DataFrame
            DataFrame containing company IDs
        company_id_column : str, default "company_id"
            Name of the company ID column
            
        Returns
        -------
        pd.DataFrame
            DataFrame with normalized company IDs
        """
        if company_id_column not in df.columns:
            logger.warning(
                f"Company ID column '{company_id_column}' not found. "
                f"Skipping normalization."
            )
            return df

        df = df.copy()
        
        # Store original count
        original_count = df[company_id_column].nunique()
        
        # Normalize: strip whitespace, convert to uppercase, remove special chars
        df[company_id_column] = df[company_id_column].apply(
            lambda x: self._normalize_id(str(x).strip().upper()) if pd.notna(x) else x
        )
        
        # Store normalized count
        normalized_count = df[company_id_column].nunique()
        
        logger.info(
            f"Normalized company IDs: {original_count} unique -> {normalized_count} unique"
        )
        
        self.normalization_log.append({
            "operation": "normalize_company_id",
            "column": company_id_column,
            "original_unique": original_count,
            "normalized_unique": normalized_count
        })
        
        return df

    def _normalize_id(self, company_id: str) -> str:
        """
        Normalize a single company ID.
        
        Parameters
        ----------
        company_id : str
            Company ID to normalize
            
        Returns
        -------
        str
            Normalized company ID
        """
        # Remove special characters except alphanumeric and underscores
        normalized = re.sub(r'[^A-Z0-9_]', '', company_id)
        
        # Remove leading/trailing underscores
        normalized = normalized.strip('_')
        
        return normalized

    def normalize_dates(
        self,
        df: pd.DataFrame,
        date_columns: List[str],
        date_format: str = "%Y-%m-%d"
    ) -> pd.DataFrame:
        """
        Normalize date columns to standard format.
        
        Parameters
        ----------
        df : pd.DataFrame
            DataFrame containing date columns
        date_columns : List[str]
            List of column names containing dates
        date_format : str, default "%Y-%m-%d"
            Target date format
            
        Returns
        -------
        pd.DataFrame
            DataFrame with normalized dates
        """
        df = df.copy()
        
        for col in date_columns:
            if col not in df.columns:
                logger.warning(f"Date column '{col}' not found. Skipping.")
                continue

            original_count = df[col].notna().sum()
            
            # Try to parse dates
            try:
                # Convert to datetime
                df[col] = pd.to_datetime(df[col], errors='coerce')
                
                # Format to target format
                df[col] = df[col].dt.strftime(date_format)
                
                normalized_count = df[col].notna().sum()
                
                logger.info(
                    f"Normalized dates in '{col}': "
                    f"{original_count} -> {normalized_count} valid dates"
                )
                
                self.normalization_log.append({
                    "operation": "normalize_dates",
                    "column": col,
                    "format": date_format,
                    "original_valid": int(original_count),
                    "normalized_valid": int(normalized_count)
                })
                
            except Exception as e:
                logger.error(f"Failed to normalize dates in '{col}': {str(e)}")

        return df

    def normalize_numeric_columns(
        self,
        df: pd.DataFrame,
        numeric_columns: List[str]
    ) -> pd.DataFrame:
        """
        Normalize numeric columns by converting to proper numeric types.
        
        Parameters
        ----------
        df : pd.DataFrame
            DataFrame containing numeric columns
        numeric_columns : List[str]
            List of column names to convert to numeric
            
        Returns
        -------
        pd.DataFrame
            DataFrame with normalized numeric columns
        """
        df = df.copy()
        
        for col in numeric_columns:
            if col not in df.columns:
                logger.warning(f"Numeric column '{col}' not found. Skipping.")
                continue

            original_count = df[col].notna().sum()
            
            # Convert to numeric, coercing errors to NaN
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
            normalized_count = df[col].notna().sum()
            
            logger.info(
                f"Normalized numeric column '{col}': "
                f"{original_count} -> {normalized_count} valid values"
            )
            
            self.normalization_log.append({
                "operation": "normalize_numeric",
                "column": col,
                "original_valid": int(original_count),
                "normalized_valid": int(normalized_count)
            })

        return df

    def remove_duplicates(
        self,
        df: pd.DataFrame,
        subset: Optional[List[str]] = None,
        keep: str = "first"
    ) -> pd.DataFrame:
        """
        Remove duplicate rows from DataFrame.
        
        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to deduplicate
        subset : List[str], optional
            Columns to consider for identifying duplicates
        keep : str, default "first"
            Which duplicate to keep ('first', 'last', False)
            
        Returns
        -------
        pd.DataFrame
            Deduplicated DataFrame
        """
        original_count = len(df)
        
        # Filter subset to only include columns that exist in DataFrame
        if subset:
            subset = [col for col in subset if col in df.columns]
        
        # Skip if no valid subset columns
        if not subset:
            logger.info("No duplicates removed (no valid subset columns)")
            return df
        
        try:
            df = df.drop_duplicates(subset=subset, keep=keep)
            
            removed_count = original_count - len(df)
            
            if removed_count > 0:
                logger.info(
                    f"Removed {removed_count} duplicate rows "
                    f"({removed_count/original_count*100:.2f}%)"
                )
                
                self.normalization_log.append({
                    "operation": "remove_duplicates",
                    "subset": subset,
                    "original_count": original_count,
                    "removed_count": removed_count,
                    "final_count": len(df)
                })
            else:
                logger.info("No duplicates found")

        except Exception as e:
            logger.warning(f"Could not remove duplicates: {str(e)}")

        return df

    def normalize_dataframe(
        self,
        df: pd.DataFrame,
        company_id_col: str = "company_id",
        date_cols: Optional[List[str]] = None,
        numeric_cols: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Normalize an entire DataFrame.
        
        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to normalize
        company_id_col : str, default "company_id"
            Company ID column name
        date_cols : List[str], optional
            List of date columns to normalize
        numeric_cols : List[str], optional
            List of numeric columns to normalize
            
        Returns
        -------
        pd.DataFrame
            Normalized DataFrame
        """
        # Normalize column names
        df = self.normalize_column_names(df)
        
        # Normalize company IDs
        df = self.normalize_company_id(df, company_id_col)
        
        # Normalize dates
        if date_cols:
            df = self.normalize_dates(df, date_cols)
        
        # Normalize numeric columns
        if numeric_cols:
            df = self.normalize_numeric_columns(df, numeric_cols)
        
        return df

    def get_normalization_log(self) -> List[Dict[str, Any]]:
        """
        Get log of all normalization operations.
        
        Returns
        -------
        List[Dict[str, Any]]
            List of normalization operations performed
        """
        return self.normalization_log

    def clear_log(self):
        """Clear normalization log."""
        self.normalization_log.clear()
        logger.info("Normalization log cleared")


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def normalize_dataframe(
    df: pd.DataFrame,
    company_id_col: str = "company_id",
    date_cols: Optional[List[str]] = None,
    numeric_cols: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Convenience function to normalize a DataFrame.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to normalize
    company_id_col : str, default "company_id"
        Company ID column name
    date_cols : List[str], optional
        List of date columns to normalize
    numeric_cols : List[str], optional
        List of numeric columns to normalize
        
    Returns
    -------
    pd.DataFrame
        Normalized DataFrame
    """
    normalizer = DataNormalizer()
    
    # Normalize column names
    df = normalizer.normalize_column_names(df)
    
    # Normalize company IDs
    df = normalizer.normalize_company_id(df, company_id_col)
    
    # Normalize dates
    if date_cols:
        df = normalizer.normalize_dates(df, date_cols)
    
    # Normalize numeric columns
    if numeric_cols:
        df = normalizer.normalize_numeric_columns(df, numeric_cols)
    
    return df


# =============================================================================
# SCRIPT TEST
# =============================================================================

if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)
    
    # Create sample DataFrame
    df = pd.DataFrame({
        "Company ID": ["TCS ", "INFY", "WIPRO", " tcs", "INFY"],
        "Date": ["2024-01-01", "2024-02-01", "2024-03-01", "2024-04-01", "2024-05-01"],
        "Revenue": ["1000", "2000", "3000", "4000", "5000"],
        "Profit": [100.5, 200.3, 300.7, 400.2, 500.9]
    })
    
    normalizer = DataNormalizer()
    
    # Normalize
    df_normalized = normalizer.normalize_column_names(df)
    df_normalized = normalizer.normalize_company_id(df_normalized, "company_id")
    df_normalized = normalizer.normalize_dates(df_normalized, ["date"])
    df_normalized = normalizer.normalize_numeric_columns(
        df_normalized, ["revenue", "profit"]
    )
    df_normalized = normalizer.remove_duplicates(df_normalized, subset=["company_id", "date"])
    
    print("\nNormalized DataFrame:")
    print(df_normalized)
    print("\nNormalization Log:")
    print(normalizer.get_normalization_log())