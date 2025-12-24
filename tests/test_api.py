# tests/test_api.py
import pytest
from fastapi.testclient import TestClient
import json

from api.main import app

client = TestClient(app)

class TestAPI:
    def test_health_check(self):
        """Test API health endpoint"""
        response = client.get("/metrics")
        assert response.status_code == 200
    
    def test_analyze_endpoint(self):
        """Test analysis endpoint"""
        payload = {
            "incident_text": "Test incident with malicious activity",
            "priority": "high"
        }
        
        response = client.post("/analyze", json=payload)
        
        # Should return 200 or 202
        assert response.status_code in [200, 202]
        
        if response.status_code == 200:
            data = response.json()
            assert "decision" in data
            assert "epistemic_status" in data
    
    def test_invalid_input(self):
        """Test invalid input handling"""
        payload = {
            "incident_text": "",  # Empty text
            "priority": "high"
        }
        
        response = client.post("/analyze", json=payload)
        # Should return 422 for validation error
        assert response.status_code == 422
    
    def test_results_endpoint(self):
        """Test results endpoint"""
        # First submit an analysis
        payload = {
            "incident_text": "Another test incident",
            "priority": "high"
        }
        
        submit_response = client.post("/analyze", json=payload)
        if submit_response.status_code == 200:
            data = submit_response.json()
            event_id = data["event_id"]
            
            # Then try to get results
            response = client.get(f"/results/{event_id}")
            assert response.status_code == 200
    
    def test_evaluation_endpoint(self):
        """Test evaluation endpoint (should be protected in production)"""
        response = client.post("/evaluate")
        # This might return 200 or 405 depending on implementation
        assert response.status_code in [200, 405, 401]