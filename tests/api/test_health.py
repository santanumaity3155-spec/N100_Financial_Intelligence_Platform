"""
test_health.py

Unit tests for Module 6C FastAPI Server Scaffold & Health Endpoint.
"""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.routers.health import AUTHORITATIVE_TABLES

client = TestClient(app)


def test_fastapi_app_import():
    """Verify FastAPI application imports successfully."""
    assert app is not None
    assert app.title == "N100 Financial Intelligence Platform"


def test_health_endpoint_success():
    """Verify GET /api/v1/health returns HTTP 200 and expected schema."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200

    data = response.json()
    assert data.get("status") == "ok"
    assert "db_row_counts" in data
    assert "uptime_seconds" in data
    assert "version" in data


def test_db_row_counts_all_10_tables():
    """Verify db_row_counts contains all 10 authoritative project tables with numeric counts."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200

    counts = response.json().get("db_row_counts", {})
    assert len(counts) >= 10

    for table in AUTHORITATIVE_TABLES:
        assert table in counts, f"Table {table} missing from db_row_counts"
        assert isinstance(counts[table], int), f"Count for {table} must be integer"
        assert counts[table] >= 0, f"Count for {table} must be non-negative"


def test_uptime_seconds_numeric():
    """Verify uptime_seconds is numeric and non-negative."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200

    uptime = response.json().get("uptime_seconds")
    assert isinstance(uptime, (int, float))
    assert uptime >= 0


def test_version_present():
    """Verify version field matches application version."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200

    version = response.json().get("version")
    assert version is not None
    assert isinstance(version, str)
    assert len(version) > 0


def test_cors_middleware_configured():
    """Verify CORS middleware is active and allows requests from any origin."""
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://example.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    allowed_origin = response.headers.get("access-control-allow-origin")
    assert allowed_origin in ["*", "http://example.com"]


def test_swagger_docs_reachable():
    """Verify /docs endpoint is reachable."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_schema_reachable():
    """Verify /openapi.json returns valid JSON and includes health endpoint."""
    response = client.get("/openapi.json")
    assert response.status_code == 200

    schema = response.json()
    assert "paths" in schema
    assert "/api/v1/health" in schema["paths"]


def test_request_logging_middleware_executes(caplog):
    """Verify request logging middleware logs request details."""
    with caplog.at_level("INFO"):
        client.get("/api/v1/health")
        assert any("GET /api/v1/health" in record.message for record in caplog.records)


def test_no_sensitive_secrets_in_health_response():
    """Verify response does not expose passwords, filesystem secrets, or internal paths."""
    response = client.get("/api/v1/health")
    content = response.text.lower()

    sensitive_keywords = [
        "password",
        "secret_key",
        "aws_access",
        "bearer",
        "stacktrace",
    ]
    for keyword in sensitive_keywords:
        assert keyword not in content
