"""
Catálogo curado del Evidence Engine (sección F/E del blueprint) — la única
fuente de verdad para las filas semilla de `evidence_sources`.

Vive en código de la app, no solo dentro de la migración de Alembic, por
una razón concreta: tests/conftest.py crea la base de datos de pruebas con
`Base.metadata.create_all` (no corriendo `alembic upgrade head`), así que
si estos datos solo existieran en la migración, las pruebas nunca verían
evidencia real. La migración
(alembic/versions/04bb1ee767bd_evidence_sources_y_fk_real_en_.py) importa
esta misma lista para no duplicarla; tests/conftest.py hace lo mismo.

Cada entrada fue investigada y verificada contra Crossref (crossref.org)
antes de escribirse — no es texto generado por un modelo de lenguaje.
"""

EVIDENCE_CATALOG: list[dict] = [
    {
        "topic": "concentracion",
        "claim": (
            "Cambiar de una tarea a otra tiene un costo medible de tiempo y precisión frente a seguir "
            "en la misma tarea — el cambio no es gratuito, aunque se sienta rápido."
        ),
        "source": "Journal of Experimental Psychology: Human Perception and Performance, 27(4), 763-797",
        "authors": "Rubinstein, J. S., Meyer, D. E., & Evans, J. E.",
        "year": 2001,
        "study_type": "Estudio experimental (varios experimentos de laboratorio)",
        "doi": "10.1037/0096-1523.27.4.763",
        "evidence_level": "moderada",
        "limitations": (
            "Estudio de laboratorio con tareas cortas y controladas, no con trabajo de oficina real de larga "
            "duración; no mide directamente si agrupar tareas de concentración en un bloque continuo mejora "
            "el resultado final del día, solo que cambiar de tarea tiene un costo."
        ),
    },
    {
        "topic": "estudio",
        "claim": (
            "Distribuir el estudio de un mismo tema en varias sesiones separadas en el tiempo produce mejor "
            "recuerdo a largo plazo que concentrarlo todo en una sola sesión larga (efecto de espaciamiento)."
        ),
        "source": "Psychological Bulletin, 132(3), 354-380",
        "authors": "Cepeda, N. J., Pashler, H., Vul, E., Wixted, J. T., & Rohrer, D.",
        "year": 2006,
        "study_type": "Meta-análisis (más de 800 tamaños de efecto)",
        "doi": "10.1037/0033-2909.132.3.354",
        "evidence_level": "solida",
        "limitations": (
            "La mayoría de los estudios incluidos miden recuerdo verbal (listas de palabras, vocabulario), no "
            "necesariamente materias complejas como matemáticas o programación; no dice cuál es el espaciado "
            "óptimo para un caso particular, solo que espaciar ayuda más que no hacerlo."
        ),
    },
    {
        "topic": "entrenamiento",
        "claim": (
            "Una sesión de ejercicio produce una mejora pequeña pero medible en el rendimiento cognitivo "
            "inmediatamente después, comparado con no hacer ejercicio."
        ),
        "source": "Brain Research, 1453, 87-101",
        "authors": "Chang, Y. K., Labban, J. D., Gapin, J. I., & Etnier, J. L.",
        "year": 2012,
        "study_type": "Meta-análisis",
        "doi": "10.1016/j.brainres.2012.02.068",
        "evidence_level": "solida",
        "limitations": (
            "Los estudios incluidos varían mucho en tipo, intensidad y duración del ejercicio, lo que hace "
            "difícil afirmar cuál protocolo específico es mejor; el efecto medido es a corto plazo, no dice "
            "nada sobre acumular hábito de ejercicio a lo largo de meses."
        ),
    },
    # Las tres entradas de abajo respaldan REGLAS GENERALES del motor (nunca
    # comprimir el sueño, siempre dejar un descanso entre bloques, combinar
    # prioridad y cercanía de fecha límite al ordenar tareas) — no la
    # colocación de un bloque específico, así que no tienen una etiqueta de
    # app/planning/engine.py::_preference_label como las tres de arriba. Se
    # sirven por separado en GET /v1/evidence/general (ver
    # app/planning/evidence.py::list_general_evidence) — antes de que ese
    # endpoint existiera no había ningún lugar honesto donde mostrarlas
    # (el esquema solo modela una evidencia POR BLOQUE), así que se dejaron
    # fuera del catálogo hasta ahora aunque ya estaban investigadas.
    {
        "topic": "descanso",
        "claim": (
            "En una tarea de atención sostenida, interrumpirla brevemente y de forma esporádica para hacer "
            "otra cosa (en vez de seguir sin parar) evita que el rendimiento se vaya deteriorando con el "
            "tiempo — un respiro breve entre bloques ayuda a mantener el enfoque, no solo a descansar."
        ),
        "source": "Cognition, 118(3), 439-443",
        "authors": "Ariga, A., & Lleras, A.",
        "year": 2011,
        "study_type": "Estudio experimental (tarea de vigilancia en laboratorio)",
        "doi": "10.1016/j.cognition.2010.12.007",
        "evidence_level": "moderada",
        "limitations": (
            "La tarea del estudio es de vigilancia (detectar señales raras durante un monitoreo prolongado, "
            "tipo control de calidad o seguridad), no trabajo de oficina variado; la 'pausa' del experimento "
            "es recordar unos dígitos memorizados, no necesariamente equivalente a levantarse a caminar o "
            "revisar el teléfono — no mide directamente el descanso entre bloques de tareas distintas."
        ),
    },
    {
        "topic": "sueno",
        "claim": (
            "Incluso una sola noche de sueño reducido (24-48 horas sin dormir lo suficiente) perjudica de "
            "forma medible el rendimiento cognitivo — el efecto es más grande en atención simple y tiempos "
            "de reacción que en razonamiento complejo."
        ),
        "source": "Psychological Bulletin, 136(3), 375-389",
        "authors": "Lim, J., & Dinges, D. F.",
        "year": 2010,
        "study_type": "Meta-análisis (70 estudios, 147 pruebas cognitivas)",
        "doi": "10.1037/a0018883",
        "evidence_level": "solida",
        "limitations": (
            "La mayoría de los estudios incluidos miden privación de sueño real (24-48 horas sin dormir), no "
            "recortar una o dos horas de forma crónica noche tras noche, que es el patrón más común fuera del "
            "laboratorio; no dice cuántas horas de sueño necesita una persona en particular, solo que dormir "
            "menos de lo debido cuesta rendimiento cognitivo medible."
        ),
    },
    {
        "topic": "priorizacion",
        "claim": (
            "Cuando una tarea urgente (con fecha límite cercana) y una tarea importante compiten, la gente "
            "tiende a elegir la urgente aunque objetivamente convenga más la importante — la urgencia por sí "
            "sola tiene un atractivo psicológico que puede llevar a decisiones peores ('mere urgency effect')."
        ),
        "source": "Journal of Consumer Research, 45(3), 673-690",
        "authors": "Zhu, M., Yang, Y., & Hsee, C. K.",
        "year": 2018,
        "study_type": "Cinco experimentos de comportamiento",
        "doi": "10.1093/jcr/ucy008",
        "evidence_level": "moderada",
        "limitations": (
            "Los experimentos usan tareas y recompensas simuladas en laboratorio/encuestas online, no "
            "decisiones reales de una agenda de trabajo de varias semanas; no mide directamente si un "
            "algoritmo de planificación que combina prioridad y fecha límite (en vez de solo fecha límite) "
            "produce mejores resultados — solo documenta el sesgo humano que motiva no depender únicamente "
            "de la urgencia."
        ),
    },
]
