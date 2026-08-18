"""
test_peers.py

Unit tests for Peer endpoints (GET /api/v1/peers/{group_name} and GET /api/v1/companies/{ticker}/peers/compare).
Implements Module 6E testing.
"""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_peer_group_known():
    response = client.get("/api/v1/peers/IT%20Services")
    assert response.status_code == 200
    data = response.json()
    assert "peer_group_name" in data
    assert "company_count" in data
    assert "companies" in data
    assert len(data["companies"]) > 0

    first = data["companies"][0]
    assert "company_id" in first
    assert "percentiles" in first
    assert "metric_details" in first
    assert len(first["metric_details"]) == 10


def test_peer_group_unknown():
    response = client.get("/api/v1/peers/UnknownPeerGroupXYZ")
    assert response.status_code == 404


def test_company_peer_compare_known():
    response = client.get("/api/v1/companies/TCS/peers/compare")
    assert response.status_code == 200
    data = response.json()
    assert "ticker" in data
    assert "peer_group_name" in data
    assert "metrics" in data
    assert len(data["metrics"]) == 8
    assert "company_values" in data
    assert "peer_average" in data
    assert "benchmark_values" in data


def test_company_peer_compare_invalid_ticker():
    response = client.get("/api/v1/companies/NONEXISTENT_TICKER/peers/compare")
    assert response.status_code == 404
