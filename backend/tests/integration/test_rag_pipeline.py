from unittest.mock import MagicMock

import pytest

SAMPLE_EOB_CONTENT = b"""PATIENT INFORMATION
Name: WALKER, JAMES R   DOB: 08/14/1952
Member ID: XYZ123456

SERVICE LINES
Date       Code    Description         Billed    Allowed   Copay
01/15/24   99213   Office Visit        $250.00   $180.00   $30.00

TOTALS
Total Billed: $687.00
Total Allowed: $485.00
Patient Responsibility: $30.00
"""


@pytest.mark.integration
def test_full_rag_pipeline(client, auth_headers, mock_pinecone):
    # Upload a document
    response = client.post(
        "/api/documents/upload",
        files={"file": ("test_eob.txt", SAMPLE_EOB_CONTENT, "text/plain")},
        headers=auth_headers,
    )
    assert response.status_code == 200
    doc = response.json()
    assert doc["chunk_count"] > 0

    # Configure mock to return a matching chunk
    fake_match = MagicMock()
    fake_match.id = "chunk_1"
    fake_match.score = 0.95
    fake_match.metadata = {
        "document_name": "test_eob.txt",
        "section_name": "TOTALS",
        "text": "Total Billed: $687.00\nTotal Allowed: $485.00\nPatient Responsibility: $30.00",
        "chunk_index": 0,
        "patient_name": "WALKER, JAMES R",
    }
    mock_pinecone.query.return_value = MagicMock(matches=[fake_match])

    # Query the RAG pipeline
    response = client.post(
        "/api/query",
        json={"question": "What was the total billed?", "top_k": 3},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()

    # Verify full response structure
    assert "answer" in data
    assert "sources" in data
    assert "metadata" in data
    assert len(data["sources"]) > 0
    assert data["sources"][0]["section_name"] == "TOTALS"
    assert data["metadata"]["total_tokens"] > 0
    assert data["metadata"]["prompt_version"] is not None
