def test_read_preferences_creates_defaults_on_first_access(client, auth_headers):
    resp = client.get("/v1/users/me/preferences", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["preferred_focus_hours"] == []
    assert body["rest_rules"] == {}


def test_upsert_preferences_round_trips(client, auth_headers):
    payload = {
        "preferred_focus_hours": [{"start": "09:00", "end": "11:30"}],
        "preferred_workout_hours": [{"start": "18:00", "end": "19:00"}],
        "preferred_study_hours": [],
        "rest_rules": {"min_break_between_blocks_min": 10, "protect_sleep_window": True},
        "blocked_hours_by_activity": {"entrenar": ["22:00-23:59"]},
    }
    put_resp = client.put("/v1/users/me/preferences", json=payload, headers=auth_headers)
    assert put_resp.status_code == 200

    get_resp = client.get("/v1/users/me/preferences", headers=auth_headers)
    body = get_resp.json()
    assert body["preferred_focus_hours"] == [{"start": "09:00", "end": "11:30"}]
    assert body["rest_rules"]["min_break_between_blocks_min"] == 10
    assert body["blocked_hours_by_activity"] == {"entrenar": ["22:00-23:59"]}


def test_invalid_hour_format_is_rejected(client, auth_headers):
    payload = {"preferred_focus_hours": [{"start": "9am", "end": "11:30"}]}
    resp = client.put("/v1/users/me/preferences", json=payload, headers=auth_headers)
    assert resp.status_code == 422


def test_preferences_require_auth(client):
    resp = client.get("/v1/users/me/preferences")
    assert resp.status_code == 401
