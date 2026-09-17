from datetime import datetime, time

from pydantic import BaseModel, ConfigDict


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    name: str | None
    timezone: str
    wake_time: time | None
    sleep_time: time | None
    onboarding_completed: bool
    created_at: datetime


class UserUpdate(BaseModel):
    name: str | None = None
    timezone: str | None = None
    wake_time: time | None = None
    sleep_time: time | None = None
    # Encontrado al construir el onboarding del frontend (Módulo 5): sin
    # este campo no había NINGUNA forma de marcar el onboarding como
    # terminado — quedaba en `false` para siempre. Se agrega aquí, no como
    # su propio endpoint, porque es exactamente el mismo patrón que el
    # resto de PATCH /v1/users/me (exclude_unset, un campo más del perfil).
    onboarding_completed: bool | None = None
