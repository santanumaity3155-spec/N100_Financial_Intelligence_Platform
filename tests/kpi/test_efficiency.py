"""
test_efficiency.py

Unit tests for efficiency ratio calculations.
"""

import pytest
import pandas as pd
import numpy as np

from src.analytics.ratios import calculate_asset_turnover


class TestAssetTurnover:
    """Test cases for Asset Turnover calculation."""

    def test_normal_calculation(self):
        """Test normal asset turnover calculation."""
        pl_data = pd.DataFrame({'sales': [50000]})
        bs_data = pd.DataFrame({'total_assets': [25000]})
        result = calculate_asset_turnover(pl_data, bs_data)
        assert result == 2.0

    def test_zero_total_assets(self):
        """Test zero total assets returns None."""
        pl_data = pd.DataFrame({'sales': [50000]})
        bs_data = pd.DataFrame({'total_assets': [0]})
        result = calculate_asset_turnover(pl_data, bs_data)
        assert result is None

    def test_missing_sales(self):
        """Test missing sales returns None."""
        pl_data = pd.DataFrame()
        bs_data = pd.DataFrame({'total_assets': [25000]})
        result = calculate_asset_turnover(pl_data, bs_data)
        assert result is None

    def test_missing_total_assets(self):
        """Test missing total assets returns None."""
        pl_data = pd.DataFrame({'sales': [50000]})
        bs_data = pd.DataFrame()
        result = calculate_asset_turnover(pl_data, bs_data)
        assert result is None

    def test_nan_sales(self):
        """Test NaN sales returns None."""
        pl_data = pd.DataFrame({'sales': [np.nan]})
        bs_data = pd.DataFrame({'total_assets': [25000]})
        result = calculate_asset_turnover(pl_data, bs_data)
        assert result is None

    def test_nan_total_assets(self):
        """Test NaN total assets returns None."""
        pl_data = pd.DataFrame({'sales': [50000]})
        bs_data = pd.DataFrame({'total_assets': [np.nan]})
        result = calculate_asset_turnover(pl_data, bs_data)
        assert result is None

    def test_empty_dataframes(self):
        """Test empty dataframes returns None."""
        pl_data = pd.DataFrame()
        bs_data = pd.DataFrame()
        result = calculate_asset_turnover(pl_data, bs_data)
        assert result is None