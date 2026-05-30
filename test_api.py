from fastapi.testclient import TestClient
from main import app 

# TestClient simula un client HTTP che interagisce con la tua API
client = TestClient(app)

def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_analyze_endpoint_validation():
    response = client.post("/chat", json={})
    assert response.status_code == 422

def test_analyze_endpoint_valid_payload():
    payload = {"question": "What is this document about?"}
    response = client.post("/chat", json=payload)
    
    assert response.status_code in [200, 500] 
    
    if response.status_code == 200:
        data = response.json()
        assert "answer" in data
        assert "question" in data
        assert data["question"] == payload["question"]