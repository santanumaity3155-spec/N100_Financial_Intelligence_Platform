"""
validate_module6d.py

Validation Script for Sprint 6 — Module 6D (API Endpoints: Company Data).
"""

import sys
import datetime
import pytest
from fastapi.testclient import TestClient

def run_validation():
    print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n" + "=" * 60)
    print("MODULE 6D VALIDATION")
    print("=" * 60 + "\n")
    
    results = {}
    
    # 1. API Application Import
    try:
        from src.api.main import app
        results["API Application Import"] = "PASS"
    except Exception as e:
        print(f"API Application Import failed: {e}")
        results["API Application Import"] = "FAIL"
        app = None

    # 2. Companies Router Import
    try:
        from src.api.routers.companies import router
        results["Companies Router Import"] = "PASS"
    except Exception as e:
        print(f"Companies Router Import failed: {e}")
        results["Companies Router Import"] = "FAIL"

    client = TestClient(app) if app else None

    # 3. GET /companies
    try:
        res = client.get("/api/v1/companies")
        if res.status_code == 200 and isinstance(res.json(), list):
            results["GET /companies"] = "PASS"
        else:
            results["GET /companies"] = "FAIL"
    except Exception as e:
        print(f"GET /companies failed: {e}")
        results["GET /companies"] = "FAIL"

    # 4. Company Count
    try:
        from src.database.connection import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM companies")
        db_count = cursor.fetchone()[0]
        
        res = client.get("/api/v1/companies")
        api_count = len(res.json())
        if api_count == db_count and db_count >= 90:
            results["Company Count"] = "PASS"
        else:
            print(f"Company count mismatch: API={api_count}, DB={db_count}")
            results["Company Count"] = "FAIL"
    except Exception as e:
        print(f"Company Count failed: {e}")
        results["Company Count"] = "FAIL"

    # 5. Required Company Fields
    try:
        res = client.get("/api/v1/companies")
        first = res.json()[0]
        req_fields = ["company_id", "company_name", "broad_sector", "sub_sector", "roe_pct", "roce_pct"]
        if all(k in first for k in req_fields):
            results["Required Company Fields"] = "PASS"
        else:
            results["Required Company Fields"] = "FAIL"
    except Exception as e:
        print(f"Required Company Fields failed: {e}")
        results["Required Company Fields"] = "FAIL"

    # 6. Sector Filter
    try:
        res = client.get("/api/v1/companies?sector=IT")
        data = res.json()
        if res.status_code == 200 and len(data) > 0:
            results["Sector Filter"] = "PASS"
        else:
            results["Sector Filter"] = "FAIL"
    except Exception as e:
        print(f"Sector Filter failed: {e}")
        results["Sector Filter"] = "FAIL"

    # 7. Market Cap Filter
    try:
        res = client.get("/api/v1/companies?market_cap_category=Large Cap")
        data = res.json()
        if res.status_code == 200 and len(data) > 0 and all(c["market_cap_category"] == "Large Cap" for c in data):
            results["Market Cap Filter"] = "PASS"
        else:
            results["Market Cap Filter"] = "FAIL"
    except Exception as e:
        print(f"Market Cap Filter failed: {e}")
        results["Market Cap Filter"] = "FAIL"

    # 8. Search Filter
    try:
        res = client.get("/api/v1/companies?search=tcs")
        data = res.json()
        if res.status_code == 200 and len(data) == 1 and data[0]["company_id"] == "TCS":
            results["Search Filter"] = "PASS"
        else:
            results["Search Filter"] = "FAIL"
    except Exception as e:
        print(f"Search Filter failed: {e}")
        results["Search Filter"] = "FAIL"

    # 9. Company Profile
    try:
        res = client.get("/api/v1/companies/TCS")
        if res.status_code == 200 and res.json().get("company_id") == "TCS":
            results["Company Profile"] = "PASS"
        else:
            results["Company Profile"] = "FAIL"
    except Exception as e:
        print(f"Company Profile failed: {e}")
        results["Company Profile"] = "FAIL"

    # 10. Latest KPI Data
    try:
        res = client.get("/api/v1/companies/TCS")
        kpis = res.json().get("latest_kpis")
        if res.status_code == 200 and isinstance(kpis, dict) and len(kpis) > 0:
            results["Latest KPI Data"] = "PASS"
        else:
            results["Latest KPI Data"] = "FAIL"
    except Exception as e:
        print(f"Latest KPI Data failed: {e}")
        results["Latest KPI Data"] = "FAIL"

    # 11. 404 Invalid Ticker
    try:
        res = client.get("/api/v1/companies/INVALID_TICKER_999")
        if res.status_code == 404 and "not found" in res.json().get("detail", "").lower():
            results["404 Invalid Ticker"] = "PASS"
        else:
            results["404 Invalid Ticker"] = "FAIL"
    except Exception as e:
        print(f"404 Invalid Ticker failed: {e}")
        results["404 Invalid Ticker"] = "FAIL"

    # 12. P&L Endpoint
    try:
        res = client.get("/api/v1/companies/TCS/pl")
        if res.status_code == 200 and len(res.json()) > 0:
            results["P&L Endpoint"] = "PASS"
        else:
            results["P&L Endpoint"] = "FAIL"
    except Exception as e:
        print(f"P&L Endpoint failed: {e}")
        results["P&L Endpoint"] = "FAIL"

    # 13. P&L Year Filtering
    try:
        res = client.get("/api/v1/companies/TCS/pl?from_year=2019-03&to_year=2024-03")
        if res.status_code == 200 and len(res.json()) > 0:
            results["P&L Year Filtering"] = "PASS"
        else:
            results["P&L Year Filtering"] = "FAIL"
    except Exception as e:
        print(f"P&L Year Filtering failed: {e}")
        results["P&L Year Filtering"] = "FAIL"

    # 14. Balance Sheet Endpoint
    try:
        res = client.get("/api/v1/companies/TCS/bs")
        if res.status_code == 200 and len(res.json()) > 0:
            results["Balance Sheet Endpoint"] = "PASS"
        else:
            results["Balance Sheet Endpoint"] = "FAIL"
    except Exception as e:
        print(f"Balance Sheet Endpoint failed: {e}")
        results["Balance Sheet Endpoint"] = "FAIL"

    # 15. Balance Sheet Filtering
    try:
        res = client.get("/api/v1/companies/TCS/bs?from_year=2018&to_year=2022")
        if res.status_code == 200 and len(res.json()) > 0:
            results["Balance Sheet Filtering"] = "PASS"
        else:
            results["Balance Sheet Filtering"] = "FAIL"
    except Exception as e:
        print(f"Balance Sheet Filtering failed: {e}")
        results["Balance Sheet Filtering"] = "FAIL"

    # 16. Cash Flow Endpoint
    try:
        res = client.get("/api/v1/companies/TCS/cashflow")
        if res.status_code == 200 and len(res.json()) > 0:
            results["Cash Flow Endpoint"] = "PASS"
        else:
            results["Cash Flow Endpoint"] = "FAIL"
    except Exception as e:
        print(f"Cash Flow Endpoint failed: {e}")
        results["Cash Flow Endpoint"] = "FAIL"

    # 17. Cash Flow Filtering
    try:
        res = client.get("/api/v1/companies/TCS/cashflow?from_year=2015&to_year=2020")
        if res.status_code == 200 and len(res.json()) > 0:
            results["Cash Flow Filtering"] = "PASS"
        else:
            results["Cash Flow Filtering"] = "FAIL"
    except Exception as e:
        print(f"Cash Flow Filtering failed: {e}")
        results["Cash Flow Filtering"] = "FAIL"

    # 18. Ratios Endpoint
    try:
        res = client.get("/api/v1/companies/TCS/ratios")
        if res.status_code == 200 and len(res.json()) > 0:
            results["Ratios Endpoint"] = "PASS"
        else:
            results["Ratios Endpoint"] = "FAIL"
    except Exception as e:
        print(f"Ratios Endpoint failed: {e}")
        results["Ratios Endpoint"] = "FAIL"

    # 19. Ratios Year Filter
    try:
        res = client.get("/api/v1/companies/TCS/ratios?year=2024")
        if res.status_code == 200:
            results["Ratios Year Filter"] = "PASS"
        else:
            results["Ratios Year Filter"] = "FAIL"
    except Exception as e:
        print(f"Ratios Year Filter failed: {e}")
        results["Ratios Year Filter"] = "FAIL"

    # 20. Tearsheet Endpoint
    try:
        res = client.get("/api/v1/companies/TCS/tearsheet")
        if res.status_code == 200 and len(res.content) > 0:
            results["Tearsheet Endpoint"] = "PASS"
        else:
            results["Tearsheet Endpoint"] = "FAIL"
    except Exception as e:
        print(f"Tearsheet Endpoint failed: {e}")
        results["Tearsheet Endpoint"] = "FAIL"

    # 21. PDF Content Type
    try:
        res = client.get("/api/v1/companies/TCS/tearsheet")
        ct = res.headers.get("content-type", "")
        if res.status_code == 200 and "application/pdf" in ct and res.content.startswith(b"%PDF"):
            results["PDF Content Type"] = "PASS"
        else:
            results["PDF Content Type"] = "FAIL"
    except Exception as e:
        print(f"PDF Content Type failed: {e}")
        results["PDF Content Type"] = "FAIL"

    # 22. Invalid Year Validation
    try:
        res1 = client.get("/api/v1/companies/TCS/pl?from_year=invalid")
        res2 = client.get("/api/v1/companies/TCS/pl?from_year=2025&to_year=2020")
        if res1.status_code == 400 and res2.status_code == 400:
            results["Invalid Year Validation"] = "PASS"
        else:
            results["Invalid Year Validation"] = "FAIL"
    except Exception as e:
        print(f"Invalid Year Validation failed: {e}")
        results["Invalid Year Validation"] = "FAIL"

    # 23. API Error Handling
    try:
        res_404 = client.get("/api/v1/companies/UNKNOWN_TICKER_XYZ")
        res_400 = client.get("/api/v1/companies/TCS/pl?from_year=abc")
        if res_404.status_code == 404 and res_400.status_code == 400:
            results["API Error Handling"] = "PASS"
        else:
            results["API Error Handling"] = "FAIL"
    except Exception as e:
        print(f"API Error Handling failed: {e}")
        results["API Error Handling"] = "FAIL"

    # 24. OpenAPI Documentation
    try:
        res = client.get("/openapi.json")
        schema = res.json()
        paths = schema.get("paths", {})
        required_paths = [
            "/api/v1/companies",
            "/api/v1/companies/{ticker}",
            "/api/v1/companies/{ticker}/pl",
            "/api/v1/companies/{ticker}/bs",
            "/api/v1/companies/{ticker}/cashflow",
            "/api/v1/companies/{ticker}/ratios",
            "/api/v1/companies/{ticker}/tearsheet",
        ]
        if res.status_code == 200 and all(p in paths for p in required_paths):
            results["OpenAPI Documentation"] = "PASS"
        else:
            print("Missing OpenAPI paths:", [p for p in required_paths if p not in paths])
            results["OpenAPI Documentation"] = "FAIL"
    except Exception as e:
        print(f"OpenAPI Documentation failed: {e}")
        results["OpenAPI Documentation"] = "FAIL"

    # 25. Unit Tests
    try:
        pytest_ret = pytest.main(["tests/api/test_companies.py", "-q"])
        if pytest_ret == 0:
            results["Unit Tests"] = "PASS"
        else:
            results["Unit Tests"] = "FAIL"
    except Exception as e:
        print(f"Unit Tests failed: {e}")
        results["Unit Tests"] = "FAIL"

    # Print Summary Table
    max_key_len = max(len(k) for k in results.keys())
    for k, v in results.items():
        print(f"{k:<{max_key_len + 4}} {v}")

    print("\n" + "=" * 60)
    all_passed = all(v == "PASS" for v in results.values())
    final_status = "PASS" if all_passed else "FAIL"
    print(f"FINAL STATUS: {final_status}")
    print("=" * 60 + "\n")

    if not all_passed:
        sys.exit(1)

if __name__ == "__main__":
    run_validation()
