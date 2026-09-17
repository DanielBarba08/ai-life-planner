"""
Racha de días consecutivos (GET /v1/planning/streak) — sección de diseño:
elemento de enganche diario pedido por Daniel para el encabezado de "Mi
día". Calculada de verdad a partir de `day_plans.date`, así que estos
tests usan la zona horaria real del usuario de prueba (default:
America/Mexico_City, ver app/models/user.py) en vez de una fecha fija,
para no depender de qué día calendario es "hoy" cuando corre la suite.
"""
from datetime import timedelta
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Mexico_City")


def _local_today(now_utc):
    return now_utc.astimezone(TZ).date()


def _dates_around_today():
    from datetime import datetime, timezone

    today = datetime.now(timezone.utc).astimezone(TZ).date()
    return today, today - timedelta(days=1), today - timedelta(days=2), today - timedelta(days=3)


def test_streak_is_zero_with_no_plans_at_all(client, auth_headers):
    resp = client.get("/v1/planning/streak", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["current_streak"] == 0
    assert body["has_plan_today"] is False


def test_streak_counts_consecutive_days_ending_yesterday_without_penalizing_missing_today(client, auth_headers):
    today, yesterday, two_days_ago, _ = _dates_around_today()

    client.post("/v1/planning/optimize", json={"date": str(yesterday)}, headers=auth_headers)
    client.post("/v1/planning/optimize", json={"date": str(two_days_ago)}, headers=auth_headers)

    resp = client.get("/v1/planning/streak", headers=auth_headers)
    body = resp.json()
    assert body["current_streak"] == 2
    assert body["has_plan_today"] is False


def test_streak_includes_today_once_optimized_and_grows(client, auth_headers):
    today, yesterday, two_days_ago, _ = _dates_around_today()

    client.post("/v1/planning/optimize", json={"date": str(two_days_ago)}, headers=auth_headers)
    client.post("/v1/planning/optimize", json={"date": str(yesterday)}, headers=auth_headers)
    client.post("/v1/planning/optimize", json={"date": str(today)}, headers=auth_headers)

    resp = client.get("/v1/planning/streak", headers=auth_headers)
    body = resp.json()
    assert body["current_streak"] == 3
    assert body["has_plan_today"] is True


def test_streak_breaks_on_a_gap(client, auth_headers):
    today, yesterday, two_days_ago, three_days_ago = _dates_around_today()

    # Falta 'yesterday' — la racha no debe saltarse el hueco.
    client.post("/v1/planning/optimize", json={"date": str(two_days_ago)}, headers=auth_headers)
    client.post("/v1/planning/optimize", json={"date": str(three_days_ago)}, headers=auth_headers)

    resp = client.get("/v1/planning/streak", headers=auth_headers)
    body = resp.json()
    assert body["current_streak"] == 0
    assert body["has_plan_today"] is False


def test_streak_requires_auth(client):
    resp = client.get("/v1/planning/streak")
    assert resp.status_code == 401
