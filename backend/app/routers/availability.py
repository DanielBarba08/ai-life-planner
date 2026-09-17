from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.availability import AvailabilityBlock
from app.models.user import User
from app.schemas.availability import AvailabilityBlockCreate, AvailabilityBlockRead

router = APIRouter(prefix="/v1/availability", tags=["availability"])


@router.get("", response_model=list[AvailabilityBlockRead])
def list_availability(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(AvailabilityBlock)
        .filter(AvailabilityBlock.user_id == current_user.id)
        .order_by(AvailabilityBlock.day_of_week, AvailabilityBlock.start)
        .all()
    )


@router.post("", response_model=AvailabilityBlockRead, status_code=status.HTTP_201_CREATED)
def create_availability(
    payload: AvailabilityBlockCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.start >= payload.end:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="La hora de inicio debe ser anterior a la hora de fin",
        )
    block = AvailabilityBlock(user_id=current_user.id, **payload.model_dump())
    db.add(block)
    db.commit()
    db.refresh(block)
    return block


@router.delete("/{block_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_availability(
    block_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    block = (
        db.query(AvailabilityBlock)
        .filter(AvailabilityBlock.id == block_id, AvailabilityBlock.user_id == current_user.id)
        .first()
    )
    # 404 tanto si no existe como si pertenece a otro usuario — nunca
    # revelamos que un ID de otro usuario "existe" (aislamiento por
    # usuario, sección J del blueprint).
    if block is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Bloque de disponibilidad no encontrado")
    db.delete(block)
    db.commit()
    return None
