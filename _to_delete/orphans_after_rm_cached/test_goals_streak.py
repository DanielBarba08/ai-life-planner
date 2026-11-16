"""
Racha de objetivos (GET/POST /v1/goals/{id}/streak|checkin) — pedido por
Daniel el 8 nov: "preguntar al usuario si ha cumplido con los objetivos
día con día y la racha debe ir actualizando". Mismo criterio de zona
horaria real que test_planning_streak.py (default: America/Mexico_City,
ver app/models/user.py), para no depender de qué día calendario es "hoy"
cuando corre la suite.

A diferencia de day_plans, aquí sí existe una respuesta explícita de "no
cumplí" (GoalCheckin.completed=False) que debe cortar la racha de
inmediato — por eso hay pruebas dedicadas a ese caso, y a que el checkin
es un upsert (contestar dos veces el mismo día actualiza, no duplica).
"""
from datetime import timedelta
from zoneinfo import ZoneInfo

from app.models.goal import GoalCheckin

TZ = ZoneInfo("America/Mexico_City")


def _dates_around_today():
    from datetime import datetime, timezone

    today = datetime.now(timezone.utc).astimezone(TZ).date()
    return today, today - timedelta(days=1), today - timedelta(days=2), today - timedelta(days=3)


def _make_goal(client, auth_headers):
    return client.post(
        "/v1/goals", json={"title": "Correr 5k", "horizon": "mes"}, headers=auth_headers
    ).json()


def _seed_checkin(db_session_factory, goal_id, day, completed):
    db = db_session_factory()
    db.add(GoalCheckin(goal_id=goal_id, date=day, completed=completed))
    db.commit()
    db.close()


def test_goal_streak_is_zero_with_no_checkins_at_all(client, auth_headers):
    goal = _make_goal(client, auth_headers)
    resp = client.get(f"/v1/goals/{goal['id']}/streak", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["current_streak"] == 0
    assert body["checked_in_today"] is False
    assert body["completed_today"] is False


def test_goal_streak_counts_consecutive_days_ending_yesterday_without_penalizing_missing_today(
    client, auth_headers, db_session_factory
):
    goal = _make_goal(client, auth_headers)
    _, yesterday, two_days_ago, _ = _dates_around_today()
    _seed_checkin(db_session_factory, goal["id"], yesterday, True)
    _seed_checkin(db_session_factory, goal["id"], two_days_ago, True)

    resp = client.get(f"/v1/goals/{goal['id']}/streak", headers=auth_headers)
    body = resp.json()
    assert body["current_streak"] == 2
    assert body["checked_in_today"] is False


def test_goal_streak_includes_today_once_checked_in_and_grows(client, auth_headers, db_session_factory):
    goal = _make_goal(client, auth_headers)
    _, yesterday, two_days_ago, _ = _dates_around_today()
    _seed_checkin(db_session_factory, goal["id"], two_days_ago, True)
    _seed_checkin(db_session_factory, goal["id"], yesterday, True)

    resp = client.post(f"/v1/goals/{goal['id']}/checkin", json={"completed": True}, headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["current_streak"] == 3
    assert body["checked_in_today"] is True
    assert body["completed_today"] is True


def test_goal_streak_breaks_on_a_gap(client, auth_headers, db_session_factory):
    goal = _make_goal(client, auth_headers)
    _, _, two_days_ago, three_days_ago = _dates_around_today()
    # Falta 'yesterday' — la racha no debe saltarse el hueco.
    _seed_checkin(db_session_factory, goal["id"], two_days_ago, True)
    _seed_checkin(db_session_factory, goal["id"], three_days_ago, True)

    resp = client.get(f"/v1/goals/{goal['id']}/streak", headers=auth_headers)
    body = resp.json()
    assert body["current_streak"] == 0
    assert body["checked_in_today"] is False


def test_goal_streak_explicit_no_today_breaks_streak_immediately(client, auth_headers, db_session_factory):
    goal = _make_goal(client, auth_headers)
    _, yesterday, two_days_ago, _ = _dates_around_today()
    _seed_checkin(db_session_factory, goal["id"], two_days_ago, True)
    _seed_checkin(db_session_factory, goal["id"], yesterday, True)

    # A diferencia del plan diario, un "no" explícito de hoy SÍ corta la
    # racha de inmediato, no se comporta como "todavía no contestó".
    resp = client.post(f"/v1/goals/{goal['id']}/checkin", json={"completed": False}, headers=auth_headers)
    body = resp.json()
    assert body["current_streak"] == 0
    assert body["checked_in_today"] is True
    assert body["completed_today"] is False


def test_goal_checkin_is_idempotent_upsert_for_the_same_day(client, auth_headers, db_session_factory):
    goal = _make_goal(client, auth_headers)

    first = client.post(f"/v1/goals/{goal['id']}/checkin", json={"completed": False}, headers=auth_headers)
    second = client.post(f"/v1/goals/{goal['id']}/checkin", json={"completed": True}, headers=auth_headers)
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["completed_today"] is True
    assert second.json()["current_streak"] == 1

    db = db_session_factory()
    rows = db.query(GoalCheckin).filter(GoalCheckin.goal_id == goal["id"]).all()
    db.close()
    assert len(rows) == 1


def test_goal_streak_requires_auth(client, auth_headers):
    goal = _make_goal(client, auth_headers)
    resp = client.get(f"/v1/goals/{goal['id']}/streak")
    assert resp.status_code == 401
    resp = client.post(f"/v1/goals/{goal['id']}/checkin", json={"completed": True})
    assert resp.status_code == 401


def test_goal_streak_is_isolated_per_user(client):
    client.post("/v1/auth/register", json={"email": "u1@example.com", "password": "supersecreta1"})
    client.post("/v1/auth/register", json={"email": "u2@example.com", "password": "supersecreta1"})
    t1 = client.post("/v1/auth/login", json={"email": "u1@example.com", "password": "supersecreta1"}).json()[
        "access_token"
    ]
    t2 = client.post("/v1/auth/login", json={"email": "u2@example.com", "password": "supersecreta1"}).json()[
        "access_token"
    ]

    goal = client.post(
        "/v1/goals",
        json={"title": "Solo de u1", "horizon": "hoy"},
        headers={"Authorization": f"Bearer {t1}"},
    ).json()

    resp = client.get(f"/v1/goals/{goal['id']}/streak", headers={"Authorization": f"Bearer {t2}"})
    assert resp.status_code == 404
