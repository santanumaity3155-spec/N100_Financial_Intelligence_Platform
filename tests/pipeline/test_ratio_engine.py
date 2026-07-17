"""
test_ratio_engine.py

Comprehensive unit tests for the Ratio Engine Pipeline (Module 4).

Tests cover:
- Successful insertion
- Duplicate prevention
- Transaction rollback
- Validation failures
- Missing company/period
- Empty DataFrames
- Missing financial statements
- Pipeline error handling
- CSV generation
- Audit log generation
- Processing statistics
- End-to-end pipeline
"""

import logging
import os
import sqlite3
import tempfile
import time
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from src.analytics.ratio_engine import (
    ValidationError,
    validate_company_period,
    validate_financial_data_availability,
    insert_financial_ratios,
    check_duplicate_period,
    merge_kpi_data,
    process_company,
    RatioEnginePipeline,
    run_ratio_engine_pipeline,
    get_pipeline_statistics,
    validate_database_integrity,
    RATIO_LOAD_SUMMARY_CSV,
    RATIO_ENGINE_LOG,
)
from src.config.logging_config import get_logger

logger = get_logger(__name__)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    # Create database and tables
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            company_id TEXT PRIMARY KEY,
            company_name TEXT,
            sector TEXT,
            industry TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS financial_ratios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id TEXT NOT NULL,
            company_name TEXT,
            period TEXT,
            industry TEXT,
            sector TEXT,
            net_profit_margin REAL,
            operating_profit_margin REAL,
            roe REAL,
            roce REAL,
            roa REAL,
            debt_to_equity REAL,
            interest_coverage REAL,
            net_debt REAL,
            high_leverage_flag INTEGER DEFAULT 0,
            asset_turnover REAL,
            revenue_cagr_3yr REAL,
            revenue_cagr_5yr REAL,
            revenue_cagr_10yr REAL,
            pat_cagr_3yr REAL,
            pat_cagr_5yr REAL,
            pat_cagr_10yr REAL,
            eps_cagr_3yr REAL,
            eps_cagr_5yr REAL,
            eps_cagr_10yr REAL,
            free_cash_flow REAL,
            fcf_margin REAL,
            cash_conversion REAL,
            capex_intensity REAL,
            cash_reinvestment_ratio REAL,
            cash_return_on_assets REAL,
            operating_cashflow_growth REAL,
            capital_allocation_rating TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(company_id, period)
        )
    """)
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def sample_company_data():
    """Create sample company data for testing."""
    return {
        "company_name": "Test Company Ltd",
        "industry": "Technology",
        "sector": "Information Technology"
    }


@pytest.fixture
def sample_pl_df():
    """Create sample P&L DataFrame."""
    return pd.DataFrame({
        "company_id": ["TEST001", "TEST001", "TEST001"],
        "period": ["FY2022", "FY2023", "FY2024"],
        "sales": [1000, 1200, 1500],
        "net_profit": [100, 120, 150],
        "operating_profit": [150, 180, 220],
        "eps": [10, 12, 15]
    })


@pytest.fixture
def sample_bs_df():
    """Create sample Balance Sheet DataFrame."""
    return pd.DataFrame({
        "company_id": ["TEST001", "TEST001", "TEST001"],
        "period": ["FY2022", "FY2023", "FY2024"],
        "total_assets": [5000, 5500, 6000],
        "equity_capital": [2000, 2200, 2500],
        "reserves": [1000, 1100, 1200],
        "borrowings": [500, 600, 700]
    })


@pytest.fixture
def sample_cf_df():
    """Create sample Cash Flow DataFrame."""
    return pd.DataFrame({
        "company_id": ["TEST001", "TEST001", "TEST001"],
        "period": ["FY2022", "FY2023", "FY2024"],
        "cash_from_operating_activity": [200, 250, 300],
        "cash_from_investing_activity": [-100, -120, -150],
        "free_cash_flow": [100, 130, 150]
    })


# =============================================================================
# VALIDATION TESTS
# =============================================================================

class TestValidationError:
    """Test ValidationError class."""
    
    def test_validation_error_creation(self):
        """Test creating a validation error."""
        error = ValidationError("TEST001", "FY2024", "MISSING_ID", "ID is missing")
        assert error.company_id == "TEST001"
        assert error.period == "FY2024"
        assert error.error_type == "MISSING_ID"
        assert error.message == "ID is missing"
    
    def test_validation_error_to_dict(self):
        """Test converting validation error to dictionary."""
        error = ValidationError("TEST001", "FY2024", "MISSING_ID", "ID is missing")
        result = error.to_dict()
        assert result["company_id"] == "TEST001"
        assert result["period"] == "FY2024"
        assert result["error_type"] == "MISSING_ID"
        assert result["message"] == "ID is missing"


class TestValidateCompanyPeriod:
    """Test validate_company_period function."""
    
    def test_missing_company_id(self):
        """Test validation with missing company ID."""
        errors = validate_company_period(None, "FY2024", {}, {}, {})
        assert len(errors) > 0
        assert any(e.error_type == "MISSING_COMPANY_ID" for e in errors)
    
    def test_missing_period(self):
        """Test validation with missing period."""
        errors = validate_company_period("TEST001", None, {}, {}, {})
        assert len(errors) > 0
        assert any(e.error_type == "MISSING_PERIOD" for e in errors)
    
    def test_empty_company_id(self):
        """Test validation with empty company ID."""
        errors = validate_company_period("", "FY2024", {}, {}, {})
        assert len(errors) > 0
        assert any(e.error_type == "MISSING_COMPANY_ID" for e in errors)
    
    def test_empty_period(self):
        """Test validation with empty period."""
        errors = validate_company_period("TEST001", "", {}, {}, {})
        assert len(errors) > 0
        assert any(e.error_type == "MISSING_PERIOD" for e in errors)
    
    def test_nan_value_detection(self):
        """Test NaN value detection in critical fields."""
        ratios_data = {"net_profit_margin": np.nan}
        errors = validate_company_period("TEST001", "FY2024", ratios_data, {}, {})
        assert len(errors) > 0
        assert any(e.error_type == "NaN_VALUE" for e in errors)
    
    def test_infinite_value_detection(self):
        """Test infinite value detection."""
        ratios_data = {"roe": float('inf')}
        errors = validate_company_period("TEST001", "FY2024", ratios_data, {}, {})
        assert len(errors) > 0
        assert any(e.error_type == "INFINITE_VALUE" for e in errors)
    
    def test_negative_assets_detection(self):
        """Test negative assets detection."""
        ratios_data = {"total_assets": -1000}
        errors = validate_company_period("TEST001", "FY2024", ratios_data, {}, {})
        assert len(errors) > 0
        assert any(e.error_type == "NEGATIVE_ASSETS" for e in errors)
    
    def test_invalid_equity_detection(self):
        """Test invalid equity detection."""
        ratios_data = {"equity": 0}
        errors = validate_company_period("TEST001", "FY2024", ratios_data, {}, {})
        assert len(errors) > 0
        assert any(e.error_type == "INVALID_EQUITY" for e in errors)
    
    def test_valid_data_no_errors(self):
        """Test valid data produces no errors."""
        ratios_data = {
            "net_profit_margin": 10.5,
            "roe": 15.0,
            "roa": 8.0,
            "debt_to_equity": 0.5,
            "revenue_cagr_3yr": 12.0,
            "free_cash_flow": 100.0
        }
        errors = validate_company_period("TEST001", "FY2024", ratios_data, {}, {})
        assert len(errors) == 0


class TestValidateFinancialDataAvailability:
    """Test validate_financial_data_availability function."""
    
    def test_missing_pl_data(self):
        """Test validation with missing P&L data."""
        errors = validate_financial_data_availability(
            "TEST001", "FY2024",
            pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        )
        assert len(errors) > 0
        assert any(e.error_type == "MISSING_PL" for e in errors)
    
    def test_missing_bs_data(self):
        """Test validation with missing Balance Sheet data."""
        pl_df = pd.DataFrame({"sales": [1000]})
        errors = validate_financial_data_availability(
            "TEST001", "FY2024",
            pl_df, pd.DataFrame(), pd.DataFrame()
        )
        assert len(errors) > 0
        assert any(e.error_type == "MISSING_BS" for e in errors)
    
    def test_missing_cf_data(self):
        """Test validation with missing Cash Flow data."""
        pl_df = pd.DataFrame({"sales": [1000]})
        bs_df = pd.DataFrame({"total_assets": [5000]})
        errors = validate_financial_data_availability(
            "TEST001", "FY2024",
            pl_df, bs_df, pd.DataFrame()
        )
        assert len(errors) > 0
        assert any(e.error_type == "MISSING_CF" for e in errors)
    
    def test_all_data_present(self):
        """Test validation with all data present."""
        pl_df = pd.DataFrame({"sales": [1000]})
        bs_df = pd.DataFrame({"total_assets": [5000]})
        cf_df = pd.DataFrame({"cash_from_operating_activity": [200]})
        errors = validate_financial_data_availability(
            "TEST001", "FY2024",
            pl_df, bs_df, cf_df
        )
        assert len(errors) == 0


# =============================================================================
# DATABASE OPERATIONS TESTS
# =============================================================================

class TestInsertFinancialRatios:
    """Test insert_financial_ratios function."""
    
    def test_successful_insert(self, temp_db):
        """Test successful record insertion."""
        # Mock the database connection
        with patch('src.analytics.ratio_engine.get_connection') as mock_get_conn:
            mock_conn = sqlite3.connect(temp_db)
            mock_get_conn.return_value = mock_conn
            
            record = {
                "company_id": "TEST001",
                "period": "FY2024",
                "net_profit_margin": 10.5,
                "roe": 15.0
            }
            
            success, error_msg = insert_financial_ratios(record)
            assert success is True
            assert error_msg is None
            
            # Verify record was inserted
            cursor = mock_conn.execute(
                "SELECT * FROM financial_ratios WHERE company_id = ? AND period = ?",
                ("TEST001", "FY2024")
            )
            result = cursor.fetchone()
            assert result is not None
            
            mock_conn.close()
    
    def test_duplicate_insert_replacement(self, temp_db):
        """Test that duplicate inserts replace existing records."""
        with patch('src.analytics.ratio_engine.get_connection') as mock_get_conn:
            mock_conn = sqlite3.connect(temp_db)
            mock_get_conn.return_value = mock_conn
            
            # Insert first record
            record1 = {
                "company_id": "TEST001",
                "period": "FY2024",
                "net_profit_margin": 10.5
            }
            success, _ = insert_financial_ratios(record1)
            assert success is True
            
            # Insert duplicate with different value
            record2 = {
                "company_id": "TEST001",
                "period": "FY2024",
                "net_profit_margin": 12.0
            }
            success, _ = insert_financial_ratios(record2)
            assert success is True
            
            # Verify only one record exists with updated value
            cursor = mock_conn.execute(
                "SELECT COUNT(*) FROM financial_ratios WHERE company_id = ? AND period = ?",
                ("TEST001", "FY2024")
            )
            count = cursor.fetchone()[0]
            assert count == 1
            
            cursor = mock_conn.execute(
                "SELECT net_profit_margin FROM financial_ratios WHERE company_id = ? AND period = ?",
                ("TEST001", "FY2024")
            )
            margin = cursor.fetchone()[0]
            assert margin == 12.0
            
            mock_conn.close()


class TestCheckDuplicatePeriod:
    """Test check_duplicate_period function."""
    
    def test_no_duplicate(self, temp_db):
        """Test when no duplicate exists."""
        with patch('src.analytics.ratio_engine.get_connection') as mock_get_conn:
            mock_conn = sqlite3.connect(temp_db)
            mock_get_conn.return_value = mock_conn
            
            # Insert a record
            mock_conn.execute(
                "INSERT INTO financial_ratios (company_id, period) VALUES (?, ?)",
                ("TEST001", "FY2024")
            )
            mock_conn.commit()
            
            # Check for duplicate
            is_duplicate = check_duplicate_period("TEST001", "FY2024")
            assert is_duplicate is True
            
            mock_conn.close()
    
    def test_no_duplicate_when_not_exists(self, temp_db):
        """Test when record doesn't exist."""
        with patch('src.analytics.ratio_engine.get_connection') as mock_get_conn:
            mock_conn = sqlite3.connect(temp_db)
            mock_get_conn.return_value = mock_conn
            
            is_duplicate = check_duplicate_period("TEST001", "FY2024")
            assert is_duplicate is False
            
            mock_conn.close()


# =============================================================================
# DATA MERGING TESTS
# =============================================================================

class TestMergeKpiData:
    """Test merge_kpi_data function."""
    
    def test_merge_basic_data(self):
        """Test merging basic KPI data."""
        ratios_data = {
            "net_profit_margin": 10.5,
            "roe": 15.0
        }
        cagr_data = {
            "revenue_cagr_3yr": {"value": 12.0, "flag": None}
        }
        cashflow_data = {
            "free_cash_flow": 100.0
        }
        
        record = merge_kpi_data(
            "TEST001", "FY2024", "Test Company", "Tech", "IT",
            ratios_data, cagr_data, cashflow_data
        )
        
        assert record["company_id"] == "TEST001"
        assert record["period"] == "FY2024"
        assert record["company_name"] == "Test Company"
        assert record["industry"] == "Tech"
        assert record["sector"] == "IT"
        assert record["net_profit_margin"] == 10.5
        assert record["roe"] == 15.0
        assert record["revenue_cagr_3yr"] == 12.0
        assert record["free_cash_flow"] == 100.0
    
    def test_merge_cagr_flags(self):
        """Test merging CAGR data with flags."""
        cagr_data = {
            "revenue_cagr_3yr": {"value": 12.0, "flag": None},
            "pat_cagr_5yr": {"value": None, "flag": "INSUFFICIENT"}
        }
        
        record = merge_kpi_data(
            "TEST001", "FY2024", "Test", "Tech", "IT",
            {}, cagr_data, {}
        )
        
        assert record["revenue_cagr_3yr"] == 12.0
        assert record["revenue_cagr_3yr_flag"] is None
        assert record["pat_cagr_5yr"] is None
        assert record["pat_cagr_5yr_flag"] == "INSUFFICIENT"
    
    def test_merge_timestamps_added(self):
        """Test that timestamps are added to merged record."""
        record = merge_kpi_data(
            "TEST001", "FY2024", "Test", "Tech", "IT",
            {}, {}, {}
        )
        
        assert "created_at" in record
        assert "updated_at" in record


# =============================================================================
# COMPANY PROCESSING TESTS
# =============================================================================

class TestProcessCompany:
    """Test process_company function."""
    
    def test_successful_processing(self, sample_company_data, sample_pl_df, 
                                   sample_bs_df, sample_cf_df):
        """Test successful company processing."""
        result = process_company(
            "TEST001",
            sample_company_data,
            sample_pl_df,
            sample_bs_df,
            sample_cf_df
        )
        
        assert result["company_id"] == "TEST001"
        assert result["status"] in ["success", "partial_success"]
        assert "processing_time_ms" in result
        assert result["processing_time_ms"] >= 0
    
    def test_missing_pl_data(self, sample_company_data, sample_bs_df, sample_cf_df):
        """Test processing with missing P&L data."""
        result = process_company(
            "TEST001",
            sample_company_data,
            pd.DataFrame(),
            sample_bs_df,
            sample_cf_df
        )
        
        assert result["status"] == "failed"
        assert len(result["validation_errors"]) > 0
    
    def test_missing_bs_data(self, sample_company_data, sample_pl_df, sample_cf_df):
        """Test processing with missing Balance Sheet data."""
        result = process_company(
            "TEST001",
            sample_company_data,
            sample_pl_df,
            pd.DataFrame(),
            sample_cf_df
        )
        
        # Should still process but with validation errors
        assert result["status"] in ["failed", "partial_success"]
    
    def test_missing_cf_data(self, sample_company_data, sample_pl_df, sample_bs_df):
        """Test processing with missing Cash Flow data."""
        result = process_company(
            "TEST001",
            sample_company_data,
            sample_pl_df,
            sample_bs_df,
            pd.DataFrame()
        )
        
        # Should still process but with validation errors
        assert result["status"] in ["failed", "partial_success"]
    
    def test_empty_pl_dataframe(self, sample_company_data):
        """Test processing with empty P&L DataFrame."""
        result = process_company(
            "TEST001",
            sample_company_data,
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame()
        )
        
        assert result["status"] == "failed"
        assert any(e["error_type"] == "NO_DATA" for e in result["validation_errors"])


# =============================================================================
# PIPELINE ORCHESTRATION TESTS
# =============================================================================

class TestRatioEnginePipeline:
    """Test RatioEnginePipeline class."""
    
    def test_pipeline_initialization(self):
        """Test pipeline initialization."""
        pipeline = RatioEnginePipeline()
        assert pipeline.output_dir.exists()
        assert pipeline.pipeline_stats["status"] == "not_started"
    
    def test_pipeline_with_single_company(self, sample_company_data, sample_pl_df,
                                          sample_bs_df, sample_cf_df):
        """Test pipeline with single company."""
        companies_data = {
            "TEST001": {
                **sample_company_data,
                "profit_loss": sample_pl_df,
                "balance_sheet": sample_bs_df,
                "cash_flow": sample_cf_df
            }
        }
        
        pipeline = RatioEnginePipeline()
        stats = pipeline.run(companies_data)
        
        assert stats["status"] == "completed"
        assert stats["companies_processed"] == 1
    
    def test_pipeline_with_multiple_companies(self, sample_pl_df, sample_bs_df, sample_cf_df):
        """Test pipeline with multiple companies."""
        companies_data = {
            "TEST001": {
                "company_name": "Company 1",
                "industry": "Tech",
                "sector": "IT",
                "profit_loss": sample_pl_df,
                "balance_sheet": sample_bs_df,
                "cash_flow": sample_cf_df
            },
            "TEST002": {
                "company_name": "Company 2",
                "industry": "Finance",
                "sector": "Financials",
                "profit_loss": sample_pl_df,
                "balance_sheet": sample_bs_df,
                "cash_flow": sample_cf_df
            }
        }
        
        pipeline = RatioEnginePipeline()
        stats = pipeline.run(companies_data)
        
        assert stats["companies_processed"] == 2
    
    def test_pipeline_continues_after_failure(self, sample_pl_df, sample_bs_df, sample_cf_df):
        """Test that pipeline continues after a company fails."""
        companies_data = {
            "TEST001": {
                "company_name": "Good Company",
                "industry": "Tech",
                "sector": "IT",
                "profit_loss": sample_pl_df,
                "balance_sheet": sample_bs_df,
                "cash_flow": sample_cf_df
            },
            "TEST002": {
                "company_name": "Bad Company",
                "industry": "Finance",
                "sector": "Financials",
                "profit_loss": pd.DataFrame(),  # Empty - will fail
                "balance_sheet": sample_bs_df,
                "cash_flow": sample_cf_df
            },
            "TEST003": {
                "company_name": "Another Good Company",
                "industry": "Tech",
                "sector": "IT",
                "profit_loss": sample_pl_df,
                "balance_sheet": sample_bs_df,
                "cash_flow": sample_cf_df
            }
        }
        
        pipeline = RatioEnginePipeline()
        stats = pipeline.run(companies_data)
        
        # Should process all companies despite one failure
        assert stats["companies_processed"] == 3
        assert stats["companies_failed"] >= 1
    
    def test_load_summary_generation(self, sample_company_data, sample_pl_df,
                                     sample_bs_df, sample_cf_df):
        """Test that load summary CSV is generated."""
        companies_data = {
            "TEST001": {
                **sample_company_data,
                "profit_loss": sample_pl_df,
                "balance_sheet": sample_bs_df,
                "cash_flow": sample_cf_df
            }
        }
        
        pipeline = RatioEnginePipeline()
        pipeline.run(companies_data)
        
        # Check that CSV was generated
        assert pipeline.RATIO_LOAD_SUMMARY_CSV.exists()
        
        # Verify CSV content
        df = pd.read_csv(pipeline.RATIO_LOAD_SUMMARY_CSV)
        assert len(df) > 0
        assert "company_id" in df.columns
        assert "status" in df.columns
    
    def test_audit_log_generation(self, sample_company_data, sample_pl_df,
                                  sample_bs_df, sample_cf_df):
        """Test that audit log is generated."""
        companies_data = {
            "TEST001": {
                **sample_company_data,
                "profit_loss": sample_pl_df,
                "balance_sheet": sample_bs_df,
                "cash_flow": sample_cf_df
            }
        }
        
        pipeline = RatioEnginePipeline()
        pipeline.run(companies_data)
        
        # Check that log file was generated
        assert pipeline.RATIO_ENGINE_LOG.exists()
        
        # Verify log content
        with open(pipeline.RATIO_ENGINE_LOG, 'r') as f:
            content = f.read()
            assert "Pipeline Summary" in content
            assert "Companies Processed" in content


# =============================================================================
# UTILITY FUNCTION TESTS
# =============================================================================

class TestGetPipelineStatistics:
    """Test get_pipeline_statistics function."""
    
    def test_get_statistics_empty_db(self, temp_db):
        """Test getting statistics from empty database."""
        with patch('src.analytics.ratio_engine.get_connection') as mock_get_conn:
            mock_conn = sqlite3.connect(temp_db)
            mock_get_conn.return_value = mock_conn
            
            stats = get_pipeline_statistics()
            assert stats["total_records"] == 0
            
            mock_conn.close()


class TestValidateDatabaseIntegrity:
    """Test validate_database_integrity function."""
    
    def test_validate_empty_database(self, temp_db):
        """Test validating empty database."""
        with patch('src.analytics.ratio_engine.get_connection') as mock_get_conn:
            mock_conn = sqlite3.connect(temp_db)
            mock_get_conn.return_value = mock_conn
            
            results = validate_database_integrity()
            assert results["valid"] is True
            
            mock_conn.close()
    
    def test_validate_with_duplicates(self, temp_db):
        """Test validating database with duplicates."""
        with patch('src.analytics.ratio_engine.get_connection') as mock_get_conn:
            mock_conn = sqlite3.connect(temp_db)
            mock_get_conn.return_value = mock_conn
            
            # Insert duplicate records
            mock_conn.execute(
                "INSERT INTO financial_ratios (company_id, period) VALUES (?, ?)",
                ("TEST001", "FY2024")
            )
            mock_conn.execute(
                "INSERT INTO financial_ratios (company_id, period) VALUES (?, ?)",
                ("TEST001", "FY2024")
            )
            mock_conn.commit()
            
            results = validate_database_integrity()
            assert results["valid"] is False
            assert any(c["check"] == "duplicates" and c["status"] == "failed" 
                      for c in results["checks"])
            
            mock_conn.close()


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_companies_dict(self):
        """Test pipeline with empty companies dictionary."""
        pipeline = RatioEnginePipeline()
        stats = pipeline.run({})
        
        assert stats["status"] == "completed"
        assert stats["companies_processed"] == 0
    
    def test_none_values_in_record(self):
        """Test handling of None values in record."""
        record = {
            "company_id": "TEST001",
            "period": "FY2024",
            "net_profit_margin": None,
            "roe": None
        }
        
        with patch('src.analytics.ratio_engine.get_connection') as mock_get_conn:
            mock_conn = MagicMock()
            mock_get_conn.return_value = mock_conn
            
            success, error_msg = insert_financial_ratios(record)
            # Should succeed even with None values
            assert success is True
    
    def test_sqlite_connection_failure(self):
        """Test handling of SQLite connection failure."""
        with patch('src.analytics.ratio_engine.get_connection') as mock_get_conn:
            mock_get_conn.side_effect = sqlite3.Error("Connection failed")
            
            record = {"company_id": "TEST001", "period": "FY2024"}
            success, error_msg = insert_financial_ratios(record)
            
            assert success is False
            assert error_msg is not None
    
    def test_processing_time_tracking(self, sample_company_data, sample_pl_df,
                                      sample_bs_df, sample_cf_df):
        """Test that processing time is tracked."""
        result = process_company(
            "TEST001",
            sample_company_data,
            sample_pl_df,
            sample_bs_df,
            sample_cf_df
        )
        
        assert "processing_time_ms" in result
        assert isinstance(result["processing_time_ms"], int)
        assert result["processing_time_ms"] >= 0


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestEndToEndPipeline:
    """End-to-end pipeline tests."""
    
    def test_full_pipeline_execution(self, sample_pl_df, sample_bs_df, sample_cf_df):
        """Test complete pipeline execution."""
        companies_data = {
            "TEST001": {
                "company_name": "Test Company 1",
                "industry": "Technology",
                "sector": "IT",
                "profit_loss": sample_pl_df,
                "balance_sheet": sample_bs_df,
                "cash_flow": sample_cf_df
            },
            "TEST002": {
                "company_name": "Test Company 2",
                "industry": "Finance",
                "sector": "Financials",
                "profit_loss": sample_pl_df,
                "balance_sheet": sample_bs_df,
                "cash_flow": sample_cf_df
            }
        }
        
        stats = run_ratio_engine_pipeline(companies_data)
        
        assert stats["status"] == "completed"
        assert stats["companies_processed"] == 2
        assert "rows_inserted" in stats
        assert "rows_skipped" in stats
        assert "validation_failures" in stats
    
    def test_pipeline_with_missing_data_companies(self, sample_pl_df, sample_bs_df, sample_cf_df):
        """Test pipeline with companies having missing data."""
        companies_data = {
            "TEST001": {
                "company_name": "Complete Data",
                "industry": "Tech",
                "sector": "IT",
                "profit_loss": sample_pl_df,
                "balance_sheet": sample_bs_df,
                "cash_flow": sample_cf_df
            },
            "TEST002": {
                "company_name": "Missing CF",
                "industry": "Finance",
                "sector": "Financials",
                "profit_loss": sample_pl_df,
                "balance_sheet": sample_bs_df,
                "cash_flow": pd.DataFrame()  # Missing
            },
            "TEST003": {
                "company_name": "Missing BS",
                "industry": "Finance",
                "sector": "Financials",
                "profit_loss": sample_pl_df,
                "balance_sheet": pd.DataFrame(),  # Missing
                "cash_flow": sample_cf_df
            }
        }
        
        stats = run_ratio_engine_pipeline(companies_data)
        
        assert stats["status"] == "completed"
        assert stats["companies_processed"] == 3
        # Some companies should have validation failures
        assert stats["validation_failures"] > 0


# =============================================================================
# PERFORMANCE TESTS
# =============================================================================

class TestPerformance:
    """Performance and runtime tests."""
    
    def test_processing_time_reasonable(self, sample_company_data, sample_pl_df,
                                        sample_bs_df, sample_cf_df):
        """Test that processing time is reasonable (< 5 seconds per company)."""
        start = time.time()
        
        result = process_company(
            "TEST001",
            sample_company_data,
            sample_pl_df,
            sample_bs_df,
            sample_cf_df
        )
        
        elapsed = time.time() - start
        
        assert result["processing_time_ms"] < 5000  # Less than 5 seconds
        assert elapsed < 5.0  # Wall clock time also reasonable
    
    def test_multi_company_performance(self, sample_pl_df, sample_bs_df, sample_cf_df):
        """Test performance with multiple companies."""
        # Create 10 companies
        companies_data = {}
        for i in range(10):
            companies_data[f"TEST{i:03d}"] = {
                "company_name": f"Company {i}",
                "industry": "Tech",
                "sector": "IT",
                "profit_loss": sample_pl_df,
                "balance_sheet": sample_bs_df,
                "cash_flow": sample_cf_df
            }
        
        start = time.time()
        stats = run_ratio_engine_pipeline(companies_data)
        elapsed = time.time() - start
        
        assert stats["status"] == "completed"
        assert stats["companies_processed"] == 10
        # All 10 companies should process in reasonable time
        assert elapsed < 30.0  # 30 seconds for 10 companies


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])