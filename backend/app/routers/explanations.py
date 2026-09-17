from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.day_plan import DayPlan, PlanBlock, RecommendationExplanation
from app.models.user import User
from app.planning.evidence import list_general_evidence
from app.schemas.explanation import EvidenceRead, ExplanationRead, GeneralEvidenceRead

router = APIRouter(prefix="/v1/explanations", tags=["explanations"])


@router.get("/general", response_model=list[GeneralEvidenceRead])
def read_general_evidence(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    "Cómo decide tus horarios" — evidencia científica real detrás de reglas
    GENERALES del motor (nunca comprimir el sueño, siempre dejar un
    descanso entre bloques, combinar prioridad y cercanía de fecha límite),
    no de un bloque en particular. Requiere sesión como el resto de la API
    aunque el contenido sea el mismo para todos los usuarios — no hay
    ninguna razón para tener un camino sin autenticación distinto.
    """
    rows = list_general_evidence(db)
    return [
        GeneralEvidenceRead(
            topic=r["topic"],
            system_rule=r["system_rule"],
            evidence=EvidenceRead(
                claim=r["evidence"].claim,
                source=r["evidence"].source,
                authors=r["evidence"].authors,
                year=r["evidence"].year,
                study_type=r["evidence"].study_type,
                doi=r["evidence"].doi,
                evidence_level=r["evidence"].evidence_level,
                limitations=r["evidence"].limitations,
            ),
        )
        for r in rows
    ]


@router.get("/{block_id}", response_model=ExplanationRead)
def read_explanation(
    block_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Panel '¿Por qué?' (sección 12 del brief). Solo devuelve explicaciones
    de bloques del propio usuario — se hace join con day_plans para
    verificar propiedad sin necesitar un user_id desnormalizado en
    plan_blocks.
    """
    block = (
        db.query(PlanBlock)
        .join(DayPlan, PlanBlock.day_plan_id == DayPlan.id)
        .filter(PlanBlock.id == block_id, DayPlan.user_id == current_user.id)
        .first()
    )
    if block is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Bloque no encontrado")

    explanation = (
        db.query(RecommendationExplanation).filter(RecommendationExplanation.plan_block_id == block.id).first()
    )
    if explanation is None:
        # Los eventos fijos no llevan explicación generada — el usuario los
        # puso ahí él mismo, no hay nada que "explicar" (sección 12: solo
        # las recomendaciones del sistema llevan este panel).
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="Este bloque no tiene una explicación asociada (por ejemplo, es un evento que agregaste tú)",
        )

    evidence = None
    if explanation.evidence is not None:
        e = explanation.evidence
        evidence = EvidenceRead(
            claim=e.claim,
            source=e.source,
            authors=e.authors,
            year=e.year,
            study_type=e.study_type,
            doi=e.doi,
            evidence_level=e.evidence_level,
            limitations=e.limitations,
        )

    return ExplanationRead(
        block_id=block.id,
        block_title=block.title,
        block_start=block.start,
        block_end=block.end,
        user_data=explanation.user_data_snippet,
        system_rule=explanation.system_rule_snippet,
        evidence=evidence,
        ai_inference=explanation.ai_inference_snippet,
        confidence=explanation.confidence,
    )
