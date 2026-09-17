"""
Hashing de contraseñas y JWT.

Sigue la sección J (security/privacy architecture) del blueprint:
- Contraseñas nunca se guardan en texto plano (bcrypt vía passlib).
- Access token de vida corta + refresh token de vida más larga (rotación
  completa de tokens firmados en DB queda fuera del MVP; ver README).
"""
from datetime import datetime, timedelta, timezone
from typing import Literal

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

TokenType = Literal["access", "refresh"]


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def _create_token(subject: str, token_type: TokenType, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: str) -> str:
    return _create_token(
        user_id, "access", timedelta(minutes=settings.access_token_expire_minutes)
    )


def create_refresh_token(user_id: str) -> str:
    return _create_token(
        user_id, "refresh", timedelta(days=settings.refresh_token_expire_days)
    )


class InvalidTokenError(Exception):
    pass


def decode_token(token: str, expected_type: TokenType) -> str:
    """Devuelve el user_id (sub) si el token es válido y del tipo esperado."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise InvalidTokenError("Token inválido o expirado") from exc

    if payload.get("type") != expected_type:
        raise InvalidTokenError(f"Se esperaba un token de tipo '{expected_type}'")

    user_id = payload.get("sub")
    if not user_id:
        raise InvalidTokenError("Token sin sujeto")
    return user_id
