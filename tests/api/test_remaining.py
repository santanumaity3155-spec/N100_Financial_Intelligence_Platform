"""
test_remaining.py

Unit and security tests for Valuation, Portfolio, Documents, and Security handling.
Implements Module 6E testing.
"""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


# =============================================================================
# VALUATION TESTS
# =============================================================================


def test_market_cap_valuation_known():
    response = client.get("/api/v1/market-cap/TCS")
    assert response.status_code == 200
    data = response.json()
    assert "ticker" in data
    assert "company_name" in data
    assert "historical_valuation" in data
    assert isinstance(data["historical_valuation"], list)


def test_market_cap_valuation_invalid_ticker():
    response = client.get("/api/v1/market-cap/INVALID_TICKER_999")
    assert response.status_code == 404


# =============================================================================
# PORTFOLIO TESTS
# =============================================================================


def test_portfolio_stats():
    response = client.get("/api/v1/portfolio/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_kpis" in data
    assert "stats" in data
    assert isinstance(data["stats"], list)
    assert len(data["stats"]) > 0

    first = data["stats"][0]
    assert "kpi" in first
    assert "P10" in first
    assert "P25" in first
    assert "P50" in first
    assert "P75" in first
    assert "P90" in first


# =============================================================================
# DOCUMENT TESTS
# =============================================================================


def test_company_documents_known():
    response = client.get("/api/v1/companies/ABB/documents")
    assert response.status_code == 200
    data = response.json()
    assert "ticker" in data
    assert "documents" in data
    assert isinstance(data["documents"], list)

    if len(data["documents"]) > 0:
        first = data["documents"][0]
        assert "is_url_valid" in first
        assert isinstance(first["is_url_valid"], bool)


def test_company_documents_invalid_ticker():
    response = client.get("/api/v1/companies/NONEXISTENT_TICKER/documents")
    assert response.status_code == 404


# =============================================================================
# SECURITY TESTS
# =============================================================================


@pytest.mark.parametrize(
    "payload",
    [
        "' OR 1=1 --",
        "../../secret",
        "<script>alert(1)</script>",
        "'; DROP TABLE companies; --",
    ],
)
def test_security_malicious_inputs(payload):
    # Test path parameter security
    res_path = client.get(f"/api/v1/companies/{payload}")
    assert res_path.status_code in (400, 404, 422)
    assert "traceback" not in res_path.text.lower()
    assert "sqlite" not in res_path.text.lower()

    # Test query parameter security
    res_query = client.get(f"/api/v1/screener?sector={payload}")
    assert res_query.status_code in (200, 400, 404, 422)
    assert "traceback" not in res_query.text.lower()
    assert "sqlite" not in res_query.text.lower()
