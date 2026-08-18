"""
test_sector_report.py

Unit tests for Day 34 Sector PDF Report Generator.
"""

import os
import re
import pytest
from pathlib import Path
import pandas as pd

from src.reports.sector_report import SectorReportGenerator, generate_sector_report, generate_all_sector_reports
from src.config.constants import REPORTS_DIR


def test_single_sector_report_generation(tmp_path):
    """
    Test generating a sector report for Financial Services.
    """
    out_pdf = tmp_path / "Financial_Services_test.pdf"
    res_path = generate_sector_report("Financial Services", output_path=out_pdf)
    assert res_path.exists()
    assert res_path.stat().st_size > 1000  # Non-empty PDF


def test_sector_report_company_data_loading():
    """
    Test loading company data for a sector.
    """
    gen = SectorReportGenerator("Information Technology")
    df = gen.company_data
    assert not df.empty
    assert "TCS" in df["company_id"].values
    assert "INFY" in df["company_id"].values
    assert len(df) >= 4


def test_generate_all_11_sector_reports():
    """
    Test generating all 11 broad sector report PDFs.
    """
    pdfs = generate_all_sector_reports()
    assert len(pdfs) == 11
    for p in pdfs:
        assert Path(p).exists()
        assert Path(p).stat().st_size > 1000
