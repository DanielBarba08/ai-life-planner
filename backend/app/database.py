from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import get_settings

settings = get_settings()

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base declarativa para todos los modelos (ver sección E del blueprint)."""


def get_db():
    """Dependencia de FastAPI: una sesión de DB por request, siempre cerrada."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
