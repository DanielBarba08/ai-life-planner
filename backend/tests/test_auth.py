def test_register_creates_user(client):
    resp = client.post(
        "/v1/auth/register",
        json={"email": "ana@example.com", "password": "supersecreta1", "name": "Ana"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "ana@example.com"
    assert "password" not in body
    assert "password_hash" not in body


def test_register_duplicate_email_is_rejected(client):
    payload = {"email": "dup@example.com", "password": "supersecreta1"}
    first = client.post("/v1/auth/register", json=payload)
    assert first.status_code == 201

    second = client.post("/v1/auth/register", json=payload)
    assert second.status_code == 409


def test_login_with_wrong_password_fails(client):
    client.post("/v1/auth/register", json={"email": "bob@example.com", "password": "supersecreta1"})
    resp = client.post("/v1/auth/login", json={"email": "bob@example.com", "password": "incorrecta"})
    assert resp.status_code == 401


def test_login_returns_access_and_refresh_tokens(registered_user_tokens):
    assert registered_user_tokens["access_token"]
    assert registered_user_tokens["refresh_token"]
    assert registered_user_tokens["token_type"] == "bearer"


def test_protected_endpoint_requires_token(client):
    resp = client.get("/v1/users/me")
    assert resp.status_code == 401


def test_protected_endpoint_works_with_valid_token(client, auth_headers):
    resp = client.get("/v1/users/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "daniel@example.com"


def test_refresh_token_issues_new_access_token(client, registered_user_tokens):
    resp = client.post(
        "/v1/auth/refresh", json={"refresh_token": registered_user_tokens["refresh_token"]}
    )
    assert resp.status_code == 200
    assert resp.json()["access_token"]


def test_access_token_cannot_be_used_as_refresh_token(client, registered_user_tokens):
    """Un access token no debe servir para pedir un refresh (separación de tipos)."""
    resp = client.post(
        "/v1/auth/refresh", json={"refresh_token": registered_user_tokens["access_token"]}
    )
    assert resp.status_code == 401


def test_garbage_token_is_rejected(client):
    resp = client.get("/v1/users/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert resp.status_code == 401
