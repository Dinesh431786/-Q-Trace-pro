"""Tests for API endpoints"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    """Test health endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    
def test_quick_scan():
    """Test quick scan endpoint"""
    response = client.post(
        "/api/v1/analysis/quick-scan",
        json={"code": "import os\\nos.system('ls')"}
    )
    assert response.status_code == 200
    assert "critical_issues" in response.json()