import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from services.features.app import app

client = TestClient(app)

def test_length_to_word_ratio():
    payload = {"features": {"length": 10, "word_count": 5}}
    response = client.post("/features", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["engineered_features"]["length_to_word_ratio"] == 2.0

