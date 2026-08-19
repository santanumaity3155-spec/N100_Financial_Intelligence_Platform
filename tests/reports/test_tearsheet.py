"""
test_tearsheet.py

Unit tests for Day 33 & Day 34 PDF Company Tearsheet Generator.
"""

import os
import re
import pytest
from pathlib import Path
import pandas as pd

from src.reports.tearsheet import (
    CompanyTearsheetGenerator,
    generate_company_tearsheet,
    generate_batch_tearsheets,
)
from src.config.constants import REPORTS_DIR, OUTPUT_DIR


def test_tearsheet_pdf_generation(tmp_path):
    """
    Test generating a tearsheet for TCS.
    """
    out_pdf = tmp_path / "TCS_test_tearsheet.pdf"
    res_path = generate_company_tearsheet("TCS", output_path=out_pdf)
    assert res_path.exists()
    assert res_path.stat().st_size > 30 * 1024  # > 30 KB requirement


def test_tearsheet_two_page_requirement(tmp_path):
    """
    Verify that generated company tearsheet PDF is exactly 2 pages.
    """
    out_pdf = tmp_path / "RELIANCE_test_tearsheet.pdf"
    res_path = generate_company_tearsheet("RELIANCE", output_path=out_pdf)

    with open(res_path, "rb") as f:
        content = f.read()
    page_count = len(re.findall(rb"/Type\s*/Page\b", content))
    assert page_count == 2, f"Expected 2 pages, found {page_count}"


def test_tearsheet_insufficient_data_handling():
    """
    Verify skip condition for companies with < 3 years of data (e.g., ATGL).
    """
    gen = CompanyTearsheetGenerator("ATGL")
    has_data, reason = gen.has_sufficient_data()
    assert not has_data
    assert "Fewer than 3 years" in reason

    with pytest.raises(ValueError, match="Cannot generate tearsheet for ATGL"):
        generate_company_tearsheet("ATGL")


def test_tearsheet_pros_cons_retrieval():
    """
    Test pros and cons retrieval for a company.
    """
    gen = CompanyTearsheetGenerator("TCS")
    signals = gen.pros_cons
    assert "pros" in signals
    assert "cons" in signals
    assert isinstance(signals["pros"], list)
    assert isinstance(signals["cons"], list)


def test_tearsheet_capital_allocation_retrieval():
    """
    Test capital allocation rating and pattern retrieval.
    """
    gen = CompanyTearsheetGenerator("HDFCBANK")
    ca = gen.capital_alloc
    assert "rating" in ca
    assert "pattern" in ca


def test_batch_tearsheet_generation():
    """
    Test batch generation execution and output logs.
    """
    res = generate_batch_tearsheets()
    assert "total_universe" in res
    assert res["total_universe"] > 0
    assert res["generated_count"] > 0
    assert res["skipped_count"] >= 1

    skipped_csv = Path(res["skipped_log"])
    assert skipped_csv.exists()

    failures_csv = Path(res["failures_log"])
    assert failures_csv.exists()

    # Verify ATGL is logged as skipped
    df_skipped = pd.read_csv(skipped_csv)
    assert "ATGL" in df_skipped["company_id"].values
