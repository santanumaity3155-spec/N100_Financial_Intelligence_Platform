"""
test_screener.py

Unit tests for Screener endpoint (GET /api/v1/screener).
Implements Module 6E testing.
"""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_screener_no_filter():
    response = client.get("/api/v1/screener")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    first = data[0]
    assert "company_id" in first
    assert "company_name" in first
    assert "rank" in first


def test_screener_min_roe_filter():
    response = client.get("/api/v1/screener?min_roe=15.0")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    for item in data:
        if item.get("roe") is not None:
            assert item["roe"] >= 15.0


def test_screener_max_de_filter():
    response = client.get("/api/v1/screener?max_de=1.0")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    for item in data:
        if item.get("debt_to_equity") is not None:
            assert item["debt_to_equity"] <= 1.0


def test_screener_min_fcf_filter():
    response = client.get("/api/v1/screener?min_fcf=0.0")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    for item in data:
        if item.get("free_cash_flow") is not None:
            assert item["free_cash_flow"] >= 0.0


def test_screener_sector_filter():
    response = client.get("/api/v1/screener?sector=IT%20Services")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    for item in data:
        assert "it" in item["sector"].lower() or "services" in item["sector"].lower()


def test_screener_min_rev_cagr_5yr_filter():
    response = client.get("/api/v1/screener?min_rev_cagr_5yr=5.0")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    for item in data:
        if item.get("revenue_cagr_5yr") is not None:
            assert item["revenue_cagr_5yr"] >= 5.0


def test_screener_min_pat_cagr_5yr_filter():
    response = client.get("/api/v1/screener?min_pat_cagr_5yr=5.0")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    for item in data:
        if item.get("pat_cagr_5yr") is not None:
            assert item["pat_cagr_5yr"] >= 5.0


def test_screener_max_pe_filter():
    response = client.get("/api/v1/screener?max_pe=50.0")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    for item in data:
        if item.get("pe_ratio") is not None:
            assert item["pe_ratio"] <= 50.0


def test_screener_multiple_filters():
    response = client.get("/api/v1/screener?min_roe=10.0&max_de=2.0&max_pe=100.0")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_screener_invalid_numeric_parameter():
    response = client.get("/api/v1/screener?min_roe=invalid_string")
    assert response.status_code == 400


def test_screener_empty_valid_result():
    response = client.get("/api/v1/screener?min_roe=9999.0")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0
