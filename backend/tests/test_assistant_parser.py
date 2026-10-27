"""
Cubre exactamente los siete ejemplos de la sección 16 del brief, más los
casos límite donde el intérprete debe pedir aclaración en vez de adivinar.

Prueba `parse_rule_based` directamente (no `parse`) a propósito: este es
el motor determinista de respaldo (ver docstring de parser.py) y tiene
que seguir dando exactamente estos resultados sin red ni variabilidad de
modelo, sea que haya una ANTHROPIC_API_KEY configurada o no. El intérprete
con Claude real (`app/assistant/llm_client.py`) se prueba aparte en
tests/test_assistant_llm_parser.py, con el cliente de Anthropic mockeado
— y además queda deshabilitado por defecto en toda la suite (ver
`_disable_llm_assistant` en conftest.py) para que correr `pytest` nunca
haga llamadas reales ni gaste crédito de la API.
"""
from datetime import date

from app.assistant.parser import parse_rule_based as parse

TODAY = date(2026, 9, 14)


def test_organiza_mi_tarde():
    intent = parse("Organiza mi tarde.", TODAY)
    assert intent.action == "replan_day"
    assert intent.target_date == TODAY


def test_reorganiza_mi_dia_cansado_detecta_fatiga():
    intent = parse("Estoy muy cansado, reorganiza mi día", TODAY)
    assert intent.action == "replan_day"
    assert intent.note == "fatiga"


def test_quiero_entrenar_tres_veces_esta_semana_crea_objetivo():
    intent = parse("Quiero entrenar tres veces esta semana", TODAY)
    assert intent.action == "create_goal"
    assert intent.goal_horizon == "semana"
    assert "entrenar" in intent.goal_title.lower()


def test_no_termine_las_tareas_de_ayer():
    intent = parse("No terminé las tareas de ayer.", TODAY)
    assert intent.action == "replan_day"
    assert intent.note == "tareas_previas_incompletas"


def test_que_deberia_hacer_ahora():
    intent = parse("¿Qué debería hacer ahora?", TODAY)
    assert intent.action == "whats_next"


def test_tengo_que_terminar_proyecto_manana_pide_aclaracion():
    """No debe adivinar cuál tarea — sección 4 del brief: la IA recomienda, no impone."""
    intent = parse("Tengo que terminar este proyecto mañana.", TODAY)
    assert intent.action == "clarify"


def test_optimiza_mi_dia():
    intent = parse("Optimiza mi día", TODAY)
    assert intent.action == "optimize_day"
    assert intent.target_date == TODAY


def test_mensaje_no_reconocido_no_inventa_accion():
    intent = parse("¿Cuál es la capital de Australia?", TODAY)
    assert intent.action == "unrecognized"


def test_goal_horizon_defaults_to_largo_plazo_sin_marco_temporal():
    intent = parse("Quiero aprender a tocar guitarra", TODAY)
    assert intent.action == "create_goal"
    assert intent.goal_horizon == "largo_plazo"


def test_parser_is_accent_insensitive():
    with_accent = parse("Organiza mi día", TODAY)
    without_accent = parse("organiza mi dia", TODAY)
    assert with_accent.action == without_accent.action == "replan_day"


def test_importa_mi_horario():
    intent = parse("Importa mi horario: trabajo de 9 a 6 lunes a viernes", TODAY)
    assert intent.action == "import_schedule"


def test_agrega_mi_horario_tambien_dispara_import_schedule():
    intent = parse("Agrega mi horario completo por favor", TODAY)
    assert intent.action == "import_schedule"


def test_importar_horario_gana_sobre_reorganiza_si_ambas_palabras_aparecen():
    """Un mensaje como 'importa mi horario y reorganiza mi semana' debe
    leerse como importación, no como un ajuste sobre lo ya cargado — ver
    el comentario en parser.py sobre el orden de estas dos reglas."""
    intent = parse("Importa mi horario y reorganiza mi semana con eso", TODAY)
    assert intent.action == "import_schedule"


def test_horario_pegado_sin_decir_la_palabra_horario_dispara_import_schedule():
    """Reporte real: un usuario pidió 'ayúdame a planificar mis semanas'
    y pegó su horario completo (escuela lunes a sábado con horas, gimnasio
    ciertos días) sin decir la palabra "horario" ni usar un verbo como
    importa/agrega — el motor de reglas debe reconocer esto igual que un
    mensaje explícito, por la heurística de _looks_like_schedule_dump."""
    intent = parse(
        "Hola me podrias ayudar a planificar mis semanas? "
        "Lunes: Escuela de 9:30 am - 2:35 pm "
        "Martes: Escuela de 7:00 am - 2:00 pm "
        "Miércoles: Escuela de 9:35 am - 3:00 pm "
        "Voy al gym los días lunes, martes y miércoles",
        TODAY,
    )
    assert intent.action == "import_schedule"


def test_dos_dias_sin_hora_no_dispara_import_schedule():
    """La heurística exige día+hora concretos — mencionar dos días de la
    semana sin ninguna hora no debe secuestrar mensajes normales de
    reorganización, como 'reorganiza mi lunes y martes que tengo mucho
    trabajo'."""
    intent = parse("Reorganiza mi lunes y martes que tengo mucho trabajo", TODAY)
    assert intent.action != "import_schedule"
