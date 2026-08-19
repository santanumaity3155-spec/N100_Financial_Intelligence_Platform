"""
test_screener_load.py

Module 6G — 10 Concurrent Screener Request Load Test.

Target:
- 10 concurrent screener API requests using Python threading / ThreadPoolExecutor.
- ALL 10 requests complete within 10 seconds (total_elapsed_seconds <= 10.0).
- ALL 10 requests return HTTP 200 success.
"""

import time
import pytest
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def execute_screener_request(request_id: int):
    """
    Execute a single screener API request and measure individual latency.
    """
    start_time = time.perf_counter()
    try:
        response = client.get("/api/v1/screener?min_roe=15")
        end_time = time.perf_counter()
        duration = end_time - start_time
        return {
            "request_id": request_id,
            "status_code": response.status_code,
            "duration": duration,
            "success": response.status_code == 200,
            "item_count": len(response.json()) if response.status_code == 200 else 0,
            "error": None,
        }
    except Exception as exc:
        end_time = time.perf_counter()
        return {
            "request_id": request_id,
            "status_code": 500,
            "duration": end_time - start_time,
            "success": False,
            "item_count": 0,
            "error": str(exc),
        }


def run_concurrent_screener_load_test(concurrency: int = 10):
    """
    Run N concurrent screener requests using ThreadPoolExecutor and return performance metrics.
    """
    start_wall_clock = time.perf_counter()
    results = []

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [
            executor.submit(execute_screener_request, i + 1)
            for i in range(concurrency)
        ]
        for future in as_completed(futures):
            results.append(future.result())

    end_wall_clock = time.perf_counter()
    total_duration = end_wall_clock - start_wall_clock

    # Sort by request_id for clean reporting
    results.sort(key=lambda r: r["request_id"])

    successful = sum(1 for r in results if r["success"])
    failed = sum(1 for r in results if not r["success"])

    return {
        "concurrency": concurrency,
        "total_wall_clock_seconds": total_duration,
        "successful_requests": successful,
        "failed_requests": failed,
        "results": results,
    }


def test_10_concurrent_screener_requests():
    """
    Module 6G Requirement 1:
    Run 10 concurrent screener API requests using Python threading.
    Target: ALL 10 requests complete within 10 seconds.
    """
    load_metrics = run_concurrent_screener_load_test(concurrency=10)

    total_time = load_metrics["total_wall_clock_seconds"]
    successful = load_metrics["successful_requests"]
    failed = load_metrics["failed_requests"]

    print(f"\n=== Screener Load Test Metrics ===")
    print(f"Total Wall-Clock Time: {total_time:.3f} s")
    print(f"Successful Requests: {successful}/10")
    print(f"Failed Requests: {failed}/10")

    for res in load_metrics["results"]:
        print(f"Req #{res['request_id']}: Status={res['status_code']}, Time={res['duration']:.3f}s, Items={res['item_count']}")

    assert successful == 10, f"Expected 10 successful requests, but got {successful} success, {failed} failed."
    assert total_time <= 10.0, f"Concurrent screener test exceeded 10-second target. Actual: {total_time:.2f} seconds."


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
