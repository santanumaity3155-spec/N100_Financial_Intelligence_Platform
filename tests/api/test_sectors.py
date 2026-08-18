"""
test_sectors.py

Unit tests for Sectors endpoints (GET /api/v1/sectors and GET /api/v1/sectors/{sector}/companies).
Implements Module 6E testing.
"""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_get_sectors():
    response = client.get("/api/v1/sectors")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

    first = data[0]
    assert "sector" in first
    assert "company_count" in first
    assert "median_roe" in first
    assert "median_pe" in first
    assert "median_de" in first


def test_get_sector_companies_known():
    # First get valid sector name
    res_sec = client.get("/api/v1/sectors")
    assert res_sec.status_code == 200
    sectors = res_sec.json()
    known_sector = sectors[0]["sector"]

    response = client.get(f"/api/v1/sectors/{known_sector}/companies")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    first = data[0]
    assert "company_id" in first
    assert "company_name" in first
    assert "latest_kpis" in first


def test_get_sector_companies_unknown():
    response = client.get("/api/v1/sectors/NonExistentSector999/companies")
    assert response.status_code == 404
