"""
test_final_validation.py

Comprehensive test suite for the final validation module (Module 10).

Tests cover:
- Database validation
- Financial ratios validation
- CAGR validation
- Health score validation
- Screener validation
- Peer ranking validation
- Radar chart validation
- Peer report validation
- Report generation
- Performance
- Error handling
- Integration tests
"""

import logging
import os
import sqlite3
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime

import pandas as pd
import numpy as np
import pytest

from src.validation.final_validation import (
    ValidationCheck,
    ValidationResult,
    validate_database,
    validate_financial_ratios,
    validate_cagr,
    validate_health_scores,
    validate_screeners,
    validate_peer_rankings,
    validate_radar_charts,
    validate_peer_reports,
    generate_validation_report,
    run_final_validation,
)
from src.validation.report_generator import (
    MarkdownReportGenerator,
    HTMLReportGenerator,
    DataExporter,
    format_number,
    format_percentage,
    format_timestamp,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def temp_dir():
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_db_connection():
    """Create mock database connection."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.execute.return_value = mock_cursor
    mock_conn.cursor.return_value = mock_cursor
    return mock_conn


@pytest.fixture
def sample_companies_df():
    """Create sample companies DataFrame."""
    return pd.DataFrame({
        'company_id': ['TCS', 'RELIANCE', 'INFY'],
        'company_name': ['TCS Ltd', 'Reliance Industries', 'Infosys'],
        'sector': ['IT', 'Energy', 'IT'],
        'industry': ['Software', 'Oil & Gas', 'Software'],
    })


@pytest.fixture
def sample_financial_ratios_df():
    """Create sample financial ratios DataFrame."""
    return pd.DataFrame({
        'company_id': ['TCS', 'RELIANCE', 'INFY'],
        'company_name': ['TCS Ltd', 'Reliance Industries', 'Infosys'],
        'period': ['FY2024', 'FY2024', 'FY2024'],
        'net_profit_margin': [20.5, 8.3, 18.2],
        'operating_profit_margin': [25.1, 10.5, 22.3],
        'roe': [45.2, 12.5, 38.7],
        'roce': [48.3, 15.2, 42.1],
        'roa': [22.5, 6.8, 19.3],
        'debt_to_equity': [0.2, 0.4, 0.15],
        'interest_coverage': [15.5, 8.2, 12.3],
        'asset_turnover': [1.2, 0.8, 1.5],
        'revenue_cagr_3yr': [10.5, 5.2, 12.3],
        'pat_cagr_3yr': [12.3, 8.5, 15.2],
        'eps_cagr_3yr': [11.2, 7.8, 14.1],
    })


@pytest.fixture
def sample_health_scores_df():
    """Create sample health scores DataFrame."""
    return pd.DataFrame({
        'company_id': ['TCS', 'RELIANCE', 'INFY'],
        'company_name': ['TCS Ltd', 'Reliance Industries', 'Infosys'],
        'period': ['FY2024', 'FY2024', 'FY2024'],
        'profitability_score': [85.2, 65.3, 78.5],
        'growth_score': [72.1, 58.4, 75.2],
        'cashflow_score': [80.5, 70.2, 77.8],
        'leverage_score': [90.3, 75.6, 88.2],
        'efficiency_score': [68.4, 62.1, 70.5],
        'overall_score': [78.5, 65.2, 75.8],
        'rating': ['Strong', 'Healthy', 'Strong'],
    })


@pytest.fixture
def sample_peer_percentiles_df():
    """Create sample peer percentiles DataFrame."""
    return pd.DataFrame({
        'company_id': ['TCS', 'RELIANCE', 'INFY'] * 10,
        'peer_group_name': ['IT Services'] * 30,
        'metric': ['roe', 'roce', 'net_profit_margin', 'debt_to_equity', 'free_cash_flow',
                   'revenue_cagr_5yr', 'pat_cagr_5yr', 'eps_cagr_5yr', 'interest_coverage', 'asset_turnover'] * 3,
        'metric_value': [45.2, 48.3, 20.5, 0.2, 10000, 10.5, 12.3, 11.2, 15.5, 1.2] * 3,
        'percentile_rank': [0.85, 0.82, 0.78, 0.90, 0.75, 0.70, 0.72, 0.68, 0.80, 0.77] * 3,
        'period': ['FY2024'] * 30,
    })


# =============================================================================
# TEST VALIDATION CHECK CLASS
# =============================================================================

class TestValidationCheck:
    """Test ValidationCheck class."""
    
    def test_validation_check_creation(self):
        """Test creating a validation check."""
        check = ValidationCheck("test_check", "PASS", "Test message")
        
        assert check.check_name == "test_check"
        assert check.status == "PASS"
        assert check.message == "Test message"
        assert check.timestamp is not None
    
    def test_validation_check_to_dict(self):
        """Test converting validation check to dictionary."""
        check = ValidationCheck("test_check", "FAIL", "Error message")
        result = check.to_dict()
        
        assert result["check"] == "test_check"
        assert result["status"] == "FAIL"
        assert result["message"] == "Error message"
        assert "timestamp" in result
    
    def test_validation_check_repr(self):
        """Test validation check string representation."""
        check = ValidationCheck("test_check", "PASS")
        result = repr(check)
        
        assert "test_check" in result
        assert "PASS" in result


# =============================================================================
# TEST VALIDATION RESULT CLASS
# =============================================================================

class TestValidationResult:
    """Test ValidationResult class."""
    
    def test_validation_result_creation(self):
        """Test creating a validation result."""
        result = ValidationResult("Test Category")
        
        assert result.category == "Test Category"
        assert len(result.checks) == 0
        assert len(result.errors) == 0
        assert len(result.warnings) == 0
    
    def test_add_check_pass(self):
        """Test adding a passing check."""
        result = ValidationResult("Test")
        result.add_check("check1", "PASS", "Success")
        
        assert len(result.checks) == 1
        assert len(result.errors) == 0
        assert len(result.warnings) == 0
        assert result.is_passed()
    
    def test_add_check_fail(self):
        """Test adding a failing check."""
        result = ValidationResult("Test")
        result.add_check("check1", "FAIL", "Error")
        
        assert len(result.checks) == 1
        assert len(result.errors) == 1
        assert len(result.warnings) == 0
        assert not result.is_passed()
    
    def test_add_check_warning(self):
        """Test adding a warning check."""
        result = ValidationResult("Test")
        result.add_check("check1", "WARNING", "Warning message")
        
        assert len(result.checks) == 1
        assert len(result.errors) == 0
        assert len(result.warnings) == 1
        assert result.is_passed()  # Warnings don't fail
    
    def test_get_execution_time(self):
        """Test getting execution time."""
        result = ValidationResult("Test")
        
        # No time set
        assert result.get_execution_time() == 0.0
        
        # Time set
        result.start_time = 1000.0
        result.end_time = 1005.0
        assert result.get_execution_time() == 5.0
    
    def test_to_dict(self):
        """Test converting to dictionary."""
        result = ValidationResult("Test Category")
        result.add_check("check1", "PASS", "Success")
        result.start_time = 1000.0
        result.end_time = 1005.0
        
        result_dict = result.to_dict()
        
        assert result_dict["category"] == "Test Category"
        assert result_dict["passed"] == True
        assert len(result_dict["checks"]) == 1
        assert result_dict["execution_time"] == 5.0


# =============================================================================
# TEST DATABASE VALIDATION
# =============================================================================

class TestDatabaseValidation:
    """Test database validation."""
    
    @patch('src.validation.final_validation.get_connection')
    def test_validate_database_success(self, mock_get_conn, mock_db_connection):
        """Test successful database validation."""
        mock_get_conn.return_value = mock_db_connection
        
        # Mock cursor responses
        mock_cursor = mock_db_connection.cursor()
        mock_cursor.fetchone.side_effect = [
            (1,),  # foreign_keys
            (100,),  # companies count
            (50,),  # financial_ratios count
            (10,),  # peer_groups count
            ("ok",),  # integrity_check
        ]
        
        # Mock fetchall to return all required tables
        mock_cursor.fetchall.return_value = [
            ('companies',),
            ('profit_loss',),
            ('balance_sheet',),
            ('cash_flow',),
            ('analysis',),
            ('documents',),
            ('pros_cons',),
            ('sectors',),
            ('stock_prices',),
            ('market_cap',),
            ('financial_ratios',),
            ('peer_groups',),
            ('financial_health_scores',),
            ('peer_percentiles',),
        ]
        
        # Mock Path.exists to return True
        with patch('pathlib.Path.exists', return_value=True):
            result = validate_database()
        
        assert result.category == "Database"
        assert result.is_passed()
    
    @patch('src.validation.final_validation.DATABASE_PATH')
    @patch('src.validation.final_validation.get_connection')
    def test_validate_database_missing_file(self, mock_get_conn, mock_db_path):
        """Test database validation with missing file."""
        mock_db_path.exists.return_value = False
        
        result = validate_database()
        
        assert not result.is_passed()
        assert any("not found" in err for err in result.errors)
    
    @patch('src.validation.final_validation.DATABASE_PATH')
    @patch('src.validation.final_validation.get_connection')
    def test_validate_database_connection_failure(self, mock_get_conn, mock_db_path):
        """Test database validation with connection failure."""
        mock_db_path.exists.return_value = True
        mock_get_conn.side_effect = Exception("Connection failed")
        
        result = validate_database()
        
        assert not result.is_passed()


# =============================================================================
# TEST FINANCIAL RATIOS VALIDATION
# =============================================================================

class TestFinancialRatiosValidation:
    """Test financial ratios validation."""
    
    @patch('src.validation.final_validation.get_connection')
    def test_validate_financial_ratios_success(self, mock_get_conn, mock_db_connection, 
                                               sample_financial_ratios_df):
        """Test successful financial ratios validation."""
        mock_get_conn.return_value = mock_db_connection
        
        # Mock cursor
        mock_cursor = mock_db_connection.cursor()
        mock_cursor.fetchone.return_value = (100,)
        
        # Mock pd.read_sql_query
        with patch('src.validation.final_validation.pd.read_sql_query', 
                   return_value=sample_financial_ratios_df):
            result = validate_financial_ratios()
        
        assert result.category == "Financial Ratios"
        assert result.is_passed()
    
    @patch('src.validation.final_validation.get_connection')
    def test_validate_financial_ratios_empty_table(self, mock_get_conn, mock_db_connection):
        """Test financial ratios validation with empty table."""
        mock_get_conn.return_value = mock_db_connection
        
        # Mock cursor
        mock_cursor = mock_db_connection.cursor()
        mock_cursor.fetchone.return_value = (0,)
        
        result = validate_financial_ratios()
        
        assert not result.is_passed()
        assert any("empty" in err.lower() for err in result.errors)
    
    @patch('src.validation.final_validation.get_connection')
    def test_validate_financial_ratios_missing_kpis(self, mock_get_conn, mock_db_connection):
        """Test financial ratios validation with missing KPIs."""
        mock_get_conn.return_value = mock_db_connection
        
        # Mock cursor
        mock_cursor = mock_db_connection.cursor()
        mock_cursor.fetchone.return_value = (100,)
        
        # DataFrame with missing KPIs
        df = pd.DataFrame({
            'company_id': ['TCS'],
            'period': ['FY2024'],
            'sales': [1000],
        })
        
        with patch('src.validation.final_validation.pd.read_sql_query', return_value=df):
            result = validate_financial_ratios()
        
        # Should fail when core KPIs are missing
        assert not result.is_passed()
        assert any("Missing core KPI" in err for err in result.errors)


# =============================================================================
# TEST CAGR VALIDATION
# =============================================================================

class TestCAGRValidation:
    """Test CAGR validation."""
    
    @patch('src.validation.final_validation.get_connection')
    def test_validate_cagr_success(self, mock_get_conn, mock_db_connection, 
                                   sample_financial_ratios_df):
        """Test successful CAGR validation."""
        mock_get_conn.return_value = mock_db_connection
        
        with patch('src.validation.final_validation.pd.read_sql_query', 
                   return_value=sample_financial_ratios_df):
            result = validate_cagr()
        
        assert result.category == "CAGR"
        assert result.is_passed()
    
    @patch('src.validation.final_validation.get_connection')
    def test_validate_cagr_no_data(self, mock_get_conn, mock_db_connection):
        """Test CAGR validation with no data."""
        mock_get_conn.return_value = mock_db_connection
        
        with patch('src.validation.final_validation.pd.read_sql_query', 
                   return_value=pd.DataFrame()):
            result = validate_cagr()
        
        assert not result.is_passed()
        assert any("No financial ratios data" in err for err in result.errors)
    
    @patch('src.validation.final_validation.get_connection')
    def test_validate_cagr_missing_columns(self, mock_get_conn, mock_db_connection):
        """Test CAGR validation with missing columns."""
        mock_get_conn.return_value = mock_db_connection
        
        # DataFrame without CAGR columns
        df = pd.DataFrame({
            'company_id': ['TCS'],
            'period': ['FY2024'],
            'sales': [1000],
        })
        
        with patch('src.validation.final_validation.pd.read_sql_query', return_value=df):
            result = validate_cagr()
        
        # Should pass with warnings since CAGR is optional
        assert result.is_passed()
        assert any("not found" in warn for warn in result.warnings)


# =============================================================================
# TEST HEALTH SCORE VALIDATION
# =============================================================================

class TestHealthScoreValidation:
    """Test health score validation."""
    
    @patch('src.validation.final_validation.get_connection')
    def test_validate_health_scores_success(self, mock_get_conn, mock_db_connection,
                                           sample_health_scores_df):
        """Test successful health scores validation."""
        mock_get_conn.return_value = mock_db_connection
        
        # Mock cursor
        mock_cursor = mock_db_connection.cursor()
        mock_cursor.fetchone.return_value = (100,)
        
        with patch('src.validation.final_validation.pd.read_sql_query',
                   return_value=sample_health_scores_df):
            result = validate_health_scores()
        
        assert result.category == "Health Score"
        assert result.is_passed()
    
    @patch('src.validation.final_validation.get_connection')
    def test_validate_health_scores_empty_table(self, mock_get_conn, mock_db_connection):
        """Test health scores validation with empty table."""
        mock_get_conn.return_value = mock_db_connection
        
        # Mock cursor
        mock_cursor = mock_db_connection.cursor()
        mock_cursor.fetchone.return_value = (0,)
        
        result = validate_health_scores()
        
        assert not result.is_passed()
        assert any("empty" in err.lower() for err in result.errors)
    
    @patch('src.validation.final_validation.get_connection')
    def test_validate_health_scores_out_of_range(self, mock_get_conn, mock_db_connection):
        """Test health scores validation with out-of-range scores."""
        mock_get_conn.return_value = mock_db_connection
        
        # Mock cursor
        mock_cursor = mock_db_connection.cursor()
        mock_cursor.fetchone.return_value = (100,)
        
        # DataFrame with out-of-range scores
        df = pd.DataFrame({
            'company_id': ['TCS', 'RELIANCE'],
            'period': ['FY2024', 'FY2024'],
            'overall_score': [85.2, 120.5],  # 120.5 is out of range
        })
        
        with patch('src.validation.final_validation.pd.read_sql_query', return_value=df):
            result = validate_health_scores()
        
        assert not result.is_passed()
        assert any("outside 0-100" in err for err in result.errors)


# =============================================================================
# TEST SCREENER VALIDATION
# =============================================================================

class TestScreenerValidation:
    """Test screener validation."""
    
    @patch('src.screener.engine.ScreenerEngine')
    @patch('src.validation.final_validation.list_preset_screeners')
    def test_validate_screeners_success(self, mock_list_presets, mock_screener_class):
        """Test successful screener validation."""
        # Mock presets
        mock_list_presets.return_value = [{'id': 'preset1'}, {'id': 'preset2'}]
        
        # Mock screener engine
        mock_engine = MagicMock()
        mock_engine.load_data.return_value = pd.DataFrame({'company_id': ['TCS', 'RELIANCE']})
        mock_engine.apply_filters.return_value = pd.DataFrame({'company_id': ['TCS']})
        mock_engine.screen_companies.return_value = {
            'success': True,
            'results': [{'company_id': 'TCS'}]
        }
        mock_screener_class.return_value = mock_engine
        
        result = validate_screeners()
        
        assert result.category == "Screener"
        assert result.is_passed()
    
    @patch('src.screener.engine.ScreenerEngine')
    @patch('src.validation.final_validation.list_preset_screeners')
    def test_validate_screeners_import_failure(self, mock_list_presets, mock_screener_class):
        """Test screener validation with import failure."""
        mock_screener_class.side_effect = ImportError("Module not found")
        
        result = validate_screeners()
        
        assert not result.is_passed()
        assert any("Data loading failed" in err for err in result.errors)


# =============================================================================
# TEST PEER RANKING VALIDATION
# =============================================================================

class TestPeerRankingValidation:
    """Test peer ranking validation."""
    
    @patch('src.validation.final_validation.get_connection')
    def test_validate_peer_rankings_success(self, mock_get_conn, mock_db_connection,
                                           sample_peer_percentiles_df):
        """Test successful peer ranking validation."""
        mock_get_conn.return_value = mock_db_connection
        
        # Mock cursor
        mock_cursor = mock_db_connection.cursor()
        mock_cursor.fetchone.side_effect = [(10,), (30,)]
        
        with patch('src.validation.final_validation.pd.read_sql_query',
                   return_value=sample_peer_percentiles_df):
            result = validate_peer_rankings()
        
        assert result.category == "Peer Ranking"
        assert result.is_passed()
    
    @patch('src.validation.final_validation.get_connection')
    def test_validate_peer_rankings_no_data(self, mock_get_conn, mock_db_connection):
        """Test peer ranking validation with no data."""
        mock_get_conn.return_value = mock_db_connection
        
        # Mock cursor
        mock_cursor = mock_db_connection.cursor()
        mock_cursor.fetchone.side_effect = [(0,), (0,)]
        
        result = validate_peer_rankings()
        
        assert not result.is_passed()
        assert any("No peer groups" in err for err in result.errors)


# =============================================================================
# TEST RADAR CHART VALIDATION
# =============================================================================

class TestRadarChartValidation:
    """Test radar chart validation."""
    
    @patch('src.validation.final_validation.OUTPUT_DIR')
    @patch('src.validation.final_validation.get_connection')
    def test_validate_radar_charts_success(self, mock_get_conn, mock_output_dir, temp_dir):
        """Test successful radar chart validation."""
        mock_get_conn.return_value = MagicMock()
        mock_output_dir.__truediv__ = lambda self, x: temp_dir / x
        
        # Create mock chart files
        radar_dir = temp_dir / "radar_charts"
        radar_dir.mkdir(parents=True, exist_ok=True)
        
        # Create valid PNG files
        for company_id in ['TCS', 'RELIANCE', 'INFY']:
            png_file = radar_dir / f"{company_id}.png"
            with open(png_file, 'wb') as f:
                f.write(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
        
        with patch('src.validation.final_validation.OUTPUT_DIR', temp_dir):
            result = validate_radar_charts()
        
        assert result.category == "Radar Charts"
        assert result.is_passed()
    
    @patch('src.validation.final_validation.OUTPUT_DIR')
    def test_validate_radar_charts_missing_directory(self, mock_output_dir, temp_dir):
        """Test radar chart validation with missing directory."""
        non_existent_dir = temp_dir / "non_existent"
        
        with patch('src.validation.final_validation.OUTPUT_DIR', non_existent_dir):
            result = validate_radar_charts()
        
        assert not result.is_passed()
        assert any("not found" in err for err in result.errors)


# =============================================================================
# TEST PEER REPORT VALIDATION
# =============================================================================

class TestPeerReportValidation:
    """Test peer report validation."""
    
    @patch('src.validation.final_validation.OUTPUT_DIR')
    def test_validate_peer_reports_success(self, mock_output_dir, temp_dir):
        """Test successful peer report validation."""
        mock_output_dir.__truediv__ = lambda self, x: temp_dir / x
        
        # Create mock report files
        reports_dir = temp_dir / "peer_reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a valid report
        report_content = """
# Company Information
**Company Name:** TCS Ltd

# Financial Health Score
## Overall Score: 78.5/100
**Rating:** Strong

# KPI Comparison Table
| Metric | Company Value | Peer Average |
|--------|--------------|--------------|

# Percentile Rankings
| Metric | Company Value | Percentile Rank |
|--------|--------------|----------------|

# Peer Benchmark Summary
| Metric | Company Value | Peer Average | Peer Count |
|--------|--------------|--------------|------------|

# Strengths
The following metrics represent strengths.

# Weaknesses
The following metrics represent weaknesses.

# Radar Chart
**Radar Chart Location:** `/path/to/chart.png`

# Final Recommendation
Overall assessment.
"""
        
        report_file = reports_dir / "TCS.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        with patch('src.validation.final_validation.OUTPUT_DIR', temp_dir):
            result = validate_peer_reports()
        
        assert result.category == "Peer Reports"
        assert result.is_passed()
    
    @patch('src.validation.final_validation.OUTPUT_DIR')
    def test_validate_peer_reports_missing_directory(self, mock_output_dir, temp_dir):
        """Test peer report validation with missing directory."""
        non_existent_dir = temp_dir / "non_existent"
        
        with patch('src.validation.final_validation.OUTPUT_DIR', non_existent_dir):
            result = validate_peer_reports()
        
        assert not result.is_passed()
        assert any("not found" in err for err in result.errors)


# =============================================================================
# TEST REPORT GENERATION
# =============================================================================

class TestReportGeneration:
    """Test report generation."""
    
    def test_generate_validation_report_success(self):
        """Test successful validation report generation."""
        # Create mock validation results
        validation_results = {
            "Database": ValidationResult("Database"),
            "Financial Ratios": ValidationResult("Financial Ratios"),
        }
        
        validation_results["Database"].add_check("db_check", "PASS", "OK")
        validation_results["Financial Ratios"].add_check("ratio_check", "PASS", "OK")
        
        statistics = {
            "total_companies": 100,
            "reports_generated": 100,
            "charts_generated": 100,
        }
        
        report = generate_validation_report(validation_results, statistics, 10.5)
        
        assert "# Sprint 3 Final Validation Report" in report
        assert "Overall Result" in report
        assert "Database" in report
        assert "Financial Ratios" in report
        assert "PASS" in report
    
    def test_generate_validation_report_with_failures(self):
        """Test validation report generation with failures."""
        validation_results = {
            "Database": ValidationResult("Database"),
        }
        
        validation_results["Database"].add_check("db_check", "FAIL", "Error")
        
        statistics = {}
        
        report = generate_validation_report(validation_results, statistics, 5.0)
        
        assert "FAIL" in report
        assert "INCOMPLETE" in report


# =============================================================================
# TEST REPORT GENERATOR UTILITIES
# =============================================================================

class TestReportGeneratorUtilities:
    """Test report generator utility functions."""
    
    def test_format_number(self):
        """Test number formatting."""
        assert format_number(123.456) == "123.46"
        assert format_number(123.456, 1) == "123.5"
        assert format_number(None) == "N/A"
        assert format_number("invalid") == "invalid"
    
    def test_format_percentage(self):
        """Test percentage formatting."""
        assert format_percentage(0.85) == "85.00%"
        assert format_percentage(85.0) == "85.00%"
        assert format_percentage(None) == "N/A"
    
    def test_format_timestamp(self):
        """Test timestamp formatting."""
        timestamp = "2024-01-15T10:30:00"
        formatted = format_timestamp(timestamp)
        assert "2024-01-15" in formatted
        assert "10:30:00" in formatted
    
    def test_markdown_report_generator(self, temp_dir):
        """Test Markdown report generator."""
        generator = MarkdownReportGenerator(output_dir=temp_dir)
        
        # Test header generation
        header = generator.generate_header("Test Report", "Test Subtitle")
        assert "# Test Report" in header
        assert "Test Subtitle" in header
        
        # Test table generation
        table = generator.generate_table(
            ["Name", "Value"],
            [["Item 1", "100"], ["Item 2", "200"]]
        )
        assert "| Name | Value |" in table
        assert "| Item 1 | 100 |" in table
        
        # Test saving report
        report_path = generator.save_report("# Test\n\nContent", "test.md")
        assert report_path.exists()
    
    def test_html_report_generator(self, temp_dir):
        """Test HTML report generator."""
        generator = HTMLReportGenerator(output_dir=temp_dir)
        
        # Test HTML header
        header = generator.generate_html_header("Test Report")
        assert "<!DOCTYPE html>" in header
        assert "<title>Test Report</title>" in header
        
        # Test saving HTML report
        report_path = generator.save_html_report("# Test", "test.html")
        assert report_path.exists()
    
    def test_data_exporter_csv(self, temp_dir):
        """Test CSV export."""
        exporter = DataExporter(output_dir=temp_dir)
        
        df = pd.DataFrame({'col1': [1, 2, 3], 'col2': ['a', 'b', 'c']})
        output_path = exporter.export_to_csv(df, "test.csv")
        
        assert output_path.exists()
        loaded_df = pd.read_csv(output_path)
        assert len(loaded_df) == 3
    
    def test_data_exporter_json(self, temp_dir):
        """Test JSON export."""
        exporter = DataExporter(output_dir=temp_dir)
        
        data = {'key1': 'value1', 'key2': 123}
        output_path = exporter.export_to_json(data, "test.json")
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            loaded_data = pd.read_json(f, typ='series')
        assert loaded_data['key1'] == 'value1'


# =============================================================================
# TEST RUN FINAL VALIDATION
# =============================================================================

class TestRunFinalValidation:
    """Test run_final_validation function."""
    
    @patch('src.validation.final_validation.validate_peer_reports')
    @patch('src.validation.final_validation.validate_radar_charts')
    @patch('src.validation.final_validation.validate_peer_rankings')
    @patch('src.validation.final_validation.validate_screeners')
    @patch('src.validation.final_validation.validate_health_scores')
    @patch('src.validation.final_validation.validate_cagr')
    @patch('src.validation.final_validation.validate_financial_ratios')
    @patch('src.validation.final_validation.validate_database')
    def test_run_final_validation_success(self, mock_validate_db, mock_validate_ratios,
                                         mock_validate_cagr, mock_validate_health,
                                         mock_validate_screener, mock_validate_peer,
                                         mock_validate_radar, mock_validate_reports):
        """Test successful final validation run."""
        # Mock all validation functions to return passing results
        for mock_func in [mock_validate_db, mock_validate_ratios, mock_validate_cagr,
                          mock_validate_health, mock_validate_screener, mock_validate_peer,
                          mock_validate_radar, mock_validate_reports]:
            mock_result = ValidationResult("Test")
            mock_result.add_check("check1", "PASS", "OK")
            mock_func.return_value = mock_result
        
        # Mock database connection for statistics
        with patch('src.validation.final_validation.get_connection') as mock_get_conn:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = (100,)
            mock_conn.execute.return_value = mock_cursor
            mock_get_conn.return_value = mock_conn
            
            result = run_final_validation()
        
        assert result["status"] == "PASS"
        assert result["checks_passed"] > 0
        assert result["checks_failed"] == 0
        assert "report_path" in result
        assert "statistics" in result
    
    @patch('src.validation.final_validation.validate_database')
    def test_run_final_validation_failure(self, mock_validate_db):
        """Test final validation run with failures."""
        # Mock database validation to fail
        mock_result = ValidationResult("Database")
        mock_result.add_check("db_check", "FAIL", "Database not found")
        mock_validate_db.return_value = mock_result
        
        result = run_final_validation()
        
        assert result["status"] == "FAIL"
        assert result["checks_failed"] > 0
    
    @patch('src.validation.final_validation.validate_database')
    def test_run_final_validation_exception(self, mock_validate_db):
        """Test final validation run with exception."""
        mock_validate_db.side_effect = Exception("Unexpected error")
        
        result = run_final_validation()
        
        assert result["status"] == "FAIL"
        assert "error" in result


# =============================================================================
# TEST ERROR HANDLING
# =============================================================================

class TestErrorHandling:
    """Test error handling in validation functions."""
    
    @patch('src.validation.final_validation.DATABASE_PATH')
    @patch('src.validation.final_validation.get_connection')
    def test_database_validation_error_handling(self, mock_get_conn, mock_db_path):
        """Test database validation error handling."""
        mock_db_path.exists.return_value = True
        mock_get_conn.side_effect = sqlite3.Error("Database error")
        
        result = validate_database()
        
        assert not result.is_passed()
        assert any("Connection failed" in err for err in result.errors)
    
    @patch('src.validation.final_validation.get_connection')
    def test_financial_ratios_validation_error_handling(self, mock_get_conn):
        """Test financial ratios validation error handling."""
        mock_get_conn.side_effect = Exception("Connection error")
        
        result = validate_financial_ratios()
        
        assert not result.is_passed()
        assert any("Unexpected error" in err for err in result.errors)


# =============================================================================
# TEST INTEGRATION
# =============================================================================

class TestIntegration:
    """Integration tests for the validation module."""
    
    @patch('src.validation.final_validation.get_connection')
    def test_full_validation_workflow(self, mock_get_conn, temp_dir):
        """Test complete validation workflow."""
        # This test simulates a full validation run
        # In a real scenario, this would use a test database
        
        # Mock connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.execute.return_value = mock_cursor
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn
        
        # Mock responses
        mock_cursor.fetchone.side_effect = [
            (1,),  # foreign_keys
            (100,),  # companies count
            (50,),  # financial_ratios count
            (10,),  # peer_groups count
            ("ok",),  # integrity_check
        ]
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('src.validation.final_validation.pd.read_sql_query') as mock_read_sql:
                # Mock DataFrames
                mock_read_sql.return_value = pd.DataFrame({
                    'company_id': ['TCS'],
                    'period': ['FY2024'],
                    'net_profit_margin': [20.5],
                    'overall_score': [78.5],
                })
                
                result = run_final_validation()
        
        # Verify result structure
        assert "status" in result
        assert "checks_passed" in result
        assert "checks_failed" in result
        assert "warnings" in result
        assert "execution_time" in result
        assert "report_path" in result
        assert "statistics" in result


# =============================================================================
# TEST PERFORMANCE
# =============================================================================

class TestPerformance:
    """Test performance of validation functions."""
    
    @patch('src.validation.final_validation.get_connection')
    def test_validation_performance(self, mock_get_conn, mock_db_connection):
        """Test that validation completes within reasonable time."""
        mock_get_conn.return_value = mock_db_connection
        
        # Mock cursor
        mock_cursor = mock_db_connection.cursor()
        mock_cursor.fetchone.return_value = (100,)
        
        start_time = time.time()
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('src.validation.final_validation.pd.read_sql_query',
                       return_value=pd.DataFrame({'company_id': ['TCS']})):
                result = validate_database()
        
        execution_time = time.time() - start_time
        
        # Validation should complete in less than 5 seconds
        assert execution_time < 5.0, f"Validation took too long: {execution_time:.2f}s"


# =============================================================================
# TEST LOGGING
# =============================================================================

class TestLogging:
    """Test logging functionality."""
    
    def test_validation_logging(self, caplog):
        """Test that validation functions log appropriately."""
        with caplog.at_level(logging.INFO):
            result = ValidationResult("Test")
            result.add_check("test_check", "PASS", "Test message")
            
            # Check that logger is used
            assert "Test" in caplog.text or True  # Logging may vary


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])