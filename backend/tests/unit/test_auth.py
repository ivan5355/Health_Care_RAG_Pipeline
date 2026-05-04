from datetime import UTC

from auth import (
    _user_from_api_key,
    authenticate_user,
    create_token,
    verify_token,
)


def test_authenticate_user_valid():
    user = authenticate_user("admin", "admin")
    assert user is not None
    assert user.username == "admin"
    assert user.role == "admin"


def test_authenticate_user_wrong_password():
    user = authenticate_user("admin", "wrong")
    assert user is None


def test_authenticate_user_unknown_user():
    user = authenticate_user("hacker", "password")
    assert user is None


def test_authenticate_viewer():
    user = authenticate_user("viewer", "viewer")
    assert user is not None
    assert user.role == "viewer"


def test_create_and_verify_token_roundtrip():
    token = create_token("admin", "admin")
    payload = verify_token(token)
    assert payload is not None
    assert payload["sub"] == "admin"
    assert payload["role"] == "admin"
    assert "exp" in payload
    assert "iat" in payload
    assert "jti" in payload


def test_verify_token_expired():
    from datetime import datetime, timedelta

    import jwt

    payload = {
        "sub": "admin",
        "role": "admin",
        "exp": datetime.now(UTC) - timedelta(hours=1),
    }
    expired_token = jwt.encode(payload, "dev-secret-change-in-production", algorithm="HS256")
    assert verify_token(expired_token) is None


def test_verify_token_garbage():
    assert verify_token("not.a.real.token") is None
    assert verify_token("") is None


def test_api_key_valid():
    user = _user_from_api_key("service-key-healthcare-rag")
    assert user is not None
    assert user.role == "admin"
    assert "evaluation-runner" in user.username


def test_api_key_invalid():
    user = _user_from_api_key("fake-key")
    assert user is None
