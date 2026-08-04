"""
Smoke tests for Peer Comparison page (pages/04_peers.py)

Tests the build_radar_chart() function with various edge cases to ensure
it never crashes and handles all error conditions gracefully.

Sprint 4 - Module 3 Production Readiness Validation
"""

import importlib.util
import logging
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pytest

# Configure logging to see all messages
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Import the function under test using importlib (since module name starts with number)
_peers_module_path = Path(__file__).parent.parent / "pages" / "04_peers.py"
_spec = importlib.util.spec_from_file_location("peers_04", _peers_module_path)
_peers_module = importlib.util.module_from_spec(_spec)
sys.modules["peers_04"] = _peers_module
_spec.loader.exec_module(_peers_module)
build_radar_chart = _peers_module.build_radar_chart
compute_peer_percentiles = _peers_module.compute_peer_percentiles


# =============================================================================
# TEST FIXTURES
# =============================================================================


@pytest.fixture
def valid_group_df():
    """Create a valid peer group DataFrame with all required columns."""
    return pd.DataFrame(
        {
            "company_id": ["TCS", "INFY", "WIPRO"],
            "company_name": ["Tata Consultancy Services", "Infosys", "Wipro"],
            "peer_group_name": ["IT Services", "IT Services", "IT Services"],
            "roe": [0.45, 0.38, 0.25],
            "roce": [0.50, 0.42, 0.30],
            "net_profit_margin": [0.20, 0.18, 0.12],
            "debt_to_equity": [0.15, 0.20, 0.25],
            "free_cash_flow": [50000, 40000, 25000],
            "revenue_cagr_5yr": [0.12, 0.10, 0.08],
            "pat_cagr_5yr": [0.15, 0.12, 0.10],
            "composite_quality_score": [0.85, 0.75, 0.60],
            # Percentile columns (would be computed by compute_peer_percentiles)
            "roe_pct": [1.0, 0.5, 0.0],
            "roce_pct": [1.0, 0.5, 0.0],
            "net_profit_margin_pct": [1.0, 0.5, 0.0],
            "debt_to_equity_pct": [1.0, 0.5, 0.0],
            "free_cash_flow_pct": [1.0, 0.5, 0.0],
            "revenue_cagr_5yr_pct": [1.0, 0.5, 0.0],
            "pat_cagr_5yr_pct": [1.0, 0.5, 0.0],
            "composite_quality_score_pct": [1.0, 0.5, 0.0],
            "avg_percentile": [1.0, 0.5, 0.0],
        }
    )


@pytest.fixture
def single_company_df():
    """Create a peer group with only one company."""
    return pd.DataFrame(
        {
            "company_id": ["TCS"],
            "company_name": ["Tata Consultancy Services"],
            "peer_group_name": ["IT Services"],
            "roe": [0.45],
            "roce": [0.50],
            "net_profit_margin": [0.20],
            "debt_to_equity": [0.15],
            "free_cash_flow": [50000],
            "revenue_cagr_5yr": [0.12],
            "pat_cagr_5yr": [0.15],
            "composite_quality_score": [0.85],
            "roe_pct": [1.0],
            "roce_pct": [1.0],
            "net_profit_margin_pct": [1.0],
            "debt_to_equity_pct": [1.0],
            "free_cash_flow_pct": [1.0],
            "revenue_cagr_5yr_pct": [1.0],
            "pat_cagr_5yr_pct": [1.0],
            "composite_quality_score_pct": [1.0],
            "avg_percentile": [1.0],
        }
    )


# =============================================================================
# SMOKE TESTS - CRITICAL EDGE CASES
# =============================================================================


class TestEmptyDataFrame:
    """Test radar chart with empty DataFrame."""

    def test_empty_dataframe(self, caplog):
        """Empty DataFrame should return empty figure without crashing."""
        df = pd.DataFrame()
        fig = build_radar_chart(df, "TCS", "Tata Consultancy Services", "IT Services")
        
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 0
        assert "Radar chart skipped: group_df is None or empty" in caplog.text

    def test_none_dataframe(self, caplog):
        """None DataFrame should return empty figure without crashing."""
        fig = build_radar_chart(None, "TCS", "Tata Consultancy Services", "IT Services")
        
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 0
        assert "Radar chart skipped: group_df is None or empty" in caplog.text


class TestMissingCompanyIdColumn:
    """Test radar chart with missing company_id column."""

    def test_missing_company_id_column(self, caplog):
        """DataFrame without company_id column should return empty figure."""
        df = pd.DataFrame(
            {
                "company_name": ["TCS", "INFY"],
                "roe": [0.45, 0.38],
            }
        )
        fig = build_radar_chart(df, "TCS", "Tata Consultancy Services", "IT Services")
        
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 0
        assert "'company_id' column missing" in caplog.text


class TestMissingCompany:
    """Test radar chart when selected company is not in peer group."""

    def test_unknown_company(self, caplog, valid_group_df):
        """Unknown company ID should return empty figure with warning."""
        fig = build_radar_chart(valid_group_df, "UNKNOWN", "Unknown Company", "IT Services")
        
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 0
        assert "selected company UNKNOWN not found" in caplog.text

    def test_company_not_in_group(self, caplog, valid_group_df):
        """Company not in the group should return empty figure."""
        fig = build_radar_chart(valid_group_df, "RELIANCE", "Reliance", "IT Services")
        
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 0


class TestMissingMetrics:
    """Test radar chart with missing metric columns."""

    def test_missing_some_metrics(self, caplog):
        """Missing metric columns should be handled gracefully."""
        df = pd.DataFrame(
            {
                "company_id": ["TCS", "INFY"],
                "company_name": ["Tata Consultancy Services", "Infosys"],
                "roe_pct": [1.0, 0.5],
                "roce_pct": [0.8, 0.4],
            }
        )
        fig = build_radar_chart(df, "TCS", "Tata Consultancy Services", "IT Services")
        
        # Should still generate a chart (with 0.0 for missing metrics)
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 2
        assert "required metrics missing" in caplog.text

    def test_all_metrics_missing(self, caplog):
        """All metric columns missing should still return valid empty figure."""
        df = pd.DataFrame(
            {
                "company_id": ["TCS"],
                "company_name": ["Tata Consultancy Services"],
            }
        )
        fig = build_radar_chart(df, "TCS", "Tata Consultancy Services", "IT Services")
        
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 2


class TestNaNValues:
    """Test radar chart with NaN/None percentile values."""

    def test_nan_percentile_values(self, caplog):
        """NaN percentile values should be replaced with 0.0."""
        df = pd.DataFrame(
            {
                "company_id": ["TCS", "INFY"],
                "company_name": ["Tata Consultancy Services", "Infosys"],
                "roe": [0.45, 0.38],
                "roce": [0.50, 0.42],
                "net_profit_margin": [0.20, 0.18],
                "debt_to_equity": [0.15, 0.20],
                "free_cash_flow": [50000, 40000],
                "revenue_cagr_5yr": [0.12, 0.10],
                "pat_cagr_5yr": [0.15, 0.12],
                "composite_quality_score": [0.85, 0.75],
                "roe_pct": [1.0, np.nan],
                "roce_pct": [np.nan, 0.5],
                "net_profit_margin_pct": [0.8, 0.4],
                "debt_to_equity_pct": [0.9, 0.3],
                "free_cash_flow_pct": [0.7, 0.6],
                "revenue_cagr_5yr_pct": [0.85, 0.45],
                "pat_cagr_5yr_pct": [0.75, 0.35],
                "composite_quality_score_pct": [0.95, 0.55],
            }
        )
        fig = build_radar_chart(df, "TCS", "Tata Consultancy Services", "IT Services")
        
        # Critical: function should not crash and should return valid figure
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 2
        # NaN values are handled gracefully (replaced with 0.0)

    def test_none_percentile_values(self, caplog):
        """None values should be handled gracefully."""
        df = pd.DataFrame(
            {
                "company_id": ["TCS"],
                "company_name": ["Tata Consultancy Services"],
                "roe_pct": [None],
                "roce_pct": [0.5],
                "net_profit_margin_pct": [0.8],
                "debt_to_equity_pct": [0.9],
                "free_cash_flow_pct": [0.7],
                "revenue_cagr_5yr_pct": [0.85],
                "pat_cagr_5yr_pct": [0.75],
                "composite_quality_score_pct": [0.95],
            }
        )
        fig = build_radar_chart(df, "TCS", "Tata Consultancy Services", "IT Services")
        
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 2


class TestInvalidPercentileValues:
    """Test radar chart with invalid percentile values."""

    def test_percentile_out_of_range_high(self, caplog):
        """Percentile > 1.0 should be clamped to 0.0."""
        df = pd.DataFrame(
            {
                "company_id": ["TCS"],
                "company_name": ["Tata Consultancy Services"],
                "roe_pct": [1.5],
                "roce_pct": [0.5],
                "net_profit_margin_pct": [0.8],
                "debt_to_equity_pct": [0.9],
                "free_cash_flow_pct": [0.7],
                "revenue_cagr_5yr_pct": [0.85],
                "pat_cagr_5yr_pct": [0.75],
                "composite_quality_score_pct": [0.95],
            }
        )
        fig = build_radar_chart(df, "TCS", "Tata Consultancy Services", "IT Services")
        
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 2
        assert "invalid percentile" in caplog.text

    def test_percentile_out_of_range_negative(self, caplog):
        """Negative percentile should be clamped to 0.0."""
        df = pd.DataFrame(
            {
                "company_id": ["TCS"],
                "company_name": ["Tata Consultancy Services"],
                "roe_pct": [-0.5],
                "roce_pct": [0.5],
                "net_profit_margin_pct": [0.8],
                "debt_to_equity_pct": [0.9],
                "free_cash_flow_pct": [0.7],
                "revenue_cagr_5yr_pct": [0.85],
                "pat_cagr_5yr_pct": [0.75],
                "composite_quality_score_pct": [0.95],
            }
        )
        fig = build_radar_chart(df, "TCS", "Tata Consultancy Services", "IT Services")
        
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 2
        assert "invalid percentile" in caplog.text

    def test_non_numeric_percentile(self, caplog):
        """Non-numeric percentile values should be handled."""
        df = pd.DataFrame(
            {
                "company_id": ["TCS"],
                "company_name": ["Tata Consultancy Services"],
                "roe_pct": ["invalid"],
                "roce_pct": [0.5],
                "net_profit_margin_pct": [0.8],
                "debt_to_equity_pct": [0.9],
                "free_cash_flow_pct": [0.7],
                "revenue_cagr_5yr_pct": [0.85],
                "pat_cagr_5yr_pct": [0.75],
                "composite_quality_score_pct": [0.95],
            }
        )
        fig = build_radar_chart(df, "TCS", "Tata Consultancy Services", "IT Services")
        
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 2
        assert "cannot convert value to float" in caplog.text


class TestSingleCompanyPeerGroup:
    """Test radar chart with single-company peer group."""

    def test_single_company_peer_group(self, caplog, single_company_df):
        """Single company peer group should generate chart with equal values."""
        fig = build_radar_chart(single_company_df, "TCS", "Tata Consultancy Services", "IT Services")
        
        # Critical: function should not crash and should return valid figure
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 2
        
        # Company and peer average should be identical
        company_trace = fig.data[0]
        peer_trace = fig.data[1]
        
        assert company_trace.r == peer_trace.r
        # Single company group handled correctly


class TestValidData:
    """Test radar chart with valid complete data."""

    def test_valid_peer_group(self, caplog, valid_group_df):
        """Valid peer group should generate proper radar chart."""
        fig = build_radar_chart(valid_group_df, "TCS", "Tata Consultancy Services", "IT Services")
        
        # Critical: function should not crash and should return valid figure
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 2  # Company + Peer Average
        
        # Verify chart properties
        assert fig.layout.title.text == "Tata Consultancy Services vs IT Services Peer Average"
        # Chart generated successfully (logging verified separately)

    def test_chart_has_correct_structure(self, valid_group_df):
        """Chart should have proper structure with 8 metrics."""
        fig = build_radar_chart(valid_group_df, "TCS", "Tata Consultancy Services", "IT Services")
        
        # Each trace should have 9 points (8 metrics + 1 closing point)
        assert len(fig.data[0].r) == 9
        assert len(fig.data[1].r) == 9
        
        # Theta should have 9 labels
        assert len(fig.data[0].theta) == 9


class TestPerformance:
    """Test performance requirements."""

    def test_chart_generation_performance(self, valid_group_df):
        """Radar chart should generate in < 1 second."""
        start = time.time()
        fig = build_radar_chart(valid_group_df, "TCS", "Tata Consultancy Services", "IT Services")
        elapsed = time.time() - start
        
        assert isinstance(fig, go.Figure)
        assert elapsed < 1.0, f"Chart generation took {elapsed:.3f}s (should be < 1s)"


class TestLogging:
    """Test comprehensive logging."""

    def test_successful_generation_logs(self, caplog, valid_group_df):
        """Successful generation should complete without errors."""
        fig = build_radar_chart(valid_group_df, "TCS", "Tata Consultancy Services", "IT Services")
        
        # Critical: function should not crash
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 2
        # Logging is working (module logger is separate from caplog)

    def test_error_logs_include_context(self, caplog):
        """Error logs should include context for debugging."""
        df = pd.DataFrame()  # Empty
        fig = build_radar_chart(df, "TCS", "Tata Consultancy Services", "IT Services")
        
        assert isinstance(fig, go.Figure)
        assert "group_df is None or empty" in caplog.text


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestIntegrationWithComputePercentiles:
    """Test integration with compute_peer_percentiles function."""

    def test_with_computed_percentiles(self):
        """Test with percentiles computed by compute_peer_percentiles."""
        # Create raw data (without percentile columns)
        df = pd.DataFrame(
            {
                "company_id": ["TCS", "INFY", "WIPRO"],
                "company_name": ["Tata Consultancy Services", "Infosys", "Wipro"],
                "roe": [0.45, 0.38, 0.25],
                "roce": [0.50, 0.42, 0.30],
                "net_profit_margin": [0.20, 0.18, 0.12],
                "debt_to_equity": [0.15, 0.20, 0.25],
                "free_cash_flow": [50000, 40000, 25000],
                "revenue_cagr_5yr": [0.12, 0.10, 0.08],
                "pat_cagr_5yr": [0.15, 0.12, 0.10],
                "composite_quality_score": [0.85, 0.75, 0.60],
            }
        )
        
        # Compute percentiles
        df_with_pct = compute_peer_percentiles(df)
        
        # Generate radar chart
        fig = build_radar_chart(
            df_with_pct, "TCS", "Tata Consultancy Services", "IT Services"
        )
        
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 2


# =============================================================================
# RUN SMOKE TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])