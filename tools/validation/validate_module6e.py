"""
validate_module6e.py

Module 6E Standalone Validation Script.
Validates all Day 40 API endpoints, parameters, error responses, security,
OpenAPI schema export, Postman collection export, and regression test suites.
"""

import sys
import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def print_check(name: str, passed: bool):
    status_str = "PASS" if passed else "FAIL"
    print(f"{name:<30} {status_str}")
    return passed


def main():
    print("=" * 60)
    print("MODULE 6E VALIDATION")
    print("=" * 60)

    all_passed = True

    # 1. Screener Endpoint
    res = client.get("/api/v1/screener")
    p1 = (res.status_code == 200 and isinstance(res.json(), list) and len(res.json()) > 0)
    all_passed &= print_check("Screener Endpoint", p1)

    # 2. Screener Filters
    res_f = client.get("/api/v1/screener?min_roe=15&max_de=2.5&max_pe=100")
    p2 = (res_f.status_code == 200 and isinstance(res_f.json(), list))
    all_passed &= print_check("Screener Filters", p2)

    # 3. Screener Validation
    res_v = client.get("/api/v1/screener?min_roe=invalid_str")
    p3 = (res_v.status_code == 400)
    all_passed &= print_check("Screener Validation", p3)

    print()

    # 4. Sector Endpoint
    res_sec = client.get("/api/v1/sectors")
    p4 = (res_sec.status_code == 200 and isinstance(res_sec.json(), list) and len(res_sec.json()) > 0)
    all_passed &= print_check("Sector Endpoint", p4)

    # 5. Sector Statistics
    sec_data = res_sec.json() if p4 else []
    p5 = (len(sec_data) > 0 and "company_count" in sec_data[0] and "median_roe" in sec_data[0])
    all_passed &= print_check("Sector Statistics", p5)

    # 6. Sector Company Endpoint
    known_sec = sec_data[0]["sector"] if p4 else "IT Services"
    res_sec_c = client.get(f"/api/v1/sectors/{known_sec}/companies")
    p6 = (res_sec_c.status_code == 200 and len(res_sec_c.json()) > 0)
    all_passed &= print_check("Sector Company Endpoint", p6)

    # 7. Unknown Sector 404
    res_sec_unk = client.get("/api/v1/sectors/NonExistentSector9999/companies")
    p7 = (res_sec_unk.status_code == 404)
    all_passed &= print_check("Unknown Sector 404", p7)

    print()

    # 8. Peer Group Endpoint
    res_pg = client.get("/api/v1/peers/IT%20Services")
    p8 = (res_pg.status_code == 200 and "companies" in res_pg.json())
    all_passed &= print_check("Peer Group Endpoint", p8)

    # 9. Peer Percentile Data
    pg_data = res_pg.json() if p8 else {}
    p9 = ("companies" in pg_data and len(pg_data["companies"]) > 0 and len(pg_data["companies"][0]["percentiles"]) == 10)
    all_passed &= print_check("Peer Percentile Data", p9)

    # 10. Peer Comparison Endpoint
    res_cmp = client.get("/api/v1/companies/TCS/peers/compare")
    p10 = (res_cmp.status_code == 200 and "company_values" in res_cmp.json())
    all_passed &= print_check("Peer Comparison Endpoint", p10)

    # 11. 8 Radar Metrics
    cmp_data = res_cmp.json() if p10 else {}
    p11 = ("metrics" in cmp_data and len(cmp_data["metrics"]) == 8)
    all_passed &= print_check("8 Radar Metrics", p11)

    # 12. Unknown Peer 404
    res_pg_unk = client.get("/api/v1/peers/UnknownPeerGroup999")
    p12 = (res_pg_unk.status_code == 404)
    all_passed &= print_check("Unknown Peer 404", p12)

    print()

    # 13. Market Cap Endpoint
    res_mc = client.get("/api/v1/market-cap/TCS")
    p13 = (res_mc.status_code == 200 and "historical_valuation" in res_mc.json())
    all_passed &= print_check("Market Cap Endpoint", p13)

    # 14. Historical Valuation Data
    mc_data = res_mc.json() if p13 else {}
    p14 = ("historical_valuation" in mc_data and isinstance(mc_data["historical_valuation"], list))
    all_passed &= print_check("Historical Valuation Data", p14)

    print()

    # 15. Portfolio Stats Endpoint
    res_port = client.get("/api/v1/portfolio/stats")
    p15 = (res_port.status_code == 200 and "stats" in res_port.json())
    all_passed &= print_check("Portfolio Stats Endpoint", p15)

    # 16. Required Percentiles
    port_data = res_port.json() if p15 else {}
    p16 = ("stats" in port_data and len(port_data["stats"]) > 0 and all(k in port_data["stats"][0] for k in ["P10", "P25", "P50", "P75", "P90"]))
    all_passed &= print_check("Required Percentiles", p16)

    print()

    # 17. Documents Endpoint
    res_doc = client.get("/api/v1/companies/ABB/documents")
    p17 = (res_doc.status_code == 200 and "documents" in res_doc.json())
    all_passed &= print_check("Documents Endpoint", p17)

    # 18. URL Validity Flag
    doc_data = res_doc.json() if p17 else {}
    p18 = ("documents" in doc_data and len(doc_data["documents"]) > 0 and "is_url_valid" in doc_data["documents"][0] and isinstance(doc_data["documents"][0]["is_url_valid"], bool))
    all_passed &= print_check("URL Validity Flag", p18)

    print()

    # 19. OpenAPI Registration
    schema = app.openapi()
    paths = schema.get("paths", {})
    required_paths = [
        "/api/v1/screener",
        "/api/v1/sectors",
        "/api/v1/sectors/{sector}/companies",
        "/api/v1/peers/{group_name}",
        "/api/v1/companies/{ticker}/peers/compare",
        "/api/v1/market-cap/{ticker}",
        "/api/v1/portfolio/stats",
        "/api/v1/companies/{ticker}/documents",
    ]
    p19 = all(path in paths for path in required_paths)
    all_passed &= print_check("OpenAPI Registration", p19)

    # 20. OpenAPI Export
    openapi_file = Path("docs/openapi.json")
    p20 = openapi_file.exists() and openapi_file.stat().st_size > 100
    all_passed &= print_check("OpenAPI Export", p20)

    # 21. Postman Collection
    postman_file = Path("docs/postman_collection.json")
    p21 = postman_file.exists() and postman_file.stat().st_size > 100
    all_passed &= print_check("Postman Collection", p21)

    print()

    # 22. Security Validation
    res_sec_inj = client.get("/api/v1/companies/' OR 1=1 --")
    p22 = (res_sec_inj.status_code in (400, 404, 422) and "traceback" not in res_sec_inj.text.lower())
    all_passed &= print_check("Security Validation", p22)

    # 23. API Unit Tests
    ret_code = pytest.main(["tests/api/", "-q"])
    p23 = (ret_code == 0)
    all_passed &= print_check("API Unit Tests", p23)

    print("=" * 60)
    final_status = "PASS" if all_passed else "FAIL"
    print(f"FINAL STATUS: {final_status}")
    print("=" * 60)

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
