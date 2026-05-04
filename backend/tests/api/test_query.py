def test_query_authenticated(client, auth_headers):
    response = client.post(
        "/api/query",
        json={"question": "What is the total billed?", "top_k": 3},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sources" in data
    assert "metadata" in data


def test_query_unauthenticated(client):
    response = client.post("/api/query", json={"question": "test"})
    assert response.status_code == 401


def test_query_response_contract(client, auth_headers):
    response = client.post(
        "/api/query",
        json={"question": "What is the member ID?", "top_k": 5},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()

    assert isinstance(data["sources"], list)

    metadata = data["metadata"]
    assert "retrieval_latency_ms" in metadata
    assert "generation_latency_ms" in metadata
    assert "total_latency_ms" in metadata
    assert "total_tokens" in metadata
    assert "model" in metadata
    assert "prompt_version" in metadata
