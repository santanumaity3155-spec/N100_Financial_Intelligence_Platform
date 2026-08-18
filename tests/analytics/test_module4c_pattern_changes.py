"""
test_module4c_pattern_changes.py

Dedicated test suite for Module 4C: Year-over-Year Capital Allocation Pattern Changes
N100 Financial Intelligence Platform (Sprint 5)
"""

import os
import pytest
import pandas as pd
from pathlib import Path

from src.database.connection import get_connection
from src.config.constants import OUTPUT_DIR
from src.analytics.capital_allocation_distribution import SUPPORTED_PATTERNS
from src.analytics.capital_allocation_pattern_changes import (
    get_available_years,
    compute_year_classifications,
    compute_pattern_changes,
    generate_output_files,
    run_module4c_pipeline,
)


@pytest.fixture
def db_conn():
    conn = get_connection()
    yield conn


def test_get_available_years(db_conn):
    years = get_available_years(db_conn)
    assert isinstance(years, list)
    assert len(years) > 0
    assert years == sorted(years, reverse=True)
    assert 2024 in years


def test_compute_year_classifications(db_conn):
    df_2024 = compute_year_classifications(2024, db_conn)
    assert isinstance(df_2024, pd.DataFrame)
    assert not df_2024.empty
    expected_cols = [
        'company_id', 'company_name', 'sector', 'year',
        'capital_allocation_rating', 'capital_allocation_pattern', 'has_data'
    ]
    for col in expected_cols:
        assert col in df_2024.columns
    assert len(df_2024) == 94


def test_compute_pattern_changes():
    changes_df, summary = compute_pattern_changes()
    assert isinstance(changes_df, pd.DataFrame)
    assert isinstance(summary, dict)
    assert 'total_companies' in summary
    assert summary['total_companies'] == 94
    assert 'companies_changed_pattern' in summary
    assert summary['companies_changed_pattern'] == len(changes_df)


def test_pattern_changes_year_ordering():
    changes_df, _ = compute_pattern_changes()
    if not changes_df.empty:
        invalid_years = changes_df[changes_df['previous_year'] >= changes_df['latest_year']]
        assert invalid_years.empty, "Found rows where previous_year >= latest_year"


def test_pattern_changes_only_diffs():
    changes_df, _ = compute_pattern_changes()
    if not changes_df.empty:
        same_patterns = changes_df[changes_df['previous_pattern'] == changes_df['latest_pattern']]
        assert same_patterns.empty, "Found rows where previous_pattern == latest_pattern"


def test_pattern_changes_valid_patterns():
    changes_df, _ = compute_pattern_changes()
    if not changes_df.empty:
        for pattern in changes_df['previous_pattern']:
            assert pattern in SUPPORTED_PATTERNS, f"Invalid previous pattern: {pattern}"
        for pattern in changes_df['latest_pattern']:
            assert pattern in SUPPORTED_PATTERNS, f"Invalid latest pattern: {pattern}"


def test_no_duplicate_companies():
    changes_df, _ = compute_pattern_changes()
    if not changes_df.empty:
        assert changes_df['company_id'].is_unique, "Duplicate companies found in pattern changes"


def test_summary_reconciliation():
    _, summary = compute_pattern_changes()
    total = summary['total_companies']
    with_prev = summary['companies_with_previous_year']
    insufficient = summary['companies_insufficient_history']
    changed = summary['companies_changed_pattern']
    unchanged = summary['companies_unchanged_pattern']

    assert total == with_prev + insufficient
    assert with_prev == changed + unchanged


def test_output_csv_generation(tmp_path):
    changes_df, summary = compute_pattern_changes()
    output_files = generate_output_files(changes_df, summary, output_dir=tmp_path)

    assert 'pattern_changes' in output_files
    changes_path = output_files['pattern_changes']
    assert changes_path.exists()

    df_out = pd.read_csv(changes_path)
    assert len(df_out) == len(changes_df)


def test_pipeline_execution():
    result = run_module4c_pipeline()
    assert 'changes_df' in result
    assert 'summary' in result
    assert 'output_files' in result
    pattern_changes_file = OUTPUT_DIR / "pattern_changes.csv"
    assert pattern_changes_file.exists()


def test_insufficient_history_handling(db_conn):
    # ATGL has missing cash flow data for historical years
    df_2024 = compute_year_classifications(2024, db_conn)
    atgl_row = df_2024[df_2024['company_id'] == 'ATGL']
    assert not atgl_row.empty