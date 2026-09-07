"""
Emploi du temps (cf §19), avec détection automatique de conflits.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_permission
from app.core.timetable_engine import find_conflicts
from app.database import get_db
from app.models.timetable import TimetableSlot
from app.models.user import User
from app.schemas.timetable import TimetableSlotCreate, TimetableSlotOut

router = APIRouter(prefix="/api", tags=["Emploi du temps"])


@router.get("/classes/{class_id}/timetable", response_model=list[TimetableSlotOut])
def list_class_timetable(class_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(require_permission("timetable.view"))):
    return db.execute(select(TimetableSlot).where(TimetableSlot.class_id == class_id)).scalars().all()


@router.get("/teachers/{teacher_id}/timetable", response_model=list[TimetableSlotOut])
def list_teacher_timetable(teacher_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(require_permission("timetable.view"))):
    return db.execute(select(TimetableSlot).where(TimetableSlot.teacher_id == teacher_id)).scalars().all()


@router.post("/timetable-slots", response_model=TimetableSlotOut, status_code=201)
def create_slot(
    payload: TimetableSlotCreate,
    force: bool = False,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("timetable.manage")),
):
    """
    Crée un créneau. Si des conflits sont détectés (enseignant, classe ou salle déjà pris),
    la création est refusée avec le détail des conflits — sauf si `force=true` est explicitement
    demandé par un administrateur qui assume la collision (cf §19, exemple de conflit affiché).
    """
    candidate = TimetableSlot(**payload.model_dump())
    conflicts = find_conflicts(db, candidate)

    if conflicts and not force:
        raise HTTPException(
            status_code=409,
            detail={"message": "Conflit(s) d'emploi du temps détecté(s).", "conflicts": conflicts},
        )

    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return candidate


@router.delete("/timetable-slots/{slot_id}", status_code=204)
def delete_slot(slot_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(require_permission("timetable.manage"))):
    slot = db.get(TimetableSlot, slot_id)
    if slot is None:
        raise HTTPException(status_code=404, detail="Créneau introuvable.")
    db.delete(slot)
    db.commit()
