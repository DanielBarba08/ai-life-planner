from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.assistant import service
from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.assistant import AssistantMessageRequest, AssistantMessageResponse

router = APIRouter(prefix="/v1/assistant", tags=["assistant"])


@router.post("/message", response_model=AssistantMessageResponse)
def send_message(
    payload: AssistantMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Asistente conversacional (sección 16 del brief). Ver
    app/assistant/parser.py para la lista de frases que reconoce hoy y por
    qué el intérprete es basado en reglas en este módulo, no en un LLM.
    """
    result = service.handle_message(db, current_user, payload.message)
    return AssistantMessageResponse(**result)
