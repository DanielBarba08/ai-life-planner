"""
Hábitos avanzados (Fase 5 del roadmap) — CRUD de hábitos + progreso y
sesiones sugeridas de la semana actual + confirmación explícita (nunca se
crea una tarea sin que el usuario la confirme, punto 14 del brief).

Usa la zona horaria real del usuario de prueba (America/Mexico_City,
default) para calcular "hoy"/"esta semana" en vez de una fecha fija — igual
que test_planning_streak.py — porque GET .../week siempre opera sobre la
semana actual real, sin parámetro para elegir otra.
"""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Mexico_City")


def _today():
    return datetime.now(timezone.utc).astimezone(TZ).date()


def _days_left_in_week(today):
    """Días de `today` al domingo de esa semana, inclusive — mismo cálculo
    que `app/habits/service.py::suggest_sessions` para saber cuántas
    sesiones distintas puede sugerir sin repetir un día (nunca más de una
    sesión por día, ver el fix del bug reportado el 8 nov)."""
    return 7 - today.weekday()


def test_habit_crud(client, auth_headers):
    resp = client.post(
        "/v1/habits",
        json={"title": "Entrenar", "target_frequency_per_week": 3, "duration_est_min": 45, "concentration_level": "media"},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    habit = resp.json()
    assert habit["status"] == "activo"
    habit_id = habit["id"]

    resp = client.get("/v1/habits", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = client.patch(f"/v1/habits/{habit_id}", json={"target_frequency_per_week": 4}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["target_frequency_per_week"] == 4

    resp = client.delete(f"/v1/habits/{habit_id}", headers=auth_headers)
    assert resp.status_code == 204

    resp = client.get(f"/v1/habits/{habit_id}", headers=auth_headers)
    assert resp.status_code == 404


def test_habit_requires_valid_goal_of_same_user(client, auth_headers):
    resp = client.post(
        "/v1/habits",
        json={
            "title": "Leer",
            "target_frequency_per_week": 2,
            "duration_est_min": 30,
            "goal_id": "no-existe",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_week_suggests_sessions_up_to_the_target(client, auth_headers):
    resp = client.post(
        "/v1/habits",
        json={"title": "Entrenar", "target_frequency_per_week": 3, "duration_est_min": 45},
        headers=auth_headers,
    )
    habit_id = resp.json()["id"]

    resp = client.get(f"/v1/habits/{habit_id}/week", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["target_frequency_per_week"] == 3
    assert body["confirmed_this_week"] == 0
    assert body["completed_this_week"] == 0
    assert body["remaining_to_suggest"] == 3
    today = _today()
    # Nunca más de una sesión sugerida por día (bug del 8 nov): si quedan
    # menos de 3 días en la semana (p. ej. se corre esto sábado o
    # domingo), se sugieren menos de 3 sesiones en vez de repetir un día.
    expected = min(3, _days_left_in_week(today))
    assert len(body["suggested_sessions"]) == expected
    suggested_dates = [datetime.strptime(s["suggested_date"], "%Y-%m-%d").date() for s in body["suggested_sessions"]]
    assert len(set(suggested_dates)) == len(suggested_dates), "nunca debe repetirse el mismo día"
    for s, d in zip(body["suggested_sessions"], suggested_dates):
        assert d >= today
        assert s["title"] == "Entrenar"
        assert s["duration_est_min"] == 45


def test_confirm_week_creates_real_tasks_and_updates_progress(client, auth_headers):
    resp = client.post(
        "/v1/habits",
        json={"title": "Entrenar", "target_frequency_per_week": 3, "duration_est_min": 45},
        headers=auth_headers,
    )
    habit_id = resp.json()["id"]

    week = client.get(f"/v1/habits/{habit_id}/week", headers=auth_headers).json()
    # Usa como mucho 2 sesiones sugeridas (puede haber menos de 2 si la
    # semana está casi terminada — ver test_week_suggests_sessions_up_to_the_target).
    two_sessions = week["suggested_sessions"][:2]
    n = len(two_sessions)

    resp = client.post(f"/v1/habits/{habit_id}/confirm-week", json={"sessions": two_sessions}, headers=auth_headers)
    assert resp.status_code == 201, resp.text
    created = resp.json()
    assert len(created) == n
    assert all(t["habit_id"] == habit_id for t in created)
    assert all(t["status"] == "pendiente" for t in created)

    week_after = client.get(f"/v1/habits/{habit_id}/week", headers=auth_headers).json()
    assert week_after["confirmed_this_week"] == n
    assert week_after["remaining_to_suggest"] == 3 - n
    # `suggest_sessions` vuelve a repartir sobre el mismo rango de días
    # disponibles de la semana (no excluye los ya confirmados), así que el
    # tope sigue siendo `_days_left_in_week`, no ese número menos `n`.
    assert len(week_after["suggested_sessions"]) == min(3 - n, _days_left_in_week(_today()))

    # Las tareas confirmadas aparecen también en el listado normal de tareas.
    tasks = client.get("/v1/tasks", headers=auth_headers).json()
    assert sum(1 for t in tasks if t.get("habit_id") == habit_id) == n

    # Completar una de las sesiones confirmadas se refleja en el progreso real.
    client.patch(f"/v1/tasks/{created[0]['id']}", json={"status": "completada"}, headers=auth_headers)
    week_completed = client.get(f"/v1/habits/{habit_id}/week", headers=auth_headers).json()
    assert week_completed["completed_this_week"] == 1
    assert week_completed["confirmed_this_week"] == n  # completar no cambia cuántas están confirmadas


def test_confirm_week_rejects_more_sessions_than_remaining(client, auth_headers):
    resp = client.post(
        "/v1/habits",
        json={"title": "Entrenar", "target_frequency_per_week": 1, "duration_est_min": 45},
        headers=auth_headers,
    )
    habit_id = resp.json()["id"]
    week = client.get(f"/v1/habits/{habit_id}/week", headers=auth_headers).json()

    # Manda dos sesiones cuando solo falta una — nunca se crea de más.
    extra_session = {**week["suggested_sessions"][0], "suggested_date": str(_today() + timedelta(days=1))}
    resp = client.post(
        f"/v1/habits/{habit_id}/confirm-week",
        json={"sessions": week["suggested_sessions"] + [extra_session]},
        headers=auth_headers,
    )
    assert resp.status_code == 422

    tasks = client.get("/v1/tasks", headers=auth_headers).json()
    assert len(tasks) == 0


def test_habits_are_isolated_per_user(client):
    a = client.post("/v1/auth/register", json={"email": "habit-a@example.com", "password": "password123"})
    b = client.post("/v1/auth/register", json={"email": "habit-b@example.com", "password": "password123"})
    assert a.status_code == 201 and b.status_code == 201

    login_a = client.post("/v1/auth/login", json={"email": "habit-a@example.com", "password": "password123"}).json()
    login_b = client.post("/v1/auth/login", json={"email": "habit-b@example.com", "password": "password123"}).json()
    headers_a = {"Authorization": f"Bearer {login_a['access_token']}"}
    headers_b = {"Authorization": f"Bearer {login_b['access_token']}"}

    resp = client.post(
        "/v1/habits",
        json={"title": "Entrenar", "target_frequency_per_week": 3, "duration_est_min": 45},
        headers=headers_a,
    )
    habit_id = resp.json()["id"]

    assert client.get(f"/v1/habits/{habit_id}", headers=headers_b).status_code == 404
    assert client.get(f"/v1/habits/{habit_id}/week", headers=headers_b).status_code == 404
    assert client.get("/v1/habits", headers=headers_b).json() == []


def test_habits_require_auth(client):
    assert client.get("/v1/habits").status_code == 401
    assert client.post("/v1/habits", json={}).status_code == 401
