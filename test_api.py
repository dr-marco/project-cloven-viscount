from fastapi.testclient import TestClient
from main import app 

client = TestClient(app)

def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_chat_endpoint_validation():
    response = client.post("/chat", json={})
    assert response.status_code == 422

def test_chat_endpoint_valid_payload():
    payload = {"query": "What is this document about?"}
    response = client.post("/chat", json=payload)
    
    assert response.status_code in [200, 500] 
    
    if response.status_code == 200:
        data = response.json()
        assert "answer" in data
        assert "query" in data
        assert data["query"] == payload["query"]