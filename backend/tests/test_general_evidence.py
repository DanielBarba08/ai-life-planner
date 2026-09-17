"""
GET /v1/explanations/general — evidencia científica real detrás de reglas
GENERALES del motor (descanso, sueño, priorización), separada del panel
"¿Por qué?" de cada bloque porque estas citas no respaldan un bloque en
particular (ver app/planning/evidence.py::list_general_evidence).
"""


def test_general_evidence_has_the_three_topics_with_real_citations(client, auth_headers):
    resp = client.get("/v1/explanations/general", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    topics = {row["topic"] for row in body}
    assert topics == {"descanso", "sueno", "priorizacion"}

    by_topic = {row["topic"]: row for row in body}
    descanso = by_topic["descanso"]
    assert descanso["evidence"]["doi"] == "10.1016/j.cognition.2010.12.007"
    assert descanso["evidence"]["authors"] == "Ariga, A., & Lleras, A."
    assert "colchón de descanso" in descanso["system_rule"]

    sueno = by_topic["sueno"]
    assert sueno["evidence"]["doi"] == "10.1037/a0018883"

    priorizacion = by_topic["priorizacion"]
    assert priorizacion["evidence"]["doi"] == "10.1093/jcr/ucy008"


def test_general_evidence_never_leaves_evidence_null(client, auth_headers):
    resp = client.get("/v1/explanations/general", headers=auth_headers)
    body = resp.json()
    assert len(body) > 0
    for row in body:
        assert row["evidence"] is not None
        assert row["evidence"]["claim"]
        assert row["evidence"]["limitations"]


def test_general_evidence_requires_auth(client):
    resp = client.get("/v1/explanations/general")
    assert resp.status_code == 401
