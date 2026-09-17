def test_create_task_with_defaults(client, auth_headers):
    resp = client.post(
        "/v1/tasks",
        json={"title": "Preparar presentación", "duration_est_min": 90},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["priority"] == "media"
    assert body["concentration_level"] == "media"
    assert body["status"] == "pendiente"


def test_create_task_full_payload(client, auth_headers):
    resp = client.post(
        "/v1/tasks",
        json={
            "title": "Preparar examen",
            "priority": "alta",
            "duration_est_min": 120,
            "concentration_level": "alta",
            "category": "Estudio",
            "deadline": "2026-09-19T23:59:00",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["priority"] == "alta"
    assert body["category"] == "Estudio"


def test_duration_must_be_positive(client, auth_headers):
    resp = client.post(
        "/v1/tasks", json={"title": "Tarea rota", "duration_est_min": 0}, headers=auth_headers
    )
    assert resp.status_code == 422


def test_list_tasks_filtered_by_status(client, auth_headers):
    t1 = client.post(
        "/v1/tasks", json={"title": "A", "duration_est_min": 30}, headers=auth_headers
    ).json()
    client.post("/v1/tasks", json={"title": "B", "duration_est_min": 30}, headers=auth_headers)
    client.patch(f"/v1/tasks/{t1['id']}", json={"status": "completada"}, headers=auth_headers)

    pending = client.get("/v1/tasks?status=pendiente", headers=auth_headers).json()
    done = client.get("/v1/tasks?status=completada", headers=auth_headers).json()
    assert len(pending) == 1
    assert len(done) == 1
    assert done[0]["title"] == "A"


def test_task_dependency_must_belong_to_same_user(client, auth_headers):
    resp = client.post(
        "/v1/tasks",
        json={"title": "Depende de nada", "duration_est_min": 30, "depends_on_id": "id-inexistente"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_task_cannot_depend_on_itself(client, auth_headers):
    task = client.post(
        "/v1/tasks", json={"title": "Autoreferencia", "duration_est_min": 30}, headers=auth_headers
    ).json()
    resp = client.patch(
        f"/v1/tasks/{task['id']}", json={"depends_on_id": task["id"]}, headers=auth_headers
    )
    assert resp.status_code == 422


def test_task_dependency_valid_case(client, auth_headers):
    base = client.post(
        "/v1/tasks", json={"title": "Investigación", "duration_est_min": 60}, headers=auth_headers
    ).json()
    dependent = client.post(
        "/v1/tasks",
        json={"title": "Redacción", "duration_est_min": 60, "depends_on_id": base["id"]},
        headers=auth_headers,
    )
    assert dependent.status_code == 201
    assert dependent.json()["depends_on_id"] == base["id"]


def test_delete_task(client, auth_headers):
    task = client.post(
        "/v1/tasks", json={"title": "Borrar", "duration_est_min": 15}, headers=auth_headers
    ).json()
    resp = client.delete(f"/v1/tasks/{task['id']}", headers=auth_headers)
    assert resp.status_code == 204
    assert client.get("/v1/tasks", headers=auth_headers).json() == []
