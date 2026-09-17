def test_create_and_list_event(client, auth_headers):
    payload = {"title": "Cita médica", "start": "2026-09-15T18:00:00", "end": "2026-09-15T19:00:00"}
    resp = client.post("/v1/events", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "Cita médica"
    assert body["is_movable"] is False
    assert body["source"] == "manual"

    listed = client.get("/v1/events", headers=auth_headers)
    assert len(listed.json()) == 1


def test_end_before_start_is_rejected(client, auth_headers):
    payload = {"title": "Evento imposible", "start": "2026-09-15T19:00:00", "end": "2026-09-15T18:00:00"}
    resp = client.post("/v1/events", json=payload, headers=auth_headers)
    assert resp.status_code == 422


def test_update_event_title(client, auth_headers):
    created = client.post(
        "/v1/events",
        json={"title": "Reunión", "start": "2026-09-16T09:00:00", "end": "2026-09-16T10:00:00"},
        headers=auth_headers,
    ).json()
    resp = client.patch(f"/v1/events/{created['id']}", json={"title": "Reunión de equipo"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["title"] == "Reunión de equipo"


def test_update_event_to_invalid_range_is_rejected(client, auth_headers):
    created = client.post(
        "/v1/events",
        json={"title": "Reunión", "start": "2026-09-16T09:00:00", "end": "2026-09-16T10:00:00"},
        headers=auth_headers,
    ).json()
    resp = client.patch(
        f"/v1/events/{created['id']}", json={"start": "2026-09-16T11:00:00"}, headers=auth_headers
    )
    assert resp.status_code == 422


def test_delete_event(client, auth_headers):
    created = client.post(
        "/v1/events",
        json={"title": "Borrar esto", "start": "2026-09-16T09:00:00", "end": "2026-09-16T10:00:00"},
        headers=auth_headers,
    ).json()
    resp = client.delete(f"/v1/events/{created['id']}", headers=auth_headers)
    assert resp.status_code == 204
    assert client.get("/v1/events", headers=auth_headers).json() == []


def test_event_not_found_for_other_user(client):
    client.post("/v1/auth/register", json={"email": "owner@example.com", "password": "supersecreta1"})
    client.post("/v1/auth/register", json={"email": "intruder@example.com", "password": "supersecreta1"})
    owner_token = client.post(
        "/v1/auth/login", json={"email": "owner@example.com", "password": "supersecreta1"}
    ).json()["access_token"]
    intruder_token = client.post(
        "/v1/auth/login", json={"email": "intruder@example.com", "password": "supersecreta1"}
    ).json()["access_token"]

    event = client.post(
        "/v1/events",
        json={"title": "Privado", "start": "2026-09-16T09:00:00", "end": "2026-09-16T10:00:00"},
        headers={"Authorization": f"Bearer {owner_token}"},
    ).json()

    resp = client.get(
        f"/v1/events/{event['id']}", headers={"Authorization": f"Bearer {intruder_token}"}
    )
    assert resp.status_code == 404
