"""
extract.py

Data extraction module for the N100 Financial Intelligence Platform.
Responsible for reading Excel files from the raw data directory.
"""

import logging
from pathlib import Path
from typing import Dict, Optional, Any

import pandas as pd

from src.config.constants import RAW_DATA_DIR, RAW_DATASETS
from src.config.logging_config import get_logger
from src.config.column_mappings import apply_column_mapping

logger = get_logger(__name__)


class DataExtractor:
    """
    Extracts data from Excel files.
    
    Responsibilities:
    1. Read Excel files from raw data directory
    2. Handle different sheet names and header rows
    3. Return DataFrames for further processing
    """

    def __init__(self, raw_data_dir: Optional[Path] = None):
        """
        Initialize the DataExtractor.
        
        Parameters
        ----------
        raw_data_dir : Path, optional
            Path to raw data directory. Defaults to RAW_DATA_DIR from constants.
        """
        self.raw_data_dir = raw_data_dir or RAW_DATA_DIR
        logger.info(f"DataExtractor initialized with directory: {self.raw_data_dir}")

    def _detect_header_row(self, file_path: Path, sheet_name: str = 0, **kwargs) -> int:
        """
        Detect which row contains the actual headers.
        
        Parameters
        ----------
        file_path : Path
            Path to the Excel file
        sheet_name : str or int, default 0
            Sheet name or index to read
        **kwargs
            Additional arguments to pass to pd.read_excel()
            
        Returns
        -------
        int
            Row number to use as header (0-indexed). Returns None if no header row exists.
        """
        # Read first 3 rows without header to inspect structure
        df_raw = pd.read_excel(file_path, sheet_name=sheet_name, header=None, nrows=3, **kwargs)
        
        if len(df_raw) == 0:
            return 0
        
        # Check row 1 (index 1) - if it contains string column names that look like headers
        if len(df_raw) > 1:
            row_1 = df_raw.iloc[1]
            string_count = sum(1 for val in row_1 if isinstance(val, str))
            numeric_count = sum(1 for val in row_1 if isinstance(val, (int, float)) and not isinstance(val, bool))
            
            # If row 1 has mostly strings and looks like headers, use header=1
            # Heuristic: headers typically have more strings than numbers
            if string_count > numeric_count and string_count > len(row_1) * 0.5:
                logger.debug(f"Detected header row at index 1 for {file_path.name}")
                return 1
        
        # Check if row 0 contains headers (no title row)
        if len(df_raw) > 0:
            row_0 = df_raw.iloc[0]
            string_count = sum(1 for val in row_0 if isinstance(val, str))
            numeric_count = sum(1 for val in row_0 if isinstance(val, (int, float)) and not isinstance(val, bool))
            
            # If row 0 has mostly strings, it might be headers
            if string_count > numeric_count and string_count > len(row_0) * 0.5:
                logger.debug(f"Detected header row at index 0 for {file_path.name}")
                return 0
        
        # If we reach here, there's no clear header row (all numeric or mixed)
        # Return None to indicate no header - data starts from row 0
        logger.debug(f"No header row detected for {file_path.name}, data starts from row 0")
        return None

    def read_excel_file(
        self,
        file_path: Path,
        sheet_name: str = 0,
        header: Optional[int] = None,
        **kwargs
    ) -> pd.DataFrame:
        """
        Read a single Excel file.
        
        Parameters
        ----------
        file_path : Path
            Path to the Excel file
        sheet_name : str or int, default 0
            Sheet name or index to read
        header : int, optional
            Row number to use as column names. If None, auto-detects header row.
        **kwargs
            Additional arguments to pass to pd.read_excel()
            
        Returns
        -------
        pd.DataFrame
            DataFrame containing the Excel data
            
        Raises
        ------
        FileNotFoundError
            If the Excel file does not exist
        ValueError
            If the file is empty or cannot be read
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Excel file not found: {file_path}")

        try:
            logger.info(f"Reading Excel file: {file_path.name}")
            
            # Auto-detect header row if not specified
            if header is None:
                header = self._detect_header_row(file_path, sheet_name, **kwargs)
            
            logger.debug(f"Using header={header} for {file_path.name}")
            
            # Read the Excel file with detected header
            df = pd.read_excel(
                file_path,
                sheet_name=sheet_name,
                header=header,
                **kwargs
            )
            
            # If no header was found (all numeric columns), assign default names
            if all(isinstance(col, (int, float)) for col in df.columns):
                logger.warning(f"No header row found for {file_path.name}, assigning default column names")
                df.columns = [f'col_{i}' for i in range(len(df.columns))]
            
            logger.info(
                f"Successfully read {file_path.name}: "
                f"{len(df)} rows, {len(df.columns)} columns"
            )
            
            return df

        except Exception as e:
            logger.error(f"Failed to read {file_path.name}: {str(e)}")
            raise ValueError(f"Failed to read Excel file {file_path}: {str(e)}") from e

    def extract_all_datasets(self) -> Dict[str, pd.DataFrame]:
        """
        Extract all datasets defined in RAW_DATASETS.
        
        Returns
        -------
        Dict[str, pd.DataFrame]
            Dictionary mapping dataset names to DataFrames
            
        Raises
        ------
        FileNotFoundError
            If any required Excel file is missing
        ValueError
            If any file cannot be read
        """
        datasets = {}
        
        for dataset_name, filename in RAW_DATASETS.items():
            file_path = self.raw_data_dir / filename
            
            try:
                # Read the Excel file - let read_excel_file auto-detect the header
                df = self.read_excel_file(file_path)
                
                # Apply column mapping if available
                try:
                    df = apply_column_mapping(df, dataset_name)
                except Exception as e:
                    logger.warning(f"Could not apply column mapping for {dataset_name}: {str(e)}")
                
                # Drop any rows that are completely empty
                df = df.dropna(how='all')
                
                # Reset index
                df = df.reset_index(drop=True)
                
                # Store with normalized name
                datasets[dataset_name] = df
                
                logger.info(
                    f"Extracted {dataset_name}: "
                    f"{len(df)} rows, {len(df.columns)} columns"
                )

            except FileNotFoundError as e:
                logger.error(f"Missing file for {dataset_name}: {filename}")
                raise
            except Exception as e:
                logger.error(f"Failed to extract {dataset_name}: {str(e)}")
                raise

        logger.info(f"Successfully extracted {len(datasets)} datasets")
        return datasets

    def extract_single_dataset(self, dataset_name: str) -> pd.DataFrame:
        """
        Extract a single dataset by name.
        
        Parameters
        ----------
        dataset_name : str
            Name of the dataset (must be in RAW_DATASETS)
            
        Returns
        -------
        pd.DataFrame
            DataFrame containing the dataset
            
        Raises
        ------
        ValueError
            If dataset_name is not in RAW_DATASETS
        FileNotFoundError
            If the Excel file does not exist
        """
        if dataset_name not in RAW_DATASETS:
            raise ValueError(
                f"Unknown dataset: {dataset_name}. "
                f"Available datasets: {list(RAW_DATASETS.keys())}"
            )

        filename = RAW_DATASETS[dataset_name]
        file_path = self.raw_data_dir / filename
        
        logger.info(f"Extracting single dataset: {dataset_name}")
        df = self.read_excel_file(file_path)
        
        return df

    def get_raw_data_info(self) -> Dict[str, Any]:
        """
        Get information about raw data files.
        
        Returns
        -------
        Dict[str, Any]
            Dictionary containing file information
        """
        info = {
            "raw_data_dir": str(self.raw_data_dir),
            "datasets": {},
            "total_files": 0,
            "missing_files": []
        }

        for dataset_name, filename in RAW_DATASETS.items():
            file_path = self.raw_data_dir / filename
            
            if file_path.exists():
                file_size = file_path.stat().st_size
                info["datasets"][dataset_name] = {
                    "filename": filename,
                    "path": str(file_path),
                    "exists": True,
                    "size_bytes": file_size
                }
                info["total_files"] += 1
            else:
                info["datasets"][dataset_name] = {
                    "filename": filename,
                    "path": str(file_path),
                    "exists": False
                }
                info["missing_files"].append(dataset_name)

        return info

    def validate_raw_files(self) -> bool:
        """
        Validate that all required raw files exist.
        
        Returns
        -------
        bool
            True if all files exist, False otherwise
        """
        info = self.get_raw_data_info()
        missing = info["missing_files"]
        
        if missing:
            logger.error(f"Missing raw data files: {missing}")
            return False
        
        logger.info(f"All {info['total_files']} raw data files validated successfully")
        return True


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def extract_all_datasets() -> Dict[str, pd.DataFrame]:
    """
    Convenience function to extract all datasets.
    
    Returns
    -------
    Dict[str, pd.DataFrame]
        Dictionary mapping dataset names to DataFrames
    """
    extractor = DataExtractor()
    return extractor.extract_all_datasets()


def extract_single_dataset(dataset_name: str) -> pd.DataFrame:
    """
    Convenience function to extract a single dataset.
    
    Parameters
    ----------
    dataset_name : str
        Name of the dataset
        
    Returns
    -------
    pd.DataFrame
        DataFrame containing the dataset
    """
    extractor = DataExtractor()
    return extractor.extract_single_dataset(dataset_name)


# =============================================================================
# SCRIPT TEST
# =============================================================================

if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)
    
    extractor = DataExtractor()
    
    # Validate files
    if extractor.validate_raw_files():
        # Extract all datasets
        datasets = extractor.extract_all_datasets()
        
        # Print summary
        for name, df in datasets.items():
            print(f"{name}: {len(df)} rows, {len(df.columns)} columns")
    else:
        print("Validation failed. Please check raw data files.")