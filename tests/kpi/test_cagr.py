"""
test_cagr.py

Unit tests for CAGR (Compound Annual Growth Rate) calculations.
"""

import pytest
import pandas as pd
import numpy as np

from src.analytics.cagr import (
    calculate_cagr,
    calculate_revenue_cagr,
    calculate_pat_cagr,
    calculate_eps_cagr,
    calculate_all_cagr,
    FLAG_NORMAL,
    FLAG_DECLINE_TO_LOSS,
    FLAG_TURNAROUND,
    FLAG_BOTH_NEGATIVE,
    FLAG_ZERO_BASE,
    FLAG_INSUFFICIENT,
)


class TestCalculateCAGR:
    """Test cases for core calculate_cagr function."""

    def test_normal_cagr_positive_to_positive(self):
        """Test normal CAGR calculation: positive to positive."""
        result = calculate_cagr(100, 200, 5)
        assert result["value"] == 14.87
        assert result["flag"] == FLAG_NORMAL

    def test_revenue_cagr_normal(self):
        """Test Revenue CAGR with normal data."""
        pl_data = pd.DataFrame({
            'sales': [100, 150, 200, 250, 300],
            'period': ['FY2019', 'FY2020', 'FY2021', 'FY2022', 'FY2023']
        })
        result = calculate_revenue_cagr(pl_data)
        
        # 4-year CAGR from 100 to 300 = 31.61%
        assert result["revenue_cagr_5yr"]["value"] == 31.61
        assert result["revenue_cagr_5yr"]["flag"] == FLAG_NORMAL

    def test_pat_cagr_normal(self):
        """Test PAT CAGR with normal data."""
        pl_data = pd.DataFrame({
            'net_profit': [50, 60, 70, 80, 90],
            'period': ['FY2019', 'FY2020', 'FY2021', 'FY2022', 'FY2023']
        })
        result = calculate_pat_cagr(pl_data)
        
        # 4-year CAGR from 50 to 90 = 15.83%
        assert result["pat_cagr_5yr"]["value"] == 15.83
        assert result["pat_cagr_5yr"]["flag"] == FLAG_NORMAL

    def test_eps_cagr_normal(self):
        """Test EPS CAGR with normal data."""
        pl_data = pd.DataFrame({
            'eps': [10, 12, 14, 16, 18],
            'period': ['FY2019', 'FY2020', 'FY2021', 'FY2022', 'FY2023']
        })
        result = calculate_eps_cagr(pl_data)
        
        # 4-year CAGR from 10 to 18 = 15.83%
        assert result["eps_cagr_5yr"]["value"] == 15.83
        assert result["eps_cagr_5yr"]["flag"] == FLAG_NORMAL

    def test_positive_to_negative_decline_to_loss(self):
        """Test Positive to Negative: DECLINE_TO_LOSS flag."""
        result = calculate_cagr(100, -50, 5)
        assert result["value"] is None
        assert result["flag"] == FLAG_DECLINE_TO_LOSS

    def test_negative_to_positive_turnaround(self):
        """Test Negative to Positive: TURNAROUND flag."""
        result = calculate_cagr(-100, 50, 5)
        assert result["value"] is None
        assert result["flag"] == FLAG_TURNAROUND

    def test_both_negative(self):
        """Test Both Negative: BOTH_NEGATIVE flag."""
        result = calculate_cagr(-100, -50, 5)
        assert result["value"] is None
        assert result["flag"] == FLAG_BOTH_NEGATIVE

    def test_zero_base(self):
        """Test Zero Base: ZERO_BASE flag."""
        result = calculate_cagr(0, 100, 5)
        assert result["value"] is None
        assert result["flag"] == FLAG_ZERO_BASE

    def test_insufficient_years(self):
        """Test Insufficient Years: INSUFFICIENT flag."""
        result = calculate_cagr(100, 200, 0)
        assert result["value"] is None
        assert result["flag"] == FLAG_INSUFFICIENT

    def test_nan_start_value(self):
        """Test NaN start value returns INSUFFICIENT."""
        result = calculate_cagr(np.nan, 100, 5)
        assert result["value"] is None
        assert result["flag"] == FLAG_INSUFFICIENT

    def test_nan_end_value(self):
        """Test NaN end value returns INSUFFICIENT."""
        result = calculate_cagr(100, np.nan, 5)
        assert result["value"] is None
        assert result["flag"] == FLAG_INSUFFICIENT

    def test_infinite_values(self):
        """Test infinite values return INSUFFICIENT."""
        result = calculate_cagr(100, np.inf, 5)
        assert result["value"] is None
        assert result["flag"] == FLAG_INSUFFICIENT


class TestRevenueCAGR:
    """Test cases for Revenue CAGR calculations."""

    def test_3_year_cagr(self):
        """Test 3-year Revenue CAGR."""
        pl_data = pd.DataFrame({
            'sales': [100, 133.1, 177.8, 237.4],
            'period': ['FY2020', 'FY2021', 'FY2022', 'FY2023']
        })
        result = calculate_revenue_cagr(pl_data)
        
        # 3-year CAGR from 100 to 237.4 = 33.40%
        assert result["revenue_cagr_3yr"]["value"] == 33.4
        assert result["revenue_cagr_3yr"]["flag"] == FLAG_NORMAL

    def test_10_year_cagr(self):
        """Test 10-year Revenue CAGR."""
        pl_data = pd.DataFrame({
            'sales': [100, 120, 144, 173, 208, 250, 300, 360, 432, 518, 622],
            'period': ['FY2013', 'FY2014', 'FY2015', 'FY2016', 'FY2017', 
                      'FY2018', 'FY2019', 'FY2020', 'FY2021', 'FY2022', 'FY2023']
        })
        result = calculate_revenue_cagr(pl_data)
        
        # 10-year CAGR from 100 to 518 = 20.05%
        assert result["revenue_cagr_10yr"]["value"] == 20.05
        assert result["revenue_cagr_10yr"]["flag"] == FLAG_NORMAL

    def test_insufficient_data_points(self):
        """Test insufficient data points returns INSUFFICIENT."""
        pl_data = pd.DataFrame({
            'sales': [100],
            'period': ['FY2023']
        })
        result = calculate_revenue_cagr(pl_data)
        assert result["revenue_cagr_3yr"]["value"] is None
        assert result["revenue_cagr_3yr"]["flag"] == FLAG_INSUFFICIENT

    def test_missing_sales_column(self):
        """Test missing sales column returns INSUFFICIENT."""
        pl_data = pd.DataFrame({
            'net_profit': [100, 200],
            'period': ['FY2022', 'FY2023']
        })
        result = calculate_revenue_cagr(pl_data)
        assert result["revenue_cagr_3yr"]["value"] is None
        assert result["revenue_cagr_3yr"]["flag"] == FLAG_INSUFFICIENT

    def test_empty_dataframe(self):
        """Test empty DataFrame returns INSUFFICIENT."""
        pl_data = pd.DataFrame()
        result = calculate_revenue_cagr(pl_data)
        assert result["revenue_cagr_3yr"]["value"] is None
        assert result["revenue_cagr_3yr"]["flag"] == FLAG_INSUFFICIENT

    def test_nan_sales_values(self):
        """Test NaN sales values are handled."""
        pl_data = pd.DataFrame({
            'sales': [100, np.nan, 200],
            'period': ['FY2021', 'FY2022', 'FY2023']
        })
        result = calculate_revenue_cagr(pl_data)
        # Should use 100 to 200 (2 years)
        assert result["revenue_cagr_3yr"]["value"] is not None
        assert result["revenue_cagr_3yr"]["flag"] == FLAG_NORMAL


class TestPATCAGR:
    """Test cases for PAT CAGR calculations."""

    def test_pat_decline_to_loss(self):
        """Test PAT decline to loss."""
        pl_data = pd.DataFrame({
            'net_profit': [100, 80, 50, 20, -30],
            'period': ['FY2019', 'FY2020', 'FY2021', 'FY2022', 'FY2023']
        })
        result = calculate_pat_cagr(pl_data)
        
        assert result["pat_cagr_3yr"]["value"] is None
        assert result["pat_cagr_3yr"]["flag"] == FLAG_DECLINE_TO_LOSS

    def test_pat_turnaround(self):
        """Test PAT turnaround from loss to profit."""
        pl_data = pd.DataFrame({
            'net_profit': [-50, -20, 10, 30, 50],
            'period': ['FY2019', 'FY2020', 'FY2021', 'FY2022', 'FY2023']
        })
        result = calculate_pat_cagr(pl_data)
        
        assert result["pat_cagr_3yr"]["value"] is None
        assert result["pat_cagr_3yr"]["flag"] == FLAG_TURNAROUND

    def test_pat_both_negative(self):
        """Test PAT both negative."""
        pl_data = pd.DataFrame({
            'net_profit': [-100, -80, -60, -40, -20],
            'period': ['FY2019', 'FY2020', 'FY2021', 'FY2022', 'FY2023']
        })
        result = calculate_pat_cagr(pl_data)
        
        assert result["pat_cagr_3yr"]["value"] is None
        assert result["pat_cagr_3yr"]["flag"] == FLAG_BOTH_NEGATIVE


class TestEPSCAGR:
    """Test cases for EPS CAGR calculations."""

    def test_eps_zero_base(self):
        """Test EPS with zero base value."""
        pl_data = pd.DataFrame({
            'eps': [0, 5, 10, 15, 20],
            'period': ['FY2019', 'FY2020', 'FY2021', 'FY2022', 'FY2023']
        })
        result = calculate_eps_cagr(pl_data)
        
        assert result["eps_cagr_3yr"]["value"] is None
        assert result["eps_cagr_3yr"]["flag"] == FLAG_ZERO_BASE

    def test_eps_normal_growth(self):
        """Test normal EPS growth."""
        pl_data = pd.DataFrame({
            'eps': [5, 7, 9, 11, 13],
            'period': ['FY2019', 'FY2020', 'FY2021', 'FY2022', 'FY2023']
        })
        result = calculate_eps_cagr(pl_data)
        
        # 4-year CAGR from 5 to 13 = 26.98%
        assert result["eps_cagr_5yr"]["value"] == 26.98
        assert result["eps_cagr_5yr"]["flag"] == FLAG_NORMAL


class TestDataValidation:
    """Test cases for data validation."""

    def test_duplicate_periods(self):
        """Test duplicate periods are detected."""
        pl_data = pd.DataFrame({
            'sales': [100, 200, 300],
            'period': ['FY2021', 'FY2022', 'FY2021']  # Duplicate FY2021
        })
        result = calculate_revenue_cagr(pl_data)
        assert result["revenue_cagr_3yr"]["flag"] == FLAG_INSUFFICIENT

    def test_out_of_order_periods(self):
        """Test out-of-order periods are detected."""
        pl_data = pd.DataFrame({
            'sales': [100, 200, 300],
            'period': ['FY2023', 'FY2021', 'FY2022']  # Not sorted
        })
        result = calculate_revenue_cagr(pl_data)
        assert result["revenue_cagr_3yr"]["flag"] == FLAG_INSUFFICIENT

    def test_missing_period_column(self):
        """Test missing period column."""
        pl_data = pd.DataFrame({
            'sales': [100, 200, 300]
        })
        result = calculate_revenue_cagr(pl_data)
        assert result["revenue_cagr_3yr"]["flag"] == FLAG_INSUFFICIENT

    def test_all_nan_values(self):
        """Test all NaN values in column."""
        pl_data = pd.DataFrame({
            'sales': [np.nan, np.nan, np.nan],
            'period': ['FY2021', 'FY2022', 'FY2023']
        })
        result = calculate_revenue_cagr(pl_data)
        assert result["revenue_cagr_3yr"]["value"] is None
        assert result["revenue_cagr_3yr"]["flag"] == FLAG_INSUFFICIENT


class TestCalculateAllCAGR:
    """Test cases for calculate_all_cagr function."""

    def test_calculate_all_metrics(self):
        """Test calculating all CAGR metrics at once."""
        pl_data = pd.DataFrame({
            'sales': [100, 150, 200, 250, 300],
            'net_profit': [10, 15, 20, 25, 30],
            'eps': [5, 7.5, 10, 12.5, 15],
            'period': ['FY2019', 'FY2020', 'FY2021', 'FY2022', 'FY2023']
        })
        
        result = calculate_all_cagr(pl_data, company_id="TEST001", period="FY2023")
        
        # Check that all metrics are calculated
        assert "revenue_cagr_5yr" in result
        assert "pat_cagr_5yr" in result
        assert "eps_cagr_5yr" in result
        
        # Check company_id and period are included
        assert result["company_id"] == "TEST001"
        assert result["period"] == "FY2023"
        
        # Verify values (4-year CAGR)
        assert result["revenue_cagr_5yr"]["value"] == 31.61
        assert result["pat_cagr_5yr"]["value"] == 31.61
        assert result["eps_cagr_5yr"]["value"] == 31.61

    def test_calculate_all_with_mixed_data(self):
        """Test calculate_all with some edge cases."""
        pl_data = pd.DataFrame({
            'sales': [100, 150, -200, 300],  # End value is positive
            'net_profit': [10, 15, -20, 25],  # End value is positive
            'eps': [5, 7.5, -10, 12.5],  # End value is positive
            'period': ['FY2020', 'FY2021', 'FY2022', 'FY2023']
        })
        
        result = calculate_all_cagr(pl_data)
        
        # All windows end with positive values, so all should be NORMAL
        # (CAGR only looks at start and end values, not intermediate values)
        assert result["revenue_cagr_3yr"]["flag"] == FLAG_NORMAL
        assert result["revenue_cagr_5yr"]["flag"] == FLAG_NORMAL
        assert result["pat_cagr_3yr"]["flag"] == FLAG_NORMAL
        assert result["eps_cagr_3yr"]["flag"] == FLAG_NORMAL


class TestEdgeCases:
    """Additional edge case tests."""

    def test_very_small_growth(self):
        """Test very small positive growth."""
        result = calculate_cagr(100, 100.1, 10)
        assert result["value"] == 0.01
        assert result["flag"] == FLAG_NORMAL

    def test_very_large_growth(self):
        """Test very large growth."""
        result = calculate_cagr(100, 1000, 5)
        assert result["value"] == 58.49
        assert result["flag"] == FLAG_NORMAL

    def test_negative_years(self):
        """Test negative years returns INSUFFICIENT."""
        result = calculate_cagr(100, 200, -5)
        assert result["value"] is None
        assert result["flag"] == FLAG_INSUFFICIENT

    def test_both_values_zero(self):
        """Test both start and end are zero."""
        result = calculate_cagr(0, 0, 5)
        assert result["value"] is None
        assert result["flag"] == FLAG_ZERO_BASE

    def test_end_value_zero(self):
        """Test end value is zero."""
        result = calculate_cagr(100, 0, 5)
        # This is positive to zero, which should be valid (decline to 0, not negative)
        # Actually, 0 is not negative, so it's positive to zero
        # The formula should work: ((0/100)^(1/5) - 1) * 100 = -100%
        assert result["value"] == -100.0
        assert result["flag"] == FLAG_NORMAL

    def test_window_capping(self):
        """Test that window size is capped at actual years."""
        pl_data = pd.DataFrame({
            'sales': [100, 200],
            'period': ['FY2020', 'FY2023']  # 3 years apart
        })
        result = calculate_revenue_cagr(pl_data)
        
        # Should calculate 3-year CAGR (actual years), not 5 or 10
        assert result["revenue_cagr_3yr"]["value"] is not None
        assert result["revenue_cagr_3yr"]["flag"] == FLAG_NORMAL
        # 5yr and 10yr should also work but use 3 years
        assert result["revenue_cagr_5yr"]["value"] is not None
        assert result["revenue_cagr_10yr"]["value"] is not None


class TestUtilityFunctions:
    """Test utility functions."""

    def test_get_cagr_descriptions(self):
        """Test get_cagr_descriptions returns all metrics."""
        from src.analytics.cagr import get_cagr_descriptions
        descriptions = get_cagr_descriptions()
        
        assert "revenue_cagr_3yr" in descriptions
        assert "pat_cagr_5yr" in descriptions
        assert "eps_cagr_10yr" in descriptions
        assert len(descriptions) == 9  # 3 metrics × 3 windows

    def test_get_cagr_formulas(self):
        """Test get_cagr_formulas returns formulas."""
        from src.analytics.cagr import get_cagr_formulas
        formulas = get_cagr_formulas()
        
        assert "revenue_cagr" in formulas
        assert "pat_cagr" in formulas
        assert "eps_cagr" in formulas
        assert "CAGR" in formulas["revenue_cagr"]

    def test_get_cagr_flag_descriptions(self):
        """Test get_cagr_flag_descriptions returns all flags."""
        from src.analytics.cagr import get_cagr_flag_descriptions
        descriptions = get_cagr_flag_descriptions()
        
        assert FLAG_NORMAL in descriptions
        assert FLAG_DECLINE_TO_LOSS in descriptions
        assert FLAG_TURNAROUND in descriptions
        assert FLAG_BOTH_NEGATIVE in descriptions
        assert FLAG_ZERO_BASE in descriptions
        assert FLAG_INSUFFICIENT in descriptions