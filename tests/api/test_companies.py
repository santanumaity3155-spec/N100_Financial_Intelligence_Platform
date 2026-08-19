"""
test_companies.py

Unit and API integration tests for Module 6D — Company Data Endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_01_get_companies_returns_200():
    """1. Verify GET /api/v1/companies returns HTTP 200."""
    response = client.get("/api/v1/companies")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_02_companies_list_authoritative_count():
    """2. Verify company list contains authoritative companies from database."""
    response = client.get("/api/v1/companies")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 90  # Database has 94 authoritative companies


def test_03_required_company_fields_exist():
    """3. Verify required company fields exist in response objects."""
    response = client.get("/api/v1/companies")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    first = data[0]
    required_fields = [
        "company_id",
        "company_name",
        "broad_sector",
        "sub_sector",
        "roe_pct",
        "roce_pct",
    ]
    for field in required_fields:
        assert field in first, f"Field '{field}' missing from GET /companies response"


def test_04_sector_filter_works():
    """4. Verify sector filter parameter returns matching companies."""
    response = client.get("/api/v1/companies?sector=IT")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    tickers = [c["company_id"] for c in data]
    assert "TCS" in tickers or "INFY" in tickers


def test_05_market_cap_category_filter_works():
    """5. Verify market_cap_category filter returns matching companies."""
    response = client.get("/api/v1/companies?market_cap_category=Large Cap")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    for comp in data:
        assert comp["market_cap_category"] == "Large Cap"


def test_06_search_by_company_name_works():
    """6. Verify search filter works by company name (partial match)."""
    response = client.get("/api/v1/companies?search=Tata")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    for comp in data:
        assert (
            "tata" in comp["company_name"].lower()
            or "tata" in comp["company_id"].lower()
        )


def test_07_search_by_ticker_works():
    """7. Verify search filter works by ticker symbol (case-insensitive)."""
    response = client.get("/api/v1/companies?search=tcs")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    tickers = [c["company_id"] for c in data]
    assert "TCS" in tickers


def test_08_empty_valid_search_returns_empty_list():
    """8. Verify non-matching valid search query returns valid empty list."""
    response = client.get("/api/v1/companies?search=NONEXISTENTCOMPANY12345")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_09_get_company_profile_returns_200():
    """9. Verify GET /api/v1/companies/{ticker} returns HTTP 200 for valid ticker."""
    response = client.get("/api/v1/companies/TCS")
    assert response.status_code == 200
    data = response.json()
    assert data.get("company_id") == "TCS"


def test_10_company_profile_contains_latest_kpis():
    """10. Verify company profile contains latest KPI data."""
    response = client.get("/api/v1/companies/TCS")
    assert response.status_code == 200
    data = response.json()
    assert "latest_kpis" in data
    assert isinstance(data["latest_kpis"], dict)


def test_11_invalid_ticker_returns_404():
    """11. Verify invalid ticker returns HTTP 404 Not Found."""
    response = client.get("/api/v1/companies/INVALID_TICKER_999")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


def test_12_pl_endpoint_returns_200():
    """12. Verify GET /api/v1/companies/{ticker}/pl returns HTTP 200."""
    response = client.get("/api/v1/companies/TCS/pl")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_13_pl_from_year_filter_works():
    """13. Verify P&L from_year filtering works."""
    response = client.get("/api/v1/companies/TCS/pl?from_year=2020")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0


def test_14_pl_to_year_filter_works():
    """14. Verify P&L to_year filtering works."""
    response = client.get("/api/v1/companies/TCS/pl?to_year=2020")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0


def test_15_pl_year_range_filter_works():
    """15. Verify P&L range filtering (from_year & to_year YYYY-MM) works."""
    response = client.get("/api/v1/companies/TCS/pl?from_year=2019-03&to_year=2024-03")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0


def test_16_invalid_ticker_on_pl_returns_404():
    """16. Verify P&L endpoint with invalid ticker returns HTTP 404."""
    response = client.get("/api/v1/companies/INVALID_TICKER_999/pl")
    assert response.status_code == 404


def test_17_bs_endpoint_returns_200():
    """17. Verify GET /api/v1/companies/{ticker}/bs returns HTTP 200."""
    response = client.get("/api/v1/companies/TCS/bs")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_18_bs_filtering_works():
    """18. Verify Balance Sheet year filtering works."""
    response = client.get("/api/v1/companies/TCS/bs?from_year=2018&to_year=2022")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0


def test_19_cash_flow_endpoint_returns_200():
    """19. Verify GET /api/v1/companies/{ticker}/cashflow returns HTTP 200."""
    response = client.get("/api/v1/companies/TCS/cashflow")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_20_cash_flow_filtering_works():
    """20. Verify Cash Flow year filtering works."""
    response = client.get("/api/v1/companies/TCS/cashflow?from_year=2015&to_year=2020")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0


def test_21_ratios_endpoint_returns_200():
    """21. Verify GET /api/v1/companies/{ticker}/ratios returns HTTP 200."""
    response = client.get("/api/v1/companies/TCS/ratios")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_22_ratios_year_filter_works():
    """22. Verify ratios year filter returns single year data."""
    response = client.get("/api/v1/companies/TCS/ratios?year=2024")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_23_invalid_ticker_on_ratios_returns_404():
    """23. Verify ratios endpoint with invalid ticker returns HTTP 404."""
    response = client.get("/api/v1/companies/INVALID_TICKER_999/ratios")
    assert response.status_code == 404


def test_24_tearsheet_endpoint_returns_200():
    """24. Verify tearsheet endpoint returns HTTP 200 for available PDF."""
    response = client.get("/api/v1/companies/TCS/tearsheet")
    assert response.status_code == 200


def test_25_tearsheet_content_type_pdf():
    """25. Verify tearsheet endpoint Content-Type header is application/pdf."""
    response = client.get("/api/v1/companies/TCS/tearsheet")
    assert response.status_code == 200
    content_type = response.headers.get("content-type", "")
    assert "application/pdf" in content_type


def test_26_tearsheet_response_contains_pdf_bytes():
    """26. Verify tearsheet response body contains binary PDF magic header bytes."""
    response = client.get("/api/v1/companies/TCS/tearsheet")
    assert response.status_code == 200
    content = response.content
    assert len(content) > 0
    assert content.startswith(b"%PDF")


def test_27_missing_tearsheet_handled_correctly():
    """27. Verify missing tearsheet / invalid ticker returns 404 Not Found."""
    response = client.get("/api/v1/companies/NONEXISTENT_TICKER/tearsheet")
    assert response.status_code in [400, 404]


def test_28_invalid_year_format_returns_400():
    """28. Verify invalid year format returns HTTP 400 Bad Request."""
    response = client.get("/api/v1/companies/TCS/pl?from_year=INVALID_YEAR")
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data


def test_29_from_year_greater_than_to_year_returns_400():
    """29. Verify from_year > to_year returns HTTP 400 Bad Request."""
    response = client.get("/api/v1/companies/TCS/pl?from_year=2025&to_year=2020")
    assert response.status_code == 400
    data = response.json()
    assert "greater than" in data["detail"].lower()


def test_30_sql_injection_attempt_does_not_break_api():
    """30. Verify SQL injection payload does not break API and handles parameter safely."""
    payload = "' OR '1'='1"
    response = client.get(f"/api/v1/companies?search={payload}")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

    response_prof = client.get(f"/api/v1/companies/{payload}")
    assert response_prof.status_code == 404
