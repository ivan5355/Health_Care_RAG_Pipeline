def test_list_documents(client, auth_headers):
    response = client.get("/api/documents", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert isinstance(data["documents"], list)


def test_upload_document_admin(client, auth_headers):
    file_content = b"PATIENT INFORMATION\nName: TEST, USER   DOB: 01/01/1990\n\nTOTALS\nTotal Billed: $100.00"
    response = client.post(
        "/api/documents/upload",
        files={"file": ("test_eob.txt", file_content, "text/plain")},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["name"] == "test_eob.txt"
    assert data["status"] == "ready"


def test_upload_document_viewer_forbidden(client, viewer_headers):
    file_content = b"some content"
    response = client.post(
        "/api/documents/upload",
        files={"file": ("test.txt", file_content, "text/plain")},
        headers=viewer_headers,
    )
    assert response.status_code == 403


def test_get_document_not_found(client, auth_headers):
    response = client.get("/api/documents/nonexistent-id", headers=auth_headers)
    assert response.status_code == 404


def test_list_documents_unauthenticated(client):
    response = client.get("/api/documents")
    assert response.status_code == 401
