import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.assistant import llm_client
from app.database import Base, get_db
from app.main import app
from app.models.evidence import EvidenceLevel, EvidenceSource
from app.planning.evidence_catalog import EVIDENCE_CATALOG


@pytest.fixture(autouse=True)
def _disable_llm_assistant(monkeypatch):
    """
    La suite normal (pytest sin flags) nunca debe llamar a la API real de
    Anthropic: sería lenta, le costaría crédito de verdad a Daniel en cada
    corrida, y volvería la suite no-determinista. Forzamos que
    `llm_client.classify_intent` siempre "no esté disponible" — así
    `app.assistant.parser.parse()` cae siempre al motor de reglas
    determinista, exactamente el comportamiento que ya prueba
    test_assistant_parser.py/test_assistant_api.py. El intérprete real con
    Claude se prueba aparte en test_assistant_llm_parser.py (con el
    cliente de Anthropic mockeado, más un smoke test real opcional detrás
    de la env var RUN_LIVE_LLM_TESTS), donde este fixture se deshabilita
    explícitamente.
    """

    def _unavailable(text, today):
        raise llm_client.LLMUnavailable("deshabilitado en la suite de tests por defecto")

    monkeypatch.setattr(llm_client, "classify_intent", _unavailable)


@pytest.fixture()
def db_session_factory(tmp_path):
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # tests corren contra create_all, no contra `alembic upgrade head`, así
    # que el catálogo semilla del Evidence Engine (que en un entorno real
    # llega por la migración) se siembra aquí a mano, desde la misma lista
    # que usa la migración — ver app/planning/evidence_catalog.py.
    seed_session = TestingSessionLocal()
    for row in EVIDENCE_CATALOG:
        seed_session.add(EvidenceSource(**{**row, "evidence_level": EvidenceLevel(row["evidence_level"])}))
    seed_session.commit()
    seed_session.close()

    yield TestingSessionLocal
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session_factory):
    def override_get_db():
        db = db_session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def registered_user_tokens(client):
    """Registra un usuario y devuelve sus tokens + email, listos para usar."""
    payload = {"email": "daniel@example.com", "password": "correcthorse123", "name": "Daniel"}
    resp = client.post("/v1/auth/register", json=payload)
    assert resp.status_code == 201, resp.text

    login = client.post("/v1/auth/login", json={"email": payload["email"], "password": payload["password"]})
    assert login.status_code == 200, login.text
    tokens = login.json()
    return {"email": payload["email"], **tokens}


@pytest.fixture()
def auth_headers(registered_user_tokens):
    return {"Authorization": f"Bearer {registered_user_tokens['access_token']}"}
