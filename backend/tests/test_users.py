def test_update_me_partial_update(client, auth_headers):
    resp = client.patch("/v1/users/me", json={"timezone": "Europe/Madrid"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["timezone"] == "Europe/Madrid"
    # el nombre no se tocó
    assert resp.json()["name"] == "Daniel"


def test_onboarding_completed_starts_false_and_can_be_marked_done(client, auth_headers):
    me = client.get("/v1/users/me", headers=auth_headers).json()
    assert me["onboarding_completed"] is False

    resp = client.patch("/v1/users/me", json={"onboarding_completed": True}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["onboarding_completed"] is True


def test_delete_me_removes_account(client, auth_headers):
    resp = client.delete("/v1/users/me", headers=auth_headers)
    assert resp.status_code == 204

    # el token ya no debería servir: el usuario no existe
    again = client.get("/v1/users/me", headers=auth_headers)
    assert again.status_code == 401


def test_cannot_read_another_users_profile_via_someone_elses_token(client):
    """
    No hay endpoint para leer el perfil de otro usuario por ID — /users/me
    siempre resuelve por el token, nunca por un ID en la URL. Este test
    documenta esa garantía de aislamiento (sección J del blueprint).
    """
    client.post("/v1/auth/register", json={"email": "a@example.com", "password": "supersecreta1"})
    client.post("/v1/auth/register", json={"email": "b@example.com", "password": "supersecreta1"})

    login_a = client.post("/v1/auth/login", json={"email": "a@example.com", "password": "supersecreta1"})
    login_b = client.post("/v1/auth/login", json={"email": "b@example.com", "password": "supersecreta1"})

    me_a = client.get(
        "/v1/users/me", headers={"Authorization": f"Bearer {login_a.json()['access_token']}"}
    ).json()
    me_b = client.get(
        "/v1/users/me", headers={"Authorization": f"Bearer {login_b.json()['access_token']}"}
    ).json()

    assert me_a["id"] != me_b["id"]
    assert me_a["email"] == "a@example.com"
    assert me_b["email"] == "b@example.com"
