from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.event import FixedEvent
from app.models.user import User
from app.schemas.event import EventCreate, EventRead, EventUpdate

router = APIRouter(prefix="/v1/events", tags=["events"])


def _get_owned_event(db: Session, event_id: str, user_id: str) -> FixedEvent:
    event = (
        db.query(FixedEvent)
        .filter(FixedEvent.id == event_id, FixedEvent.user_id == user_id)
        .first()
    )
    if event is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Evento no encontrado")
    return event


@router.get("", response_model=list[EventRead])
def list_events(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(FixedEvent)
        .filter(FixedEvent.user_id == current_user.id)
        .order_by(FixedEvent.start)
        .all()
    )


@router.post("", response_model=EventRead, status_code=status.HTTP_201_CREATED)
def create_event(
    payload: EventCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = FixedEvent(user_id=current_user.id, **payload.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.get("/{event_id}", response_model=EventRead)
def read_event(
    event_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _get_owned_event(db, event_id, current_user.id)


@router.patch("/{event_id}", response_model=EventRead)
def update_event(
    event_id: str,
    payload: EventUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = _get_owned_event(db, event_id, current_user.id)
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(event, field, value)

    if event.end <= event.start:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="La hora de fin debe ser posterior a la hora de inicio",
        )

    db.commit()
    db.refresh(event)
    return event


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(
    event_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = _get_owned_event(db, event_id, current_user.id)
    db.delete(event)
    db.commit()
    return None
