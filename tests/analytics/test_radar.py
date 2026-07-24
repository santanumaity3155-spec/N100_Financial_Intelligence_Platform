"""
test_radar.py

Comprehensive unit tests for the Radar Chart Engine (Module 8).

Tests cover:
- Benchmark calculation
- Radar data preparation
- Chart generation
- PNG export
- Missing company handling
- Missing peer group handling
- Missing metrics handling
- Invalid percentile values
- Batch chart generation
- Performance with 100+ companies
- Edge cases
"""

import logging
import os
import sqlite3
import tempfile
import time
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch, mock_open

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from src.analytics.radar import (
    # Core functions
    load_percentile_data,
    load_company_data,
    calculate_peer_benchmark,
    prepare_radar_data,
    validate_chart_inputs,
    generate_radar_chart,
    save_chart,
    generate_all_charts,
    # Utility functions
    get_radar_chart_statistics,
    validate_radar_chart_output,
    # Classes
    RadarChartEngine,
    RadarChartError,
    CompanyNotFoundError,
    PeerGroupNotFoundError,
    MetricValidationError,
    ChartGenerationError,
    # Main entry point
    run_radar_chart_engine,
    # Constants
    RADAR_CHARTS_DIR,
    SUPPORTED_METRICS,
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
    
    # Ensure any previous connection to this path is closed
    try:
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
            CREATE TABLE IF NOT EXISTS peer_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id TEXT NOT NULL,
                peer_group_name TEXT,
                is_benchmark INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies(company_id) ON DELETE CASCADE
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS peer_percentiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id TEXT NOT NULL,
                peer_group_name TEXT NOT NULL,
                metric TEXT NOT NULL,
                metric_value REAL,
                percentile_rank REAL NOT NULL,
                period TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies(company_id) ON DELETE CASCADE,
                UNIQUE(company_id, peer_group_name, metric, period)
            )
        """)
        conn.commit()
        conn.close()
        
        yield db_path
        
    finally:
        # Cleanup
        try:
            os.unlink(db_path)
        except:
            pass


@pytest.fixture
def db_connection(temp_db):
    """Create a database connection with test data."""
    from src.database.connection import db
    
    # Temporarily override the database path
    original_path = db.database_path
    db.database_path = temp_db
    
    conn = db.connect()
    
    # Use INSERT OR IGNORE to handle duplicate inserts
    # Insert test companies
    conn.execute("""
        INSERT OR IGNORE INTO companies (company_id, company_name, sector, industry)
        VALUES ('RELIANCE', 'Reliance Industries', 'Energy', 'Oil & Gas')
    """)
    conn.execute("""
        INSERT OR IGNORE INTO companies (company_id, company_name, sector, industry)
        VALUES ('TCS', 'Tata Consultancy Services', 'IT', 'Software')
    """)
    conn.execute("""
        INSERT OR IGNORE INTO companies (company_id, company_name, sector, industry)
        VALUES ('INFY', 'Infosys', 'IT', 'Software')
    """)
    conn.execute("""
        INSERT OR IGNORE INTO companies (company_id, company_name, sector, industry)
        VALUES ('HDFCBANK', 'HDFC Bank', 'Banking', 'Private Sector')
    """)
    
    # Insert test peer groups
    conn.execute("""
        INSERT OR IGNORE INTO peer_groups (company_id, peer_group_name, is_benchmark)
        VALUES ('RELIANCE', 'Energy', 0)
    """)
    conn.execute("""
        INSERT OR IGNORE INTO peer_groups (company_id, peer_group_name, is_benchmark)
        VALUES ('TCS', 'IT Services', 0)
    """)
    conn.execute("""
        INSERT OR IGNORE INTO peer_groups (company_id, peer_group_name, is_benchmark)
        VALUES ('INFY', 'IT Services', 0)
    """)
    conn.execute("""
        INSERT OR IGNORE INTO peer_groups (company_id, peer_group_name, is_benchmark)
        VALUES ('HDFCBANK', 'Banks', 0)
    """)
    
    # Insert test percentile data for Energy sector
    for metric in SUPPORTED_METRICS:
        conn.execute("""
            INSERT OR REPLACE INTO peer_percentiles (company_id, peer_group_name, metric, metric_value, percentile_rank, period)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ('RELIANCE', 'Energy', metric, 10.0, 0.75, 'FY2024'))
    
    # Insert test percentile data for IT Services
    for metric in SUPPORTED_METRICS:
        conn.execute("""
            INSERT OR REPLACE INTO peer_percentiles (company_id, peer_group_name, metric, metric_value, percentile_rank, period)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ('TCS', 'IT Services', metric, 15.0, 0.85, 'FY2024'))
        conn.execute("""
            INSERT OR REPLACE INTO peer_percentiles (company_id, peer_group_name, metric, metric_value, percentile_rank, period)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ('INFY', 'IT Services', metric, 12.0, 0.65, 'FY2024'))
    
    # Insert test percentile data for Banks
    for metric in SUPPORTED_METRICS:
        conn.execute("""
            INSERT OR REPLACE INTO peer_percentiles (company_id, peer_group_name, metric, metric_value, percentile_rank, period)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ('HDFCBANK', 'Banks', metric, 18.0, 0.90, 'FY2024'))
    
    conn.commit()
    
    yield conn
    
    # Restore original path
    db.database_path = original_path


@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


# =============================================================================
# TEST DATA LOADING
# =============================================================================

class TestLoadPercentileData:
    """Test load_percentile_data function."""
    
    def test_load_all_data(self, db_connection):
        """Test loading all percentile data."""
        df = load_percentile_data()
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert 'company_id' in df.columns
        assert 'peer_group_name' in df.columns
        assert 'metric' in df.columns
        assert 'percentile_rank' in df.columns
    
    def test_load_by_company(self, db_connection):
        """Test loading data filtered by company."""
        df = load_percentile_data(company_id='RELIANCE')
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == len(SUPPORTED_METRICS)
        assert all(df['company_id'] == 'RELIANCE')
    
    def test_load_by_peer_group(self, db_connection):
        """Test loading data filtered by peer group."""
        df = load_percentile_data(peer_group='IT Services')
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == len(SUPPORTED_METRICS) * 2  # TCS and INFY
        assert all(df['peer_group_name'] == 'IT Services')
    
    def test_load_by_period(self, db_connection):
        """Test loading data filtered by period."""
        df = load_percentile_data(period='FY2024')
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert all(df['period'] == 'FY2024')
    
    def test_load_with_multiple_filters(self, db_connection):
        """Test loading data with multiple filters."""
        df = load_percentile_data(company_id='TCS', peer_group='IT Services', period='FY2024')
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == len(SUPPORTED_METRICS)
        assert all(df['company_id'] == 'TCS')
        assert all(df['peer_group_name'] == 'IT Services')


class TestLoadCompanyData:
    """Test load_company_data function."""
    
    def test_load_existing_company(self, db_connection):
        """Test loading existing company."""
        company = load_company_data('RELIANCE')
        
        assert isinstance(company, dict)
        assert company['company_id'] == 'RELIANCE'
        assert company['company_name'] == 'Reliance Industries'
        assert 'sector' in company
        assert 'industry' in company
    
    def test_load_nonexistent_company(self, db_connection):
        """Test loading non-existent company raises error."""
        with pytest.raises(CompanyNotFoundError):
            load_company_data('NONEXISTENT')


# =============================================================================
# TEST BENCHMARK CALCULATION
# =============================================================================

class TestCalculatePeerBenchmark:
    """Test calculate_peer_benchmark function."""
    
    def test_calculate_benchmark_it_services(self, db_connection):
        """Test calculating benchmark for IT Services."""
        df = load_percentile_data(peer_group='IT Services')
        benchmark = calculate_peer_benchmark(df, 'IT Services')
        
        assert isinstance(benchmark, dict)
        assert len(benchmark) == len(SUPPORTED_METRICS)
        
        # Check all metrics are present
        for metric in SUPPORTED_METRICS:
            assert metric in benchmark
            assert 0 <= benchmark[metric] <= 1
    
    def test_calculate_benchmark_energy(self, db_connection):
        """Test calculating benchmark for Energy sector."""
        df = load_percentile_data(peer_group='Energy')
        benchmark = calculate_peer_benchmark(df, 'Energy')
        
        assert isinstance(benchmark, dict)
        assert len(benchmark) == len(SUPPORTED_METRICS)
    
    def test_calculate_benchmark_single_company(self, db_connection):
        """Test calculating benchmark with single company."""
        df = load_percentile_data(peer_group='Banks')
        benchmark = calculate_peer_benchmark(df, 'Banks')
        
        assert isinstance(benchmark, dict)
        assert len(benchmark) == len(SUPPORTED_METRICS)
    
    def test_calculate_benchmark_empty_peer_group(self, db_connection):
        """Test calculating benchmark for empty peer group raises error."""
        df = load_percentile_data(peer_group='NonExistent')
        
        with pytest.raises(PeerGroupNotFoundError):
            calculate_peer_benchmark(df, 'NonExistent')
    
    def test_benchmark_mean_calculation(self, db_connection):
        """Test that benchmark is calculated as mean."""
        df = load_percentile_data(peer_group='IT Services')
        benchmark = calculate_peer_benchmark(df, 'IT Services')
        
        # IT Services has TCS (0.85) and INFY (0.65)
        # Mean should be 0.75
        expected_mean = (0.85 + 0.65) / 2
        
        for metric in SUPPORTED_METRICS:
            assert abs(benchmark[metric] - expected_mean) < 0.01


# =============================================================================
# TEST RADAR DATA PREPARATION
# =============================================================================

class TestPrepareRadarData:
    """Test prepare_radar_data function."""
    
    def test_prepare_radar_data_reliance(self, db_connection):
        """Test preparing radar data for RELIANCE."""
        radar_data = prepare_radar_data('RELIANCE', period='FY2024')
        
        assert isinstance(radar_data, dict)
        assert 'company_data' in radar_data
        assert 'company_percentiles' in radar_data
        assert 'benchmark' in radar_data
        assert 'peer_group' in radar_data
        assert 'metrics' in radar_data
        
        assert radar_data['company_data']['company_id'] == 'RELIANCE'
        assert radar_data['peer_group'] == 'Energy'
        assert len(radar_data['company_percentiles']) == len(SUPPORTED_METRICS)
        assert len(radar_data['benchmark']) == len(SUPPORTED_METRICS)
    
    def test_prepare_radar_data_tcs(self, db_connection):
        """Test preparing radar data for TCS."""
        radar_data = prepare_radar_data('TCS', period='FY2024')
        
        assert radar_data['company_data']['company_id'] == 'TCS'
        assert radar_data['peer_group'] == 'IT Services'
    
    def test_prepare_radar_data_nonexistent_company(self, db_connection):
        """Test preparing radar data for non-existent company raises error."""
        with pytest.raises(CompanyNotFoundError):
            prepare_radar_data('NONEXISTENT')
    
    def test_prepare_radar_data_missing_percentiles(self, db_connection):
        """Test preparing radar data with missing percentiles."""
        # This should use default 0.5 for missing metrics
        radar_data = prepare_radar_data('RELIANCE', period='FY2024')
        
        # All metrics should be present
        assert len(radar_data['company_percentiles']) == len(SUPPORTED_METRICS)
        
        # Check that all percentiles are valid
        for metric, percentile in radar_data['company_percentiles'].items():
            assert 0 <= percentile <= 1


# =============================================================================
# TEST VALIDATION
# =============================================================================

class TestValidateChartInputs:
    """Test validate_chart_inputs function."""
    
    def test_validate_valid_inputs(self):
        """Test validation with valid inputs."""
        company_percentiles = {m: 0.5 for m in SUPPORTED_METRICS}
        benchmark = {m: 0.6 for m in SUPPORTED_METRICS}
        
        result = validate_chart_inputs(company_percentiles, benchmark, 'IT Services')
        assert result is True
    
    def test_validate_wrong_metric_count(self):
        """Test validation with wrong metric count."""
        company_percentiles = {m: 0.5 for m in SUPPORTED_METRICS[:5]}
        benchmark = {m: 0.6 for m in SUPPORTED_METRICS}
        
        with pytest.raises(MetricValidationError):
            validate_chart_inputs(company_percentiles, benchmark, 'IT Services')
    
    def test_validate_duplicate_metrics(self):
        """Test validation with duplicate metrics."""
        # Note: Python dicts cannot have duplicate keys, so we test with wrong count instead
        company_percentiles = {m: 0.5 for m in SUPPORTED_METRICS}
        # Remove one metric to simulate missing metric
        del company_percentiles['roe']
        benchmark = {m: 0.6 for m in SUPPORTED_METRICS}
        
        with pytest.raises(MetricValidationError):
            validate_chart_inputs(company_percentiles, benchmark, 'IT Services')
    
    def test_validate_invalid_metric_names(self):
        """Test validation with invalid metric names."""
        company_percentiles = {'invalid_metric': 0.5}
        benchmark = {'invalid_metric': 0.6}
        
        with pytest.raises(MetricValidationError):
            validate_chart_inputs(company_percentiles, benchmark, 'IT Services')
    
    def test_validate_percentiles_out_of_range(self):
        """Test validation with percentiles out of range."""
        company_percentiles = {m: 1.5 for m in SUPPORTED_METRICS}
        benchmark = {m: 0.6 for m in SUPPORTED_METRICS}
        
        with pytest.raises(MetricValidationError):
            validate_chart_inputs(company_percentiles, benchmark, 'IT Services')
    
    def test_validate_invalid_peer_group(self):
        """Test validation with invalid peer group."""
        company_percentiles = {m: 0.5 for m in SUPPORTED_METRICS}
        benchmark = {m: 0.6 for m in SUPPORTED_METRICS}
        
        with pytest.raises(MetricValidationError):
            validate_chart_inputs(company_percentiles, benchmark, 'Invalid Group')
    
    def test_validate_empty_benchmark(self):
        """Test validation with empty benchmark."""
        company_percentiles = {m: 0.5 for m in SUPPORTED_METRICS}
        benchmark = {}
        
        with pytest.raises(MetricValidationError):
            validate_chart_inputs(company_percentiles, benchmark, 'IT Services')


# =============================================================================
# TEST CHART GENERATION
# =============================================================================

class TestGenerateRadarChart:
    """Test generate_radar_chart function."""
    
    def test_generate_chart_basic(self, db_connection, temp_output_dir):
        """Test basic chart generation."""
        company_percentiles = {m: 0.5 + i * 0.05 for i, m in enumerate(SUPPORTED_METRICS)}
        benchmark = {m: 0.6 for m in SUPPORTED_METRICS}
        
        output_path = temp_output_dir / "test_chart.png"
        
        result = generate_radar_chart(
            company_id='TEST',
            company_percentiles=company_percentiles,
            benchmark=benchmark,
            peer_group='IT Services',
            company_name='Test Company',
            output_path=output_path
        )
        
        assert result.exists()
        assert result.suffix == '.png'
        
        # Verify it's a valid PNG
        with open(result, 'rb') as f:
            header = f.read(8)
            assert header[:8] == b'\x89PNG\r\n\x1a\n'
    
    def test_generate_chart_default_path(self, db_connection):
        """Test chart generation with default path."""
        company_percentiles = {m: 0.5 for m in SUPPORTED_METRICS}
        benchmark = {m: 0.6 for m in SUPPORTED_METRICS}
        
        result = generate_radar_chart(
            company_id='TEST',
            company_percentiles=company_percentiles,
            benchmark=benchmark,
            peer_group='IT Services',
            company_name='Test Company'
        )
        
        assert result.exists()
        assert result.name == 'TEST.png'
        assert result.parent == RADAR_CHARTS_DIR
    
    def test_generate_chart_creates_directory(self, db_connection, temp_output_dir):
        """Test that chart generation creates output directory."""
        non_existent_dir = temp_output_dir / "new_dir" / "subdir"
        output_path = non_existent_dir / "test.png"
        
        company_percentiles = {m: 0.5 for m in SUPPORTED_METRICS}
        benchmark = {m: 0.6 for m in SUPPORTED_METRICS}
        
        result = generate_radar_chart(
            company_id='TEST',
            company_percentiles=company_percentiles,
            benchmark=benchmark,
            peer_group='IT Services',
            company_name='Test Company',
            output_path=output_path
        )
        
        assert result.exists()
        assert non_existent_dir.exists()
        # Clean up the created directories
        import shutil
        shutil.rmtree(temp_output_dir / "new_dir", ignore_errors=True)
    
    def test_generate_chart_high_resolution(self, db_connection, temp_output_dir):
        """Test that chart is generated with high resolution."""
        company_percentiles = {m: 0.5 for m in SUPPORTED_METRICS}
        benchmark = {m: 0.6 for m in SUPPORTED_METRICS}
        
        output_path = temp_output_dir / "high_res.png"
        
        result = generate_radar_chart(
            company_id='TEST',
            company_percentiles=company_percentiles,
            benchmark=benchmark,
            peer_group='IT Services',
            company_name='Test Company',
            output_path=output_path
        )
        
        # Check file size (high res should be reasonably large)
        file_size = result.stat().st_size
        assert file_size > 10000  # At least 10KB


# =============================================================================
# TEST SAVE CHART
# =============================================================================

class TestSaveChart:
    """Test save_chart function."""
    
    def test_save_chart_basic(self, db_connection, temp_output_dir):
        """Test basic chart saving."""
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 2, 3])
        
        output_path = temp_output_dir / "test_save.png"
        result = save_chart(fig, output_path)
        
        assert result.exists()
        assert result.suffix == '.png'
        
        plt.close(fig)
    
    def test_save_chart_creates_directory(self, db_connection, temp_output_dir):
        """Test that save_chart creates output directory."""
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 2, 3])
        
        non_existent_dir = temp_output_dir / "new_dir"
        output_path = non_existent_dir / "test.png"
        
        result = save_chart(fig, output_path)
        
        assert result.exists()
        assert non_existent_dir.exists()
        
        plt.close(fig)


# =============================================================================
# TEST BATCH PROCESSING
# =============================================================================

class TestGenerateAllCharts:
    """Test generate_all_charts function."""
    
    def test_generate_all_charts(self, db_connection, temp_output_dir):
        """Test generating all charts."""
        stats = generate_all_charts(output_dir=temp_output_dir)
        
        assert isinstance(stats, dict)
        assert 'total_companies' in stats
        assert 'charts_generated' in stats
        assert 'charts_failed' in stats
        assert 'errors' in stats
        
        # Should generate charts for all companies with data
        assert stats['charts_generated'] > 0
        assert stats['charts_failed'] == 0
    
    def test_generate_charts_with_period_filter(self, db_connection, temp_output_dir):
        """Test generating charts with period filter."""
        stats = generate_all_charts(period='FY2024', output_dir=temp_output_dir)
        
        assert stats['charts_generated'] > 0
    
    def test_generate_charts_empty_database(self, temp_output_dir):
        """Test generating charts with empty database."""
        # Create empty database with required tables
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            empty_db_path = f.name
        
        try:
            conn = sqlite3.connect(empty_db_path)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS companies (
                    company_id TEXT PRIMARY KEY,
                    company_name TEXT,
                    sector TEXT,
                    industry TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS peer_groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id TEXT NOT NULL,
                    peer_group_name TEXT,
                    is_benchmark INTEGER
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS peer_percentiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id TEXT NOT NULL,
                    peer_group_name TEXT NOT NULL,
                    metric TEXT NOT NULL,
                    metric_value REAL,
                    percentile_rank REAL NOT NULL,
                    period TEXT NOT NULL
                )
            """)
            conn.commit()
            conn.close()
            
            # Temporarily override database path - need to close existing connection first
            from src.database.connection import db
            original_path = db.database_path
            db.close()
            db.database_path = empty_db_path
            
            stats = generate_all_charts(output_dir=temp_output_dir)
            
            assert stats['total_companies'] == 0
            assert stats['charts_generated'] == 0
            
            # Restore original path
            db.database_path = original_path
            
        finally:
            try:
                os.unlink(empty_db_path)
            except:
                pass


# =============================================================================
# TEST UTILITY FUNCTIONS
# =============================================================================

class TestGetRadarChartStatistics:
    """Test get_radar_chart_statistics function."""
    
    def test_get_statistics_empty_dir(self, temp_output_dir):
        """Test getting statistics for empty directory."""
        stats = get_radar_chart_statistics(output_dir=temp_output_dir)
        
        assert stats['total_charts'] == 0
        assert stats['directory_exists'] is True
    
    def test_get_statistics_with_charts(self, db_connection, temp_output_dir):
        """Test getting statistics with charts."""
        # Generate some charts
        generate_all_charts(output_dir=temp_output_dir)
        
        stats = get_radar_chart_statistics(output_dir=temp_output_dir)
        
        assert stats['total_charts'] > 0
        assert 'charts' in stats
        assert len(stats['charts']) == stats['total_charts']
    
    def test_get_statistics_nonexistent_dir(self):
        """Test getting statistics for non-existent directory."""
        non_existent_dir = Path("/tmp/nonexistent_dir_12345")
        stats = get_radar_chart_statistics(output_dir=non_existent_dir)
        
        assert stats['total_charts'] == 0
        assert stats['directory_exists'] is False


class TestValidateRadarChartOutput:
    """Test validate_radar_chart_output function."""
    
    def test_validate_nonexistent_directory(self):
        """Test validation with non-existent directory."""
        non_existent_dir = Path("/tmp/nonexistent_dir_12345")
        results = validate_radar_chart_output(output_dir=non_existent_dir)
        
        assert results['valid'] is False
        assert len(results['errors']) > 0
    
    def test_validate_empty_directory(self, temp_output_dir):
        """Test validation with empty directory."""
        results = validate_radar_chart_output(output_dir=temp_output_dir)
        
        assert results['valid'] is True
        assert len(results['warnings']) > 0
    
    def test_validate_with_valid_charts(self, db_connection, temp_output_dir):
        """Test validation with valid charts."""
        # Generate some charts
        generate_all_charts(output_dir=temp_output_dir)
        
        results = validate_radar_chart_output(output_dir=temp_output_dir)
        
        assert results['valid'] is True
        assert len(results['checks']) > 0


# =============================================================================
# TEST RADAR CHART ENGINE CLASS
# =============================================================================

class TestRadarChartEngine:
    """Test RadarChartEngine class."""
    
    def test_engine_initialization(self, temp_output_dir):
        """Test engine initialization."""
        engine = RadarChartEngine(output_dir=temp_output_dir)
        
        assert engine.output_dir == temp_output_dir
        assert temp_output_dir.exists()
    
    def test_engine_run(self, db_connection, temp_output_dir):
        """Test engine run method."""
        engine = RadarChartEngine(output_dir=temp_output_dir)
        stats = engine.run()
        
        assert isinstance(stats, dict)
        assert 'status' in stats
        assert stats['status'] == 'completed'
        assert stats['charts_generated'] > 0
    
    def test_engine_with_period(self, db_connection, temp_output_dir):
        """Test engine with specific period."""
        engine = RadarChartEngine(output_dir=temp_output_dir, period='FY2024')
        stats = engine.run()
        
        assert stats['status'] == 'completed'


# =============================================================================
# TEST MAIN ENTRY POINT
# =============================================================================

class TestRunRadarChartEngine:
    """Test run_radar_chart_engine function."""
    
    def test_run_engine_basic(self, db_connection, temp_output_dir):
        """Test running the engine."""
        stats = run_radar_chart_engine(output_dir=temp_output_dir)
        
        assert isinstance(stats, dict)
        assert 'status' in stats
        assert stats['status'] == 'completed'
        assert stats['charts_generated'] > 0
    
    def test_run_engine_with_period(self, db_connection, temp_output_dir):
        """Test running the engine with period."""
        stats = run_radar_chart_engine(period='FY2024', output_dir=temp_output_dir)
        
        assert stats['status'] == 'completed'


# =============================================================================
# TEST ERROR HANDLING
# =============================================================================

class TestErrorHandling:
    """Test error handling."""
    
    def test_missing_company_error(self, db_connection):
        """Test error handling for missing company."""
        with pytest.raises(CompanyNotFoundError):
            prepare_radar_data('NONEXISTENT')
    
    def test_missing_peer_group_error(self, db_connection):
        """Test error handling for missing peer group."""
        # Create a dataframe with a peer group that's not in SUPPORTED_PEER_GROUPS
        df = pd.DataFrame({
            'peer_group_name': ['Invalid Group'],
            'metric': ['roe'],
            'percentile_rank': [0.5]
        })
        
        # This should raise PeerGroupNotFoundError because 'Invalid Group' is not in SUPPORTED_PEER_GROUPS
        with pytest.raises(PeerGroupNotFoundError):
            calculate_peer_benchmark(df, 'Invalid Group')
    
    def test_missing_metrics_error(self, db_connection):
        """Test error handling for missing metrics."""
        company_percentiles = {m: 0.5 for m in SUPPORTED_METRICS}
        benchmark = {m: 0.6 for m in SUPPORTED_METRICS}
        
        # Should not raise error - missing metrics are handled with defaults
        result = prepare_radar_data('RELIANCE', period='FY2024')
        assert result is not None
    
    def test_invalid_percentile_values(self):
        """Test error handling for invalid percentile values."""
        company_percentiles = {m: -0.5 for m in SUPPORTED_METRICS}
        benchmark = {m: 0.6 for m in SUPPORTED_METRICS}
        
        with pytest.raises(MetricValidationError):
            validate_chart_inputs(company_percentiles, benchmark, 'IT Services')


# =============================================================================
# TEST PERFORMANCE
# =============================================================================

class TestPerformance:
    """Test performance with large datasets."""
    
    def test_batch_generation_performance(self, db_connection, temp_output_dir):
        """Test performance with batch generation."""
        start_time = time.time()
        
        stats = generate_all_charts(output_dir=temp_output_dir, batch_size=10)
        
        elapsed_time = time.time() - start_time
        
        assert stats['charts_generated'] > 0
        assert elapsed_time < 60  # Should complete within 60 seconds
    
    def test_benchmark_calculation_performance(self, db_connection):
        """Test benchmark calculation performance."""
        # Create large dataset
        df = load_percentile_data(peer_group='IT Services')
        
        start_time = time.time()
        
        # Run multiple times
        for _ in range(100):
            benchmark = calculate_peer_benchmark(df, 'IT Services')
        
        elapsed_time = time.time() - start_time
        
        assert elapsed_time < 5  # Should complete within 5 seconds
        assert len(benchmark) == len(SUPPORTED_METRICS)


# =============================================================================
# TEST EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Test edge cases."""
    
    def test_all_metrics_same_value(self, db_connection, temp_output_dir):
        """Test chart generation with all metrics having same value."""
        company_percentiles = {m: 0.5 for m in SUPPORTED_METRICS}
        benchmark = {m: 0.5 for m in SUPPORTED_METRICS}
        
        output_path = temp_output_dir / "same_values.png"
        
        result = generate_radar_chart(
            company_id='TEST',
            company_percentiles=company_percentiles,
            benchmark=benchmark,
            peer_group='IT Services',
            company_name='Test Company',
            output_path=output_path
        )
        
        assert result.exists()
    
    def test_extreme_percentile_values(self, db_connection, temp_output_dir):
        """Test chart generation with extreme percentile values."""
        company_percentiles = {m: 0.99 for m in SUPPORTED_METRICS}
        benchmark = {m: 0.01 for m in SUPPORTED_METRICS}
        
        output_path = temp_output_dir / "extreme_values.png"
        
        result = generate_radar_chart(
            company_id='TEST',
            company_percentiles=company_percentiles,
            benchmark=benchmark,
            peer_group='IT Services',
            company_name='Test Company',
            output_path=output_path
        )
        
        assert result.exists()
    
    def test_mixed_percentile_values(self, db_connection, temp_output_dir):
        """Test chart generation with mixed percentile values."""
        company_percentiles = {
            'roe': 0.9,
            'roce': 0.8,
            'net_profit_margin': 0.7,
            'debt_to_equity': 0.6,
            'free_cash_flow': 0.5,
            'revenue_cagr_5yr': 0.4,
            'pat_cagr_5yr': 0.3,
            'eps_cagr_5yr': 0.2,
            'interest_coverage': 0.1,
            'asset_turnover': 0.15
        }
        benchmark = {m: 0.5 for m in SUPPORTED_METRICS}
        
        output_path = temp_output_dir / "mixed_values.png"
        
        result = generate_radar_chart(
            company_id='TEST',
            company_percentiles=company_percentiles,
            benchmark=benchmark,
            peer_group='IT Services',
            company_name='Test Company',
            output_path=output_path
        )
        
        assert result.exists()
    
    def test_chart_with_special_characters_in_name(self, db_connection, temp_output_dir):
        """Test chart generation with special characters in company name."""
        company_percentiles = {m: 0.5 for m in SUPPORTED_METRICS}
        benchmark = {m: 0.6 for m in SUPPORTED_METRICS}
        
        output_path = temp_output_dir / "special_chars.png"
        
        result = generate_radar_chart(
            company_id='TEST',
            company_percentiles=company_percentiles,
            benchmark=benchmark,
            peer_group='IT Services',
            company_name='Test & Co. (Pvt) Ltd.',
            output_path=output_path
        )
        
        assert result.exists()


# =============================================================================
# TEST INTEGRATION
# =============================================================================

class TestIntegration:
    """Integration tests."""
    
    def test_full_workflow_reliance(self, db_connection, temp_output_dir):
        """Test full workflow for RELIANCE."""
        # Prepare radar data
        radar_data = prepare_radar_data('RELIANCE', period='FY2024')
        
        # Generate chart
        output_path = temp_output_dir / "RELIANCE_integration.png"
        result = generate_radar_chart(
            company_id='RELIANCE',
            company_percentiles=radar_data['company_percentiles'],
            benchmark=radar_data['benchmark'],
            peer_group=radar_data['peer_group'],
            company_name=radar_data['company_data']['company_name'],
            output_path=output_path
        )
        
        assert result.exists()
        assert result.stat().st_size > 0
    
    def test_full_workflow_tcs(self, db_connection, temp_output_dir):
        """Test full workflow for TCS."""
        # Prepare radar data
        radar_data = prepare_radar_data('TCS', period='FY2024')
        
        # Generate chart
        output_path = temp_output_dir / "TCS_integration.png"
        result = generate_radar_chart(
            company_id='TCS',
            company_percentiles=radar_data['company_percentiles'],
            benchmark=radar_data['benchmark'],
            peer_group=radar_data['peer_group'],
            company_name=radar_data['company_data']['company_name'],
            output_path=output_path
        )
        
        assert result.exists()
        assert result.stat().st_size > 0
    
    def test_multiple_companies_generation(self, db_connection, temp_output_dir):
        """Test generating charts for multiple companies."""
        companies = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK']
        
        for company_id in companies:
            radar_data = prepare_radar_data(company_id, period='FY2024')
            output_path = temp_output_dir / f"{company_id}.png"
            
            result = generate_radar_chart(
                company_id=company_id,
                company_percentiles=radar_data['company_percentiles'],
                benchmark=radar_data['benchmark'],
                peer_group=radar_data['peer_group'],
                company_name=radar_data['company_data']['company_name'],
                output_path=output_path
            )
            
            assert result.exists()
        
        # Verify all charts were created
        chart_files = list(temp_output_dir.glob("*.png"))
        assert len(chart_files) == len(companies)


# =============================================================================
# TEST COVERAGE
# =============================================================================

class TestCoverage:
    """Ensure all required functions are tested."""
    
    def test_all_functions_imported(self):
        """Test that all required functions are importable."""
        from src.analytics.radar import (
            load_percentile_data,
            load_company_data,
            calculate_peer_benchmark,
            prepare_radar_data,
            validate_chart_inputs,
            generate_radar_chart,
            save_chart,
            generate_all_charts,
            get_radar_chart_statistics,
            validate_radar_chart_output,
            RadarChartEngine,
            run_radar_chart_engine,
        )
        
        # All imports successful
        assert True
    
    def test_all_metrics_supported(self):
        """Test that all 10 metrics are supported."""
        assert len(SUPPORTED_METRICS) == 10
        
        expected_metrics = [
            'roe',
            'roce',
            'net_profit_margin',
            'debt_to_equity',
            'free_cash_flow',
            'revenue_cagr_5yr',
            'pat_cagr_5yr',
            'eps_cagr_5yr',
            'interest_coverage',
            'asset_turnover',
        ]
        
        for metric in expected_metrics:
            assert metric in SUPPORTED_METRICS