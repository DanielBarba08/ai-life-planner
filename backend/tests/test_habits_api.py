"""
Hábitos avanzados (Fase 5 del roadmap) — CRUD de hábitos + progreso y
sesiones de la semana actual.

Desde el 12 nov (pedido de Daniel: "que se agreguen al horario") las
sesiones de un hábito ACTIVO se auto-confirman solas cada semana —
ver app/habits/service.py::auto_confirm_due_sessions — en vez de esperar
a que el usuario entre a Hábitos y toque "confirmar". El endpoint manual
POST .../confirm-week sigue existiendo (por ejemplo para una sesión que
ya se cree de más tarde en la semana), pero en la práctica
remaining_to_suggest llega a 0 solo o casi solo con crear el hábito.

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


def test_deleting_a_habit_deletes_its_sessions_too(client, auth_headers):
    """Pedido por Daniel el 16 nov, después de confundir las sobras de un
    hábito "Leer" ya borrado con tareas duplicadas de uno nuevo: antes
    borrar un hábito dejaba sus sesiones (tareas con habit_id) sueltas
    como tareas normales para siempre — ahora se borran con él, pendientes
    y completadas por igual."""
    resp = client.post(
        "/v1/habits",
        json={"title": "Leer", "target_frequency_per_week": 3, "duration_est_min": 45, "concentration_level": "media"},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    habit_id = resp.json()["id"]

    resp = client.get("/v1/tasks", headers=auth_headers)
    sessions = [t for t in resp.json() if t["habit_id"] == habit_id]
    assert len(sessions) == 3, sessions

    # Completa una de las sesiones, para probar que una COMPLETADA también
    # se borra con el hábito, no solo las pendientes.
    resp = client.patch(f"/v1/tasks/{sessions[0]['id']}", json={"status": "completada"}, headers=auth_headers)
    assert resp.status_code == 200

    resp = client.delete(f"/v1/habits/{habit_id}", headers=auth_headers)
    assert resp.status_code == 204

    resp = client.get("/v1/tasks", headers=auth_headers)
    assert resp.status_code == 200
    remaining_ids = {t["id"] for t in resp.json()}
    assert not remaining_ids.intersection({s["id"] for s in sessions}), (
        "las sesiones del hábito borrado no deberían seguir en Tareas"
    )


def test_deleting_a_habit_also_removes_its_plan_blocks(client, auth_headers):
    """Regresión encontrada el 16 nov, un día después del fix de arriba:
    si una sesión del hábito ya había sido colocada en un día optimizado
    (POST /v1/planning/optimize), borrar el hábito borraba la tarea pero
    dejaba el PlanBlock huérfano apuntando a un source_id que ya no
    existe — un bloque "zombi" que GET /v1/planning/day/{date} (lo que
    de verdad muestra Mi semana/Mi día, sin volver a optimizar) seguía
    devolviendo para siempre, imposible de quitar (404 al reintentar
    DELETE /v1/tasks/{id} sobre un id que ya no está). Esto es justo lo
    que reportó Daniel: un bloque de "leer" que no se podía eliminar."""
    resp = client.post(
        "/v1/habits",
        json={"title": "Leer", "target_frequency_per_week": 1, "duration_est_min": 45, "concentration_level": "media"},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    habit_id = resp.json()["id"]

    resp = client.get("/v1/tasks", headers=auth_headers)
    sessions = [t for t in resp.json() if t["habit_id"] == habit_id]
    assert len(sessions) == 1, sessions
    session_date = sessions[0]["deadline"][:10]
    session_task_id = sessions[0]["id"]

    resp = client.post("/v1/planning/optimize", json={"date": session_date}, headers=auth_headers)
    assert resp.status_code == 200, resp.text
    plan = resp.json()
    assert any(b["source_id"] == session_task_id for b in plan["blocks"]), (
        "la sesión del hábito debería haber quedado colocada en el plan de ese día"
    )

    resp = client.delete(f"/v1/habits/{habit_id}", headers=auth_headers)
    assert resp.status_code == 204

    # Sin volver a optimizar nada — exactamente como Mi semana/Mi día
    # leen el plan ya guardado — el bloque de la sesión borrada no
    # debería seguir apareciendo.
    resp = client.get(f"/v1/planning/day/{session_date}", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    plan_after = resp.json()
    assert not any(b["source_id"] == session_task_id for b in plan_after["blocks"]), (
        "el PlanBlock de la sesión borrada no debería seguir apareciendo al releer el día sin re-optimizar"
    )


def test_creating_a_habit_auto_confirms_sessions_for_the_current_week(client, auth_headers):
    """Pedido por Daniel el 12 nov: "que se agreguen al horario" — ya no
    hace falta entrar a Hábitos y confirmar nada a mano."""
    resp = client.post(
        "/v1/habits",
        json={"title": "Entrenar", "target_frequency_per_week": 3, "duration_est_min": 45},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    habit_id = resp.json()["id"]
    today = _today()
    # Nunca más de una sesión por día (bug del 8 nov): si quedan menos de
    # 3 días en la semana (p. ej. se corre esto sábado o domingo), se
    # confirman menos de 3 sesiones en vez de repetir un día.
    expected = min(3, _days_left_in_week(today))

    resp = client.get(f"/v1/habits/{habit_id}/week", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["target_frequency_per_week"] == 3
    assert body["confirmed_this_week"] == expected
    assert body["completed_this_week"] == 0
    assert body["remaining_to_suggest"] == 3 - expected
    # Ya no queda nada "por sugerir": lo disponible esta semana ya se
    # confirmó solo al crear el hábito.
    assert body["suggested_sessions"] == []

    tasks = [t for t in client.get("/v1/tasks", headers=auth_headers).json() if t.get("habit_id") == habit_id]
    assert len(tasks) == expected
    assert all(t["status"] == "pendiente" for t in tasks)
    assert all(t["duration_est_min"] == 45 for t in tasks)
    dates = [datetime.fromisoformat(t["deadline"]).date() for t in tasks]
    assert len(set(dates)) == len(dates), "nunca debe repetirse el mismo día"
    assert all(d >= today for d in dates)

    # Completar una de las sesiones confirmadas se refleja en el progreso real.
    client.patch(f"/v1/tasks/{tasks[0]['id']}", json={"status": "completada"}, headers=auth_headers)
    week_completed = client.get(f"/v1/habits/{habit_id}/week", headers=auth_headers).json()
    assert week_completed["completed_this_week"] == 1
    assert week_completed["confirmed_this_week"] == expected  # completar no cambia cuántas están confirmadas


def test_pausing_a_habit_stops_auto_confirming_new_sessions(client, auth_headers):
    resp = client.post(
        "/v1/habits",
        json={"title": "Entrenar", "target_frequency_per_week": 1, "duration_est_min": 45},
        headers=auth_headers,
    )
    habit_id = resp.json()["id"]

    def _tasks():
        return [t for t in client.get("/v1/tasks", headers=auth_headers).json() if t.get("habit_id") == habit_id]

    # Con frecuencia 1 ya quedó confirmada (al crear) la única sesión
    # posible esta semana. Libera ese cupo borrando la tarea, para poder
    # comprobar que, pausado, el hábito NO la vuelve a agregar solo.
    assert len(_tasks()) == 1
    client.delete(f"/v1/tasks/{_tasks()[0]['id']}", headers=auth_headers)
    assert len(_tasks()) == 0

    client.patch(f"/v1/habits/{habit_id}", json={"status": "pausado"}, headers=auth_headers)
    client.get("/v1/habits", headers=auth_headers)
    client.get(f"/v1/habits/{habit_id}/week", headers=auth_headers)
    assert len(_tasks()) == 0, "un hábito pausado no debe auto-confirmar nada"

    # Reactivarlo sí vuelve a dejarlo al día — confirma que lo anterior
    # era por estar pausado, no por algún otro motivo.
    client.patch(f"/v1/habits/{habit_id}", json={"status": "activo"}, headers=auth_headers)
    client.get("/v1/habits", headers=auth_headers)
    assert len(_tasks()) == 1


def test_auto_confirm_never_duplicates_a_day_when_target_exceeds_days_left(client, auth_headers):
    """Si target_frequency_per_week es mayor que los días que quedan en la
    semana, remaining_to_suggest se queda arriba de 0 para siempre (hasta
    el lunes siguiente) — sin excluir los días ya confirmados,
    auto_confirm_due_sessions volvería a "sugerir" esos mismos días en
    cada lectura y crearía una sesión duplicada por día cada vez que se
    abre la app (la versión automática del bug del 8 nov)."""
    resp = client.post(
        "/v1/habits",
        json={"title": "Entrenar", "target_frequency_per_week": 14, "duration_est_min": 45},
        headers=auth_headers,
    )
    habit_id = resp.json()["id"]

    def _task_count():
        return len([t for t in client.get("/v1/tasks", headers=auth_headers).json() if t.get("habit_id") == habit_id])

    first_count = _task_count()
    assert 1 <= first_count <= 7

    # Releer varias veces (como abrir Hábitos/Mi día repetidas veces el
    # mismo día) nunca debe agregar tareas nuevas: ya se usó cada día
    # disponible de la semana una sola vez.
    for _ in range(3):
        client.get("/v1/habits", headers=auth_headers)
        client.get(f"/v1/habits/{habit_id}/week", headers=auth_headers)
    assert _task_count() == first_count

    tasks = [t for t in client.get("/v1/tasks", headers=auth_headers).json() if t.get("habit_id") == habit_id]
    dates = [datetime.fromisoformat(t["deadline"]).date() for t in tasks]
    assert len(set(dates)) == len(dates), "nunca debe repetirse el mismo día"


def test_confirm_week_rejects_more_sessions_than_remaining(client, auth_headers):
    resp = client.post(
        "/v1/habits",
        json={"title": "Entrenar", "target_frequency_per_week": 1, "duration_est_min": 45},
        headers=auth_headers,
    )
    habit_id = resp.json()["id"]
    # La única sesión posible esta semana ya se auto-confirmó al crear el
    # hábito — remaining_to_suggest ya es 0, así que cualquier sesión que
    # se intente confirmar a mano excede lo que falta.
    extra_session = {
        "title": "Entrenar",
        "duration_est_min": 45,
        "concentration_level": "media",
        "category": None,
        "suggested_date": str(_today() + timedelta(days=1)),
    }
    resp = client.post(
        f"/v1/habits/{habit_id}/confirm-week",
        json={"sessions": [extra_session]},
        headers=auth_headers,
    )
    assert resp.status_code == 422

    tasks = [t for t in client.get("/v1/tasks", headers=auth_headers).json() if t.get("habit_id") == habit_id]
    assert len(tasks) == 1  # solo la que se confirmó sola al crear


def test_habit_progress_history_covers_requested_number_of_weeks(client, auth_headers):
    resp = client.post(
        "/v1/habits",
        json={"title": "Entrenar", "target_frequency_per_week": 3, "duration_est_min": 45},
        headers=auth_headers,
    )
    habit_id = resp.json()["id"]
    today = _today()
    expected_this_week = min(3, _days_left_in_week(today))

    resp = client.get(f"/v1/habits/{habit_id}/progress?weeks=4", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["habit_id"] == habit_id
    assert len(body["weeks"]) == 4
    # La más reciente (última del arreglo) es la semana actual — las
    # anteriores no tienen ninguna sesión confirmada todavía.
    assert body["weeks"][-1]["confirmed"] == expected_this_week
    assert all(w["confirmed"] == 0 for w in body["weeks"][:-1])
    assert all(w["target_frequency_per_week"] == 3 for w in body["weeks"])


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
