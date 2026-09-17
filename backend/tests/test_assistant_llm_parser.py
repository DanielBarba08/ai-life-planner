"""
Prueba el intérprete de intención con Claude real (app/assistant/llm_client.py).

Dos capas, a propósito:

1. Pruebas con el cliente de Anthropic MOCKEADO (la mayoría de este
   archivo) — deterministas, rápidas, sin red ni costo, cubren: que el
   contrato Intent se arma bien a partir de la respuesta de la
   herramienta, que target_date se calcula del lado del servidor (nunca
   confiamos en que el modelo haga aritmética de fechas), que sin
   ANTHROPIC_API_KEY se cae directo a LLMUnavailable, y que cualquier
   excepción de la API (o una respuesta sin tool_use) también cae a
   LLMUnavailable en vez de propagar — así `parser.parse()` puede
   recuperarse siempre.

2. Un smoke test contra la API REAL de Anthropic (al final del archivo),
   protegido detrás de la env var RUN_LIVE_LLM_TESTS=1 — no corre en la
   suite normal (ni siquiera necesita el fixture `_disable_llm_assistant`
   de conftest.py, porque llama a `classify_intent` directamente, no a
   través de `parser.parse()`). Es la verificación "contra la API de
   verdad, al menos una vez" que sigue la misma disciplina del resto del
   proyecto (secciones 11/27 del brief) — se corre a mano cuando se
   cambia el prompt/tool schema, no en cada `pytest`.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date
from typing import Any

import pytest

from app.assistant import llm_client
from app.config import get_settings

TODAY = date(2026, 9, 15)


@pytest.fixture(autouse=True)
def _disable_llm_assistant():
    """Anula, solo en este módulo, el fixture autouse del mismo nombre en
    conftest.py que desactiva `llm_client.classify_intent` para el resto
    de la suite — aquí es precisamente lo que estamos probando, así que
    no debe quedar parcheado a un stub que siempre truena."""
    yield


@dataclass
class _FakeToolUseBlock:
    type: str
    input: dict[str, Any]


@dataclass
class _FakeMessage:
    content: list[Any]


class _FakeMessagesResource:
    def __init__(self, next_input: dict[str, Any] | None, raise_error: Exception | None = None):
        self._next_input = next_input
        self._raise_error = raise_error
        self.last_call_kwargs: dict[str, Any] | None = None

    def create(self, **kwargs):
        self.last_call_kwargs = kwargs
        if self._raise_error:
            raise self._raise_error
        content = [_FakeToolUseBlock(type="tool_use", input=self._next_input)] if self._next_input is not None else []
        return _FakeMessage(content=content)


class _FakeAnthropicClient:
    def __init__(self, next_input: dict[str, Any] | None = None, raise_error: Exception | None = None):
        self.messages = _FakeMessagesResource(next_input, raise_error)


@pytest.fixture(autouse=True)
def _fake_key(monkeypatch):
    """Estas pruebas nunca deben depender de si hay una key real en el
    entorno — cada una controla explícitamente si `settings.anthropic_api_key`
    existe o no."""
    get_settings.cache_clear()
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-fake-key")
    yield
    get_settings.cache_clear()


def test_sin_api_key_cae_a_llmunavailable(monkeypatch):
    # OJO: no basta con delenv — pydantic-settings sigue leyendo el .env
    # real del proyecto (que si tiene una key de verdad) como fuente de
    # respaldo cuando la variable de entorno está ausente. Hay que
    # sobreescribirla explícitamente con un valor vacío para que gane
    # sobre el archivo (las variables de entorno tienen prioridad sobre
    # el .env en el orden de fuentes de pydantic-settings).
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    get_settings.cache_clear()
    with pytest.raises(llm_client.LLMUnavailable):
        llm_client.classify_intent("optimiza mi día", TODAY)


def test_clasifica_whats_next(monkeypatch):
    fake = _FakeAnthropicClient(next_input={"action": "whats_next"})
    monkeypatch.setattr(llm_client.anthropic, "Anthropic", lambda api_key: fake)

    intent = llm_client.classify_intent("¿qué hago ahora?", TODAY)

    assert intent.action == "whats_next"
    assert intent.target_date is None
    assert intent.goal_title is None
    assert intent.note is None


def test_optimize_day_siempre_usa_la_fecha_del_servidor_nunca_la_del_modelo(monkeypatch):
    # el modelo NO manda target_date en el input — el contrato de la
    # herramienta ni siquiera expone ese campo — así que esto prueba que
    # el backend lo calcula, no que lo "pasa a través".
    fake = _FakeAnthropicClient(next_input={"action": "optimize_day"})
    monkeypatch.setattr(llm_client.anthropic, "Anthropic", lambda api_key: fake)

    intent = llm_client.classify_intent("arma mi agenda de hoy", TODAY)

    assert intent.action == "optimize_day"
    assert intent.target_date == TODAY


def test_replan_day_con_nota_de_fatiga(monkeypatch):
    fake = _FakeAnthropicClient(next_input={"action": "replan_day", "note": "fatiga"})
    monkeypatch.setattr(llm_client.anthropic, "Anthropic", lambda api_key: fake)

    intent = llm_client.classify_intent("ya no puedo más hoy, estoy exhausto, ajusta lo que sigue", TODAY)

    assert intent.action == "replan_day"
    assert intent.target_date == TODAY
    assert intent.note == "fatiga"


def test_create_goal_con_titulo_y_horizonte(monkeypatch):
    fake = _FakeAnthropicClient(
        next_input={"action": "create_goal", "goal_title": "Meditar todos los días", "goal_horizon": "largo_plazo"}
    )
    monkeypatch.setattr(llm_client.anthropic, "Anthropic", lambda api_key: fake)

    intent = llm_client.classify_intent("quiero meditar todos los días", TODAY)

    assert intent.action == "create_goal"
    assert intent.goal_title == "Meditar todos los días"
    assert intent.goal_horizon == "largo_plazo"
    assert intent.target_date is None


def test_note_se_ignora_fuera_de_replan_day(monkeypatch):
    # si el modelo manda un campo fuera de lo que aplica a la acción (no
    # debería, por el prompt, pero no confiamos ciegamente), lo
    # descartamos en vez de propagarlo a un Intent que no lo espera.
    fake = _FakeAnthropicClient(next_input={"action": "whats_next", "note": "fatiga", "goal_title": "algo"})
    monkeypatch.setattr(llm_client.anthropic, "Anthropic", lambda api_key: fake)

    intent = llm_client.classify_intent("¿qué hago ahora?", TODAY)

    assert intent.action == "whats_next"
    assert intent.note is None
    assert intent.goal_title is None


def test_accion_fuera_del_contrato_cae_a_llmunavailable(monkeypatch):
    fake = _FakeAnthropicClient(next_input={"action": "borrar_todo"})
    monkeypatch.setattr(llm_client.anthropic, "Anthropic", lambda api_key: fake)

    with pytest.raises(llm_client.LLMUnavailable):
        llm_client.classify_intent("mensaje cualquiera", TODAY)


def test_respuesta_sin_tool_use_cae_a_llmunavailable(monkeypatch):
    fake = _FakeAnthropicClient(next_input=None)
    monkeypatch.setattr(llm_client.anthropic, "Anthropic", lambda api_key: fake)

    with pytest.raises(llm_client.LLMUnavailable):
        llm_client.classify_intent("mensaje cualquiera", TODAY)


def test_error_de_api_cae_a_llmunavailable(monkeypatch):
    import anthropic as anthropic_module

    api_error = anthropic_module.APIError("fallo simulado", request=None, body=None)
    fake = _FakeAnthropicClient(raise_error=api_error)
    monkeypatch.setattr(llm_client.anthropic, "Anthropic", lambda api_key: fake)

    with pytest.raises(llm_client.LLMUnavailable):
        llm_client.classify_intent("mensaje cualquiera", TODAY)


def test_parser_parse_cae_al_motor_de_reglas_si_el_llm_falla(monkeypatch):
    """Confirma el flujo completo de fallback descrito en parser.py: si
    classify_intent truena, parse() no propaga el error — regresa lo mismo
    que el motor de reglas para el mismo mensaje."""
    from app.assistant import parser

    monkeypatch.setattr(llm_client, "classify_intent", lambda text, today: (_ for _ in ()).throw(llm_client.LLMUnavailable("x")))

    intent = parser.parse("Organiza mi tarde.", TODAY)

    assert intent.action == "replan_day"
    assert intent.target_date == TODAY


# ---------------------------------------------------------------------------
# Smoke test contra la API real — solo corre con RUN_LIVE_LLM_TESTS=1.
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    os.environ.get("RUN_LIVE_LLM_TESTS") != "1",
    reason="Smoke test contra la API real de Anthropic — correr a mano con RUN_LIVE_LLM_TESTS=1",
)
def test_llm_real_clasifica_los_siete_ejemplos_del_brief(monkeypatch):
    # el fixture autouse `_fake_key` de este módulo sobreescribe
    # ANTHROPIC_API_KEY con una key falsa para el resto de las pruebas —
    # aquí sí queremos la key real del .env del proyecto, así que quitamos
    # el override de entorno para que pydantic-settings vuelva a leerla
    # del archivo.
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    get_settings.cache_clear()
    real_today = date(2026, 9, 15)
    cases = [
        ("¿qué hago ahora?", "whats_next"),
        ("optimiza mi día", "optimize_day"),
        ("reorganiza mi tarde", "replan_day"),
        ("no terminé las tareas de ayer", "replan_day"),
        ("quiero entrenar tres veces esta semana", "create_goal"),
        ("tengo que terminar este proyecto mañana", "clarify"),
        ("cuéntame un chiste", "unrecognized"),
    ]
    for text, expected_action in cases:
        intent = llm_client.classify_intent(text, real_today)
        assert intent.action == expected_action, f"{text!r} -> {intent.action}, esperaba {expected_action}"
    get_settings.cache_clear()
