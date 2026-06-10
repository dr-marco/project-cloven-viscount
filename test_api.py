from fastapi.testclient import TestClient
from main import app 

client = TestClient(app)

def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_chat_endpoint_validation():
    response = client.post("/chat", json={})
    assert response.status_code == 422 # Unprocessable Entity

def test_db_status_endpoint():
    response = client.get("/db-status")
    assert response.status_code == 200
    data = response.json()
    assert "has_documents" in data
    assert data["has_documents"] is False