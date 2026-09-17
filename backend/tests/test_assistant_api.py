def test_optimize_via_assistant_actually_creates_a_day_plan(client, auth_headers):
    client.post("/v1/tasks", json={"title": "Leer", "duration_est_min": 30}, headers=auth_headers)
    resp = client.post("/v1/assistant/message", json={"message": "Optimiza mi día"}, headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["action"] == "optimize_day"
    assert body["day_plan"] is not None
    assert len(body["day_plan"]["blocks"]) == 1

    # el plan quedó realmente guardado, no solo en la respuesta del chat
    today = body["day_plan"]["date"]
    persisted = client.get(f"/v1/planning/day/{today}", headers=auth_headers)
    assert persisted.status_code == 200
    assert persisted.json()["id"] == body["day_plan"]["id"]


def test_quiero_entrenar_crea_un_objetivo_real(client, auth_headers):
    resp = client.post(
        "/v1/assistant/message",
        json={"message": "Quiero entrenar tres veces esta semana"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["action"] == "create_goal"
    assert body["goal"]["horizon"] == "semana"
    assert body["goal"]["confirmed_by_user"] is True

    goals = client.get("/v1/goals", headers=auth_headers).json()
    assert any(g["id"] == body["goal"]["id"] for g in goals)


def test_no_termine_las_tareas_de_ayer_replanifica_con_datos_reales(client, auth_headers):
    client.post("/v1/tasks", json={"title": "Tarea atrasada", "duration_est_min": 45}, headers=auth_headers)
    resp = client.post(
        "/v1/assistant/message", json={"message": "No terminé las tareas de ayer"}, headers=auth_headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["action"] == "replan_day"
    titles = {b["title"] for b in body["day_plan"]["blocks"]}
    assert "Tarea atrasada" in titles


def test_que_hago_ahora_via_assistant(client, auth_headers):
    resp = client.post("/v1/assistant/message", json={"message": "¿Qué hago ahora?"}, headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["action"] == "whats_next"
    assert body["reply"]
    assert body["day_plan"] is None


def test_ambiguous_deadline_message_asks_for_clarification_without_changing_data(client, auth_headers):
    task = client.post(
        "/v1/tasks", json={"title": "Proyecto", "duration_est_min": 60}, headers=auth_headers
    ).json()
    resp = client.post(
        "/v1/assistant/message",
        json={"message": "Tengo que terminar este proyecto mañana"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["action"] == "clarify"
    assert body["day_plan"] is None
    assert body["goal"] is None

    # la tarea no se tocó sola
    unchanged = client.get(f"/v1/tasks/{task['id']}", headers=auth_headers).json()
    assert unchanged["deadline"] is None


def test_unrecognized_message_is_honest_not_generic_fluff(client, auth_headers):
    resp = client.post(
        "/v1/assistant/message", json={"message": "cuéntame un chiste"}, headers=auth_headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["action"] == "unrecognized"
    assert "no entiendo" in body["reply"].lower() or "todavía no entiendo" in body["reply"].lower()


def test_assistant_requires_auth(client):
    resp = client.post("/v1/assistant/message", json={"message": "optimiza mi día"})
    assert resp.status_code == 401


def test_assistant_message_cannot_be_empty(client, auth_headers):
    resp = client.post("/v1/assistant/message", json={"message": ""}, headers=auth_headers)
    assert resp.status_code == 422
