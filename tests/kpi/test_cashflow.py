"""
test_cashflow.py

Unit tests for Cash Flow KPI calculations.
"""

import pytest
import pandas as pd
import numpy as np
import os

from src.analytics.cashflow_kpis import (
    calculate_free_cash_flow,
    calculate_fcf_margin,
    calculate_cash_conversion,
    calculate_capex_intensity,
    calculate_cash_reinvestment_ratio,
    calculate_cash_return_on_assets,
    calculate_operating_cashflow_growth,
    classify_capital_allocation,
    calculate_all_cashflow_kpis,
    generate_capital_allocation_csv,
    RATING_EXCELLENT,
    RATING_GOOD,
    RATING_MODERATE,
    RATING_WEAK,
    RATING_DISTRESSED,
)


class TestFreeCashFlow:
    """Test cases for Free Cash Flow calculation."""

    def test_normal_fcf_calculation(self):
        """Test normal FCF calculation."""
        cf_data = pd.DataFrame({
            'cash_from_operating_activity': [1000],
            'cash_from_investing_activity': [-300]
        })
        result = calculate_free_cash_flow(cf_data)
        assert result == 700.0

    def test_fcf_with_positive_capex(self):
        """Test FCF with positive CapEx value."""
        cf_data = pd.DataFrame({
            'cash_from_operating_activity': [1000],
            'cash_from_investing_activity': [300]
        })
        result = calculate_free_cash_flow(cf_data)
        assert result == 700.0

    def test_fcf_missing_ocf(self):
        """Test FCF with missing OCF returns None."""
        cf_data = pd.DataFrame({
            'cash_from_investing_activity': [-300]
        })
        result = calculate_free_cash_flow(cf_data)
        assert result is None

    def test_fcf_missing_capex(self):
        """Test FCF with missing CapEx returns None."""
        cf_data = pd.DataFrame({
            'cash_from_operating_activity': [1000]
        })
        result = calculate_free_cash_flow(cf_data)
        assert result is None

    def test_fcf_empty_dataframe(self):
        """Test FCF with empty DataFrame returns None."""
        cf_data = pd.DataFrame()
        result = calculate_free_cash_flow(cf_data)
        assert result is None

    def test_fcf_nan_values(self):
        """Test FCF with NaN values returns None."""
        cf_data = pd.DataFrame({
            'cash_from_operating_activity': [np.nan],
            'cash_from_investing_activity': [-300]
        })
        result = calculate_free_cash_flow(cf_data)
        assert result is None


class TestFCFMargin:
    """Test cases for FCF Margin calculation."""

    def test_normal_fcf_margin(self):
        """Test normal FCF Margin calculation."""
        cf_data = pd.DataFrame({
            'cash_from_operating_activity': [1000],
            'cash_from_investing_activity': [-300]
        })
        pl_data = pd.DataFrame({'sales': [5000]})
        result = calculate_fcf_margin(cf_data, pl_data)
        assert result == 14.0

    def test_fcf_margin_zero_sales(self):
        """Test FCF Margin with zero sales returns None."""
        cf_data = pd.DataFrame({
            'cash_from_operating_activity': [1000],
            'cash_from_investing_activity': [-300]
        })
        pl_data = pd.DataFrame({'sales': [0]})
        result = calculate_fcf_margin(cf_data, pl_data)
        assert result is None

    def test_fcf_margin_missing_sales(self):
        """Test FCF Margin with missing sales returns None."""
        cf_data = pd.DataFrame({
            'cash_from_operating_activity': [1000],
            'cash_from_investing_activity': [-300]
        })
        pl_data = pd.DataFrame({'net_profit': [500]})
        result = calculate_fcf_margin(cf_data, pl_data)
        assert result is None

    def test_fcf_margin_negative_fcf(self):
        """Test FCF Margin with negative FCF."""
        cf_data = pd.DataFrame({
            'cash_from_operating_activity': [500],
            'cash_from_investing_activity': [-800]
        })
        pl_data = pd.DataFrame({'sales': [5000]})
        result = calculate_fcf_margin(cf_data, pl_data)
        assert result == -6.0


class TestCashConversion:
    """Test cases for Cash Conversion calculation."""

    def test_normal_cash_conversion(self):
        """Test normal Cash Conversion calculation."""
        cf_data = pd.DataFrame({'cash_from_operating_activity': [1000]})
        pl_data = pd.DataFrame({'net_profit': [800]})
        result = calculate_cash_conversion(cf_data, pl_data)
        assert result["value"] == 125.0
        assert result["flag"] is None

    def test_cash_conversion_excellent(self):
        """Test Cash Conversion >100%."""
        cf_data = pd.DataFrame({'cash_from_operating_activity': [1200]})
        pl_data = pd.DataFrame({'net_profit': [1000]})
        result = calculate_cash_conversion(cf_data, pl_data)
        assert result["value"] == 120.0
        assert result["flag"] is None

    def test_cash_conversion_zero_profit(self):
        """Test Cash Conversion with zero net profit returns INVALID_PROFIT."""
        cf_data = pd.DataFrame({'cash_from_operating_activity': [1000]})
        pl_data = pd.DataFrame({'net_profit': [0]})
        result = calculate_cash_conversion(cf_data, pl_data)
        assert result["value"] is None
        assert result["flag"] == "INVALID_PROFIT"

    def test_cash_conversion_negative_profit(self):
        """Test Cash Conversion with negative net profit returns INVALID_PROFIT."""
        cf_data = pd.DataFrame({'cash_from_operating_activity': [1000]})
        pl_data = pd.DataFrame({'net_profit': [-100]})
        result = calculate_cash_conversion(cf_data, pl_data)
        assert result["value"] is None
        assert result["flag"] == "INVALID_PROFIT"

    def test_cash_conversion_missing_data(self):
        """Test Cash Conversion with missing data returns INVALID_PROFIT."""
        cf_data = pd.DataFrame({'cash_from_operating_activity': [1000]})
        pl_data = pd.DataFrame({'sales': [5000]})
        result = calculate_cash_conversion(cf_data, pl_data)
        assert result["value"] is None
        assert result["flag"] == "INVALID_PROFIT"


class TestCapExIntensity:
    """Test cases for CapEx Intensity calculation."""

    def test_normal_capex_intensity(self):
        """Test normal CapEx Intensity calculation."""
        cf_data = pd.DataFrame({
            'cash_from_operating_activity': [1000],
            'cash_from_investing_activity': [-300]
        })
        result = calculate_capex_intensity(cf_data)
        assert result == 30.0

    def test_capex_intensity_zero_ocf(self):
        """Test CapEx Intensity with zero OCF returns None."""
        cf_data = pd.DataFrame({
            'cash_from_operating_activity': [0],
            'cash_from_investing_activity': [-300]
        })
        result = calculate_capex_intensity(cf_data)
        assert result is None

    def test_capex_intensity_high(self):
        """Test CapEx Intensity >100%."""
        cf_data = pd.DataFrame({
            'cash_from_operating_activity': [500],
            'cash_from_investing_activity': [-800]
        })
        result = calculate_capex_intensity(cf_data)
        assert result == 160.0


class TestCashReinvestmentRatio:
    """Test cases for Cash Reinvestment Ratio calculation."""

    def test_normal_cash_reinvestment(self):
        """Test normal Cash Reinvestment Ratio."""
        cf_data = pd.DataFrame({
            'cash_from_operating_activity': [1000],
            'cash_from_investing_activity': [-300]
        })
        result = calculate_cash_reinvestment_ratio(cf_data)
        assert result == 0.3

    def test_cash_reinvestment_zero_ocf(self):
        """Test Cash Reinvestment Ratio with zero OCF returns None."""
        cf_data = pd.DataFrame({
            'cash_from_operating_activity': [0],
            'cash_from_investing_activity': [-300]
        })
        result = calculate_cash_reinvestment_ratio(cf_data)
        assert result is None

    def test_cash_reinvestment_high(self):
        """Test Cash Reinvestment Ratio >1."""
        cf_data = pd.DataFrame({
            'cash_from_operating_activity': [500],
            'cash_from_investing_activity': [-800]
        })
        result = calculate_cash_reinvestment_ratio(cf_data)
        assert result == 1.6


class TestCashReturnOnAssets:
    """Test cases for Cash Return on Assets calculation."""

    def test_normal_cash_roa(self):
        """Test normal Cash ROA calculation."""
        cf_data = pd.DataFrame({'cash_from_operating_activity': [1000]})
        bs_data = pd.DataFrame({'total_assets': [10000]})
        result = calculate_cash_return_on_assets(cf_data, bs_data)
        assert result == 10.0

    def test_cash_roa_zero_assets(self):
        """Test Cash ROA with zero total assets returns None."""
        cf_data = pd.DataFrame({'cash_from_operating_activity': [1000]})
        bs_data = pd.DataFrame({'total_assets': [0]})
        result = calculate_cash_return_on_assets(cf_data, bs_data)
        assert result is None

    def test_cash_roa_missing_data(self):
        """Test Cash ROA with missing data returns None."""
        cf_data = pd.DataFrame({'cash_from_operating_activity': [1000]})
        bs_data = pd.DataFrame({'equity_capital': [5000]})
        result = calculate_cash_return_on_assets(cf_data, bs_data)
        assert result is None


class TestOperatingCashflowGrowth:
    """Test cases for Operating Cash Flow Growth calculation."""

    def test_normal_ocf_growth(self):
        """Test normal OCF growth calculation."""
        cf_data = pd.DataFrame({
            'cash_from_operating_activity': [100, 150, 200, 250, 300],
            'period': ['FY2019', 'FY2020', 'FY2021', 'FY2022', 'FY2023']
        })
        result = calculate_operating_cashflow_growth(cf_data)
        assert result["ocf_cagr_5yr"]["value"] is not None
        assert result["ocf_cagr_5yr"]["flag"] is None

    def test_ocf_growth_insufficient_data(self):
        """Test OCF growth with insufficient data."""
        cf_data = pd.DataFrame({
            'cash_from_operating_activity': [100],
            'period': ['FY2023']
        })
        result = calculate_operating_cashflow_growth(cf_data)
        assert result["ocf_cagr_3yr"]["value"] is None
        assert result["ocf_cagr_3yr"]["flag"] == "INSUFFICIENT"

    def test_ocf_growth_missing_column(self):
        """Test OCF growth with missing column."""
        cf_data = pd.DataFrame({
            'period': ['FY2022', 'FY2023']
        })
        result = calculate_operating_cashflow_growth(cf_data)
        assert result["ocf_cagr_3yr"]["flag"] == "INSUFFICIENT"


class TestCapitalAllocationClassifier:
    """Test cases for Capital Allocation Classifier."""

    def test_excellent_classification(self):
        """Test EXCELLENT classification."""
        rating = classify_capital_allocation(500, 120, 40, 1000)
        assert rating == RATING_EXCELLENT

    def test_good_classification_high_conversion(self):
        """Test GOOD classification with high conversion."""
        rating = classify_capital_allocation(500, 95, 60, 1000)
        assert rating == RATING_GOOD

    def test_moderate_classification(self):
        """Test MODERATE classification."""
        rating = classify_capital_allocation(500, 70, 60, 1000)
        assert rating == RATING_MODERATE

    def test_weak_classification(self):
        """Test WEAK classification."""
        rating = classify_capital_allocation(500, 40, 60, 1000)
        assert rating == RATING_WEAK

    def test_distressed_negative_fcf(self):
        """Test DISTRESSED classification with negative FCF."""
        rating = classify_capital_allocation(-100, 90, 60, 500)
        assert rating == RATING_DISTRESSED

    def test_distressed_negative_ocf(self):
        """Test DISTRESSED classification with negative OCF."""
        rating = classify_capital_allocation(100, 90, 60, -500)
        assert rating == RATING_DISTRESSED

    def test_distressed_missing_data(self):
        """Test DISTRESSED classification with missing data."""
        rating = classify_capital_allocation(None, 90, 60, 1000)
        assert rating == RATING_DISTRESSED

    def test_moderate_missing_conversion(self):
        """Test MODERATE classification when cash conversion is None."""
        rating = classify_capital_allocation(500, None, 60, 1000)
        assert rating == RATING_MODERATE


class TestCalculateAllCashflowKPIs:
    """Test cases for calculate_all_cashflow_kpis function."""

    def test_calculate_all_kpis(self):
        """Test calculating all cash flow KPIs."""
        cf_data = pd.DataFrame({
            'cash_from_operating_activity': [1000],
            'cash_from_investing_activity': [-300],
            'period': ['FY2023']
        })
        pl_data = pd.DataFrame({
            'sales': [5000],
            'net_profit': [800]
        })
        bs_data = pd.DataFrame({
            'total_assets': [10000]
        })
        
        result = calculate_all_cashflow_kpis(cf_data, pl_data, bs_data, "TEST001", "FY2023")
        
        assert result["company_id"] == "TEST001"
        assert result["period"] == "FY2023"
        assert result["free_cash_flow"] == 700.0
        assert result["fcf_margin"] == 14.0
        assert result["cash_conversion"] == 125.0
        assert result["capex_intensity"] == 30.0
        assert result["cash_reinvestment_ratio"] == 0.3
        assert result["cash_return_on_assets"] == 10.0
        assert result["capital_allocation_rating"] == RATING_EXCELLENT

    def test_calculate_all_with_distress(self):
        """Test calculating all KPIs with distressed signals."""
        cf_data = pd.DataFrame({
            'cash_from_operating_activity': [-500],
            'cash_from_investing_activity': [-300],
            'period': ['FY2023']
        })
        pl_data = pd.DataFrame({
            'sales': [5000],
            'net_profit': [800]
        })
        bs_data = pd.DataFrame({
            'total_assets': [10000]
        })
        
        result = calculate_all_cashflow_kpis(cf_data, pl_data, bs_data)
        
        assert result["capital_allocation_rating"] == RATING_DISTRESSED


class TestCSVGeneration:
    """Test cases for CSV generation."""

    def test_generate_csv(self):
        """Test CSV generation."""
        results = [
            {
                "company_id": "TEST001",
                "company_name": "Test Company",
                "period": "FY2023",
                "free_cash_flow": 700.0,
                "fcf_margin": 14.0,
                "cash_conversion": 125.0,
                "capex_intensity": 30.0,
                "cash_return_on_assets": 10.0,
                "cash_reinvestment_ratio": 0.3,
                "ocf_cagr_3yr": {"value": 15.0, "flag": None},
                "capital_allocation_rating": RATING_EXCELLENT
            }
        ]
        
        output_path = "output/test_capital_allocation.csv"
        generate_capital_allocation_csv(results, output_path)
        
        assert os.path.exists(output_path)
        
        # Clean up
        if os.path.exists(output_path):
            os.remove(output_path)
            os.rmdir("output")

    def test_generate_csv_empty_results(self):
        """Test CSV generation with empty results."""
        output_path = "output/test_empty.csv"
        generate_capital_allocation_csv([], output_path)
        
        # Should not create file for empty results
        assert not os.path.exists(output_path)


class TestEdgeCases:
    """Additional edge case tests."""

    def test_nan_ocf_value(self):
        """Test with NaN OCF value."""
        cf_data = pd.DataFrame({
            'cash_from_operating_activity': [np.nan],
            'cash_from_investing_activity': [-300]
        })
        result = calculate_free_cash_flow(cf_data)
        assert result is None

    def test_infinite_values(self):
        """Test with infinite values."""
        cf_data = pd.DataFrame({
            'cash_from_operating_activity': [np.inf],
            'cash_from_investing_activity': [-300]
        })
        result = calculate_free_cash_flow(cf_data)
        assert result is None

    def test_negative_capex_handling(self):
        """Test that negative CapEx is handled correctly."""
        cf_data = pd.DataFrame({
            'cash_from_operating_activity': [1000],
            'cash_from_investing_activity': [-300]  # Negative in statement
        })
        result = calculate_capex_intensity(cf_data)
        # Should use absolute value: 300/1000 * 100 = 30%
        assert result == 30.0

    def test_duplicate_periods(self):
        """Test with duplicate periods."""
        cf_data = pd.DataFrame({
            'cash_from_operating_activity': [100, 200, 300],
            'period': ['FY2021', 'FY2022', 'FY2021']
        })
        result = calculate_operating_cashflow_growth(cf_data)
        assert result["ocf_cagr_3yr"]["flag"] == "INSUFFICIENT"

    def test_out_of_order_periods(self):
        """Test with out-of-order periods."""
        cf_data = pd.DataFrame({
            'cash_from_operating_activity': [100, 200, 300],
            'period': ['FY2023', 'FY2021', 'FY2022']
        })
        result = calculate_operating_cashflow_growth(cf_data)
        assert result["ocf_cagr_3yr"]["flag"] == "INSUFFICIENT"

    def test_missing_columns(self):
        """Test with missing required columns."""
        cf_data = pd.DataFrame({
            'cash_from_operating_activity': [1000]
        })
        result = calculate_free_cash_flow(cf_data)
        assert result is None

    def test_all_ratings_have_descriptions(self):
        """Test that all ratings have descriptions."""
        from src.analytics.cashflow_kpis import get_capital_allocation_descriptions
        descriptions = get_capital_allocation_descriptions()
        
        assert RATING_EXCELLENT in descriptions
        assert RATING_GOOD in descriptions
        assert RATING_MODERATE in descriptions
        assert RATING_WEAK in descriptions
        assert RATING_DISTRESSED in descriptions
        assert len(descriptions) == 5

    def test_cashflow_descriptions(self):
        """Test cash flow descriptions utility."""
        from src.analytics.cashflow_kpis import get_cashflow_descriptions
        descriptions = get_cashflow_descriptions()
        
        assert "free_cash_flow" in descriptions
        assert "fcf_margin" in descriptions
        assert "cash_conversion" in descriptions
        assert len(descriptions) == 10

    def test_cashflow_formulas(self):
        """Test cash flow formulas utility."""
        from src.analytics.cashflow_kpis import get_cashflow_formulas
        formulas = get_cashflow_formulas()
        
        assert "free_cash_flow" in formulas
        assert "fcf_margin" in formulas
        assert "cash_conversion" in formulas
        assert "FCF" in formulas["free_cash_flow"]