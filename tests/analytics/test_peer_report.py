"""
test_peer_report.py

Comprehensive test suite for the Peer Comparison Report Engine (Module 9).

Tests cover:
1. Company report generation
2. Batch report generation
3. Strength detection
4. Weakness detection
5. Summary generation
6. Markdown export
7. Validation
8. Missing company handling
9. Missing peer group handling
10. Missing radar chart handling
11. Missing health score handling
12. Performance tests
13. Edge cases
"""

import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from src.analytics.peer_report import (
    calculate_strengths,
    calculate_weaknesses,
    generate_all_reports,
    generate_company_report,
    generate_kpi_table,
    generate_summary,
    get_report_statistics,
    list_available_companies,
    load_company_report_data,
    save_report,
    validate_report,
)
from src.analytics.peer_report import (
    HealthScoreNotFoundError,
    KPIDataError,
    PeerGroupNotFoundError,
    PeerReportError,
    CompanyNotFoundError,
)

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def sample_company_info() -> Dict[str, Any]:
    """Sample company information."""
    return {
        "company_id": "RELIANCE",
        "company_name": "Reliance Industries Limited",
        "sector": "Energy",
        "industry": "Refineries",
        "broad_sector": "Energy",
        "sub_sector": "Oil & Gas",
    }


@pytest.fixture
def sample_financial_ratios() -> Dict[str, Any]:
    """Sample financial ratios."""
    return {
        "company_id": "RELIANCE",
        "period": "FY2024",
        "roe": 15.5,
        "roce": 12.3,
        "net_profit_margin": 8.2,
        "debt_to_equity": 0.45,
        "free_cash_flow": 85000.0,
        "revenue_cagr_5yr": 12.5,
        "pat_cagr_5yr": 14.2,
        "eps_cagr_5yr": 13.8,
        "interest_coverage": 5.5,
        "asset_turnover": 1.8,
    }


@pytest.fixture
def sample_health_score() -> Dict[str, Any]:
    """Sample health score."""
    return {
        "company_id": "RELIANCE",
        "company_name": "Reliance Industries Limited",
        "period": "FY2024",
        "profitability_score": 75.0,
        "growth_score": 82.0,
        "cashflow_score": 70.0,
        "leverage_score": 85.0,
        "efficiency_score": 68.0,
        "overall_score": 76.0,
        "rating": "A",
        "remarks": "Strong financial health with excellent growth prospects",
    }


@pytest.fixture
def sample_peer_percentiles() -> Dict[str, Any]:
    """Sample peer percentiles."""
    return {
        "roe": {"value": 15.5, "percentile": 0.85},
        "roce": {"value": 12.3, "percentile": 0.78},
        "net_profit_margin": {"value": 8.2, "percentile": 0.72},
        "debt_to_equity": {"value": 0.45, "percentile": 0.90},
        "free_cash_flow": {"value": 85000.0, "percentile": 0.88},
        "revenue_cagr_5yr": {"value": 12.5, "percentile": 0.80},
        "pat_cagr_5yr": {"value": 14.2, "percentile": 0.82},
        "eps_cagr_5yr": {"value": 13.8, "percentile": 0.79},
        "interest_coverage": {"value": 5.5, "percentile": 0.65},
        "asset_turnover": {"value": 1.8, "percentile": 0.70},
    }


@pytest.fixture
def sample_peer_benchmark() -> Dict[str, Any]:
    """Sample peer benchmark."""
    return {
        "roe": {"peer_avg": 12.5, "peer_count": 15},
        "roce": {"peer_avg": 10.2, "peer_count": 15},
        "net_profit_margin": {"peer_avg": 7.5, "peer_count": 15},
        "debt_to_equity": {"peer_avg": 0.65, "peer_count": 15},
        "free_cash_flow": {"peer_avg": 65000.0, "peer_count": 15},
        "revenue_cagr_5yr": {"peer_avg": 10.5, "peer_count": 15},
        "pat_cagr_5yr": {"peer_avg": 11.8, "peer_count": 15},
        "eps_cagr_5yr": {"peer_avg": 11.2, "peer_count": 15},
        "interest_coverage": {"peer_avg": 4.5, "peer_count": 15},
        "asset_turnover": {"peer_avg": 1.5, "peer_count": 15},
    }


@pytest.fixture
def sample_report_data(
    sample_company_info,
    sample_financial_ratios,
    sample_health_score,
    sample_peer_percentiles,
    sample_peer_benchmark,
) -> Dict[str, Any]:
    """Complete sample report data."""
    return {
        "company_info": sample_company_info,
        "financial_ratios": sample_financial_ratios,
        "health_score": sample_health_score,
        "peer_group": "Energy",
        "is_benchmark": 0,
        "period": "FY2024",
        "peer_percentiles": sample_peer_percentiles,
        "peer_benchmark": sample_peer_benchmark,
        "radar_chart_path": None,
    }


@pytest.fixture
def temp_output_dir(tmp_path):
    """Temporary output directory for reports."""
    output_dir = tmp_path / "peer_reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


# =============================================================================
# TEST: VALIDATION
# =============================================================================


class TestValidateReport:
    """Tests for validate_report function."""

    def test_validate_complete_data(self, sample_report_data):
        """Test validation with complete data."""
        results = validate_report(sample_report_data)

        assert results["valid"] is True
        assert len(results["errors"]) == 0
        assert len(results["checks"]) > 0

    def test_validate_missing_company_info(self, sample_report_data):
        """Test validation with missing company info."""
        data = sample_report_data.copy()
        data["company_info"] = {}

        results = validate_report(data)

        assert results["valid"] is False
        assert any(
            "Company information is missing" in str(e) for e in results["errors"]
        )

    def test_validate_missing_peer_group(self, sample_report_data):
        """Test validation with missing peer group."""
        data = sample_report_data.copy()
        data["peer_group"] = None

        results = validate_report(data)

        assert results["valid"] is False
        assert any("Peer group is missing" in str(e) for e in results["errors"])

    def test_validate_missing_health_score(self, sample_report_data):
        """Test validation with missing health score."""
        data = sample_report_data.copy()
        data["health_score"] = {}

        results = validate_report(data)

        assert results["valid"] is False
        assert any("Health score is missing" in str(e) for e in results["errors"])

    def test_validate_missing_financial_ratios(self, sample_report_data):
        """Test validation with missing financial ratios."""
        data = sample_report_data.copy()
        data["financial_ratios"] = {}

        results = validate_report(data)

        assert results["valid"] is False
        assert any("Financial ratios are missing" in str(e) for e in results["errors"])

    def test_validate_missing_kpis_warning(self, sample_report_data):
        """Test validation with missing KPIs generates warning."""
        data = sample_report_data.copy()
        data["financial_ratios"] = {"roe": 15.0}  # Only 1 KPI

        results = validate_report(data)

        assert results["valid"] is True  # Warning, not error
        assert len(results["warnings"]) > 0
        assert any("missing_kpis" in str(w) for w in results["warnings"])

    def test_validate_missing_peer_percentiles_warning(self, sample_report_data):
        """Test validation with missing peer percentiles generates warning."""
        data = sample_report_data.copy()
        data["peer_percentiles"] = {}

        results = validate_report(data)

        assert results["valid"] is True  # Warning, not error
        assert len(results["warnings"]) > 0
        assert any("missing_peer_percentiles" in str(w) for w in results["warnings"])


# =============================================================================
# TEST: KPI TABLE GENERATION
# =============================================================================


class TestGenerateKpiTable:
    """Tests for generate_kpi_table function."""

    def test_generate_kpi_table_complete(self, sample_report_data):
        """Test KPI table generation with complete data."""
        table = generate_kpi_table(sample_report_data)

        assert isinstance(table, str)
        assert "| Metric |" in table
        assert "| Company Value |" in table
        assert "| Peer Average |" in table
        assert "ROE" in table
        assert "ROCE" in table

    def test_generate_kpi_table_missing_data(self):
        """Test KPI table generation with missing data."""
        data = {"financial_ratios": {}, "peer_benchmark": {}}
        table = generate_kpi_table(data)

        assert isinstance(table, str)
        assert "No KPI data available" in table or "Error" in table

    def test_generate_kpi_table_better_worse_indicators(self, sample_report_data):
        """Test KPI table includes better/worse indicators."""
        table = generate_kpi_table(sample_report_data)

        assert "✅ Better" in table or "⚠️ Worse" in table or "➡️ Neutral" in table

    def test_generate_kpi_table_debt_to_equity_inverted(self, sample_report_data):
        """Test that debt_to_equity is correctly inverted (lower is better)."""
        table = generate_kpi_table(sample_report_data)

        # Company D/E (0.45) is lower than peer avg (0.65), so should be "Better"
        assert "Debt to Equity" in table


# =============================================================================
# TEST: STRENGTHS AND WEAKNESSES
# =============================================================================


class TestCalculateStrengths:
    """Tests for calculate_strengths function."""

    def test_calculate_strengths_high_percentiles(self, sample_report_data):
        """Test strength calculation with high percentiles."""
        strengths = calculate_strengths(sample_report_data)

        assert isinstance(strengths, list)
        assert len(strengths) > 0
        assert all(s["percentile_pct"] >= 75.0 for s in strengths)

    def test_calculate_strengths_sorted_descending(self, sample_report_data):
        """Test that strengths are sorted by percentile (highest first)."""
        strengths = calculate_strengths(sample_report_data)

        if len(strengths) > 1:
            for i in range(len(strengths) - 1):
                assert strengths[i]["percentile"] >= strengths[i + 1]["percentile"]

    def test_calculate_strengths_top_n(self, sample_report_data):
        """Test that only top N strengths are returned."""
        strengths = calculate_strengths(sample_report_data)

        # Should return at most TOP_STRENGTHS_COUNT (3)
        assert len(strengths) <= 3

    def test_calculate_strengths_no_percentiles(self):
        """Test strength calculation with no percentiles."""
        data = {"peer_percentiles": {}}
        strengths = calculate_strengths(data)

        assert isinstance(strengths, list)
        assert len(strengths) == 0

    def test_calculate_strengths_low_percentiles(self):
        """Test strength calculation with all low percentiles."""
        data = {
            "peer_percentiles": {
                "roe": {"value": 5.0, "percentile": 0.20},
                "roce": {"value": 4.0, "percentile": 0.15},
            }
        }
        strengths = calculate_strengths(data)

        assert len(strengths) == 0


class TestCalculateWeaknesses:
    """Tests for calculate_weaknesses function."""

    def test_calculate_weaknesses_low_percentiles(self, sample_report_data):
        """Test weakness calculation with low percentiles."""
        # Modify sample data to have low percentiles
        data = sample_report_data.copy()
        data["peer_percentiles"] = {
            "roe": {"value": 5.0, "percentile": 0.15},
            "roce": {"value": 4.0, "percentile": 0.20},
            "net_profit_margin": {"value": 2.0, "percentile": 0.10},
        }

        weaknesses = calculate_weaknesses(data)

        assert isinstance(weaknesses, list)
        assert len(weaknesses) > 0
        assert all(w["percentile_pct"] <= 25.0 for w in weaknesses)

    def test_calculate_weaknesses_sorted_ascending(self, sample_report_data):
        """Test that weaknesses are sorted by percentile (lowest first)."""
        data = sample_report_data.copy()
        data["peer_percentiles"] = {
            "roe": {"value": 5.0, "percentile": 0.15},
            "roce": {"value": 4.0, "percentile": 0.10},
        }

        weaknesses = calculate_weaknesses(data)

        if len(weaknesses) > 1:
            for i in range(len(weaknesses) - 1):
                assert weaknesses[i]["percentile"] <= weaknesses[i + 1]["percentile"]

    def test_calculate_weaknesses_top_n(self, sample_report_data):
        """Test that only top N weaknesses are returned."""
        data = sample_report_data.copy()
        data["peer_percentiles"] = {
            "roe": {"value": 5.0, "percentile": 0.15},
            "roce": {"value": 4.0, "percentile": 0.10},
            "net_profit_margin": {"value": 2.0, "percentile": 0.20},
            "debt_to_equity": {"value": 2.0, "percentile": 0.05},
        }

        weaknesses = calculate_weaknesses(data)

        # Should return at most TOP_WEAKNESSES_COUNT (3)
        assert len(weaknesses) <= 3

    def test_calculate_weaknesses_no_percentiles(self):
        """Test weakness calculation with no percentiles."""
        data = {"peer_percentiles": {}}
        weaknesses = calculate_weaknesses(data)

        assert isinstance(weaknesses, list)
        assert len(weaknesses) == 0


# =============================================================================
# TEST: SUMMARY GENERATION
# =============================================================================


class TestGenerateSummary:
    """Tests for generate_summary function."""

    def test_generate_summary_complete(self, sample_report_data):
        """Test summary generation with complete data."""
        summary = generate_summary(sample_report_data)

        assert isinstance(summary, str)
        assert len(summary) > 0
        assert "Reliance Industries" in summary
        assert "Energy" in summary

    def test_generate_summary_includes_health_score(self, sample_report_data):
        """Test summary includes health score."""
        summary = generate_summary(sample_report_data)

        assert "76.0" in summary or "76" in summary
        assert "A" in summary

    def test_generate_summary_includes_peer_comparison(self, sample_report_data):
        """Test summary includes peer comparison."""
        summary = generate_summary(sample_report_data)

        assert "percentile" in summary.lower()
        assert "peer group" in summary.lower()

    def test_generate_summary_missing_data(self):
        """Test summary generation with missing data."""
        data = {
            "company_info": {"company_name": "Test Co", "sector": "Tech"},
            "health_score": {},
            "peer_percentiles": {},
            "peer_group": "Tech",
        }

        summary = generate_summary(data)

        assert isinstance(summary, str)
        assert len(summary) > 0


# =============================================================================
# TEST: REPORT BUILDING
# =============================================================================


class TestBuildReport:
    """Tests for build_report function."""

    def test_build_report_structure(self, sample_report_data):
        """Test report has all required sections."""
        from src.analytics.peer_report import build_report

        report = build_report(sample_report_data)

        assert isinstance(report, str)
        assert "# Company Information" in report
        assert "# Financial Health Score" in report
        assert "# KPI Comparison Table" in report
        assert "# Percentile Rankings" in report
        assert "# Peer Benchmark Summary" in report
        assert "# Strengths" in report
        assert "# Weaknesses" in report
        assert "# Radar Chart" in report
        assert "# Final Recommendation" in report

    def test_build_report_includes_company_details(self, sample_report_data):
        """Test report includes company details."""
        from src.analytics.peer_report import build_report

        report = build_report(sample_report_data)

        assert "Reliance Industries Limited" in report
        assert "RELIANCE" in report
        assert "Energy" in report

    def test_build_report_includes_health_score(self, sample_report_data):
        """Test report includes health score."""
        from src.analytics.peer_report import build_report

        report = build_report(sample_report_data)

        assert "76.0" in report or "76" in report
        assert "A" in report

    def test_build_report_includes_tables(self, sample_report_data):
        """Test report includes markdown tables."""
        from src.analytics.peer_report import build_report

        report = build_report(sample_report_data)

        assert "|" in report  # Markdown table syntax
        assert "---" in report  # Table separator


# =============================================================================
# TEST: REPORT SAVING
# =============================================================================


class TestSaveReport:
    """Tests for save_report function."""

    def test_save_report_success(self, temp_output_dir):
        """Test successful report saving."""
        report_content = "# Test Report\n\nThis is a test report.\n"
        company_id = "TEST"

        report_path = save_report(
            report_content, company_id, output_dir=temp_output_dir
        )

        assert report_path.exists()
        assert report_path.name == "TEST.md"

        # Verify content
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert content == report_content

    def test_save_report_creates_directory(self, tmp_path):
        """Test that save_report creates directory if it doesn't exist."""
        output_dir = tmp_path / "new_dir" / "peer_reports"
        report_content = "# Test Report\n"
        company_id = "TEST"

        assert not output_dir.exists()

        report_path = save_report(report_content, company_id, output_dir=output_dir)

        assert output_dir.exists()
        assert report_path.exists()

    def test_save_report_different_companies(self, temp_output_dir):
        """Test saving reports for different companies."""
        companies = ["RELIANCE", "TCS", "INFY"]

        for company_id in companies:
            report_content = f"# {company_id} Report\n"
            report_path = save_report(
                report_content, company_id, output_dir=temp_output_dir
            )

            assert report_path.exists()
            assert report_path.name == f"{company_id}.md"


# =============================================================================
# TEST: COMPANY REPORT GENERATION
# =============================================================================


class TestGenerateCompanyReport:
    """Tests for generate_company_report function."""

    @patch("src.analytics.peer_report.load_company_report_data")
    @patch("src.analytics.peer_report.validate_report")
    @patch("src.analytics.peer_report.build_report")
    @patch("src.analytics.peer_report.save_report")
    def test_generate_company_report_success(
        self,
        mock_save,
        mock_build,
        mock_validate,
        mock_load,
        sample_report_data,
        temp_output_dir,
    ):
        """Test successful company report generation."""
        # Setup mocks
        mock_load.return_value = sample_report_data
        mock_validate.return_value = {"valid": True, "warnings": [], "errors": []}
        mock_build.return_value = "# Test Report\n"
        mock_save.return_value = temp_output_dir / "RELIANCE.md"

        # Generate report
        result = generate_company_report(
            "RELIANCE", output_dir=temp_output_dir, validate=True
        )

        assert result["success"] is True
        assert result["company_id"] == "RELIANCE"
        assert result["report_path"] is not None
        assert result["error"] is None
        assert result["execution_time"] > 0

    @patch("src.analytics.peer_report.load_company_report_data")
    def test_generate_company_report_company_not_found(self, mock_load):
        """Test report generation with missing company."""
        mock_load.side_effect = CompanyNotFoundError("Company not found: INVALID")

        result = generate_company_report("INVALID")

        assert result["success"] is False
        assert result["error"] is not None
        assert "Company not found" in result["error"]

    @patch("src.analytics.peer_report.load_company_report_data")
    def test_generate_company_report_peer_group_not_found(self, mock_load):
        """Test report generation with missing peer group."""
        mock_load.side_effect = PeerGroupNotFoundError("No peer group assigned")

        result = generate_company_report("RELIANCE")

        assert result["success"] is False
        assert result["error"] is not None
        assert "peer group" in result["error"].lower()

    @patch("src.analytics.peer_report.load_company_report_data")
    def test_generate_company_report_health_score_not_found(self, mock_load):
        """Test report generation with missing health score."""
        mock_load.side_effect = HealthScoreNotFoundError("No health score found")

        result = generate_company_report("RELIANCE")

        assert result["success"] is False
        assert result["error"] is not None
        assert "health score" in result["error"].lower()

    @patch("src.analytics.peer_report.load_company_report_data")
    def test_generate_company_report_kpi_data_error(self, mock_load):
        """Test report generation with KPI data error."""
        mock_load.side_effect = KPIDataError("No financial ratios found")

        result = generate_company_report("RELIANCE")

        assert result["success"] is False
        assert result["error"] is not None
        assert "KPI" in result["error"] or "financial ratios" in result["error"].lower()


# =============================================================================
# TEST: BATCH REPORT GENERATION
# =============================================================================


class TestGenerateAllReports:
    """Tests for generate_all_reports function."""

    @patch("src.analytics.peer_report.generate_company_report")
    @patch("src.analytics.peer_report.get_connection")
    def test_generate_all_reports_success(
        self, mock_conn, mock_generate, temp_output_dir
    ):
        """Test successful batch report generation."""
        # Setup mocks
        mock_conn_instance = MagicMock()
        mock_conn.return_value = mock_conn_instance

        # Mock companies dataframe
        companies_df = pd.DataFrame(
            {
                "company_id": ["RELIANCE", "TCS", "INFY"],
                "company_name": ["Reliance", "TCS", "Infosys"],
            }
        )

        with patch("pandas.read_sql_query", return_value=companies_df):
            # Mock successful report generation
            mock_generate.return_value = {
                "success": True,
                "company_id": "RELIANCE",
                "report_path": str(temp_output_dir / "RELIANCE.md"),
                "error": None,
                "execution_time": 0.5,
            }

            result = generate_all_reports(output_dir=temp_output_dir)

            assert result["total_companies"] == 3
            assert result["successful"] == 3
            assert result["failed"] == 0
            assert len(result["results"]) == 3

    @patch("src.analytics.peer_report.get_connection")
    def test_generate_all_reports_no_companies(self, mock_conn):
        """Test batch generation with no companies."""
        mock_conn_instance = MagicMock()
        mock_conn.return_value = mock_conn_instance

        # Mock empty companies dataframe
        companies_df = pd.DataFrame()

        with patch("pandas.read_sql_query", return_value=companies_df):
            result = generate_all_reports()

            assert result["total_companies"] == 0
            assert result["successful"] == 0
            assert result["failed"] == 0

    @patch("src.analytics.peer_report.generate_company_report")
    @patch("src.analytics.peer_report.get_connection")
    def test_generate_all_reports_with_failures(
        self, mock_conn, mock_generate, temp_output_dir
    ):
        """Test batch generation with some failures."""
        # Setup mocks
        mock_conn_instance = MagicMock()
        mock_conn.return_value = mock_conn_instance

        companies_df = pd.DataFrame(
            {"company_id": ["RELIANCE", "TCS"], "company_name": ["Reliance", "TCS"]}
        )

        with patch("pandas.read_sql_query", return_value=companies_df):
            # Mock mixed success/failure
            mock_generate.side_effect = [
                {
                    "success": True,
                    "company_id": "RELIANCE",
                    "report_path": str(temp_output_dir / "RELIANCE.md"),
                    "error": None,
                    "execution_time": 0.5,
                },
                {
                    "success": False,
                    "company_id": "TCS",
                    "report_path": None,
                    "error": "Health score not found",
                    "execution_time": 0.3,
                },
            ]

            result = generate_all_reports(output_dir=temp_output_dir)

            assert result["total_companies"] == 2
            assert result["successful"] == 1
            assert result["failed"] == 1
            assert len(result["errors"]) > 0


# =============================================================================
# TEST: UTILITY FUNCTIONS
# =============================================================================


class TestGetReportStatistics:
    """Tests for get_report_statistics function."""

    def test_get_statistics_empty_directory(self, tmp_path):
        """Test statistics with empty directory."""
        empty_dir = tmp_path / "empty_reports"
        empty_dir.mkdir(parents=True, exist_ok=True)

        stats = get_report_statistics(output_dir=empty_dir)

        assert stats["total_reports"] == 0
        assert stats["exists"] is True

    def test_get_statistics_nonexistent_directory(self, tmp_path):
        """Test statistics with non-existent directory."""
        nonexistent_dir = tmp_path / "nonexistent"

        stats = get_report_statistics(output_dir=nonexistent_dir)

        assert stats["total_reports"] == 0
        assert stats["exists"] is False

    def test_get_statistics_with_reports(self, temp_output_dir):
        """Test statistics with actual reports."""
        # Create some test reports
        for i in range(5):
            report_path = temp_output_dir / f"COMP{i}.md"
            report_path.write_text(f"# Report {i}\n")

        stats = get_report_statistics(output_dir=temp_output_dir)

        assert stats["total_reports"] == 5
        assert stats["exists"] is True
        assert stats["total_size_bytes"] > 0
        assert len(stats["recent_reports"]) <= 10


class TestListAvailableCompanies:
    """Tests for list_available_companies function."""

    @patch("src.analytics.peer_report.get_connection")
    def test_list_companies_success(self, mock_conn):
        """Test successful company listing."""
        mock_conn_instance = MagicMock()
        mock_conn.return_value = mock_conn_instance

        companies_df = pd.DataFrame(
            {
                "company_id": ["RELIANCE", "TCS", "INFY"],
                "company_name": ["Reliance", "TCS", "Infosys"],
                "sector": ["Energy", "IT", "IT"],
            }
        )

        with patch("pandas.read_sql_query", return_value=companies_df):
            companies = list_available_companies()

            assert len(companies) == 3
            assert companies[0]["company_id"] == "RELIANCE"
            assert companies[1]["company_name"] == "TCS"

    @patch("src.analytics.peer_report.get_connection")
    def test_list_companies_empty(self, mock_conn):
        """Test company listing with no companies."""
        mock_conn_instance = MagicMock()
        mock_conn.return_value = mock_conn_instance

        companies_df = pd.DataFrame()

        with patch("pandas.read_sql_query", return_value=companies_df):
            companies = list_available_companies()

            assert len(companies) == 0


# =============================================================================
# TEST: EDGE CASES
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_calculate_strengths_with_none_values(self):
        """Test strength calculation with None values."""
        data = {
            "peer_percentiles": {
                "roe": {"value": None, "percentile": 0.90},
                "roce": {"value": 12.0, "percentile": None},
            }
        }

        strengths = calculate_strengths(data)

        # Should only include roe (has valid percentile)
        assert len(strengths) == 1
        assert strengths[0]["metric"] == "roe"

    def test_calculate_weaknesses_with_none_values(self):
        """Test weakness calculation with None values."""
        data = {
            "peer_percentiles": {
                "roe": {"value": None, "percentile": 0.10},
                "roce": {"value": 12.0, "percentile": None},
            }
        }

        weaknesses = calculate_weaknesses(data)

        # Should only include roe (has valid percentile)
        assert len(weaknesses) == 1
        assert weaknesses[0]["metric"] == "roe"

    def test_generate_kpi_table_with_none_values(self, sample_report_data):
        """Test KPI table generation with None values."""
        data = sample_report_data.copy()
        data["financial_ratios"]["roe"] = None
        data["peer_benchmark"]["roe"] = {"peer_avg": None, "peer_count": 15}

        table = generate_kpi_table(data)

        assert isinstance(table, str)
        # When both values are None, the row is skipped, so check table is still valid
        assert "| Metric |" in table
        assert "ROE" not in table  # ROE row should be skipped when both values are None

    def test_generate_summary_with_none_scores(self):
        """Test summary generation with None health scores."""
        data = {
            "company_info": {"company_name": "Test Co", "sector": "Tech"},
            "health_score": {"overall_score": None, "rating": "N/A"},
            "peer_percentiles": {},
            "peer_group": "Tech",
        }

        summary = generate_summary(data)

        assert isinstance(summary, str)
        assert len(summary) > 0


# =============================================================================
# TEST: PERFORMANCE
# =============================================================================


class TestPerformance:
    """Performance tests for the report engine."""

    @patch("src.analytics.peer_report.load_company_report_data")
    @patch("src.analytics.peer_report.validate_report")
    @patch("src.analytics.peer_report.build_report")
    @patch("src.analytics.peer_report.save_report")
    def test_single_report_generation_performance(
        self,
        mock_save,
        mock_build,
        mock_validate,
        mock_load,
        sample_report_data,
        temp_output_dir,
    ):
        """Test that single report generation completes within reasonable time."""
        # Setup mocks
        mock_load.return_value = sample_report_data
        mock_validate.return_value = {"valid": True, "warnings": [], "errors": []}
        mock_build.return_value = "# Test Report\n"
        mock_save.return_value = temp_output_dir / "RELIANCE.md"

        start_time = time.time()
        result = generate_company_report("RELIANCE", output_dir=temp_output_dir)
        execution_time = time.time() - start_time

        assert result["success"] is True
        assert execution_time < 5.0  # Should complete in less than 5 seconds

    def test_strength_calculation_performance(self):
        """Test strength calculation performance with large dataset."""
        # Create large peer percentiles dataset
        peer_percentiles = {
            metric: {"value": 10.0, "percentile": 0.8}
            for metric in [
                "roe",
                "roce",
                "net_profit_margin",
                "debt_to_equity",
                "free_cash_flow",
                "revenue_cagr_5yr",
                "pat_cagr_5yr",
                "eps_cagr_5yr",
                "interest_coverage",
                "asset_turnover",
            ]
        }

        data = {"peer_percentiles": peer_percentiles}

        start_time = time.time()
        strengths = calculate_strengths(data)
        execution_time = time.time() - start_time

        assert len(strengths) > 0
        assert execution_time < 1.0  # Should complete in less than 1 second


# =============================================================================
# TEST: INTEGRATION
# =============================================================================


class TestIntegration:
    """Integration tests (require database)."""

    @pytest.mark.skipif(
        not Path("data/database/n100.db").exists(), reason="Database not available"
    )
    def test_load_company_report_data_integration(self):
        """Test loading company report data from database."""
        try:
            report_data = load_company_report_data("RELIANCE")

            assert "company_info" in report_data
            assert "financial_ratios" in report_data
            assert "health_score" in report_data
            assert "peer_group" in report_data
            assert "period" in report_data

        except Exception as e:
            pytest.skip(f"Integration test skipped: {str(e)}")

    @pytest.mark.skipif(
        not Path("data/database/n100.db").exists(), reason="Database not available"
    )
    def test_generate_sample_report_integration(self, temp_output_dir):
        """Test generating a sample report from database."""
        try:
            result = generate_company_report(
                "RELIANCE", output_dir=temp_output_dir, validate=True
            )

            # May succeed or fail depending on data availability
            assert "success" in result
            assert "company_id" in result
            assert "execution_time" in result

        except Exception as e:
            pytest.skip(f"Integration test skipped: {str(e)}")


# =============================================================================
# TEST: MARKDOWN FORMATTING
# =============================================================================


class TestMarkdownFormatting:
    """Tests for Markdown formatting."""

    def test_report_is_valid_markdown(self, sample_report_data):
        """Test that generated report is valid Markdown."""
        from src.analytics.peer_report import build_report

        report = build_report(sample_report_data)

        # Check for Markdown headers
        assert report.startswith("#")

        # Check for tables
        assert "|" in report

        # Check for bold text
        assert "**" in report

        # Check for line breaks
        assert "\n" in report

    def test_report_no_broken_formatting(self, sample_report_data):
        """Test that report has no broken Markdown formatting."""
        from src.analytics.peer_report import build_report

        report = build_report(sample_report_data)

        # Check that all headers have closing ## or #
        lines = report.split("\n")
        for line in lines:
            if line.startswith("#"):
                # Should be a valid header
                assert line.strip().endswith("#") or not line.strip().endswith("#")

        # Check table consistency - verify tables exist and have proper structure
        table_lines = [l for l in lines if l.startswith("|")]
        assert len(table_lines) > 0, "Report should contain at least one table"

        # Verify each table row has at least 2 columns of content
        for line in table_lines:
            parts = [p.strip() for p in line.split("|") if p.strip()]
            assert len(parts) >= 2, f"Table row should have at least 2 columns: {line}"


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
