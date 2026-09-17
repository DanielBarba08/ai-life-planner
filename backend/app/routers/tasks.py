from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.task import Task, TaskStatus
from app.models.user import User
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate

router = APIRouter(prefix="/v1/tasks", tags=["tasks"])


def _get_owned_task(db: Session, task_id: str, user_id: str) -> Task:
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()
    if task is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Tarea no encontrada")
    return task


def _validate_dependency(db: Session, depends_on_id: str | None, user_id: str, self_id: str | None):
    if depends_on_id is None:
        return
    if depends_on_id == self_id:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Una tarea no puede depender de sí misma"
        )
    dependency = (
        db.query(Task).filter(Task.id == depends_on_id, Task.user_id == user_id).first()
    )
    if dependency is None:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="depends_on_id debe ser una tarea existente del mismo usuario",
        )


@router.get("", response_model=list[TaskRead])
def list_tasks(
    status_filter: TaskStatus | None = Query(default=None, alias="status"),
    category: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Task).filter(Task.user_id == current_user.id)
    if status_filter is not None:
        query = query.filter(Task.status == status_filter)
    if category is not None:
        query = query.filter(Task.category == category)
    return query.order_by(Task.deadline.is_(None), Task.deadline, Task.created_at).all()


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(
    payload: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _validate_dependency(db, payload.depends_on_id, current_user.id, self_id=None)
    task = Task(user_id=current_user.id, **payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("/{task_id}", response_model=TaskRead)
def read_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _get_owned_task(db, task_id, current_user.id)


@router.patch("/{task_id}", response_model=TaskRead)
def update_task(
    task_id: str,
    payload: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = _get_owned_task(db, task_id, current_user.id)
    updates = payload.model_dump(exclude_unset=True)

    if "depends_on_id" in updates:
        _validate_dependency(db, updates["depends_on_id"], current_user.id, self_id=task.id)

    for field, value in updates.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = _get_owned_task(db, task_id, current_user.id)
    db.delete(task)
    db.commit()
    return None
