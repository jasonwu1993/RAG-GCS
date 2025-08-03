import pytest
import requests
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_endpoint():
    """Test that health endpoint returns 200"""
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["status"] == "healthy"

def test_sync_status_endpoint():
    """Test sync status endpoint"""
    response = client.get("/sync_status")
    assert response.status_code == 200
    assert "is_syncing" in response.json()
