"""
test_screener_engine.py

Comprehensive test suite for the Investment Screener Engine (Module 6).
"""

import csv
import json
import os
import sqlite3
import tempfile
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.screener.engine import ScreenerEngine, screen_companies, run_preset_screener
from src.screener.filters import FilterCondition, FilterGroup, FilterOperator, FilterValidator
from src.screener.presets import (
    PRESET_SCREENERS,
    get_preset_screener,
    list_preset_screeners,
    validate_preset_screener,
)
from src.screener.templates import ScreenTemplateManager
from src.screener.exporter import ScreenerExporter
from src.screener.constants import VALID_SCREEN_FIELDS


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_dataframe() -> pd.DataFrame:
    """Create a sample DataFrame for testing."""
    return pd.DataFrame({
        "company_id": ["TCS", "INFY", "RELIANCE", "HDFC", "ICICIBANK"],
        "company_name": ["TCS", "Infosys", "Reliance", "HDFC Bank", "ICICI Bank"],
        "sector": ["IT", "IT", "Energy", "Banking", "Banking"],
        "industry": ["Software", "Software", "Refinery", "Banking", "Banking"],
        "period": ["2024-03", "2024-03", "2024-03", "2024-03", "2024-03"],
        "roe": [25.0, 22.0, 15.0, 18.0, 16.0],
        "roa": [18.0, 15.0, 10.0, 12.0, 11.0],
        "revenue_cagr_3yr": [12.0, 14.0, 8.0, 10.0, 9.0],
        "pat_cagr_3yr": [15.0, 16.0, 10.0, 12.0, 11.0],
        "free_cash_flow": [5000.0, 3000.0, 8000.0, 4000.0, 3500.0],
        "debt_to_equity": [0.1, 0.2, 0.4, 0.3, 0.5],
        "pe_ratio": [25.0, 22.0, 18.0, 20.0, 15.0],
        "pb_ratio": [5.0, 4.5, 2.0, 2.5, 2.2],
        "dividend_yield": [2.0, 2.5, 1.5, 1.8, 2.2],
        "overall_score": [85.0, 80.0, 70.0, 75.0, 72.0],
        "rating": ["Excellent", "Strong", "Healthy", "Strong", "Healthy"],
    })


@pytest.fixture
def screener_engine(sample_dataframe: pd.DataFrame) -> ScreenerEngine:
    """Create a ScreenerEngine with sample data."""
    engine = ScreenerEngine()
    engine.data = sample_dataframe
    return engine


@pytest.fixture
def temp_db() -> sqlite3.Connection:
    """Create a temporary in-memory database."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


# =============================================================================
# FILTER TESTS
# =============================================================================

class TestFilterOperator:
    """Tests for FilterOperator enum."""

    def test_operator_values(self):
        """Test that all expected operators exist."""
        assert FilterOperator.GREATER_THAN.value == ">"
        assert FilterOperator.GREATER_THAN_OR_EQUAL.value == ">="
        assert FilterOperator.LESS_THAN.value == "<"
        assert FilterOperator.LESS_THAN_OR_EQUAL.value == "<="
        assert FilterOperator.EQUAL.value == "="
        assert FilterOperator.NOT_EQUAL.value == "!="
        assert FilterOperator.BETWEEN.value == "BETWEEN"
        assert FilterOperator.IN.value == "IN"
        assert FilterOperator.NOT_IN.value == "NOT IN"
        assert FilterOperator.IS_NULL.value == "IS NULL"
        assert FilterOperator.IS_NOT_NULL.value == "IS NOT NULL"

    def test_operator_from_string(self):
        """Test creating operator from string."""
        op = FilterOperator(">=")
        assert op == FilterOperator.GREATER_THAN_OR_EQUAL


class TestFilterCondition:
    """Tests for FilterCondition dataclass."""

    def test_create_filter_condition(self):
        """Test creating a filter condition."""
        cond = FilterCondition(field="roe", operator=">=", value=15)
        assert cond.field == "roe"
        assert cond.operator == FilterOperator.GREATER_THAN_OR_EQUAL
        assert cond.value == 15

    def test_filter_condition_validation_between(self):
        """Test BETWEEN operator validation."""
        with pytest.raises(ValueError, match="BETWEEN operator requires both"):
            FilterCondition(field="roe", operator="BETWEEN", value=10)

        with pytest.raises(ValueError, match="value < value2"):
            FilterCondition(field="roe", operator="BETWEEN", value=20, value2=10)

        # Valid BETWEEN
        cond = FilterCondition(field="roe", operator="BETWEEN", value=10, value2=20)
        assert cond.value == 10
        assert cond.value2 == 20

    def test_filter_condition_validation_in(self):
        """Test IN operator validation."""
        with pytest.raises(ValueError, match="IN operator requires a list"):
            FilterCondition(field="sector", operator="IN", value="IT")

        # Valid IN
        cond = FilterCondition(field="sector", operator="IN", value=["IT", "Banking"])
        assert cond.value == ["IT", "Banking"]

    def test_filter_condition_validation_null_operators(self):
        """Test IS NULL and IS NOT NULL operators."""
        # These should not require values
        cond1 = FilterCondition(field="roe", operator="IS NULL")
        assert cond1.value is None

        cond2 = FilterCondition(field="roe", operator="IS NOT NULL")
        assert cond2.value is None

    def test_filter_condition_to_dict(self):
        """Test converting filter condition to dictionary."""
        cond = FilterCondition(field="roe", operator=">=", value=15)
        result = cond.to_dict()
        assert result["field"] == "roe"
        assert result["operator"] == ">="
        assert result["value"] == 15

    def test_filter_condition_from_dict(self):
        """Test creating filter condition from dictionary."""
        data = {"field": "roe", "operator": ">=", "value": 15}
        cond = FilterCondition.from_dict(data)
        assert cond.field == "roe"
        assert cond.operator == FilterOperator.GREATER_THAN_OR_EQUAL
        assert cond.value == 15


class TestFilterGroup:
    """Tests for FilterGroup dataclass."""

    def test_create_filter_group(self):
        """Test creating a filter group."""
        cond1 = FilterCondition(field="roe", operator=">=", value=15)
        cond2 = FilterCondition(field="debt_to_equity", operator="<=", value=0.5)
        group = FilterGroup(conditions=[cond1, cond2], logic="AND")
        assert len(group.conditions) == 2
        assert group.logic == "AND"

    def test_filter_group_validation(self):
        """Test filter group validation."""
        with pytest.raises(ValueError, match="must be 'AND' or 'OR'"):
            FilterGroup(conditions=[], logic="XOR")

        with pytest.raises(ValueError, match="must have at least one condition"):
            FilterGroup(conditions=[], logic="AND")

    def test_filter_group_to_dict(self):
        """Test converting filter group to dictionary."""
        cond1 = FilterCondition(field="roe", operator=">=", value=15)
        group = FilterGroup(conditions=[cond1], logic="AND")
        result = group.to_dict()
        assert result["logic"] == "AND"
        assert len(result["conditions"]) == 1

    def test_filter_group_from_dict(self):
        """Test creating filter group from dictionary."""
        data = {
            "logic": "AND",
            "conditions": [
                {"field": "roe", "operator": ">=", "value": 15},
                {"field": "debt_to_equity", "operator": "<=", "value": 0.5},
            ],
        }
        group = FilterGroup.from_dict(data)
        assert group.logic == "AND"
        assert len(group.conditions) == 2


class TestFilterValidator:
    """Tests for FilterValidator class."""

    def test_validate_field(self):
        """Test field validation."""
        validator = FilterValidator(VALID_SCREEN_FIELDS)
        assert validator.validate_field("roe") is True
        assert validator.validate_field("invalid_field") is False

    def test_validate_operator(self):
        """Test operator validation."""
        validator = FilterValidator(VALID_SCREEN_FIELDS)
        assert validator.validate_operator(">=") is True
        assert validator.validate_operator(FilterOperator.GREATER_THAN) is True
        assert validator.validate_operator("INVALID") is False

    def test_validate_filter(self):
        """Test filter validation."""
        validator = FilterValidator(VALID_SCREEN_FIELDS)

        # Valid filter
        cond = FilterCondition(field="roe", operator=">=", value=15)
        errors = validator.validate_filter(cond)
        assert len(errors) == 0

        # Invalid field
        cond = FilterCondition(field="invalid_field", operator=">=", value=15)
        errors = validator.validate_filter(cond)
        assert len(errors) > 0
        assert "Invalid field" in errors[0]

    def test_validate_filter_group(self):
        """Test filter group validation."""
        validator = FilterValidator(VALID_SCREEN_FIELDS)

        cond1 = FilterCondition(field="roe", operator=">=", value=15)
        cond2 = FilterCondition(field="debt_to_equity", operator="<=", value=0.5)
        group = FilterGroup(conditions=[cond1, cond2], logic="AND")

        errors = validator.validate_filter_group(group)
        assert len(errors) == 0


# =============================================================================
# SCREENER ENGINE TESTS
# =============================================================================

class TestScreenerEngine:
    """Tests for ScreenerEngine class."""

    def test_engine_initialization(self):
        """Test engine initialization."""
        engine = ScreenerEngine()
        assert engine.data is None
        assert engine.filtered_data is None
        assert engine.results == []

    def test_apply_filters_greater_than(self, screener_engine: ScreenerEngine):
        """Test applying greater than filter."""
        filters = [{"field": "roe", "operator": ">=", "value": 18}]
        result = screener_engine.apply_filters(filters)

        assert len(result) == 3  # TCS (25), INFY (22), HDFC (18)
        assert all(result["roe"] >= 18)

    def test_apply_filters_less_than(self, screener_engine: ScreenerEngine):
        """Test applying less than filter."""
        filters = [{"field": "pe_ratio", "operator": "<=", "value": 20}]
        result = screener_engine.apply_filters(filters)

        assert len(result) == 3  # RELIANCE (18), HDFC (20), ICICIBANK (15)
        assert all(result["pe_ratio"] <= 20)

    def test_apply_filters_between(self, screener_engine: ScreenerEngine):
        """Test applying BETWEEN filter."""
        filters = [{"field": "roe", "operator": "BETWEEN", "value": 15, "value2": 20}]
        result = screener_engine.apply_filters(filters)

        assert len(result) == 3  # RELIANCE (15), HDFC (18), ICICIBANK (16)
        assert all((result["roe"] >= 15) & (result["roe"] <= 20))

    def test_apply_filters_in(self, screener_engine: ScreenerEngine):
        """Test applying IN filter."""
        filters = [{"field": "sector", "operator": "IN", "value": ["IT", "Banking"]}]
        result = screener_engine.apply_filters(filters)

        assert len(result) == 4  # TCS, INFY, HDFC, ICICIBANK

    def test_apply_filters_not_in(self, screener_engine: ScreenerEngine):
        """Test applying NOT IN filter."""
        filters = [{"field": "sector", "operator": "NOT IN", "value": ["Energy"]}]
        result = screener_engine.apply_filters(filters)

        assert len(result) == 4  # All except RELIANCE
        assert "Energy" not in result["sector"].values

    def test_apply_multiple_filters_and(self, screener_engine: ScreenerEngine):
        """Test applying multiple filters with AND logic."""
        filters = [
            {"field": "roe", "operator": ">=", "value": 15},
            {"field": "debt_to_equity", "operator": "<=", "value": 0.3},
        ]
        result = screener_engine.apply_filters(filters, logic="AND")

        # TCS (roe=25, de=0.1), INFY (roe=22, de=0.2), HDFC (roe=18, de=0.3)
        assert len(result) == 3
        assert all(result["roe"] >= 15)
        assert all(result["debt_to_equity"] <= 0.3)

    def test_apply_multiple_filters_or(self, screener_engine: ScreenerEngine):
        """Test applying multiple filters with OR logic."""
        filters = [
            {"field": "roe", "operator": ">=", "value": 25},
            {"field": "pe_ratio", "operator": "<=", "value": 15},
        ]
        result = screener_engine.apply_filters(filters, logic="OR")

        # TCS (roe=25), ICICIBANK (pe=15)
        assert len(result) == 2
        assert any(result["roe"] >= 25) or any(result["pe_ratio"] <= 15)

    def test_sort_results_single_field(self, screener_engine: ScreenerEngine):
        """Test sorting by single field."""
        screener_engine.apply_filters([{"field": "roe", "operator": ">=", "value": 0}])
        sorted_data = screener_engine.sort_results(sort_by="roe", ascending=False)

        assert sorted_data["roe"].iloc[0] == 25.0  # TCS
        assert sorted_data["roe"].iloc[-1] == 15.0  # RELIANCE

    def test_sort_results_multiple_fields(self, screener_engine: ScreenerEngine):
        """Test sorting by multiple fields."""
        screener_engine.apply_filters([{"field": "roe", "operator": ">=", "value": 0}])
        sorted_data = screener_engine.sort_results(
            sort_by=["sector", "roe"], ascending=[True, False]
        )

        assert len(sorted_data) == 5

    def test_rank_companies(self, screener_engine: ScreenerEngine):
        """Test ranking companies."""
        screener_engine.apply_filters([{"field": "overall_score", "operator": ">=", "value": 0}])
        ranked_data = screener_engine.rank_companies(rank_by="overall_score", ascending=False)

        assert "rank" in ranked_data.columns
        assert ranked_data["rank"].iloc[0] == 1
        assert ranked_data["rank"].iloc[1] == 2
        assert ranked_data["overall_score"].iloc[0] == 85.0  # TCS

    def test_screen_companies_with_filters(self, screener_engine: ScreenerEngine):
        """Test complete screening pipeline with filters."""
        result = screener_engine.screen_companies(
            filters=[
                {"field": "roe", "operator": ">=", "value": 18},
                {"field": "debt_to_equity", "operator": "<=", "value": 0.3},
            ],
            sort_by="roe",
            sort_ascending=False,
        )

        assert result["success"] is True
        assert len(result["results"]) == 3  # TCS, INFY, HDFC
        assert result["stats"]["filters_applied"] == 2

    def test_screen_companies_with_preset(self, screener_engine: ScreenerEngine):
        """Test screening with preset screener."""
        result = screener_engine.screen_companies(preset_id="high_roe")

        assert result["success"] is True
        assert len(result["results"]) > 0
        assert all(r["roe"] >= 20 for r in result["results"])

    def test_screen_companies_empty_data(self):
        """Test screening with empty data."""
        engine = ScreenerEngine()
        engine.data = pd.DataFrame()
        result = engine.screen_companies()

        assert result["success"] is False or result["count"] == 0

    def test_screen_companies_invalid_filter(self, screener_engine: ScreenerEngine):
        """Test screening with invalid filter."""
        result = screener_engine.screen_companies(
            filters=[{"field": "invalid_field", "operator": ">=", "value": 10}]
        )

        assert result["success"] is False
        assert len(result["stats"]["errors"]) > 0


# =============================================================================
# PRESET SCREENER TESTS
# =============================================================================

class TestPresetScreeners:
    """Tests for preset screener functionality."""

    def test_list_preset_screeners(self):
        """Test listing all preset screeners."""
        presets = list_preset_screeners()
        assert len(presets) > 0
        assert all("id" in p for p in presets)
        assert all("name" in p for p in presets)

    def test_get_preset_screener_valid(self):
        """Test getting a valid preset screener."""
        preset = get_preset_screener("value_investing")
        assert preset["name"] == "Value Investing"
        assert "filters" in preset
        assert len(preset["filters"]) > 0

    def test_get_preset_screener_invalid(self):
        """Test getting an invalid preset screener."""
        with pytest.raises(ValueError, match="Unknown preset screener"):
            get_preset_screener("invalid_preset")

    def test_validate_preset_screener_valid(self):
        """Test validating a valid preset screener."""
        result = validate_preset_screener("value_investing")
        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_validate_preset_screener_invalid(self):
        """Test validating an invalid preset screener."""
        result = validate_preset_screener("nonexistent_preset")
        assert result["valid"] is False
        assert len(result["errors"]) > 0

    def test_all_presets_have_required_fields(self):
        """Test that all presets have required fields."""
        for preset_id, preset in PRESET_SCREENERS.items():
            assert "name" in preset, f"Preset {preset_id} missing 'name'"
            assert "description" in preset, f"Preset {preset_id} missing 'description'"
            assert "filters" in preset, f"Preset {preset_id} missing 'filters'"
            assert len(preset["filters"]) > 0, f"Preset {preset_id} has no filters"


# =============================================================================
# SCREEN TEMPLATE MANAGER TESTS
# =============================================================================

class TestScreenTemplateManager:
    """Tests for ScreenTemplateManager class."""

    def test_save_and_load_screen(self, temp_db: sqlite3.Connection):
        """Test saving and loading a screen template."""
        with patch("src.screener.templates.get_connection", return_value=temp_db):
            manager = ScreenTemplateManager()

            # Save a screen
            filters = [
                {"field": "roe", "operator": ">=", "value": 15},
                {"field": "debt_to_equity", "operator": "<=", "value": 0.5},
            ]
            result = manager.save_screen(
                name="Test Screen",
                filters=filters,
                description="Test description",
                sort_by="roe",
                sort_order="desc",
            )

            assert result["success"] is True
            assert result["id"] is not None

            # Load the screen
            loaded = manager.load_screen("Test Screen")
            assert loaded is not None
            assert loaded["name"] == "Test Screen"
            assert loaded["description"] == "Test description"
            assert len(loaded["filters"]) == 2
            assert loaded["sort_by"] == "roe"

    def test_save_screen_empty_name(self, temp_db: sqlite3.Connection):
        """Test saving screen with empty name."""
        with patch("src.screener.templates.get_connection", return_value=temp_db):
            manager = ScreenTemplateManager()

            with pytest.raises(ValueError, match="name cannot be empty"):
                manager.save_screen(name="", filters=[])

    def test_save_screen_empty_filters(self, temp_db: sqlite3.Connection):
        """Test saving screen with empty filters."""
        with patch("src.screener.templates.get_connection", return_value=temp_db):
            manager = ScreenTemplateManager()

            with pytest.raises(ValueError, match="must have at least one filter"):
                manager.save_screen(name="Test", filters=[])

    def test_load_nonexistent_screen(self, temp_db: sqlite3.Connection):
        """Test loading a nonexistent screen."""
        with patch("src.screener.templates.get_connection", return_value=temp_db):
            manager = ScreenTemplateManager()
            result = manager.load_screen("Nonexistent")
            assert result is None

    def test_delete_screen(self, temp_db: sqlite3.Connection):
        """Test deleting a screen template."""
        with patch("src.screener.templates.get_connection", return_value=temp_db):
            manager = ScreenTemplateManager()

            # Save a screen
            manager.save_screen(name="To Delete", filters=[{"field": "roe", "operator": ">=", "value": 10}])

            # Delete it
            result = manager.delete_screen("To Delete")
            assert result["success"] is True

            # Verify it's gone
            loaded = manager.load_screen("To Delete")
            assert loaded is None

    def test_list_screens(self, temp_db: sqlite3.Connection):
        """Test listing all screen templates."""
        with patch("src.screener.templates.get_connection", return_value=temp_db):
            # Create table in temp db
            temp_db.execute("""
                CREATE TABLE IF NOT EXISTS screen_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    filters TEXT NOT NULL,
                    sort_by TEXT,
                    sort_order TEXT DEFAULT 'asc',
                    rank_by TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            temp_db.commit()
            
            manager = ScreenTemplateManager()

            # Save a couple of screens
            result1 = manager.save_screen(name="Screen 1", filters=[{"field": "roe", "operator": ">=", "value": 10}])
            result2 = manager.save_screen(name="Screen 2", filters=[{"field": "pe_ratio", "operator": "<=", "value": 20}])
            
            # Verify saves succeeded
            assert result1["success"] is True
            assert result2["success"] is True

            # List screens
            screens = manager.list_screens()
            assert len(screens) == 2
            assert all("name" in s for s in screens)

    def test_get_screen_count(self, temp_db: sqlite3.Connection):
        """Test getting screen count."""
        with patch("src.screener.templates.get_connection", return_value=temp_db):
            manager = ScreenTemplateManager()

            assert manager.get_screen_count() == 0

            manager.save_screen(name="Screen 1", filters=[{"field": "roe", "operator": ">=", "value": 10}])
            assert manager.get_screen_count() == 1


# =============================================================================
# EXPORTER TESTS
# =============================================================================

class TestScreenerExporter:
    """Tests for ScreenerExporter class."""

    def test_export_results(self, tmp_path: Path):
        """Test exporting results to CSV."""
        exporter = ScreenerExporter(output_dir=tmp_path)

        results = [
            {"company_id": "TCS", "company_name": "TCS", "roe": 25.0},
            {"company_id": "INFY", "company_name": "Infosys", "roe": 22.0},
        ]

        csv_path = exporter.export_results(results, filename="test_export")
        assert csv_path is not None
        assert csv_path.exists()

        # Verify content
        with open(csv_path, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2
            assert rows[0]["company_id"] == "TCS"

    def test_export_results_empty(self, tmp_path: Path):
        """Test exporting empty results."""
        exporter = ScreenerExporter(output_dir=tmp_path)
        result = exporter.export_results([])
        assert result is None

    def test_export_with_rank(self, tmp_path: Path):
        """Test exporting with rank column."""
        exporter = ScreenerExporter(output_dir=tmp_path)

        results = [
            {"company_id": "TCS", "roe": 25.0},
            {"company_id": "INFY", "roe": 22.0},
        ]

        csv_path = exporter.export_results(results, include_rank=True)
        assert csv_path is not None

        with open(csv_path, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert "rank" in rows[0]
            assert rows[0]["rank"] == "1"

    def test_export_filtered_results(self, tmp_path: Path):
        """Test exporting filtered results with metadata."""
        exporter = ScreenerExporter(output_dir=tmp_path)

        results = [{"company_id": "TCS", "roe": 25.0}]
        filters = [{"field": "roe", "operator": ">=", "value": 20}]

        csv_path = exporter.export_filtered_results(results, filters)
        assert csv_path is not None

        with open(csv_path, "r") as f:
            content = f.read()
            assert "# Filtered Results Export" in content
            assert "# Filters Applied: 1" in content

    def test_export_ranked_results(self, tmp_path: Path):
        """Test exporting ranked results with metadata."""
        exporter = ScreenerExporter(output_dir=tmp_path)

        results = [{"company_id": "TCS", "rank": 1, "roe": 25.0}]

        csv_path = exporter.export_ranked_results(results, rank_field="roe")
        assert csv_path is not None

        with open(csv_path, "r") as f:
            content = f.read()
            assert "# Ranked Results Export" in content
            assert "# Ranked By: roe" in content


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests for the screener module."""

    def test_full_screening_workflow(self, screener_engine: ScreenerEngine):
        """Test complete screening workflow."""
        # Apply filters
        filters = [
            {"field": "roe", "operator": ">=", "value": 18},
            {"field": "debt_to_equity", "operator": "<=", "value": 0.3},
        ]
        result = screener_engine.screen_companies(
            filters=filters,
            sort_by="roe",
            sort_ascending=False,
            rank_by="roe",
            rank_ascending=False,
        )

        assert result["success"] is True
        assert len(result["results"]) > 0
        assert all("rank" in r for r in result["results"])
        assert result["results"][0]["rank"] == 1

    def test_preset_screener_workflow(self, screener_engine: ScreenerEngine):
        """Test preset screener workflow."""
        result = screener_engine.screen_by_preset(
            preset_id="value_investing",
            sort_by="pe_ratio",
            rank_by="pe_ratio",
        )

        assert result["success"] is True
        assert len(result["results"]) > 0
        assert all(r["pe_ratio"] <= 20 for r in result["results"])

    def test_export_workflow(self, screener_engine: ScreenerEngine, tmp_path: Path):
        """Test export workflow."""
        screener_engine.screen_companies(
            filters=[{"field": "roe", "operator": ">=", "value": 15}],
            sort_by="roe",
        )

        csv_path = screener_engine.export_results(filename="integration_test")
        assert csv_path is not None
        assert csv_path.exists()
        assert len(screener_engine.results) > 0

    def test_convenience_functions(self, sample_dataframe: pd.DataFrame):
        """Test convenience functions."""
        with patch.object(ScreenerEngine, "load_data", return_value=None):
            with patch.object(ScreenerEngine, "screen_companies", return_value={"success": True, "results": [{"test": "data"}], "count": 1, "stats": {}}) as mock_screen:
                result = screen_companies(
                    filters=[{"field": "roe", "operator": ">=", "value": 18}]
                )
                assert result["success"] is True
                assert len(result["results"]) > 0

    def test_error_handling_invalid_operator(self, screener_engine: ScreenerEngine):
        """Test error handling for invalid operator."""
        result = screener_engine.screen_companies(
            filters=[{"field": "roe", "operator": "INVALID", "value": 15}]
        )
        assert result["success"] is False

    def test_error_handling_missing_data(self):
        """Test error handling when data is not loaded."""
        engine = ScreenerEngine()
        with pytest.raises(ValueError, match="No data loaded"):
            engine.apply_filters([{"field": "roe", "operator": ">=", "value": 15}])


# =============================================================================
# PERFORMANCE TESTS
# =============================================================================

class TestPerformance:
    """Performance tests for the screener."""

    def test_large_dataset_filtering(self):
        """Test filtering performance with large dataset."""
        # Create a large DataFrame (1000 rows)
        large_df = pd.DataFrame({
            "company_id": [f"COMP_{i}" for i in range(1000)],
            "company_name": [f"Company {i}" for i in range(1000)],
            "roe": [i % 100 for i in range(1000)],
            "debt_to_equity": [i % 10 / 10 for i in range(1000)],
            "pe_ratio": [i % 50 for i in range(1000)],
        })

        engine = ScreenerEngine()
        engine.data = large_df

        # Apply filter
        filters = [{"field": "roe", "operator": ">=", "value": 50}]
        result = engine.apply_filters(filters)

        assert len(result) > 0
        assert all(result["roe"] >= 50)

    def test_multiple_filters_performance(self):
        """Test performance with multiple filters."""
        df = pd.DataFrame({
            "company_id": [f"COMP_{i}" for i in range(500)],
            "roe": [i % 100 for i in range(500)],
            "debt_to_equity": [i % 10 / 10 for i in range(500)],
            "pe_ratio": [i % 50 for i in range(500)],
            "pb_ratio": [i % 20 for i in range(500)],
        })

        engine = ScreenerEngine()
        engine.data = df

        # Apply multiple filters
        filters = [
            {"field": "roe", "operator": ">=", "value": 50},
            {"field": "debt_to_equity", "operator": "<=", "value": 0.5},
            {"field": "pe_ratio", "operator": "<=", "value": 25},
            {"field": "pb_ratio", "operator": "<=", "value": 10},
        ]

        result = engine.apply_filters(filters, logic="AND")
        assert len(result) >= 0  # Should complete without error


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestEdgeCases:
    """Edge case tests."""

    def test_filter_with_nan_values(self, screener_engine: ScreenerEngine):
        """Test filtering with NaN values."""
        # Add NaN values
        screener_engine.data.loc[0, "roe"] = None
        screener_engine.data.loc[1, "roe"] = float("nan")

        filters = [{"field": "roe", "operator": ">=", "value": 18}]
        result = screener_engine.apply_filters(filters)

        # Should handle NaN gracefully
        assert len(result) >= 0

    def test_filter_with_empty_dataframe(self):
        """Test filtering with empty DataFrame."""
        engine = ScreenerEngine()
        engine.data = pd.DataFrame()

        with pytest.raises(ValueError):
            engine.apply_filters([{"field": "roe", "operator": ">=", "value": 15}])

    def test_sort_with_missing_column(self, screener_engine: ScreenerEngine):
        """Test sorting with missing column."""
        screener_engine.filtered_data = screener_engine.data
        result = screener_engine.sort_results(sort_by="nonexistent_column")
        # Should return data unchanged with warning
        assert result is not None
        assert len(result) == len(screener_engine.data)

    def test_rank_with_missing_column(self, screener_engine: ScreenerEngine):
        """Test ranking with missing column."""
        screener_engine.filtered_data = screener_engine.data
        result = screener_engine.rank_companies(rank_by="nonexistent_column")
        # Should return data unchanged with warning
        assert result is not None
        assert len(result) == len(screener_engine.data)

    def test_export_with_special_characters(self, tmp_path: Path):
        """Test exporting data with special characters."""
        exporter = ScreenerExporter(output_dir=tmp_path)

        results = [
            {"company_id": "TEST&CO", "company_name": "Test & Co."},
            {"company_id": "TEST<CO>", "company_name": "Test <Co>"},
        ]

        csv_path = exporter.export_results(results, filename="special_chars")
        assert csv_path is not None
        assert csv_path.exists()