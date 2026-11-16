def test_create_goal_defaults_to_confirmed_and_active(client, auth_headers):
    resp = client.post(
        "/v1/goals", json={"title": "Aprender programación", "horizon": "largo_plazo"}, headers=auth_headers
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "activo"
    assert body["confirmed_by_user"] is True


def test_list_goals_filtered_by_status(client, auth_headers):
    g1 = client.post(
        "/v1/goals", json={"title": "Meta 1", "horizon": "mes"}, headers=auth_headers
    ).json()
    client.post("/v1/goals", json={"title": "Meta 2", "horizon": "semana"}, headers=auth_headers)
    client.patch(f"/v1/goals/{g1['id']}", json={"status": "completado"}, headers=auth_headers)

    active = client.get("/v1/goals?status=activo", headers=auth_headers).json()
    completed = client.get("/v1/goals?status=completado", headers=auth_headers).json()
    assert len(active) == 1
    assert len(completed) == 1


def test_invalid_horizon_is_rejected(client, auth_headers):
    resp = client.post(
        "/v1/goals", json={"title": "Meta rara", "horizon": "eventualmente"}, headers=auth_headers
    )
    assert resp.status_code == 422


def test_delete_goal(client, auth_headers):
    goal = client.post(
        "/v1/goals", json={"title": "Borrar", "horizon": "hoy"}, headers=auth_headers
    ).json()
    resp = client.delete(f"/v1/goals/{goal['id']}", headers=auth_headers)
    assert resp.status_code == 204
    assert client.get("/v1/goals", headers=auth_headers).json() == []


def test_goal_isolated_per_user(client):
    client.post("/v1/auth/register", json={"email": "u1@example.com", "password": "supersecreta1"})
    client.post("/v1/auth/register", json={"email": "u2@example.com", "password": "supersecreta1"})
    t1 = client.post(
        "/v1/auth/login", json={"email": "u1@example.com", "password": "supersecreta1"}
    ).json()["access_token"]
    t2 = client.post(
        "/v1/auth/login", json={"email": "u2@example.com", "password": "supersecreta1"}
    ).json()["access_token"]

    client.post(
        "/v1/goals",
        json={"title": "Solo de u1", "horizon": "hoy"},
        headers={"Authorization": f"Bearer {t1}"},
    )
    goals_u2 = client.get("/v1/goals", headers={"Authorization": f"Bearer {t2}"}).json()
    assert goals_u2 == []
