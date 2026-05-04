from unittest.mock import MagicMock, patch

import pytest

MOCK_CONVERSE_RESPONSE = {
    "output": {
        "message": {
            "content": [
                {
                    "text": '{"reasoning": "Looking at the TOTALS section", "answer": "The total billed was $687.00", "citations": [1]}'
                }
            ]
        }
    },
    "usage": {"inputTokens": 100, "outputTokens": 50},
}

MOCK_EMBEDDING = [0.1] * 1024


@pytest.fixture
def mock_bedrock():
    with (
        patch("services.rag.converse", return_value=MOCK_CONVERSE_RESPONSE) as mock_conv,
        patch("services.embeddings.invoke_model", return_value={"embedding": MOCK_EMBEDDING}) as mock_inv,
    ):
        yield {"converse": mock_conv, "invoke_model": mock_inv}


@pytest.fixture
def mock_pinecone():
    mock_index = MagicMock()
    mock_index.describe_index_stats.return_value = MagicMock(total_vector_count=10)
    mock_index.query.return_value = MagicMock(matches=[])
    mock_index.upsert.return_value = None
    mock_index.delete.return_value = None

    with patch("services.pinecone_store.get_pinecone_index", return_value=mock_index):
        yield mock_index


@pytest.fixture
def mock_embeddings():
    with patch("services.embeddings.generate_embedding", return_value=MOCK_EMBEDDING) as mock_emb:
        yield mock_emb


@pytest.fixture
def client(mock_bedrock, mock_pinecone, mock_embeddings):
    from starlette.testclient import TestClient

    from main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_headers():
    from auth import create_token

    token = create_token("admin", "admin")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def viewer_headers():
    from auth import create_token

    token = create_token("viewer", "viewer")
    return {"Authorization": f"Bearer {token}"}
