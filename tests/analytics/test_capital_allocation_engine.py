"""
test_capital_allocation_engine.py

Unit tests for Capital Allocation Engine specifically for Module 4A validation.
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
from src.analytics.cashflow_kpis import (
    classify_capital_allocation,
    RATING_EXCELLENT,
    RATING_GOOD,
    RATING_MODERATE,
    RATING_WEAK,
    RATING_DISTRESSED
)


class TestCapitalAllocationEngine:
    """Test cases for Capital Allocation Engine validation."""

    def test_excellent_classification(self):
        """Test EXCELLENT classification."""
        # Excellent: Positive FCF, Cash Conversion >100%, CapEx Intensity <50%
        rating = classify_capital_allocation(500, 120, 40, 1000)
        assert rating == RATING_EXCELLENT

    def test_good_classification_high_conversion(self):
        """Test GOOD classification with high conversion."""
        # Good: Positive FCF, Cash Conversion >80% (but not Excellent due to CapEx)
        rating = classify_capital_allocation(500, 95, 60, 1000)
        assert rating == RATING_GOOD

    def test_moderate_classification(self):
        """Test MODERATE classification."""
        # Moderate: Positive FCF, Cash Conversion >50%
        rating = classify_capital_allocation(500, 70, 60, 1000)
        assert rating == RATING_MODERATE

    def test_weak_classification(self):
        """Test WEAK classification."""
        # Weak: Positive FCF, Cash Conversion <50%
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

    def test_distressed_missing_fcf(self):
        """Test DISTRESSED classification with missing FCF."""
        rating = classify_capital_allocation(None, 90, 60, 1000)
        assert rating == RATING_DISTRESSED

    def test_distressed_missing_ocf(self):
        """Test DISTRESSED classification with missing OCF."""
        rating = classify_capital_allocation(500, 90, 60, None)
        assert rating == RATING_DISTRESSED

    def test_moderate_missing_conversion(self):
        """Test MODERATE classification when cash conversion is None."""
        # When cash_conversion is None but FCF and OCF are present and positive -> MODERATE
        rating = classify_capital_allocation(500, None, 60, 1000)
        assert rating == RATING_MODERATE

    def test_edge_case_zero_values(self):
        """Test edge cases with zero values."""
        # Zero FCF but positive OCF and conversion -> depends on conversion value
        # FCF = 0 (not negative), OCF = 100 (positive), cash_conversion = 75 (<80, >50) -> MODERATE
        rating = classify_capital_allocation(0, 75, 30, 100)
        assert rating == RATING_MODERATE

        # Zero OCF with positive FCF and conversion -> GOOD (not distressed as OCF=0 is not <0)
        rating = classify_capital_allocation(100, 90, 60, 0)
        assert rating == RATING_GOOD

    def test_boundary_conditions(self):
        """Test boundary conditions for conversion thresholds."""
        # Exactly 100% conversion should be GOOD (not EXCELLENT, as EXCELLENT requires >100)
        rating = classify_capital_allocation(500, 100.0, 40, 1000)
        assert rating == RATING_GOOD

        # Exactly 80% conversion should be MODERATE (not GOOD, as GOOD requires >80)
        rating = classify_capital_allocation(500, 80.0, 60, 1000)
        assert rating == RATING_MODERATE

        # Exactly 50% conversion should be WEAK (not MODERATE, as MODERATE requires >50)
        rating = classify_capital_allocation(500, 50.0, 60, 1000)
        assert rating == RATING_WEAK

        # Exactly 50% CapEx Intensity should allow EXCELLENT if conversion >100
        rating = classify_capital_allocation(500, 101, 50.0, 1000)
        # Conversion >100 but CapEx Intensity = 50 (not <50) -> GOOD
        assert rating == RATING_GOOD

        # CapEx Intensity just under 50 should allow EXCELLENT
        rating = classify_capital_allocation(500, 101, 49.9, 1000)
        # Conversion >100 and CapEx Intensity <50 -> EXCELLENT
        assert rating == RATING_EXCELLENT


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])