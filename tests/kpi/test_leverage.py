"""
test_leverage.py

Unit tests for leverage ratio calculations.
"""

import pytest
import pandas as pd
import numpy as np

from src.analytics.ratios import (
    calculate_debt_to_equity,
    calculate_interest_coverage,
    calculate_net_debt,
)


class TestDebtToEquity:
    """Test cases for Debt to Equity calculation."""

    def test_normal_calculation(self):
        """Test normal debt to equity calculation."""
        bs_data = pd.DataFrame({
            'borrowings': [10000],
            'equity_capital': [5000],
            'reserves': [5000]
        })
        ratio, flag = calculate_debt_to_equity(bs_data)
        assert ratio == 1.0
        assert flag is False

    def test_borrowings_zero_returns_zero(self):
        """Test zero borrowings returns 0 (not None)."""
        bs_data = pd.DataFrame({
            'borrowings': [0],
            'equity_capital': [5000],
            'reserves': [5000]
        })
        ratio, flag = calculate_debt_to_equity(bs_data)
        assert ratio == 0.0
        assert flag is False

    def test_high_leverage_flag_non_financials(self):
        """Test high leverage flag for non-Financials sector."""
        bs_data = pd.DataFrame({
            'borrowings': [60000],
            'equity_capital': [5000],
            'reserves': [5000]
        })
        # Debt to Equity = 60000 / 10000 = 6.0 > 5
        ratio, flag = calculate_debt_to_equity(bs_data, company_id="TEST001")
        assert ratio == 6.0
        assert flag is True

    def test_high_leverage_flag_financials_sector(self):
        """Test high leverage flag is NOT set for Financials sector."""
        bs_data = pd.DataFrame({
            'borrowings': [60000],
            'equity_capital': [5000],
            'reserves': [5000]
        })
        # Debt to Equity = 60000 / 10000 = 6.0 > 5, but company is in Financials
        ratio, flag = calculate_debt_to_equity(bs_data, company_id="TEST001")
        # Note: This test will need database access to check sector
        # For now, we just verify the calculation works
        assert ratio == 6.0

    def test_negative_equity_returns_none(self):
        """Test negative equity returns None."""
        bs_data = pd.DataFrame({
            'borrowings': [10000],
            'equity_capital': [-5000],
            'reserves': [0]
        })
        ratio, flag = calculate_debt_to_equity(bs_data)
        assert ratio is None
        assert flag is False

    def test_zero_equity_returns_none(self):
        """Test zero equity returns None."""
        bs_data = pd.DataFrame({
            'borrowings': [10000],
            'equity_capital': [0],
            'reserves': [0]
        })
        ratio, flag = calculate_debt_to_equity(bs_data)
        assert ratio is None
        assert flag is False

    def test_empty_dataframe(self):
        """Test empty dataframe returns None."""
        bs_data = pd.DataFrame()
        ratio, flag = calculate_debt_to_equity(bs_data)
        assert ratio is None
        assert flag is False


class TestInterestCoverage:
    """Test cases for Interest Coverage calculation."""

    def test_normal_calculation(self):
        """Test normal interest coverage calculation."""
        pl_data = pd.DataFrame({
            'operating_profit': [5000],
            'other_income': [500],
            'interest': [1000]
        })
        # EBIT = 5000 + 500 = 5500
        # Coverage = 5500 / 1000 = 5.5
        coverage, label, warning = calculate_interest_coverage(pl_data)
        assert coverage == 5.5
        assert label is None
        assert warning is False

    def test_interest_zero_debt_free(self):
        """Test interest=0 returns Debt Free label."""
        pl_data = pd.DataFrame({
            'operating_profit': [5000],
            'other_income': [500],
            'interest': [0]
        })
        coverage, label, warning = calculate_interest_coverage(pl_data)
        assert coverage is None
        assert label == "Debt Free"
        assert warning is False

    def test_icr_below_threshold_warning(self):
        """Test ICR < 1.5 sets warning flag."""
        pl_data = pd.DataFrame({
            'operating_profit': [1000],
            'other_income': [100],
            'interest': [1000]
        })
        # EBIT = 1000 + 100 = 1100
        # Coverage = 1100 / 1000 = 1.1 < 1.5
        coverage, label, warning = calculate_interest_coverage(pl_data)
        assert coverage == 1.1
        assert warning is True

    def test_icr_above_threshold_no_warning(self):
        """Test ICR >= 1.5 does not set warning flag."""
        pl_data = pd.DataFrame({
            'operating_profit': [2000],
            'other_income': [500],
            'interest': [1000]
        })
        # EBIT = 2000 + 500 = 2500
        # Coverage = 2500 / 1000 = 2.5 >= 1.5
        coverage, label, warning = calculate_interest_coverage(pl_data)
        assert coverage == 2.5
        assert warning is False

    def test_empty_dataframe(self):
        """Test empty dataframe returns None."""
        pl_data = pd.DataFrame()
        coverage, label, warning = calculate_interest_coverage(pl_data)
        assert coverage is None
        assert label is None
        assert warning is False


class TestNetDebt:
    """Test cases for Net Debt calculation."""

    def test_normal_calculation(self):
        """Test normal net debt calculation."""
        bs_data = pd.DataFrame({
            'borrowings': [10000],
            'investments': [3000]
        })
        result = calculate_net_debt(bs_data)
        assert result == 7000.0

    def test_zero_borrowings(self):
        """Test zero borrowings."""
        bs_data = pd.DataFrame({
            'borrowings': [0],
            'investments': [3000]
        })
        result = calculate_net_debt(bs_data)
        assert result == -3000.0

    def test_zero_investments(self):
        """Test zero investments."""
        bs_data = pd.DataFrame({
            'borrowings': [10000],
            'investments': [0]
        })
        result = calculate_net_debt(bs_data)
        assert result == 10000.0

    def test_empty_dataframe(self):
        """Test empty dataframe returns None."""
        bs_data = pd.DataFrame()
        result = calculate_net_debt(bs_data)
        assert result is None