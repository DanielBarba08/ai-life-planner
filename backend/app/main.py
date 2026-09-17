from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import (
    assistant,
    auth,
    availability,
    events,
    explanations,
    goals,
    habits,
    planning,
    preferences,
    tasks,
    users,
)

# A partir del Módulo 2, el esquema de base de datos se gestiona con
# Alembic (ver alembic/), no con Base.metadata.create_all en el arranque:
# corre `alembic upgrade head` antes de levantar la app (ver README).

app = FastAPI(
    title="AI Life Planner API",
    description=(
        "Backend del AI Life Planner — Módulo 1 (auth, perfil, disponibilidad) "
        "+ Módulo 2 (eventos, tareas, objetivos) + Módulo 3 (Planning Engine) "
        "+ Módulo 4 (asistente conversacional) + Evidence Engine (citas "
        "científicas reales y verificadas en el panel '¿Por qué?') + Personal "
        "Productivity Model (confianza que aprende del historial real de "
        "finalización) + Fase 5 (hábitos avanzados, con confirmación "
        "explícita del usuario antes de crear cualquier sesión)."
    ),
    version="0.6.0",
)

_settings = get_settings()
_origins = [o.strip() for o in _settings.cors_allowed_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=_origins != ["*"],  # allow_credentials=True es incompatible con origin "*"
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(preferences.router)
app.include_router(availability.router)
app.include_router(events.router)
app.include_router(tasks.router)
app.include_router(goals.router)
app.include_router(habits.router)
app.include_router(planning.router)
app.include_router(explanations.router)
app.include_router(assistant.router)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}
