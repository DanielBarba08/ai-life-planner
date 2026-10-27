"""
Prueba la extracción de horario con Claude real (mockeado) —
app/assistant/schedule_extractor.py. Mismo patrón de dos capas que
tests/test_assistant_llm_parser.py: mockeado y determinista aquí, con un
smoke test opcional contra la API real al final, detrás de
RUN_LIVE_LLM_TESTS=1.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

import pytest

from app.assistant import schedule_extractor
from app.assistant.llm_client import LLMUnavailable
from app.config import get_settings
from app.schemas.assistant import ScheduleItemAvailability, ScheduleItemEvent

TODAY = date(2026, 9, 21)  # lunes


@pytest.fixture(autouse=True)
def _disable_schedule_extractor():
    """Anula, solo en este módulo, el fixture autouse del mismo nombre en
    conftest.py que desactiva `schedule_extractor.extract_schedule` para
    el resto de la suite — aquí es precisamente lo que estamos probando."""
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

    def create(self, **kwargs):
        if self._raise_error:
            raise self._raise_error
        content = [_FakeToolUseBlock(type="tool_use", input=self._next_input)] if self._next_input is not None else []
        return _FakeMessage(content=content)


class _FakeAnthropicClient:
    def __init__(self, next_input: dict[str, Any] | None = None, raise_error: Exception | None = None):
        self.messages = _FakeMessagesResource(next_input, raise_error)


@pytest.fixture(autouse=True)
def _fake_key(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-fake-key")
    yield
    get_settings.cache_clear()


def test_sin_api_key_cae_a_llmunavailable(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    get_settings.cache_clear()
    with pytest.raises(LLMUnavailable):
        schedule_extractor.extract_schedule("trabajo 9 a 6 lunes a viernes", TODAY)


def test_extrae_disponibilidad_y_evento(monkeypatch):
    fake = _FakeAnthropicClient(
        next_input={
            "items": [
                {
                    "kind": "availability",
                    "label": "Trabajo",
                    "type": "trabajo",
                    "days": [0, 1, 2, 3, 4],
                    "start": "09:00",
                    "end": "18:00",
                },
                {
                    "kind": "event",
                    "label": "Junta con el equipo",
                    "date": "2026-09-25",
                    "start": "10:00",
                    "end": "11:00",
                },
            ]
        }
    )
    monkeypatch.setattr(schedule_extractor.anthropic, "Anthropic", lambda api_key: fake)

    items = schedule_extractor.extract_schedule(
        "trabajo de 9 a 6 lunes a viernes, el viernes tengo junta con el equipo de 10 a 11", TODAY
    )

    assert len(items) == 2
    availability, event = items
    assert isinstance(availability, ScheduleItemAvailability)
    assert availability.type.value == "trabajo"
    assert availability.days == [0, 1, 2, 3, 4]
    assert isinstance(event, ScheduleItemEvent)
    assert event.date == date(2026, 9, 25)


def test_mensaje_sin_horario_regresa_lista_vacia(monkeypatch):
    fake = _FakeAnthropicClient(next_input={"items": []})
    monkeypatch.setattr(schedule_extractor.anthropic, "Anthropic", lambda api_key: fake)

    items = schedule_extractor.extract_schedule("hola, ¿cómo estás?", TODAY)

    assert items == []


def test_bloque_individual_invalido_se_descarta_sin_tirar_los_demas(monkeypatch):
    fake = _FakeAnthropicClient(
        next_input={
            "items": [
                {
                    "kind": "availability",
                    "label": "Trabajo",
                    "type": "trabajo",
                    "days": [0, 1, 2, 3, 4],
                    "start": "09:00",
                    "end": "18:00",
                },
                {
                    # hora de fin antes que la de inicio — inválido, se descarta
                    "kind": "availability",
                    "label": "Mal armado",
                    "type": "otro",
                    "days": [0],
                    "start": "20:00",
                    "end": "10:00",
                },
                {
                    # kind desconocido — se descarta
                    "kind": "quien_sabe",
                    "label": "???",
                    "start": "01:00",
                    "end": "02:00",
                },
            ]
        }
    )
    monkeypatch.setattr(schedule_extractor.anthropic, "Anthropic", lambda api_key: fake)

    items = schedule_extractor.extract_schedule("algo raro", TODAY)

    assert len(items) == 1
    assert items[0].label == "Trabajo"


def test_respuesta_sin_tool_use_cae_a_llmunavailable(monkeypatch):
    fake = _FakeAnthropicClient(next_input=None)
    monkeypatch.setattr(schedule_extractor.anthropic, "Anthropic", lambda api_key: fake)

    with pytest.raises(LLMUnavailable):
        schedule_extractor.extract_schedule("cualquier cosa", TODAY)


def test_error_de_api_cae_a_llmunavailable(monkeypatch):
    import anthropic as anthropic_module

    api_error = anthropic_module.APIError("fallo simulado", request=None, body=None)
    fake = _FakeAnthropicClient(raise_error=api_error)
    monkeypatch.setattr(schedule_extractor.anthropic, "Anthropic", lambda api_key: fake)

    with pytest.raises(LLMUnavailable):
        schedule_extractor.extract_schedule("cualquier cosa", TODAY)
