"""
load.py

Data loading module for the N100 Financial Intelligence Platform.
Loads transformed data into SQLite database with proper error handling.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from src.config.logging_config import get_logger
from src.database.connection import get_connection, commit, rollback, close_connection
from src.database.schema import get_table_schema, get_all_schemas, get_indexes, TABLE_SCHEMAS

logger = get_logger(__name__)


class DataLoader:
    """
    Loads data into SQLite database.
    
    Responsibilities:
    1. Create database tables
    2. Load DataFrames into tables
    3. Handle errors and rollbacks
    4. Track load statistics
    5. Verify loaded data
    """

    def __init__(self):
        """Initialize the DataLoader."""
        self.load_stats = {
            "total_tables": 0,
            "successful_loads": 0,
            "failed_loads": [],
            "total_rows_loaded": 0,
            "tables": {}
        }

    def _sanitize_dataframe_columns(self, df: pd.DataFrame, table_name: str) -> pd.DataFrame:
        """
        Sanitize DataFrame column names to match the table schema.
        
        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to sanitize
        table_name : str
            Name of the table
            
        Returns
        -------
        pd.DataFrame
            DataFrame with sanitized column names
        """
        # Sanitize column names (replace spaces and special chars with underscores)
        sanitized_columns = []
        for col in df.columns:
            col_str = str(col)
            # Replace spaces, dots, dashes with underscores
            sanitized = col_str.replace(' ', '_').replace('.', '_').replace('-', '_')
            # Remove any other special characters
            sanitized = ''.join(c if c.isalnum() or c == '_' else '_' for c in sanitized)
            # Ensure it doesn't start with a number
            if sanitized and sanitized[0].isdigit():
                sanitized = f'col_{sanitized}'
            # Ensure it's not empty
            if not sanitized:
                sanitized = f'col_{len(sanitized_columns)}'
            sanitized_columns.append(sanitized)
        
        # Rename DataFrame columns to match sanitized names
        df = df.copy()
        df.columns = sanitized_columns
        
        return df

    def _create_table_from_dataframe(self, table_name: str, df: pd.DataFrame) -> str:
        """
        Generate CREATE TABLE SQL based on DataFrame columns and dtypes.
        
        Parameters
        ----------
        table_name : str
            Name of the table
        df : pd.DataFrame
            DataFrame to create table from
            
        Returns
        -------
        str
            CREATE TABLE SQL statement
        """
        # Map pandas dtypes to SQLite types
        type_mapping = {
            'int64': 'INTEGER',
            'int32': 'INTEGER',
            'float64': 'REAL',
            'float32': 'REAL',
            'object': 'TEXT',
            'bool': 'INTEGER',
            'datetime64[ns]': 'TEXT',
            'timedelta64[ns]': 'TEXT'
        }
        
        # Sanitize column names (replace spaces and special chars with underscores)
        sanitized_columns = []
        for col in df.columns:
            col_str = str(col)
            # Replace spaces, dots, dashes with underscores
            sanitized = col_str.replace(' ', '_').replace('.', '_').replace('-', '_')
            # Remove any other special characters
            sanitized = ''.join(c if c.isalnum() or c == '_' else '_' for c in sanitized)
            # Ensure it doesn't start with a number
            if sanitized and sanitized[0].isdigit():
                sanitized = f'col_{sanitized}'
            # Ensure it's not empty
            if not sanitized:
                sanitized = f'col_{len(sanitized_columns)}'
            sanitized_columns.append(sanitized)
        
        # Build column definitions
        columns = []
        for col, dtype in zip(sanitized_columns, df.dtypes):
            sql_type = type_mapping.get(str(dtype), 'TEXT')
            columns.append(f"    {col} {sql_type}")
        
        # Create table SQL (DROP IF EXISTS to ensure fresh schema)
        create_sql = f"""DROP TABLE IF EXISTS {table_name};
CREATE TABLE {table_name} (
{','.join(columns)}
);"""
        
        return create_sql

    def create_tables(self, datasets: Optional[Dict[str, pd.DataFrame]] = None) -> bool:
        """
        Create all database tables.
        
        Parameters
        ----------
        datasets : Dict[str, pd.DataFrame], optional
            Dictionary of datasets to create tables from. If provided, creates tables
            based on actual DataFrame columns. If None, uses predefined schemas.
            
        Returns
        -------
        bool
            True if all tables created successfully
        """
        logger.info("Creating database tables")
        
        try:
            conn = get_connection()
            cursor = conn.cursor()

            if datasets:
                # Create tables based on actual DataFrame columns (Problem 3 & 4 fix)
                for table_name, df in datasets.items():
                    if df.empty:
                        logger.warning(f"Skipping empty dataset: {table_name}")
                        continue
                    
                    # Drop table if exists
                    try:
                        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
                    except Exception as e:
                        logger.warning(f"Could not drop table {table_name}: {str(e)}")
                    
                    # Create table from DataFrame
                    create_sql = self._create_table_from_dataframe(table_name, df)
                    try:
                        # Execute each statement separately (SQLite doesn't support multi-statement)
                        for statement in create_sql.split(';'):
                            statement = statement.strip()
                            if statement:
                                cursor.execute(statement)
                        logger.debug(f"Created table {table_name} with {len(df.columns)} columns")
                    except Exception as e:
                        logger.error(f"Failed to create table {table_name}: {str(e)}")
                        raise
            else:
                # Use predefined schemas
                schemas = get_all_schemas()
                for schema in schemas:
                    try:
                        cursor.execute(schema)
                        logger.debug(f"Created table: {schema.split('(')[0].split()[-1]}")
                    except Exception as e:
                        logger.error(f"Failed to create table: {str(e)}")
                        raise

            # Create indexes (only for columns that exist)
            all_indexes = []
            for table_name in TABLE_SCHEMAS.keys():
                # Get actual columns from the table
                try:
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = [row[1] for row in cursor.fetchall()]
                    
                    # Get safe indexes that only reference existing columns
                    indexes = get_safe_indexes(table_name, columns)
                    all_indexes.extend(indexes)
                except Exception as e:
                    logger.warning(f"Could not get columns for {table_name}: {str(e)}")

            for index_sql in all_indexes:
                try:
                    cursor.execute(index_sql)
                    logger.debug(f"Created index: {index_sql.split()[-1]}")
                except Exception as e:
                    logger.warning(f"Failed to create index: {str(e)}")

            commit()
            logger.info(f"Successfully created tables and {len(all_indexes)} indexes")
            return True

        except Exception as e:
            logger.error(f"Failed to create tables: {str(e)}")
            rollback()
            return False

    def load_table(
        self,
        table_name: str,
        df: pd.DataFrame,
        if_exists: str = "append",
        method: str = "multi",
        chunksize: int = 500
    ) -> Tuple[bool, int]:
        """
        Load DataFrame into a database table.
        
        Parameters
        ----------
        table_name : str
            Name of the table to load into
        df : pd.DataFrame
            DataFrame to load
        if_exists : str, default "append"
            What to do if table exists ('fail', 'replace', 'append')
        method : str, default "multi"
            SQL insertion method ('multi' for batch insert)
        chunksize : int, default 500
            Number of rows to insert per batch (prevents "too many SQL variables" error)
            
        Returns
        -------
        Tuple[bool, int]
            (success, rows_loaded)
        """
        logger.info(f"Loading {len(df)} rows into table: {table_name}")

        try:
            # Sanitize DataFrame columns to match table schema
            df = self._sanitize_dataframe_columns(df, table_name)
            
            conn = get_connection()

            # Load data using pandas to_sql with chunking to avoid "too many SQL variables"
            df.to_sql(
                name=table_name,
                con=conn,
                if_exists=if_exists,
                index=False,
                method=method,
                chunksize=chunksize
            )

            commit()

            rows_loaded = len(df)
            logger.info(f"Successfully loaded {rows_loaded} rows into {table_name}")

            # Update stats
            self.load_stats["successful_loads"] += 1
            self.load_stats["total_rows_loaded"] += rows_loaded
            self.load_stats["tables"][table_name] = {
                "rows_loaded": rows_loaded,
                "success": True
            }

            return True, rows_loaded

        except Exception as e:
            logger.error(f"Failed to load {table_name}: {str(e)}")
            rollback()
            
            self.load_stats["failed_loads"].append(table_name)
            self.load_stats["tables"][table_name] = {
                "rows_loaded": 0,
                "success": False,
                "error": str(e)
            }
            
            return False, 0

    def load_all_datasets(
        self,
        datasets: Dict[str, pd.DataFrame],
        table_mapping: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Load all datasets into database.
        
        Parameters
        ----------
        datasets : Dict[str, pd.DataFrame]
            Dictionary mapping dataset names to DataFrames
        table_mapping : Dict[str, str], optional
            Mapping of dataset names to table names
            
        Returns
        -------
        Dict[str, Any]
            Load statistics
        """
        logger.info(f"Starting to load {len(datasets)} datasets")

        # Use default table mapping if not provided
        if table_mapping is None:
            table_mapping = {name: name for name in datasets.keys()}

        self.load_stats["total_tables"] = len(datasets)

        for dataset_name, df in datasets.items():
            table_name = table_mapping.get(dataset_name, dataset_name)

            # Skip if DataFrame is empty
            if df.empty:
                logger.warning(f"Skipping empty dataset: {dataset_name}")
                self.load_stats["tables"][table_name] = {
                    "rows_loaded": 0,
                    "success": False,
                    "error": "Empty DataFrame"
                }
                self.load_stats["failed_loads"].append(table_name)
                continue

            # Load the table
            success, rows_loaded = self.load_table(table_name, df)

            if not success:
                logger.error(f"Failed to load {dataset_name} into {table_name}")

        logger.info(
            f"Load complete: {self.load_stats['successful_loads']}/{self.load_stats['total_tables']} "
            f"tables loaded successfully"
        )

        return self.load_stats

    def verify_table_counts(
        self,
        expected_counts: Dict[str, int]
    ) -> Dict[str, Any]:
        """
        Verify row counts in database tables.
        
        Parameters
        ----------
        expected_counts : Dict[str, int]
            Dictionary mapping table names to expected row counts
            
        Returns
        -------
        Dict[str, Any]
            Verification results
        """
        logger.info("Verifying table row counts")

        results = {
            "verified": True,
            "tables": {}
        }

        try:
            conn = get_connection()
            cursor = conn.cursor()

            for table_name, expected_count in expected_counts.items():
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    actual_count = cursor.fetchone()[0]

                    match = actual_count == expected_count
                    results["tables"][table_name] = {
                        "expected": expected_count,
                        "actual": actual_count,
                        "match": match
                    }

                    if not match:
                        results["verified"] = False
                        logger.warning(
                            f"Row count mismatch for {table_name}: "
                            f"expected {expected_count}, got {actual_count}"
                        )
                    else:
                        logger.info(f"Row count verified for {table_name}: {actual_count}")

                except Exception as e:
                    logger.error(f"Failed to verify {table_name}: {str(e)}")
                    results["verified"] = False
                    results["tables"][table_name] = {
                        "expected": expected_count,
                        "actual": 0,
                        "match": False,
                        "error": str(e)
                    }

        except Exception as e:
            logger.error(f"Failed to verify table counts: {str(e)}")
            results["verified"] = False

        return results

    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """
        Get information about a database table.
        
        Parameters
        ----------
        table_name : str
            Name of the table
            
        Returns
        -------
        Dict[str, Any]
            Table information
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]

            # Get column info
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()

            info = {
                "table_name": table_name,
                "row_count": row_count,
                "columns": [
                    {
                        "name": col[1],
                        "type": col[2],
                        "not_null": bool(col[3]),
                        "primary_key": bool(col[5])
                    }
                    for col in columns
                ]
            }

            return info

        except Exception as e:
            logger.error(f"Failed to get table info for {table_name}: {str(e)}")
            return {"table_name": table_name, "error": str(e)}

    def get_load_stats(self) -> Dict[str, Any]:
        """
        Get load statistics.
        
        Returns
        -------
        Dict[str, Any]
            Load statistics
        """
        return self.load_stats

    def clear_stats(self):
        """Clear load statistics."""
        self.load_stats = {
            "total_tables": 0,
            "successful_loads": 0,
            "failed_loads": [],
            "total_rows_loaded": 0,
            "tables": {}
        }
        logger.info("Load statistics cleared")


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def load_table(table_name: str, df: pd.DataFrame, **kwargs) -> Tuple[bool, int]:
    """
    Convenience function to load a DataFrame into a table.
    
    Parameters
    ----------
    table_name : str
        Name of the table
    df : pd.DataFrame
        DataFrame to load
    **kwargs
        Additional arguments for DataLoader.load_table()
        
    Returns
    -------
    Tuple[bool, int]
        (success, rows_loaded)
    """
    loader = DataLoader()
    return loader.load_table(table_name, df, **kwargs)


def load_all_datasets(
    datasets: Dict[str, pd.DataFrame],
    **kwargs
) -> Dict[str, Any]:
    """
    Convenience function to load all datasets.
    
    Parameters
    ----------
    datasets : Dict[str, pd.DataFrame]
        Dictionary mapping dataset names to DataFrames
    **kwargs
        Additional arguments for DataLoader.load_all_datasets()
        
    Returns
    -------
    Dict[str, Any]
        Load statistics
    """
    loader = DataLoader()
    return loader.load_all_datasets(datasets, **kwargs)


# =============================================================================
# SCRIPT TEST
# =============================================================================

if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)

    # Create sample DataFrame
    df = pd.DataFrame({
        "company_id": ["TCS", "INFY", "WIPRO"],
        "period": ["2024-Q1", "2024-Q2", "2024-Q3"],
        "revenue": [1000.0, 2000.0, 3000.0]
    })

    loader = DataLoader()

    # Create tables
    if loader.create_tables():
        # Load data
        stats = loader.load_all_datasets({"test_table": df})
        print("Load Stats:", stats)

        # Verify
        verification = loader.verify_table_counts({"test_table": 3})
        print("Verification:", verification)

    # Close connection
    close_connection()