def test_list_evaluations(client, auth_headers):
    response = client.get("/api/evaluations", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_run_evaluation_requires_admin(client, viewer_headers):
    response = client.post("/api/evaluations/run", headers=viewer_headers)
    assert response.status_code == 403


def test_compare_requires_admin(client, viewer_headers):
    response = client.post(
        "/api/evaluations/compare",
        json={"version_a": "v1", "version_b": "v1"},
        headers=viewer_headers,
    )
    assert response.status_code == 403
