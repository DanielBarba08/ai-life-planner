from datetime import datetime

PLAN_DATE = "2026-11-16"  # lunes fijo y arbitrario — determinista, no depende del día real


def test_day_not_found_before_optimizing(client, auth_headers):
    resp = client.get(f"/v1/planning/day/{PLAN_DATE}", headers=auth_headers)
    assert resp.status_code == 404


def test_optimize_with_no_data_returns_empty_plan(client, auth_headers):
    resp = client.post("/v1/planning/optimize", json={"date": PLAN_DATE}, headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["blocks"] == []
    assert body["unplaced"] == []
    assert body["conflicts"] == []


def test_optimize_places_a_task_and_explanation_is_fetchable(client, auth_headers):
    client.post(
        "/v1/tasks",
        json={"title": "Preparar presentación", "duration_est_min": 90, "priority": "alta", "concentration_level": "alta"},
        headers=auth_headers,
    )
    resp = client.post("/v1/planning/optimize", json={"date": PLAN_DATE}, headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["blocks"]) == 1
    block = body["blocks"][0]
    assert block["source_type"] == "task"

    explanation = client.get(f"/v1/explanations/{block['id']}", headers=auth_headers)
    assert explanation.status_code == 200
    exp_body = explanation.json()
    assert exp_body["confidence"] == "baja"
    assert exp_body["evidence"] is None
    assert "prioridad" in exp_body["user_data"]


def test_explanation_includes_real_evidence_when_task_lands_in_preferred_window(client, auth_headers):
    client.put(
        "/v1/users/me/preferences",
        json={"preferred_focus_hours": [{"start": "09:00", "end": "12:00"}]},
        headers=auth_headers,
    )
    client.post(
        "/v1/tasks",
        json={"title": "Preparar presentación", "duration_est_min": 90, "priority": "alta", "concentration_level": "alta"},
        headers=auth_headers,
    )
    plan = client.post("/v1/planning/optimize", json={"date": PLAN_DATE}, headers=auth_headers).json()
    block = plan["blocks"][0]

    explanation = client.get(f"/v1/explanations/{block['id']}", headers=auth_headers).json()
    assert explanation["evidence"] is not None
    assert explanation["evidence"]["doi"] == "10.1037/0096-1523.27.4.763"
    assert explanation["evidence"]["evidence_level"] == "moderada"
    assert "Rubinstein" in explanation["evidence"]["authors"]
    assert explanation["evidence"]["limitations"]  # nunca se presenta sin sus límites


def test_optimize_persists_and_get_day_returns_same_plan(client, auth_headers):
    client.post("/v1/tasks", json={"title": "Leer", "duration_est_min": 30}, headers=auth_headers)
    optimize_resp = client.post("/v1/planning/optimize", json={"date": PLAN_DATE}, headers=auth_headers)
    get_resp = client.get(f"/v1/planning/day/{PLAN_DATE}", headers=auth_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == optimize_resp.json()["id"]


def test_fixed_event_and_availability_appear_as_blocks(client, auth_headers):
    client.post(
        "/v1/events",
        json={"title": "Cita médica", "start": f"{PLAN_DATE}T18:00:00", "end": f"{PLAN_DATE}T19:00:00"},
        headers=auth_headers,
    )
    # 2026-11-16 es lunes -> day_of_week 0
    client.post(
        "/v1/availability",
        json={"type": "trabajo", "day_of_week": 0, "start": "09:00:00", "end": "17:00:00"},
        headers=auth_headers,
    )
    resp = client.post("/v1/planning/optimize", json={"date": PLAN_DATE}, headers=auth_headers)
    titles = {b["title"] for b in resp.json()["blocks"]}
    assert "Cita médica" in titles
    assert any("Trabajo" in t for t in titles)


def test_overcommitted_day_surfaces_conflict_via_api(client, auth_headers):
    client.post(
        "/v1/availability",
        json={"type": "trabajo", "day_of_week": 0, "start": "09:00:00", "end": "23:00:00"},
        headers=auth_headers,
    )
    client.post(
        "/v1/tasks",
        json={"title": "Tarea imposible", "duration_est_min": 180, "priority": "alta"},
        headers=auth_headers,
    )
    resp = client.post("/v1/planning/optimize", json={"date": PLAN_DATE}, headers=auth_headers)
    body = resp.json()
    assert len(body["conflicts"]) == 1
    assert len(body["unplaced"]) == 1
    assert body["unplaced"][0]["suggestion"]


def test_explanation_not_found_for_event_block(client, auth_headers):
    client.post(
        "/v1/events",
        json={"title": "Evento manual", "start": f"{PLAN_DATE}T10:00:00", "end": f"{PLAN_DATE}T11:00:00"},
        headers=auth_headers,
    )
    plan = client.post("/v1/planning/optimize", json={"date": PLAN_DATE}, headers=auth_headers).json()
    event_block = next(b for b in plan["blocks"] if b["source_type"] == "event")
    resp = client.get(f"/v1/explanations/{event_block['id']}", headers=auth_headers)
    assert resp.status_code == 404


def test_explanation_isolated_per_user(client):
    client.post("/v1/auth/register", json={"email": "owner@example.com", "password": "supersecreta1"})
    client.post("/v1/auth/register", json={"email": "intruder@example.com", "password": "supersecreta1"})
    owner_token = client.post(
        "/v1/auth/login", json={"email": "owner@example.com", "password": "supersecreta1"}
    ).json()["access_token"]
    intruder_token = client.post(
        "/v1/auth/login", json={"email": "intruder@example.com", "password": "supersecreta1"}
    ).json()["access_token"]
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    intruder_headers = {"Authorization": f"Bearer {intruder_token}"}

    client.post("/v1/tasks", json={"title": "Privada", "duration_est_min": 30}, headers=owner_headers)
    plan = client.post("/v1/planning/optimize", json={"date": PLAN_DATE}, headers=owner_headers).json()
    block_id = plan["blocks"][0]["id"]

    resp = client.get(f"/v1/explanations/{block_id}", headers=intruder_headers)
    assert resp.status_code == 404


def test_replan_keeps_working_and_reflects_newly_added_task(client, auth_headers):
    client.post("/v1/tasks", json={"title": "Tarea 1", "duration_est_min": 30}, headers=auth_headers)
    client.post("/v1/planning/optimize", json={"date": PLAN_DATE}, headers=auth_headers)

    client.post("/v1/tasks", json={"title": "Tarea agregada después", "duration_est_min": 30}, headers=auth_headers)
    replanned = client.post("/v1/planning/replan", json={"date": PLAN_DATE, "reason": "agregué algo"}, headers=auth_headers)
    assert replanned.status_code == 200
    titles = {b["title"] for b in replanned.json()["blocks"]}
    assert "Tarea agregada después" in titles


def test_whats_next_auto_generates_plan_for_today(client, auth_headers):
    client.post("/v1/tasks", json={"title": "Algo para hoy", "duration_est_min": 30}, headers=auth_headers)
    resp = client.get("/v1/planning/now", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["situation"] in {"en_curso", "hueco_libre", "dia_libre"}
    assert body["message"]


def test_planning_endpoints_require_auth(client):
    assert client.post("/v1/planning/optimize", json={"date": PLAN_DATE}).status_code == 401
    assert client.get(f"/v1/planning/day/{PLAN_DATE}").status_code == 401
    assert client.get("/v1/planning/now").status_code == 401


def test_optimize_only_schedules_habit_sessions_on_their_own_day(client, auth_headers):
    """
    Regresión del bug reportado por Daniel el 8 nov: al confirmar las
    sesiones sugeridas de un hábito para varios días distintos de la
    semana, "Optimizar mi día" para UN solo día no debe meter todas las
    sesiones de la semana en ese día — cada sesión confirmada tiene su
    propio deadline (el día que le tocaba) y solo debe poder programarse
    ahí, nunca adelantada a otro día solo porque hay tiempo libre.

    Las fechas se fabrican a mano (en vez de usar las que /week sugiere
    de verdad) para que la prueba sea determinista sin importar qué día
    de la semana real se ejecute — confirm-week solo valida la CANTIDAD
    de sesiones contra lo que falta, no que coincidan exactamente con lo
    sugerido (ver app/routers/habits.py::confirm_habit_week).
    """
    habit_resp = client.post(
        "/v1/habits",
        json={"title": "Entrenar", "target_frequency_per_week": 3, "duration_est_min": 45},
        headers=auth_headers,
    )
    habit_id = habit_resp.json()["id"]

    day_a, day_b = "2026-11-17", "2026-11-19"  # martes y jueves, arbitrarios y fijos
    sessions = [
        {
            "title": "Entrenar",
            "duration_est_min": 45,
            "concentration_level": "media",
            "category": None,
            "suggested_date": day,
        }
        for day in (day_a, day_b)
    ]

    confirm = client.post(f"/v1/habits/{habit_id}/confirm-week", json={"sessions": sessions}, headers=auth_headers)
    assert confirm.status_code == 201, confirm.text
    created = confirm.json()
    assert len(created) == 2
    # Cada tarea creada trae su propio deadline (fin del día sugerido) —
    # lo leemos directo de /v1/tasks en vez de adivinar por título.
    tasks = client.get("/v1/tasks", headers=auth_headers).json()
    deadline_date_by_id = {
        t["id"]: datetime.fromisoformat(t["deadline"]).date().isoformat()
        for t in tasks
        if t.get("habit_id") == habit_id and t.get("deadline")
    }
    assert set(deadline_date_by_id.values()) == {day_a, day_b}

    plan = client.post("/v1/planning/optimize", json={"date": day_a}, headers=auth_headers).json()
    scheduled_task_ids = {b["source_id"] for b in plan["blocks"] if b["source_type"] == "task"}

    # La sesión de day_a sí debe poder programarse en el plan de day_a...
    task_a = next(tid for tid, d in deadline_date_by_id.items() if d == day_a)
    assert task_a in scheduled_task_ids
    # ...pero la de day_b no debe colarse ahí solo porque hay tiempo libre.
    task_b = next(tid for tid, d in deadline_date_by_id.items() if d == day_b)
    assert task_b not in scheduled_task_ids


def test_deleting_a_task_removes_its_block_from_an_already_optimized_plan(client, auth_headers):
    """
    Segunda parte del pedido de Daniel el 8 nov: borrar una tarea
    manualmente desde el calendario (Mi día/Mi semana) debe quitar
    también su bloque de un plan ya generado — no solo borrarla de
    /v1/tasks — porque un plan optimizado guarda sus bloques por separado
    en plan_blocks (ver app/routers/tasks.py::delete_task).
    """
    task = client.post(
        "/v1/tasks", json={"title": "Leer", "duration_est_min": 30}, headers=auth_headers
    ).json()
    plan = client.post("/v1/planning/optimize", json={"date": PLAN_DATE}, headers=auth_headers).json()
    block = next(b for b in plan["blocks"] if b["source_type"] == "task" and b["source_id"] == task["id"])

    resp = client.delete(f"/v1/tasks/{task['id']}", headers=auth_headers)
    assert resp.status_code == 204

    refreshed = client.get(f"/v1/planning/day/{PLAN_DATE}", headers=auth_headers).json()
    assert all(b["id"] != block["id"] for b in refreshed["blocks"])
    assert all(b["source_id"] != task["id"] for b in refreshed["blocks"])

    # La explicación del bloque borrado tampoco debe seguir accesible.
    explanation = client.get(f"/v1/explanations/{block['id']}", headers=auth_headers)
    assert explanation.status_code == 404
