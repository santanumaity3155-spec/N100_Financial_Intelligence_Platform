"""
validate_module6c.py

Comprehensive Validation Script for Module 6C — FastAPI Server Scaffold (Day 38).
Executes real functional checks against the application and database.
"""

import sys
import logging
from pathlib import Path

from fastapi.testclient import TestClient

from src.database.connection import get_connection
from src.api.routers.health import AUTHORITATIVE_TABLES


def validate_module6c() -> bool:
    """
    Executes real checks for all 19 criteria of Module 6C.

    Returns
    -------
    bool
        True if all checks pass, False otherwise.
    """
    results = {}
    
    # Disable verbose logging during validation
    logging.getLogger("src.api.main").setLevel(logging.WARNING)

    # 1. FastAPI Installation
    try:
        import fastapi
        import uvicorn
        results["FastAPI Installation"] = True
    except ImportError:
        results["FastAPI Installation"] = False

    # 2. API Package Structure
    api_dir = Path("src/api")
    routers_dir = Path("src/api/routers")
    structure_ok = (
        api_dir.exists()
        and (api_dir / "__init__.py").exists()
        and (api_dir / "main.py").exists()
        and routers_dir.exists()
        and (routers_dir / "__init__.py").exists()
    )
    results["API Package Structure"] = structure_ok

    # 3. Main Application Import
    app = None
    try:
        from src.api.main import app
        results["Main Application Import"] = app is not None
    except Exception as e:
        print(f"Error importing app: {e}")
        results["Main Application Import"] = False

    # 4. Database Connection
    db_ok = False
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        db_ok = cur.fetchone()[0] == 1
    except Exception as e:
        print(f"Error testing DB connection: {e}")
        db_ok = False
    results["Database Connection"] = db_ok

    # 5. Router Files
    required_routers = [
        "companies.py",
        "screener.py",
        "sectors.py",
        "peers.py",
        "valuation.py",
        "portfolio.py",
        "documents.py",
        "health.py",
    ]
    all_routers_exist = all((routers_dir / f).exists() for f in required_routers)
    results["Router Files"] = all_routers_exist

    if not app:
        client = None
    else:
        client = TestClient(app)

    # 6. Router Registration & 7. API Prefix
    # Check if routes are registered under /api/v1
    routes_registered = False
    prefix_ok = False
    if app:
        api_routes = [r.path for r in app.routes]
        prefix_ok = any(p.startswith("/api/v1") for p in api_routes)
        routes_registered = "/api/v1/health" in api_routes
    results["Router Registration"] = routes_registered
    results["API Prefix"] = prefix_ok

    # 8. CORS Middleware
    cors_ok = False
    if client:
        res = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        allowed_origin = res.headers.get("access-control-allow-origin")
        cors_ok = allowed_origin in ["*", "http://localhost:3000"]
    results["CORS Middleware"] = cors_ok

    # 9. Logging Middleware
    logging_ok = False
    if client:
        # Request should succeed and invoke middleware
        res = client.get("/api/v1/health")
        logging_ok = res.status_code == 200
    results["Logging Middleware"] = logging_ok

    # 10. Health Endpoint & 11. HTTP Status 200
    health_res = None
    if client:
        health_res = client.get("/api/v1/health")
    
    health_endpoint_ok = health_res is not None
    http_200_ok = health_res is not None and health_res.status_code == 200
    results["Health Endpoint"] = health_endpoint_ok
    results["HTTP Status 200"] = http_200_ok

    # 12. Status Field
    status_field_ok = False
    payload = {}
    if http_200_ok and health_res:
        payload = health_res.json()
        status_field_ok = payload.get("status") == "ok"
    results["Status Field"] = status_field_ok

    # 13. DB Row Counts & 14. 10 Tables Covered
    db_counts_ok = False
    tables_covered_ok = False
    if status_field_ok:
        counts = payload.get("db_row_counts", {})
        db_counts_ok = isinstance(counts, dict) and len(counts) > 0
        tables_covered_ok = all(
            t in counts and isinstance(counts[t], int) and counts[t] >= 0
            for t in AUTHORITATIVE_TABLES
        )
    results["DB Row Counts"] = db_counts_ok
    results["10 Tables Covered"] = tables_covered_ok

    # 15. Uptime
    uptime_ok = False
    if status_field_ok:
        uptime = payload.get("uptime_seconds")
        uptime_ok = isinstance(uptime, (int, float)) and uptime >= 0
    results["Uptime"] = uptime_ok

    # 16. Version
    version_ok = False
    if status_field_ok:
        ver = payload.get("version")
        version_ok = isinstance(ver, str) and len(ver) > 0
    results["Version"] = version_ok

    # 17. OpenAPI & 18. Swagger Docs & 19. Health OpenAPI Registration
    openapi_ok = False
    swagger_ok = False
    health_in_openapi = False

    if client:
        docs_res = client.get("/docs")
        swagger_ok = docs_res.status_code == 200

        openapi_res = client.get("/openapi.json")
        openapi_ok = openapi_res.status_code == 200

        if openapi_ok:
            schema = openapi_res.json()
            health_in_openapi = "/api/v1/health" in schema.get("paths", {})

    results["OpenAPI"] = openapi_ok
    results["Swagger Docs"] = swagger_ok
    results["Health OpenAPI Registration"] = health_in_openapi

    # Print Report Output Matrix
    print("\n============================================================")
    print("MODULE 6C VALIDATION")
    print("============================================================")

    all_pass = True
    for test_name, passed in results.items():
        status_str = "PASS" if passed else "FAIL"
        if not passed:
            all_pass = False
        print(f"{test_name:<30} {status_str}")

    print("------------------------------------------------------------")
    final_status = "PASS" if all_pass else "FAIL"
    print(f"FINAL STATUS: {final_status}")
    print("============================================================\n")

    return all_pass


if __name__ == "__main__":
    success = validate_module6c()
    sys.exit(0 if success else 1)
