"""
GET /v1/planning/week/{start_date} — cierra el hueco de API que el
frontend identificó al construir "Mi semana" (ver frontend/README.md).
Fecha fija y arbitraria como en test_planning_api.py — determinista, no
depende de qué día es "hoy" cuando corre la suite.
"""
from datetime import date, timedelta

WEEK_START = date(2026, 11, 16)  # lunes fijo


def test_week_with_no_plans_returns_seven_days_all_without_plan(client, auth_headers):
    resp = client.get(f"/v1/planning/week/{WEEK_START}", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 7
    assert [d["date"] for d in body] == [str(WEEK_START + timedelta(days=i)) for i in range(7)]
    assert all(d["has_plan"] is False for d in body)
    assert all(d["blocks"] == [] for d in body)


def test_week_includes_real_blocks_for_optimized_days_only(client, auth_headers):
    client.post("/v1/tasks", json={"title": "Leer", "duration_est_min": 30}, headers=auth_headers)

    monday = WEEK_START
    wednesday = WEEK_START + timedelta(days=2)
    client.post("/v1/planning/optimize", json={"date": str(monday)}, headers=auth_headers)
    client.post("/v1/planning/optimize", json={"date": str(wednesday)}, headers=auth_headers)

    resp = client.get(f"/v1/planning/week/{WEEK_START}", headers=auth_headers)
    body = resp.json()

    by_date = {d["date"]: d for d in body}
    assert by_date[str(monday)]["has_plan"] is True
    assert len(by_date[str(monday)]["blocks"]) == 1
    assert by_date[str(monday)]["blocks"][0]["title"] == "Leer"

    assert by_date[str(wednesday)]["has_plan"] is True
    # Las tareas no están ancladas a un día — siguen "pendientes" hasta que
    # alguien las marca completadas (sección "Qué NO incluye todavía" del
    # backend: no hay agenda semanal automática de tareas). Cada
    # optimize() vuelve a mirar el mismo pool de pendientes, así que la
    # misma tarea puede aparecer en más de un día si se optimizan varios.
    assert len(by_date[str(wednesday)]["blocks"]) == 1
    assert by_date[str(wednesday)]["blocks"][0]["title"] == "Leer"

    tuesday = WEEK_START + timedelta(days=1)
    assert by_date[str(tuesday)]["has_plan"] is False


def test_week_is_isolated_per_user(client):
    a = client.post("/v1/auth/register", json={"email": "week-a@example.com", "password": "password123"})
    b = client.post("/v1/auth/register", json={"email": "week-b@example.com", "password": "password123"})
    assert a.status_code == 201 and b.status_code == 201

    login_a = client.post("/v1/auth/login", json={"email": "week-a@example.com", "password": "password123"}).json()
    login_b = client.post("/v1/auth/login", json={"email": "week-b@example.com", "password": "password123"}).json()
    headers_a = {"Authorization": f"Bearer {login_a['access_token']}"}
    headers_b = {"Authorization": f"Bearer {login_b['access_token']}"}

    client.post("/v1/planning/optimize", json={"date": str(WEEK_START)}, headers=headers_a)

    week_b = client.get(f"/v1/planning/week/{WEEK_START}", headers=headers_b).json()
    assert all(d["has_plan"] is False for d in week_b)


def test_week_requires_auth(client):
    resp = client.get(f"/v1/planning/week/{WEEK_START}")
    assert resp.status_code == 401
