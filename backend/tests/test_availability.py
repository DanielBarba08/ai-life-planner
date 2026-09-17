def test_create_and_list_availability_block(client, auth_headers):
    payload = {"type": "trabajo", "day_of_week": 0, "start": "09:00:00", "end": "17:00:00"}
    create_resp = client.post("/v1/availability", json=payload, headers=auth_headers)
    assert create_resp.status_code == 201
    block = create_resp.json()
    assert block["type"] == "trabajo"

    list_resp = client.get("/v1/availability", headers=auth_headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1


def test_start_after_end_is_rejected(client, auth_headers):
    payload = {"type": "trabajo", "day_of_week": 1, "start": "18:00:00", "end": "09:00:00"}
    resp = client.post("/v1/availability", json=payload, headers=auth_headers)
    assert resp.status_code == 422


def test_invalid_day_of_week_is_rejected(client, auth_headers):
    payload = {"type": "escuela", "day_of_week": 9, "start": "09:00:00", "end": "10:00:00"}
    resp = client.post("/v1/availability", json=payload, headers=auth_headers)
    assert resp.status_code == 422


def test_delete_availability_block(client, auth_headers):
    payload = {"type": "personal", "day_of_week": 2, "start": "20:00:00", "end": "21:00:00"}
    created = client.post("/v1/availability", json=payload, headers=auth_headers).json()

    delete_resp = client.delete(f"/v1/availability/{created['id']}", headers=auth_headers)
    assert delete_resp.status_code == 204

    list_resp = client.get("/v1/availability", headers=auth_headers)
    assert list_resp.json() == []


def test_cannot_delete_another_users_block(client):
    client.post("/v1/auth/register", json={"email": "owner@example.com", "password": "supersecreta1"})
    client.post("/v1/auth/register", json={"email": "intruder@example.com", "password": "supersecreta1"})

    owner_login = client.post(
        "/v1/auth/login", json={"email": "owner@example.com", "password": "supersecreta1"}
    ).json()
    intruder_login = client.post(
        "/v1/auth/login", json={"email": "intruder@example.com", "password": "supersecreta1"}
    ).json()

    owner_headers = {"Authorization": f"Bearer {owner_login['access_token']}"}
    intruder_headers = {"Authorization": f"Bearer {intruder_login['access_token']}"}

    block = client.post(
        "/v1/availability",
        json={"type": "trabajo", "day_of_week": 3, "start": "09:00:00", "end": "17:00:00"},
        headers=owner_headers,
    ).json()

    # el aislamiento por usuario (sección J) debe impedir que otro usuario
    # borre (o vea la existencia de) un recurso ajeno
    resp = client.delete(f"/v1/availability/{block['id']}", headers=intruder_headers)
    assert resp.status_code == 404

    still_there = client.get("/v1/availability", headers=owner_headers).json()
    assert len(still_there) == 1
