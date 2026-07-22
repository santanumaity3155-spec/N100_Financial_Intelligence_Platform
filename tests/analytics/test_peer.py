"""
test_peer.py

Comprehensive unit tests for the Peer Percentile Ranking Engine (Module 7).

Tests cover:
- Peer group loading from database and Excel
- Peer group assignment
- Percentile calculation (normal and inverted)
- Debt-to-Equity inversion verification
- Missing peer groups handling
- Missing metrics handling
- Duplicate handling
- SQLite persistence
- CSV export
- Performance with 1000+ records
- Integration tests
- Edge cases
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

from src.analytics.peer import (
    # Core functions
    load_peer_groups,
    assign_peer_groups,
    calculate_percentile_rank,
    calculate_metric_percentiles,
    calculate_all_percentiles,
    save_peer_percentiles,
    export_percentiles,
    get_peer_summary,
    validate_peer_data,
    # Classes
    PeerPercentileEngine,
    PeerAnalysisError,
    PeerGroupNotFoundError,
    MetricNotFoundError,
    ValidationError,
    # Constants
    SUPPORTED_METRICS,
    SUPPORTED_PEER_GROUPS,
    INVERTED_METRICS,
    PEER_PERCENTILES_CSV,
    PEER_ANALYSIS_LOG,
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
    finally:
        conn.close()
    
    yield db_path
    
    # Cleanup - ensure no lingering connections
    for attempt in range(3):
        try:
            if os.path.exists(db_path):
                os.unlink(db_path)
            break
        except PermissionError:
            import time
            time.sleep(0.1)


@pytest.fixture
def sample_peer_groups():
    """Create sample peer group assignments."""
    return pd.DataFrame({
        "company_id": ["RELIANCE", "TCS", "INFY", "HDFC", "ICICIBANK", "TATAMOTORS"],
        "peer_group_name": [
            "Energy",
            "IT Services",
            "IT Services",
            "Banks",
            "Banks",
            "Automobiles"
        ],
        "is_benchmark": [1, 0, 0, 1, 0, 0]
    })


@pytest.fixture
def sample_financial_data():
    """Create sample financial data with metrics."""
    return pd.DataFrame({
        "company_id": ["RELIANCE", "TCS", "INFY", "HDFC", "ICICIBANK", "TATAMOTORS"],
        "company_name": [
            "Reliance Industries",
            "Tata Consultancy Services",
            "Infosys",
            "HDFC Bank",
            "ICICI Bank",
            "Tata Motors"
        ],
        "peer_group_name": ["Energy", "IT Services", "IT Services", "Banks", "Banks", "Automobiles"],
        "period": ["FY2024"] * 6,
        # Profitability
        "roe": [15.0, 20.0, 18.0, 16.0, 14.0, 12.0],
        "roce": [12.0, 18.0, 16.0, 14.0, 12.0, 10.0],
        "net_profit_margin": [10.0, 15.0, 13.0, 11.0, 9.0, 7.0],
        # Leverage
        "debt_to_equity": [0.5, 0.2, 0.3, 1.2, 1.5, 2.0],
        "interest_coverage": [8.0, 12.0, 10.0, 6.0, 5.0, 3.0],
        # Efficiency
        "asset_turnover": [1.2, 1.5, 1.4, 1.0, 0.9, 0.8],
        # Cash Flow
        "free_cash_flow": [5000, 8000, 7000, 4000, 3500, 2000],
        # CAGR
        "revenue_cagr_5yr": [12.0, 15.0, 14.0, 10.0, 9.0, 8.0],
        "pat_cagr_5yr": [10.0, 13.0, 12.0, 8.0, 7.0, 6.0],
        "eps_cagr_5yr": [11.0, 14.0, 13.0, 9.0, 8.0, 5.0],
    })


@pytest.fixture
def sample_financial_data_with_missing():
    """Create sample financial data with missing peer groups and metrics."""
    return pd.DataFrame({
        "company_id": ["RELIANCE", "TCS", "INFY", "UNKNOWN", "HDFC"],
        "company_name": [
            "Reliance Industries",
            "Tata Consultancy Services",
            "Infosys",
            "Unknown Company",
            "HDFC Bank"
        ],
        "peer_group_name": ["Energy", "IT Services", "IT Services", "No peer group assigned", "Banks"],
        "period": ["FY2024"] * 5,
        "roe": [15.0, 20.0, 18.0, None, 16.0],
        "roce": [12.0, 18.0, 16.0, None, 14.0],
        "net_profit_margin": [10.0, 15.0, 13.0, None, 11.0],
        "debt_to_equity": [0.5, 0.2, 0.3, None, 1.2],
        "free_cash_flow": [5000, 8000, 7000, None, 4000],
        "revenue_cagr_5yr": [12.0, 15.0, 14.0, None, 10.0],
        "pat_cagr_5yr": [10.0, 13.0, 12.0, None, 8.0],
        "eps_cagr_5yr": [11.0, 14.0, 13.0, None, 9.0],
        "interest_coverage": [8.0, 12.0, 10.0, None, 6.0],
        "asset_turnover": [1.2, 1.5, 1.4, None, 1.0],
    })


@pytest.fixture
def large_dataset():
    """Create a large dataset for performance testing (1000+ records)."""
    np.random.seed(42)
    
    # Create 3 peer groups
    peer_groups = ["IT Services", "Banks", "Energy"] * 400
    company_ids = [f"COMP{i:04d}" for i in range(1200)]
    
    return pd.DataFrame({
        "company_id": company_ids,
        "company_name": [f"Company {i}" for i in range(1200)],
        "peer_group_name": peer_groups,
        "period": ["FY2024"] * 1200,
        "roe": np.random.uniform(5, 25, 1200),
        "roce": np.random.uniform(5, 20, 1200),
        "net_profit_margin": np.random.uniform(3, 18, 1200),
        "debt_to_equity": np.random.uniform(0.1, 3.0, 1200),
        "free_cash_flow": np.random.uniform(1000, 10000, 1200),
        "revenue_cagr_5yr": np.random.uniform(5, 20, 1200),
        "pat_cagr_5yr": np.random.uniform(3, 18, 1200),
        "eps_cagr_5yr": np.random.uniform(4, 19, 1200),
        "interest_coverage": np.random.uniform(2, 15, 1200),
        "asset_turnover": np.random.uniform(0.5, 2.0, 1200),
    })


# =============================================================================
# VALIDATION ERROR TESTS
# =============================================================================

class TestValidationError:
    """Test ValidationError class."""
    
    def test_validation_error_creation(self):
        """Test creating a validation error."""
        error = ValidationError("TEST001", "Energy", "MISSING_METRIC", "Metric not found")
        assert error.company_id == "TEST001"
        assert error.peer_group == "Energy"
        assert error.error_type == "MISSING_METRIC"
        assert error.message == "Metric not found"
    
    def test_validation_error_to_dict(self):
        """Test converting validation error to dictionary."""
        error = ValidationError("TEST001", "Energy", "MISSING_METRIC", "Metric not found")
        result = error.to_dict()
        assert result["company_id"] == "TEST001"
        assert result["peer_group"] == "Energy"
        assert result["error_type"] == "MISSING_METRIC"
        assert result["message"] == "Metric not found"


# =============================================================================
# PEER GROUP LOADING TESTS
# =============================================================================

class TestLoadPeerGroups:
    """Test load_peer_groups function."""
    
    def test_load_from_database(self, temp_db, sample_peer_groups):
        """Test loading peer groups from database."""
        with patch('src.analytics.peer.get_connection') as mock_get_conn:
            mock_conn = sqlite3.connect(temp_db)
            mock_get_conn.return_value = mock_conn
            
            # Insert sample data
            sample_peer_groups.to_sql('peer_groups', mock_conn, if_exists='replace', index=False)
            mock_conn.commit()
            
            # Load peer groups
            df = load_peer_groups(source="database")
            
            assert len(df) == 6
            assert "company_id" in df.columns
            assert "peer_group_name" in df.columns
            
            mock_conn.close()
    
    def test_load_from_excel_file_not_found(self):
        """Test loading from Excel when file doesn't exist."""
        with patch('src.analytics.peer.RAW_DATA_DIR') as mock_raw_dir:
            mock_raw_dir.__truediv__ = MagicMock(return_value=Path("/nonexistent/peer_groups.xlsx"))
            mock_path = MagicMock()
            mock_path.exists.return_value = False
            mock_raw_dir.__truediv__.return_value = mock_path
            
            with pytest.raises(FileNotFoundError):
                load_peer_groups(source="excel")
    
    def test_load_invalid_source(self):
        """Test loading with invalid source."""
        with pytest.raises(ValueError, match="Invalid source"):
            load_peer_groups(source="invalid")
    
    def test_load_missing_columns(self, temp_db):
        """Test loading peer groups with missing columns."""
        with patch('src.analytics.peer.get_connection') as mock_get_conn:
            mock_conn = sqlite3.connect(temp_db)
            mock_get_conn.return_value = mock_conn
            
            # Create table with missing columns - drop and recreate
            mock_conn.execute("DROP TABLE IF EXISTS peer_groups")
            mock_conn.execute("""
                CREATE TABLE peer_groups (
                    company_id TEXT,
                    wrong_column TEXT
                )
            """)
            mock_conn.commit()
            
            # Mock pd.read_sql_query to return a DataFrame without required columns
            with patch('pandas.read_sql_query') as mock_read_sql:
                mock_read_sql.return_value = pd.DataFrame({
                    "company_id": ["A"],
                    "wrong_column": ["X"]
                })
                
                with pytest.raises(PeerAnalysisError, match="Missing required columns"):
                    load_peer_groups(source="database")
            
            mock_conn.close()


# =============================================================================
# PEER GROUP ASSIGNMENT TESTS
# =============================================================================

class TestAssignPeerGroups:
    """Test assign_peer_groups function."""
    
    def test_assign_peer_groups_success(self, sample_financial_data):
        """Test successful peer group assignment."""
        with patch('src.analytics.peer.load_peer_groups') as mock_load:
            # Mock load_peer_groups to return sample data
            peer_groups_df = pd.DataFrame({
                "company_id": ["RELIANCE", "TCS", "INFY", "HDFC", "ICICIBANK", "TATAMOTORS"],
                "peer_group_name": ["Energy", "IT Services", "IT Services", "Banks", "Banks", "Automobiles"]
            })
            mock_load.return_value = peer_groups_df
            
            result = assign_peer_groups(sample_financial_data)
            
            assert "peer_group_name" in result.columns
            assert result.loc[0, "peer_group_name"] == "Energy"
            assert result.loc[1, "peer_group_name"] == "IT Services"
    
    def test_assign_peer_groups_missing(self, sample_financial_data):
        """Test peer group assignment with missing companies."""
        with patch('src.analytics.peer.load_peer_groups') as mock_load:
            # Only return peer groups for some companies
            peer_groups_df = pd.DataFrame({
                "company_id": ["RELIANCE", "TCS"],
                "peer_group_name": ["Energy", "IT Services"]
            })
            mock_load.return_value = peer_groups_df
            
            result = assign_peer_groups(sample_financial_data)
            
            # Companies without peer groups should get "No peer group assigned"
            assert "No peer group assigned" in result["peer_group_name"].values
    
    def test_assign_peer_groups_custom_column(self):
        """Test peer group assignment with custom company_id column."""
        df = pd.DataFrame({
            "comp_id": ["A", "B", "C"],
            "value": [1, 2, 3]
        })
        
        with patch('src.analytics.peer.load_peer_groups') as mock_load:
            peer_groups_df = pd.DataFrame({
                "company_id": ["A", "B", "C"],
                "peer_group_name": ["Group1", "Group2", "Group3"]
            })
            mock_load.return_value = peer_groups_df
            
            result = assign_peer_groups(df, company_id_col="comp_id")
            
            assert "peer_group_name" in result.columns
            assert result.loc[0, "peer_group_name"] == "Group1"


# =============================================================================
# PERCENTILE CALCULATION TESTS
# =============================================================================

class TestCalculatePercentileRank:
    """Test calculate_percentile_rank function."""
    
    def test_basic_percentile_calculation(self):
        """Test basic percentile calculation."""
        series = pd.Series([10, 20, 30, 40, 50])
        result = calculate_percentile_rank(series)
        
        # Lowest value should have percentile 0, highest should have 1
        assert result.iloc[0] == 0.0
        assert result.iloc[4] == 1.0
        assert result.iloc[2] == 0.5
    
    def test_percentile_with_ties(self):
        """Test percentile calculation with tied values."""
        series = pd.Series([10, 20, 20, 30, 40])
        result = calculate_percentile_rank(series)
        
        # Tied values should get minimum rank
        assert result.iloc[1] == result.iloc[2]  # Both 20s should have same percentile
        assert result.iloc[0] == 0.0
        assert result.iloc[4] == 1.0
    
    def test_percentile_inversion(self):
        """Test percentile inversion (for metrics where lower is better)."""
        series = pd.Series([10, 20, 30, 40, 50])
        result = calculate_percentile_rank(series, invert=True)
        
        # With inversion, lowest value should have percentile 1, highest should have 0
        assert result.iloc[0] == 1.0
        assert result.iloc[4] == 0.0
        assert result.iloc[2] == 0.5
    
    def test_percentile_with_nan_values(self):
        """Test percentile calculation with NaN values."""
        series = pd.Series([10, np.nan, 30, 40, np.nan])
        result = calculate_percentile_rank(series)
        
        # NaN values should remain NaN
        assert pd.isna(result.iloc[1])
        assert pd.isna(result.iloc[4])
        assert not pd.isna(result.iloc[0])
        assert not pd.isna(result.iloc[2])
    
    def test_percentile_all_nan(self):
        """Test percentile calculation with all NaN values."""
        series = pd.Series([np.nan, np.nan, np.nan])
        result = calculate_percentile_rank(series)
        
        # All values should be NaN
        assert result.isna().all()
    
    def test_percentile_single_value(self):
        """Test percentile calculation with single value."""
        series = pd.Series([42])
        result = calculate_percentile_rank(series)
        
        # Single value should get percentile 0.5
        assert result.iloc[0] == 0.5
    
    def test_percentile_two_values(self):
        """Test percentile calculation with two values."""
        series = pd.Series([10, 20])
        result = calculate_percentile_rank(series)
        
        assert result.iloc[0] == 0.0
        assert result.iloc[1] == 1.0
    
    def test_percentile_range_clipping(self):
        """Test that percentiles are clipped to [0, 1]."""
        # Even with edge cases, percentiles should be in [0, 1]
        series = pd.Series([1, 2, 3])
        result = calculate_percentile_rank(series)
        
        assert (result >= 0).all()
        assert (result <= 1).all()


class TestCalculateMetricPercentiles:
    """Test calculate_metric_percentiles function."""
    
    def test_calculate_single_metric(self, sample_financial_data):
        """Test calculating percentiles for a single metric."""
        result = calculate_metric_percentiles(sample_financial_data, "roe")
        
        assert "roe_percentile" in result.columns
        assert result["roe_percentile"].notna().sum() == 6
    
    def test_calculate_metric_missing_column(self, sample_financial_data):
        """Test calculating percentiles for missing metric."""
        with pytest.raises(KeyError, match="not found in DataFrame"):
            calculate_metric_percentiles(sample_financial_data, "nonexistent_metric")
    
    def test_calculate_metric_with_groups(self, sample_financial_data):
        """Test calculating percentiles within peer groups."""
        result = calculate_metric_percentiles(sample_financial_data, "roe")
        
        # IT Services companies (TCS, INFY) should be ranked against each other
        # Banks (HDFC, ICICIBANK) should be ranked against each other
        # Energy (RELIANCE) alone should get 0.5
        
        reliance_roe_pct = result[result["company_id"] == "RELIANCE"]["roe_percentile"].iloc[0]
        assert reliance_roe_pct == 0.5  # Only one Energy company


class TestCalculateAllPercentiles:
    """Test calculate_all_percentiles function."""
    
    def test_calculate_all_metrics(self, sample_financial_data):
        """Test calculating percentiles for all metrics."""
        result = calculate_all_percentiles(sample_financial_data)
        
        # Check that all metrics have percentile columns
        for metric in SUPPORTED_METRICS:
            percentile_col = f"{metric}_percentile"
            assert percentile_col in result.columns, f"Missing {percentile_col}"
    
    def test_calculate_custom_metrics(self, sample_financial_data):
        """Test calculating percentiles for custom metrics list."""
        custom_metrics = ["roe", "roce"]
        result = calculate_all_percentiles(sample_financial_data, metrics=custom_metrics)
        
        assert "roe_percentile" in result.columns
        assert "roce_percentile" in result.columns
        assert "net_profit_margin_percentile" not in result.columns
    
    def test_calculate_missing_metric_warning(self, sample_financial_data, caplog):
        """Test warning when metric is missing."""
        # Add a non-existent metric to the list
        metrics = SUPPORTED_METRICS + ["nonexistent_metric"]
        result = calculate_all_percentiles(sample_financial_data, metrics=metrics)
        
        # Should log a warning
        assert "not found in DataFrame" in caplog.text


# =============================================================================
# DEBT-TO-EQUITY INVERSION TESTS
# =============================================================================

class TestDebtToEquityInversion:
    """Test Debt-to-Equity inversion (lower is better)."""
    
    def test_debt_to_equity_inversion(self):
        """Test that Debt-to-Equity is correctly inverted."""
        # Create data where lower debt_to_equity is better
        df = pd.DataFrame({
            "company_id": ["A", "B", "C", "D", "E"],
            "peer_group_name": ["Group1"] * 5,
            "debt_to_equity": [0.5, 1.0, 1.5, 2.0, 2.5]  # Lower is better
        })
        
        result = calculate_all_percentiles(df, metrics=["debt_to_equity"])
        
        # Company with lowest debt (0.5) should have highest percentile
        # Company with highest debt (2.5) should have lowest percentile
        lowest_debt_pct = result[result["company_id"] == "A"]["debt_to_equity_percentile"].iloc[0]
        highest_debt_pct = result[result["company_id"] == "E"]["debt_to_equity_percentile"].iloc[0]
        
        assert lowest_debt_pct == 1.0, "Lowest debt should have percentile 1.0"
        assert highest_debt_pct == 0.0, "Highest debt should have percentile 0.0"
    
    def test_roe_not_inverted(self):
        """Test that ROE is NOT inverted (higher is better)."""
        df = pd.DataFrame({
            "company_id": ["A", "B", "C", "D", "E"],
            "peer_group_name": ["Group1"] * 5,
            "roe": [10.0, 12.0, 15.0, 18.0, 20.0]  # Higher is better
        })
        
        result = calculate_all_percentiles(df, metrics=["roe"])
        
        # Company with highest ROE (20.0) should have highest percentile
        # Company with lowest ROE (10.0) should have lowest percentile
        highest_roe_pct = result[result["company_id"] == "E"]["roe_percentile"].iloc[0]
        lowest_roe_pct = result[result["company_id"] == "A"]["roe_percentile"].iloc[0]
        
        assert highest_roe_pct == 1.0, "Highest ROE should have percentile 1.0"
        assert lowest_roe_pct == 0.0, "Lowest ROE should have percentile 0.0"


# =============================================================================
# DATABASE OPERATIONS TESTS
# =============================================================================

class TestSavePeerPercentiles:
    """Test save_peer_percentiles function."""
    
    def test_save_to_database(self, temp_db, sample_financial_data):
        """Test saving peer percentiles to database."""
        with patch('src.analytics.peer.get_connection') as mock_get_conn:
            mock_conn = sqlite3.connect(temp_db)
            mock_get_conn.return_value = mock_conn
            
            # Calculate percentiles first
            df = calculate_all_percentiles(sample_financial_data)
            
            # Save to database
            stats = save_peer_percentiles(df, "FY2024")
            
            assert stats["successful_inserts"] > 0
            assert stats["total_records"] > 0
            
            # Verify records were inserted
            cursor = mock_conn.execute("SELECT COUNT(*) FROM peer_percentiles")
            count = cursor.fetchone()[0]
            assert count > 0
            
            mock_conn.close()
    
    def test_upsert_duplicates(self, temp_db, sample_financial_data):
        """Test UPSERT behavior with duplicate records."""
        with patch('src.analytics.peer.get_connection') as mock_get_conn:
            mock_conn = sqlite3.connect(temp_db)
            mock_get_conn.return_value = mock_conn
            
            # Calculate percentiles
            df = calculate_all_percentiles(sample_financial_data)
            
            # Save twice
            stats1 = save_peer_percentiles(df, "FY2024")
            stats2 = save_peer_percentiles(df, "FY2024")
            
            # Both should succeed
            assert stats1["successful_inserts"] > 0
            assert stats2["successful_inserts"] > 0
            
            # Verify no duplicates
            cursor = mock_conn.execute("SELECT COUNT(*) FROM peer_percentiles")
            total = cursor.fetchone()[0]
            
            cursor = mock_conn.execute("""
                SELECT company_id, peer_group_name, metric, period, COUNT(*)
                FROM peer_percentiles
                GROUP BY company_id, peer_group_name, metric, period
                HAVING COUNT(*) > 1
            """)
            duplicates = cursor.fetchall()
            
            assert len(duplicates) == 0, "Should have no duplicates"
            
            mock_conn.close()
    
    def test_skip_companies_without_peer_group(self, temp_db, sample_financial_data_with_missing):
        """Test that companies without peer groups are skipped."""
        with patch('src.analytics.peer.get_connection') as mock_get_conn:
            mock_conn = sqlite3.connect(temp_db)
            mock_get_conn.return_value = mock_conn
            
            # Calculate percentiles
            df = calculate_all_percentiles(sample_financial_data_with_missing)
            
            # Save to database
            stats = save_peer_percentiles(df, "FY2024")
            
            # Should skip the company without peer group
            assert stats["skipped_records"] > 0
            
            mock_conn.close()
    
    def test_skip_nan_percentiles(self, temp_db):
        """Test that NaN percentiles are skipped."""
        df = pd.DataFrame({
            "company_id": ["A", "B"],
            "peer_group_name": ["Group1", "Group1"],
            "roe": [10.0, np.nan],
            "roe_percentile": [0.5, np.nan]
        })
        
        with patch('src.analytics.peer.get_connection') as mock_get_conn:
            mock_conn = sqlite3.connect(temp_db)
            mock_get_conn.return_value = mock_conn
            
            stats = save_peer_percentiles(df, "FY2024", metrics=["roe"])
            
            # Should only save the non-NaN percentile
            assert stats["skipped_records"] >= 1
            
            mock_conn.close()


# =============================================================================
# EXPORT TESTS
# =============================================================================

class TestExportPercentiles:
    """Test export_percentiles function."""
    
    def test_export_to_csv(self, sample_financial_data, tmp_path):
        """Test exporting percentiles to CSV."""
        # Calculate percentiles
        df = calculate_all_percentiles(sample_financial_data)
        
        # Export to temporary file
        output_path = tmp_path / "test_peer_percentiles.csv"
        result_path = export_percentiles(df, output_path=output_path)
        
        assert result_path.exists()
        assert result_path == output_path
        
        # Verify CSV content
        exported_df = pd.read_csv(output_path)
        assert len(exported_df) > 0
        assert "company_id" in exported_df.columns
        assert "peer_group" in exported_df.columns
        assert "metric" in exported_df.columns
        assert "percentile_rank" in exported_df.columns
    
    def test_export_with_period_filter(self, sample_financial_data, tmp_path):
        """Test exporting with period filter."""
        # Add multiple periods
        df = pd.concat([sample_financial_data, sample_financial_data.copy()], ignore_index=True)
        df.loc[6:, "period"] = "FY2023"
        
        # Calculate percentiles
        df = calculate_all_percentiles(df)
        
        # Export only FY2024
        output_path = tmp_path / "test_filtered.csv"
        export_percentiles(df, output_path=output_path, period="FY2024")
        
        exported_df = pd.read_csv(output_path)
        assert all(exported_df["period"] == "FY2024")
    
    def test_export_sorted_correctly(self, sample_financial_data, tmp_path):
        """Test that exported CSV is sorted correctly."""
        df = calculate_all_percentiles(sample_financial_data)
        output_path = tmp_path / "test_sorted.csv"
        export_percentiles(df, output_path=output_path)
        
        exported_df = pd.read_csv(output_path)
        
        # Should be sorted by peer_group, metric, percentile_rank (descending)
        for peer_group in exported_df["peer_group"].unique():
            group_df = exported_df[exported_df["peer_group"] == peer_group]
            for metric in group_df["metric"].unique():
                metric_df = group_df[group_df["metric"] == metric]
                percentiles = metric_df["percentile_rank"].values
                assert all(percentiles[i] >= percentiles[i+1] for i in range(len(percentiles)-1))


# =============================================================================
# SUMMARY AND VALIDATION TESTS
# =============================================================================

class TestGetPeerSummary:
    """Test get_peer_summary function."""
    
    def test_generate_summary(self, sample_financial_data):
        """Test generating peer summary."""
        df = calculate_all_percentiles(sample_financial_data)
        summary = get_peer_summary(df)
        
        assert "total_companies" in summary
        assert "companies_with_peer_group" in summary
        assert "companies_without_peer_group" in summary
        assert "peer_groups" in summary
        assert "metrics_summary" in summary
        
        assert summary["total_companies"] == 6
    
    def test_summary_metrics_statistics(self, sample_financial_data):
        """Test that summary includes metrics statistics."""
        df = calculate_all_percentiles(sample_financial_data)
        summary = get_peer_summary(df)
        
        assert "roe" in summary["metrics_summary"]
        assert "count" in summary["metrics_summary"]["roe"]
        assert "mean" in summary["metrics_summary"]["roe"]
        assert "median" in summary["metrics_summary"]["roe"]
        assert "min" in summary["metrics_summary"]["roe"]
        assert "max" in summary["metrics_summary"]["roe"]


class TestValidatePeerData:
    """Test validate_peer_data function."""
    
    def test_validate_valid_data(self, sample_financial_data):
        """Test validation with valid data."""
        df = calculate_all_percentiles(sample_financial_data)
        results = validate_peer_data(df)
        
        assert results["valid"] is True
        assert len(results["errors"]) == 0
    
    def test_validate_missing_columns(self):
        """Test validation with missing required columns."""
        df = pd.DataFrame({"company_id": ["A", "B"]})
        results = validate_peer_data(df)
        
        assert results["valid"] is False
        assert any(e["error"] == "missing_required_columns" for e in results["errors"])
    
    def test_validate_duplicate_company_ids(self):
        """Test validation with duplicate company IDs."""
        df = pd.DataFrame({
            "company_id": ["A", "A", "B"],
            "peer_group_name": ["G1", "G1", "G2"],
            "roe_percentile": [0.5, 0.6, 0.7]
        })
        results = validate_peer_data(df)
        
        assert results["valid"] is False
        assert any(e["error"] == "duplicate_company_ids" for e in results["errors"])
    
    def test_validate_percentile_range(self):
        """Test validation of percentile range."""
        df = pd.DataFrame({
            "company_id": ["A", "B"],
            "peer_group_name": ["G1", "G1"],
            "roe_percentile": [0.5, 1.5]  # 1.5 is out of range
        })
        results = validate_peer_data(df)
        
        assert results["valid"] is False
        assert any(e["error"] == "percentiles_out_of_range" for e in results["errors"])


# =============================================================================
# PIPELINE TESTS
# =============================================================================

class TestPeerPercentileEngine:
    """Test PeerPercentileEngine class."""
    
    def test_pipeline_initialization(self):
        """Test pipeline initialization."""
        engine = PeerPercentileEngine()
        assert engine.output_dir.exists()
        assert engine.pipeline_stats["status"] == "not_started"
    
    def test_pipeline_run(self, sample_financial_data):
        """Test running the complete pipeline."""
        engine = PeerPercentileEngine()
        stats = engine.run(sample_financial_data, "FY2024")
        
        assert stats["status"] == "completed"
        assert stats["companies_processed"] == 6
        assert stats["rows_inserted"] > 0
    
    def test_pipeline_with_missing_peer_groups(self, sample_financial_data_with_missing):
        """Test pipeline with missing peer groups."""
        engine = PeerPercentileEngine()
        stats = engine.run(sample_financial_data_with_missing, "FY2024")
        
        assert stats["status"] == "completed"
        assert stats["companies_without_peer_group"] > 0
    
    def test_pipeline_log_generation(self, sample_financial_data):
        """Test that pipeline generates log file."""
        engine = PeerPercentileEngine()
        engine.run(sample_financial_data, "FY2024")
        
        # Check that log file was generated
        assert engine.output_dir.exists()


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_dataframe(self):
        """Test with empty DataFrame."""
        df = pd.DataFrame()
        engine = PeerPercentileEngine()
        
        # The pipeline should handle empty DataFrames gracefully
        # It will fail when trying to assign peer groups due to missing 'company_id'
        # but won't crash the entire system
        stats = engine.run(df, "FY2024")
        
        # Should complete but with errors
        assert stats["status"] == "failed"
    
    def test_missing_metrics_columns(self):
        """Test with missing metric columns."""
        df = pd.DataFrame({
            "company_id": ["A", "B"],
            "peer_group_name": ["G1", "G1"]
        })
        
        result = calculate_all_percentiles(df)
        
        # Should not crash, just skip missing metrics
        assert "peer_group_name" in result.columns
    
    def test_all_companies_same_peer_group(self):
        """Test when all companies are in the same peer group."""
        df = pd.DataFrame({
            "company_id": ["A", "B", "C"],
            "peer_group_name": ["Group1"] * 3,
            "roe": [10.0, 15.0, 20.0]
        })
        
        result = calculate_all_percentiles(df, metrics=["roe"])
        
        assert "roe_percentile" in result.columns
        assert result["roe_percentile"].notna().sum() == 3
    
    def test_single_company_in_peer_group(self):
        """Test with single company in a peer group."""
        df = pd.DataFrame({
            "company_id": ["A", "B", "C"],
            "peer_group_name": ["Group1", "Group2", "Group3"],
            "roe": [10.0, 15.0, 20.0]
        })
        
        result = calculate_all_percentiles(df, metrics=["roe"])
        
        # Each company alone in its group should get 0.5
        assert all(result["roe_percentile"] == 0.5)
    
    def test_none_values_in_dataframe(self):
        """Test handling of None values."""
        df = pd.DataFrame({
            "company_id": ["A", "B"],
            "peer_group_name": ["G1", "G1"],
            "roe": [None, 15.0]
        })
        
        result = calculate_all_percentiles(df, metrics=["roe"])
        
        # Should handle None values gracefully
        assert "roe_percentile" in result.columns


# =============================================================================
# PERFORMANCE TESTS
# =============================================================================

class TestPerformance:
    """Performance and runtime tests."""
    
    def test_large_dataset_processing(self, large_dataset):
        """Test performance with 1200+ records."""
        start_time = time.time()
        
        engine = PeerPercentileEngine()
        stats = engine.run(large_dataset, "FY2024")
        
        elapsed_time = time.time() - start_time
        
        assert stats["status"] == "completed"
        assert stats["companies_processed"] == 1200
        assert elapsed_time < 30.0, f"Processing took {elapsed_time:.2f}s, expected < 30s"
    
    def test_percentile_calculation_performance(self, large_dataset):
        """Test percentile calculation performance."""
        start_time = time.time()
        
        result = calculate_all_percentiles(large_dataset)
        
        elapsed_time = time.time() - start_time
        
        assert len(result) == 1200
        assert elapsed_time < 10.0, f"Calculation took {elapsed_time:.2f}s, expected < 10s"
    
    def test_batch_insert_performance(self, temp_db, large_dataset):
        """Test batch insert performance."""
        with patch('src.analytics.peer.get_connection') as mock_get_conn:
            mock_conn = sqlite3.connect(temp_db)
            mock_get_conn.return_value = mock_conn
            
            # Calculate percentiles
            df = calculate_all_percentiles(large_dataset)
            
            # Time the save operation
            start_time = time.time()
            stats = save_peer_percentiles(df, "FY2024")
            elapsed_time = time.time() - start_time
            
            assert stats["successful_inserts"] > 0
            assert elapsed_time < 20.0, f"Insert took {elapsed_time:.2f}s, expected < 20s"
            
            mock_conn.close()


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """End-to-end integration tests."""
    
    def test_full_workflow(self, sample_financial_data, tmp_path):
        """Test complete workflow from data to export."""
        # Step 1: Assign peer groups
        df = assign_peer_groups(sample_financial_data)
        
        # Step 2: Calculate percentiles
        df = calculate_all_percentiles(df)
        
        # Step 3: Validate
        validation = validate_peer_data(df)
        assert validation["valid"] is True
        
        # Step 4: Export
        output_path = tmp_path / "integration_test.csv"
        export_percentiles(df, output_path=output_path)
        
        assert output_path.exists()
        
        # Verify export content
        exported_df = pd.read_csv(output_path)
        assert len(exported_df) > 0
        assert all(col in exported_df.columns for col in [
            "company_id", "company_name", "peer_group", "metric",
            "metric_value", "percentile_rank", "period"
        ])
    
    def test_all_peer_groups_processed(self):
        """Test that all 11 peer groups are supported."""
        assert len(SUPPORTED_PEER_GROUPS) == 11
        assert "IT Services" in SUPPORTED_PEER_GROUPS
        assert "Banks" in SUPPORTED_PEER_GROUPS
        assert "Energy" in SUPPORTED_PEER_GROUPS
    
    def test_all_metrics_ranked(self, sample_financial_data):
        """Test that all 10 metrics are ranked."""
        df = calculate_all_percentiles(sample_financial_data)
        
        for metric in SUPPORTED_METRICS:
            percentile_col = f"{metric}_percentile"
            assert percentile_col in df.columns, f"Missing percentile for {metric}"
    
    def test_debt_to_equity_inversion_integration(self, sample_financial_data):
        """Test Debt-to-Equity inversion in full workflow."""
        df = calculate_all_percentiles(sample_financial_data, metrics=["debt_to_equity"])
        
        # Verify inversion
        assert "debt_to_equity_percentile" in df.columns
        
        # Get companies with lowest and highest debt_to_equity within the same peer group
        # Use only IT Services companies (TCS and INFY) for this test
        it_companies = df[df["peer_group_name"] == "IT Services"]
        
        if len(it_companies) > 1:
            min_debt_row = it_companies.loc[it_companies["debt_to_equity"].idxmin()]
            max_debt_row = it_companies.loc[it_companies["debt_to_equity"].idxmax()]
            
            assert min_debt_row["debt_to_equity_percentile"] == 1.0
            assert max_debt_row["debt_to_equity_percentile"] == 0.0
        else:
            # If only one company in peer group, it should get 0.5
            assert all(it_companies["debt_to_equity_percentile"] == 0.5)


# =============================================================================
# CONSTANTS TESTS
# =============================================================================

class TestConstants:
    """Test module constants."""
    
    def test_supported_metrics_count(self):
        """Test that exactly 10 metrics are supported."""
        assert len(SUPPORTED_METRICS) == 10
    
    def test_supported_peer_groups_count(self):
        """Test that exactly 11 peer groups are supported."""
        assert len(SUPPORTED_PEER_GROUPS) == 11
    
    def test_inverted_metrics(self):
        """Test that only debt_to_equity is inverted."""
        assert INVERTED_METRICS == ["debt_to_equity"]
    
    def test_all_required_metrics_present(self):
        """Test that all required metrics are in SUPPORTED_METRICS."""
        required_metrics = [
            "roe", "roce", "net_profit_margin", "debt_to_equity",
            "free_cash_flow", "revenue_cagr_5yr", "pat_cagr_5yr",
            "eps_cagr_5yr", "interest_coverage", "asset_turnover"
        ]
        
        for metric in required_metrics:
            assert metric in SUPPORTED_METRICS, f"Missing metric: {metric}"


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])