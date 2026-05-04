def test_health_returns_200(client):
    response = client.get("/api/health")
    assert response.status_code == 200


def test_health_response_structure(client):
    response = client.get("/api/health")
    data = response.json()
    assert "status" in data
    assert "checks" in data
    assert "pinecone" in data["checks"]
    assert "bedrock" in data["checks"]
