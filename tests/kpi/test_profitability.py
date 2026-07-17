"""
test_profitability.py

Unit tests for profitability ratio calculations.
"""

import pytest
import pandas as pd
import numpy as np

from src.analytics.ratios import (
    calculate_net_profit_margin,
    calculate_operating_profit_margin,
    calculate_roe,
    calculate_roce,
    calculate_roa,
)


class TestNetProfitMargin:
    """Test cases for Net Profit Margin calculation."""

    def test_normal_calculation(self):
        """Test normal net profit margin calculation."""
        pl_data = pd.DataFrame({
            'net_profit': [1000],
            'sales': [10000]
        })
        result = calculate_net_profit_margin(pl_data)
        assert result == 10.0

    def test_zero_sales(self):
        """Test zero sales returns None."""
        pl_data = pd.DataFrame({
            'net_profit': [1000],
            'sales': [0]
        })
        result = calculate_net_profit_margin(pl_data)
        assert result is None

    def test_missing_data(self):
        """Test missing data returns None."""
        pl_data = pd.DataFrame()
        result = calculate_net_profit_margin(pl_data)
        assert result is None

    def test_nan_values(self):
        """Test NaN values return None."""
        pl_data = pd.DataFrame({
            'net_profit': [np.nan],
            'sales': [10000]
        })
        result = calculate_net_profit_margin(pl_data)
        assert result is None


class TestOperatingProfitMargin:
    """Test cases for Operating Profit Margin calculation."""

    def test_normal_calculation(self):
        """Test normal operating profit margin calculation."""
        pl_data = pd.DataFrame({
            'operating_profit': [1500],
            'sales': [10000],
            'opm_percentage': [15.0]
        })
        result = calculate_operating_profit_margin(pl_data)
        assert result == 15.0

    def test_zero_sales(self):
        """Test zero sales returns None."""
        pl_data = pd.DataFrame({
            'operating_profit': [1500],
            'sales': [0]
        })
        result = calculate_operating_profit_margin(pl_data)
        assert result is None

    def test_opm_mismatch_logs_warning(self, caplog):
        """Test OPM mismatch > 1% logs warning."""
        pl_data = pd.DataFrame({
            'operating_profit': [2000],
            'sales': [10000],
            'opm_percentage': [15.0]  # Source says 15%, calculated is 20%
        })
        result = calculate_operating_profit_margin(pl_data)
        assert result == 20.0
        assert "OPM mismatch detected" in caplog.text

    def test_opm_within_tolerance_no_warning(self, caplog):
        """Test OPM within 1% tolerance does not log warning."""
        pl_data = pd.DataFrame({
            'operating_profit': [1550],
            'sales': [10000],
            'opm_percentage': [15.0]  # Calculated is 15.5%, difference is 0.5%
        })
        result = calculate_operating_profit_margin(pl_data)
        assert result == 15.5
        assert "OPM mismatch detected" not in caplog.text


class TestROE:
    """Test cases for Return on Equity calculation."""

    def test_normal_calculation(self):
        """Test normal ROE calculation."""
        pl_data = pd.DataFrame({'net_profit': [1000]})
        bs_data = pd.DataFrame({
            'equity_capital': [5000],
            'reserves': [5000]
        })
        result = calculate_roe(pl_data, bs_data)
        assert result == 10.0

    def test_negative_equity(self):
        """Test negative equity returns None."""
        pl_data = pd.DataFrame({'net_profit': [1000]})
        bs_data = pd.DataFrame({
            'equity_capital': [-1000],
            'reserves': [0]
        })
        result = calculate_roe(pl_data, bs_data)
        assert result is None

    def test_zero_equity(self):
        """Test zero equity returns None."""
        pl_data = pd.DataFrame({'net_profit': [1000]})
        bs_data = pd.DataFrame({
            'equity_capital': [0],
            'reserves': [0]
        })
        result = calculate_roe(pl_data, bs_data)
        assert result is None

    def test_fallback_to_share_capital(self):
        """Test fallback to share_capital + reserves when equity_capital is 0."""
        pl_data = pd.DataFrame({'net_profit': [1000]})
        bs_data = pd.DataFrame({
            'share_capital': [5000],
            'reserves': [5000]
        })
        result = calculate_roe(pl_data, bs_data)
        assert result == 10.0


class TestROCE:
    """Test cases for Return on Capital Employed calculation."""

    def test_normal_calculation(self):
        """Test normal ROCE calculation."""
        pl_data = pd.DataFrame({
            'operating_profit': [2000],
            'other_income': [500]
        })
        bs_data = pd.DataFrame({
            'equity_capital': [5000],
            'reserves': [5000],
            'borrowings': [10000]
        })
        result = calculate_roce(pl_data, bs_data, company_id="TEST001")
        # EBIT = 2000 + 500 = 2500
        # Capital Employed = 10000 + 10000 = 20000
        # ROCE = 2500 / 20000 * 100 = 12.5
        assert result == 12.5

    def test_financials_sector_handling(self):
        """Test Financials sector is handled (no hardcoded thresholds)."""
        pl_data = pd.DataFrame({
            'operating_profit': [2000],
            'other_income': [500]
        })
        bs_data = pd.DataFrame({
            'equity_capital': [5000],
            'reserves': [5000],
            'borrowings': [10000]
        })
        # Should not raise error, just log debug message
        result = calculate_roce(pl_data, bs_data, company_id="TEST001")
        assert result is not None


class TestROA:
    """Test cases for Return on Assets calculation."""

    def test_normal_calculation(self):
        """Test normal ROA calculation."""
        pl_data = pd.DataFrame({'net_profit': [1000]})
        bs_data = pd.DataFrame({'total_assets': [20000]})
        result = calculate_roa(pl_data, bs_data)
        assert result == 5.0

    def test_zero_total_assets(self):
        """Test zero total assets returns None."""
        pl_data = pd.DataFrame({'net_profit': [1000]})
        bs_data = pd.DataFrame({'total_assets': [0]})
        result = calculate_roa(pl_data, bs_data)
        assert result is None

    def test_missing_data(self):
        """Test missing data returns None."""
        pl_data = pd.DataFrame()
        bs_data = pd.DataFrame()
        result = calculate_roa(pl_data, bs_data)
        assert result is None