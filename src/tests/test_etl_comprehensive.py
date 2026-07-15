"""Comprehensive ETL tests for the N100 Financial Intelligence Platform.

This module contains extensive tests for:
- DataLoader (loading, verification, stats)
- DataValidator (validation, missing values, duplicates, types)
- DataNormalizer (normalization, company/year normalization)
- Database operations (foreign keys, integrity)
- Edge cases and error handling
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import sqlite3

import pandas as pd
import numpy as np

from src.etl.load import DataLoader
from src.etl.validator import DataValidator, validate_dataset
from src.etl.normalizer import DataNormalizer
from src.database.connection import get_connection, close_connection


class TestDataLoader(unittest.TestCase):
    """Test cases for DataLoader class."""

    def setUp(self):
        """Set up test database."""
        self.loader = DataLoader()
        # Use in-memory database for testing
        self.loader.db_path = ':memory:'
        
    def tearDown(self):
        """Clean up after tests."""
        self.loader.clear_stats()
    
    def test_load_table_success(self):
        """Test successful table load."""
        df = pd.DataFrame({
            'company_id': ['TCS', 'INFY', 'WIPRO'],
            'period': ['2024-Q1', '2024-Q2', '2024-Q3'],
            'sales': [1000.0, 2000.0, 3000.0]
        })
        
        # Create table first
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE test_table (
                company_id TEXT,
                period TEXT,
                sales REAL
            )
        """)
        conn.commit()
        conn.close()
        
        # Load data
        success, rows_loaded = self.loader.load_table('test_table', df)
        
        self.assertTrue(success)
        self.assertEqual(rows_loaded, 3)
    
    def test_load_table_empty_dataframe(self):
        """Test loading empty DataFrame."""
        df = pd.DataFrame()
        
        success, rows_loaded = self.loader.load_table('test_table', df)
        
        self.assertFalse(success)
        self.assertEqual(rows_loaded, 0)
    
    def test_load_table_duplicate_removal(self):
        """Test that duplicates are removed for tables with unique constraints."""
        df = pd.DataFrame({
            'company_id': ['TCS', 'TCS', 'INFY'],
            'date': ['2024-01-01', '2024-01-01', '2024-01-01'],
            'close_price': [100.0, 200.0, 300.0]
        })
        
        # Create table
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE stock_prices (
                company_id TEXT,
                date TEXT,
                close_price REAL
            )
        """)
        conn.commit()
        conn.close()
        
        # Load data
        success, rows_loaded = self.loader.load_table('stock_prices', df)
        
        self.assertTrue(success)
        self.assertEqual(rows_loaded, 2)  # Duplicate removed
    
    def test_verify_table_counts_success(self):
        """Test successful table count verification."""
        # Create and populate table
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE test_table (id INTEGER)")
        cursor.execute("INSERT INTO test_table VALUES (1)")
        cursor.execute("INSERT INTO test_table VALUES (2)")
        cursor.execute("INSERT INTO test_table VALUES (3)")
        conn.commit()
        conn.close()
        
        result = self.loader.verify_table_counts({'test_table': 3})
        
        self.assertTrue(result['verified'])
        self.assertEqual(result['tables']['test_table']['actual'], 3)
    
    def test_verify_table_counts_mismatch(self):
        """Test table count verification with mismatch."""
        # Create and populate table
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE test_table (id INTEGER)")
        cursor.execute("INSERT INTO test_table VALUES (1)")
        cursor.execute("INSERT INTO test_table VALUES (2)")
        conn.commit()
        conn.close()
        
        result = self.loader.verify_table_counts({'test_table': 5})
        
        self.assertFalse(result['verified'])
        self.assertEqual(result['tables']['test_table']['actual'], 2)
    
    def test_get_load_stats(self):
        """Test getting load statistics."""
        stats = self.loader.get_load_stats()
        
        self.assertIn('total_tables', stats)
        self.assertIn('successful_loads', stats)
        self.assertIn('failed_loads', stats)
        self.assertIn('total_rows_loaded', stats)
    
    def test_clear_stats(self):
        """Test clearing load statistics."""
        self.loader.load_stats['total_tables'] = 5
        self.loader.load_stats['successful_loads'] = 3
        
        self.loader.clear_stats()
        
        stats = self.loader.get_load_stats()
        self.assertEqual(stats['total_tables'], 0)
        self.assertEqual(stats['successful_loads'], 0)


class TestDataValidator(unittest.TestCase):
    """Test cases for DataValidator class."""

    def setUp(self):
        """Set up validator."""
        self.validator = DataValidator()
    
    def test_validate_required_columns_success(self):
        """Test validation with all required columns present."""
        df = pd.DataFrame({
            'company_id': ['TCS', 'INFY'],
            'company_name': ['Tata Consultancy', 'Infosys'],
            'sales': [1000.0, 2000.0]
        })
        
        result = self.validator.validate_required_columns(
            df, ['company_id', 'company_name'], 'test_dataset'
        )
        
        self.assertTrue(result['passed'])
        self.assertEqual(len(result['missing_columns']), 0)
    
    def test_validate_required_columns_missing(self):
        """Test validation with missing required columns."""
        df = pd.DataFrame({
            'company_id': ['TCS', 'INFY'],
            'sales': [1000.0, 2000.0]
        })
        
        result = self.validator.validate_required_columns(
            df, ['company_id', 'company_name'], 'test_dataset'
        )
        
        self.assertFalse(result['passed'])
        self.assertIn('company_name', result['missing_columns'])
    
    def test_detect_missing_values_no_missing(self):
        """Test missing value detection with no missing values."""
        df = pd.DataFrame({
            'col1': [1, 2, 3],
            'col2': ['A', 'B', 'C']
        })
        
        result = self.validator.detect_missing_values(df, 'test_dataset')
        
        self.assertTrue(result['passed'])
        self.assertEqual(len(result['columns_with_missing']), 0)
    
    def test_detect_missing_values_with_missing(self):
        """Test missing value detection with missing values."""
        df = pd.DataFrame({
            'col1': [1, None, 3],
            'col2': ['A', 'B', None]
        })
        
        result = self.validator.detect_missing_values(df, 'test_dataset', threshold=50.0)
        
        self.assertFalse(result['passed'])
        self.assertIn('col1', result['columns_with_missing'])
        self.assertIn('col2', result['columns_with_missing'])
    
    def test_detect_missing_values_threshold(self):
        """Test missing value threshold."""
        df = pd.DataFrame({
            'col1': [1, None, None, None, None],  # 80% missing
            'col2': [1, 2, 3, 4, 5]  # 0% missing
        })
        
        result = self.validator.detect_missing_values(df, 'test_dataset', threshold=50.0)
        
        self.assertFalse(result['passed'])
        self.assertIn('col1', result['columns_exceeding_threshold'])
        self.assertNotIn('col2', result['columns_exceeding_threshold'])
    
    def test_detect_duplicates_with_duplicates(self):
        """Test duplicate detection with duplicates present."""
        df = pd.DataFrame({
            'company_id': ['TCS', 'INFY', 'TCS'],
            'period': ['2024-Q1', '2024-Q1', '2024-Q1']
        })
        
        result = self.validator.detect_duplicates(
            df, 'test_dataset', subset=['company_id', 'period']
        )
        
        self.assertFalse(result['passed'])
        self.assertEqual(result['duplicate_count'], 1)
    
    def test_detect_duplicates_no_duplicates(self):
        """Test duplicate detection with no duplicates."""
        df = pd.DataFrame({
            'company_id': ['TCS', 'INFY', 'WIPRO'],
            'period': ['2024-Q1', '2024-Q2', '2024-Q3']
        })
        
        result = self.validator.detect_duplicates(
            df, 'test_dataset', subset=['company_id', 'period']
        )
        
        self.assertTrue(result['passed'])
        self.assertEqual(result['duplicate_count'], 0)
    
    def test_validate_data_types_success(self):
        """Test data type validation with correct types."""
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['A', 'B', 'C'],
            'value': [1.0, 2.0, 3.0]
        })
        
        result = self.validator.validate_data_types(
            df, {'id': 'int', 'name': 'str', 'value': 'float'}, 'test_dataset'
        )
        
        self.assertTrue(result['passed'])
        self.assertEqual(len(result['type_mismatches']), 0)
    
    def test_validate_data_types_mismatch(self):
        """Test data type validation with type mismatch."""
        df = pd.DataFrame({
            'id': ['1', '2', '3'],  # String instead of int
            'value': [1.0, 2.0, 3.0]
        })
        
        result = self.validator.validate_data_types(
            df, {'id': 'int', 'value': 'float'}, 'test_dataset'
        )
        
        self.assertFalse(result['passed'])
        self.assertEqual(len(result['type_mismatches']), 1)
    
    def test_validate_dataset_comprehensive(self):
        """Test comprehensive dataset validation."""
        df = pd.DataFrame({
            'company_id': ['TCS', 'INFY', 'WIPRO'],
            'period': ['2024-Q1', '2024-Q2', '2024-Q3'],
            'sales': [1000.0, 2000.0, 3000.0]
        })
        
        result = self.validator.validate_dataset(
            df=df,
            dataset_name='test_dataset',
            required_columns=['company_id', 'period'],
            expected_types={'sales': 'float'},
            missing_threshold=10.0,
            duplicate_subset=['company_id', 'period']
        )
        
        self.assertTrue(result['overall_passed'])
        self.assertEqual(len(result['checks']), 3)  # columns, missing, duplicates
    
    def test_get_validation_summary(self):
        """Test getting validation summary."""
        df1 = pd.DataFrame({'col1': [1, 2, 3]})
        df2 = pd.DataFrame({'col2': [4, 5, 6]})
        
        self.validator.validate_dataset(df1, 'dataset1', required_columns=['col1'])
        self.validator.validate_dataset(df2, 'dataset2', required_columns=['col2'])
        
        summary = self.validator.get_validation_summary()
        
        self.assertEqual(summary['total_datasets'], 2)
        self.assertEqual(summary['passed'], 2)
        self.assertEqual(summary['failed'], 0)


class TestDataNormalizer(unittest.TestCase):
    """Test cases for DataNormalizer class."""

    def setUp(self):
        """Set up normalizer."""
        self.normalizer = DataNormalizer()
    
    def test_normalize_company_id(self):
        """Test company ID normalization."""
        test_cases = [
            ('TCS', 'TCS'),
            ('tcs', 'TCS'),
            ('  TCS  ', 'TCS'),
            ('TATA CONSULTANCY', 'TATA_CONSULTANCY'),
        ]
        
        for input_id, expected in test_cases:
            result = self.normalizer._normalize_company_id(input_id)
            self.assertEqual(result, expected)
    
    def test_normalize_year(self):
        """Test year normalization."""
        test_cases = [
            ('2024-Q1', '2024-Q1'),
            ('2024-Q4', '2024-Q4'),
            ('FY2024', '2024-FY'),
            ('2023-24', '2023-24'),
        ]
        
        for input_year, expected in test_cases:
            result = self.normalizer._normalize_year(input_year)
            self.assertEqual(result, expected)
    
    def test_normalize_dataframe(self):
        """Test DataFrame normalization."""
        df = pd.DataFrame({
            'company_id': ['TCS', 'INFY', 'WIPRO'],
            'period': ['2024-Q1', '2024-Q2', '2024-Q3'],
            'sales': [1000.0, 2000.0, 3000.0]
        })
        
        result = self.normalizer.normalize_dataframe(
            df=df,
            company_id_col='company_id',
            date_cols=[],
            numeric_cols=['sales']
        )
        
        self.assertEqual(len(result), 3)
        self.assertIn('company_id', result.columns)
        self.assertIn('period', result.columns)
    
    def test_remove_duplicates(self):
        """Test duplicate removal."""
        df = pd.DataFrame({
            'company_id': ['TCS', 'INFY', 'TCS'],
            'period': ['2024-Q1', '2024-Q2', '2024-Q1'],
            'sales': [1000.0, 2000.0, 1000.0]
        })
        
        result = self.normalizer.remove_duplicates(
            df, subset=['company_id', 'period']
        )
        
        self.assertEqual(len(result), 2)
    
    def test_get_normalization_log(self):
        """Test getting normalization log."""
        log = self.normalizer.get_normalization_log()
        
        self.assertIsInstance(log, list)


class TestDatabaseOperations(unittest.TestCase):
    """Test cases for database operations."""

    def setUp(self):
        """Set up test database."""
        self.test_db = ':memory:'
        self.conn = sqlite3.connect(self.test_db)
        self.cursor = self.conn.cursor()
    
    def tearDown(self):
        """Clean up test database."""
        self.conn.close()
    
    def test_foreign_key_check_empty(self):
        """Test foreign key check with no violations."""
        # Create tables
        self.cursor.execute("""
            CREATE TABLE companies (
                company_id TEXT PRIMARY KEY,
                company_name TEXT
            )
        """)
        self.cursor.execute("""
            CREATE TABLE profit_loss (
                id INTEGER PRIMARY KEY,
                company_id TEXT,
                period TEXT,
                FOREIGN KEY (company_id) REFERENCES companies(company_id)
            )
        """)
        
        # Insert valid data
        self.cursor.execute("INSERT INTO companies VALUES ('TCS', 'Tata Consultancy')")
        self.cursor.execute("INSERT INTO profit_loss VALUES (1, 'TCS', '2024-Q1')")
        self.conn.commit()
        
        # Check foreign keys
        self.cursor.execute("PRAGMA foreign_key_check")
        violations = self.cursor.fetchall()
        
        self.assertEqual(len(violations), 0)
    
    def test_foreign_key_check_violations(self):
        """Test foreign key check with violations."""
        # Create tables
        self.cursor.execute("""
            CREATE TABLE companies (
                company_id TEXT PRIMARY KEY,
                company_name TEXT
            )
        """)
        self.cursor.execute("""
            CREATE TABLE profit_loss (
                id INTEGER PRIMARY KEY,
                company_id TEXT,
                period TEXT,
                FOREIGN KEY (company_id) REFERENCES companies(company_id)
            )
        """)
        
        # Insert invalid data (company_id doesn't exist)
        self.cursor.execute("INSERT INTO profit_loss VALUES (1, 'NONEXISTENT', '2024-Q1')")
        self.conn.commit()
        
        # Check foreign keys
        self.cursor.execute("PRAGMA foreign_key_check")
        violations = self.cursor.fetchall()
        
        self.assertGreater(len(violations), 0)
    
    def test_orphaned_records_check(self):
        """Test detection of orphaned records."""
        # Create tables
        self.cursor.execute("""
            CREATE TABLE companies (
                company_id TEXT PRIMARY KEY
            )
        """)
        self.cursor.execute("""
            CREATE TABLE profit_loss (
                id INTEGER PRIMARY KEY,
                company_id TEXT
            )
        """)
        
        # Insert data with orphaned record
        self.cursor.execute("INSERT INTO companies VALUES ('TCS')")
        self.cursor.execute("INSERT INTO profit_loss VALUES (1, 'TCS')")
        self.cursor.execute("INSERT INTO profit_loss VALUES (2, 'INFY')")  # Orphaned
        self.conn.commit()
        
        # Check for orphaned records
        self.cursor.execute("""
            SELECT COUNT(*) FROM profit_loss 
            WHERE company_id NOT IN (SELECT company_id FROM companies)
        """)
        orphaned_count = self.cursor.fetchone()[0]
        
        self.assertEqual(orphaned_count, 1)
    
    def test_duplicate_records_check(self):
        """Test detection of duplicate records."""
        # Create table
        self.cursor.execute("""
            CREATE TABLE profit_loss (
                id INTEGER PRIMARY KEY,
                company_id TEXT,
                period TEXT
            )
        """)
        
        # Insert duplicate records
        self.cursor.execute("INSERT INTO profit_loss VALUES (1, 'TCS', '2024-Q1')")
        self.cursor.execute("INSERT INTO profit_loss VALUES (2, 'TCS', '2024-Q1')")  # Duplicate
        self.cursor.execute("INSERT INTO profit_loss VALUES (3, 'INFY', '2024-Q1')")
        self.conn.commit()
        
        # Check for duplicates
        self.cursor.execute("""
            SELECT company_id, period, COUNT(*) as cnt 
            FROM profit_loss 
            GROUP BY company_id, period 
            HAVING COUNT(*) > 1
        """)
        duplicates = self.cursor.fetchall()
        
        self.assertEqual(len(duplicates), 1)
        self.assertEqual(duplicates[0][0], 'TCS')
        self.assertEqual(duplicates[0][1], '2024-Q1')
        self.assertEqual(duplicates[0][2], 2)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""

    def test_empty_dataframe_validation(self):
        """Test validation of empty DataFrame."""
        validator = DataValidator()
        df = pd.DataFrame()
        
        result = validator.validate_dataset(
            df, 'empty_dataset', required_columns=['col1']
        )
        
        self.assertFalse(result['overall_passed'])
    
    def test_none_values_handling(self):
        """Test handling of None values in DataFrame."""
        df = pd.DataFrame({
            'company_id': ['TCS', None, 'WIPRO'],
            'sales': [1000.0, None, 3000.0]
        })
        
        validator = DataValidator()
        result = validator.detect_missing_values(df, 'test_dataset')
        
        self.assertIn('company_id', result['columns_with_missing'])
        self.assertIn('sales', result['columns_with_missing'])
    
    def test_special_characters_in_company_id(self):
        """Test handling of special characters in company IDs."""
        normalizer = DataNormalizer()
        
        test_ids = [
            'TCS-123',
            'INFY & CO',
            'WIPRO@2024',
            'HDFC$BANK'
        ]
        
        for company_id in test_ids:
            normalized = normalizer._normalize_company_id(company_id)
            # Should not raise exception
            self.assertIsInstance(normalized, str)
    
    def test_large_dataset_loading(self):
        """Test loading large dataset."""
        loader = DataLoader()
        
        # Create large DataFrame
        df = pd.DataFrame({
            'company_id': [f'COMP_{i}' for i in range(1000)],
            'period': ['2024-Q1'] * 1000,
            'sales': np.random.rand(1000) * 1000000
        })
        
        # Create table
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE large_test (
                company_id TEXT,
                period TEXT,
                sales REAL
            )
        """)
        conn.commit()
        conn.close()
        
        # Load data
        success, rows_loaded = loader.load_table('large_test', df)
        
        self.assertTrue(success)
        self.assertEqual(rows_loaded, 1000)
    
    def test_null_threshold_by_dataset(self):
        """Test dataset-specific null thresholds."""
        validator = DataValidator()
        
        # Test companies dataset (5% threshold)
        df_companies = pd.DataFrame({
            'company_id': ['TCS', 'INFY', None, 'WIPRO', 'HDFC'],
            'company_name': ['A', 'B', 'C', 'D', 'E']
        })
        result = validator.validate_dataset(df_companies, 'companies', required_columns=['company_id'])
        # Should fail with 20% missing (threshold is 5%)
        self.assertFalse(result['overall_passed'])
        
        # Test pros_cons dataset (80% threshold)
        df_pros_cons = pd.DataFrame({
            'company_id': ['TCS', 'INFY', 'WIPRO'],
            'pros': ['A', None, 'C']
        })
        result = validator.validate_dataset(df_pros_cons, 'pros_cons', required_columns=['company_id'])
        # Should pass with 33% missing (threshold is 80%)
        self.assertTrue(result['overall_passed'])


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions."""

    def test_validate_dataset_function(self):
        """Test validate_dataset convenience function."""
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['A', 'B', 'C']
        })
        
        result = validate_dataset(
            df, 'test_dataset', required_columns=['id', 'name']
        )
        
        self.assertTrue(result['overall_passed'])


# =============================================================================
# TEST RUNNER
# =============================================================================

if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)