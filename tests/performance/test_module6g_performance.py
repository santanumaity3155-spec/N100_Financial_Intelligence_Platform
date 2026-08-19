"""
test_module6g_performance.py

Module 6G — Master Performance Test Suite.

Requirements:
1. 10 concurrent screener API requests complete within 10.0 seconds with 100% success.
2. Company profile backend data load for 5 distinct tickers each completes in < 3.0 seconds.
"""

import time
import sqlite3
import importlib
import pytest

from src.config.settings import SQLITE_DATABASE

try:
    from tests.performance.test_screener_load import run_concurrent_screener_load_test
except ImportError:
    from test_screener_load import run_concurrent_screener_load_test

profile_module = importlib.import_module("src.dashboard.pages.02_profile")
load_company_full_intelligence = profile_module.load_company_full_intelligence


def get_5_representative_tickers():
    """
    Retrieve 5 distinct valid tickers from the authoritative database.
    """
    conn = sqlite3.connect(SQLITE_DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    rows = cursor.execute("""
        SELECT company_id 
        FROM companies 
        ORDER BY company_id
        LIMIT 5
    """).fetchall()
    conn.close()

    tickers = [r["company_id"] for r in rows]
    return tickers


def test_10_concurrent_screener_requests():
    """
    Validation 1: 10 Concurrent Screener Requests <= 10.0s.
    """
    load_metrics = run_concurrent_screener_load_test(concurrency=10)

    total_time = load_metrics["total_wall_clock_seconds"]
    successful = load_metrics["successful_requests"]

    print(f"\n=== Screener Load Test Result ===")
    print(f"Total Wall-Clock Duration: {total_time:.3f} s")
    print(f"Successful Requests: {successful}/10")

    assert successful == 10, f"Expected 10 successful requests, got {successful}."
    assert (
        total_time <= 10.0
    ), f"FAILED: Concurrent screener test exceeded 10-second target. Actual: {total_time:.2f} seconds."


def test_company_profile_performance_5_tickers():
    """
    Validation 2: Company Profile screen load time for 5 tickers (< 3.0s each).
    Measurement method: Measures the backend intelligence loading function `load_company_full_intelligence(ticker)`.
    """
    tickers = get_5_representative_tickers()
    assert len(tickers) == 5, f"Expected 5 distinct tickers, found {len(tickers)}."

    print(f"\n=== Company Profile Load Performance (5 Tickers) ===")
    print(f"{'Ticker':<12} | {'Duration (s)':<12} | {'Target':<10} | {'Status':<6}")
    print("-" * 50)

    failed_tickers = []
    for ticker in tickers:
        start_time = time.perf_counter()
        data = load_company_full_intelligence(ticker)
        end_time = time.perf_counter()
        duration = end_time - start_time
        passed = duration < 3.0
        status_str = "PASS" if passed else "FAIL"

        print(f"{ticker:<12} | {duration:<12.3f} | < 3.0 s    | {status_str:<6}")

        assert (
            data and data.get("profile") is not None
        ), f"Failed to load profile data for ticker {ticker}"

        if not passed:
            failed_tickers.append((ticker, duration))

    assert (
        len(failed_tickers) == 0
    ), f"FAILED: Company Profile load time exceeded 3-second target for tickers: {failed_tickers}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
