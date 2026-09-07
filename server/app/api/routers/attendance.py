"""
Vie scolaire : présences/absences (§26) et discipline (§27).
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import record_audit
from app.core.deps import require_permission
from app.database import get_db
from app.models.attendance import AttendanceRecord
from app.models.discipline import DisciplinaryRecord
from app.models.student import Student
from app.models.user import User
from app.schemas.attendance import (
    AttendanceRecordCreate, AttendanceRecordOut, AttendanceJustify,
    DisciplinaryRecordCreate, DisciplinaryRecordOut,
)

router = APIRouter(prefix="/api", tags=["Vie scolaire"])


# ---------- Présences ----------

@router.get("/classes/{class_id}/attendance", response_model=list[AttendanceRecordOut])
def list_attendance(
    class_id: uuid.UUID,
    record_date: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("attendance.view")),
):
    stmt = select(AttendanceRecord).where(AttendanceRecord.class_id == class_id)
    if record_date:
        stmt = stmt.where(AttendanceRecord.record_date == record_date)
    return db.execute(stmt).scalars().all()


@router.post("/attendance", response_model=AttendanceRecordOut, status_code=201)
def record_attendance(
    payload: AttendanceRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("attendance.record")),
):
    record = AttendanceRecord(**payload.model_dump(), recorded_by_id=current_user.id)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.post("/attendance/{record_id}/justify", response_model=AttendanceRecordOut)
def justify_attendance(
    record_id: uuid.UUID,
    payload: AttendanceJustify,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("attendance.justify")),
):
    """Le censeur (ou poste habilité) peut valider la justification (cf §26)."""
    record = db.get(AttendanceRecord, record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Enregistrement introuvable.")

    record.is_justified = True
    record.motif = payload.motif
    record.justified_by_id = current_user.id
    record.justified_at = datetime.now(timezone.utc)

    record_audit(
        db, user=current_user, school_id=None, action="attendance.justify",
        entity_type="AttendanceRecord", entity_id=str(record.id), new_value={"motif": payload.motif},
    )
    db.commit()
    db.refresh(record)
    return record


@router.get("/students/{student_id}/attendance-summary")
def attendance_summary(
    student_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("attendance.view")),
):
    """Détection simple d'anomalie (cf §26 : "Élève absent 3 fois cette semaine")."""
    from sqlalchemy import func
    from app.models.attendance import AttendanceStatus

    total_absences = db.execute(
        select(func.count()).select_from(AttendanceRecord).where(
            AttendanceRecord.student_id == student_id, AttendanceRecord.status == AttendanceStatus.ABSENT
        )
    ).scalar_one()
    unjustified = db.execute(
        select(func.count()).select_from(AttendanceRecord).where(
            AttendanceRecord.student_id == student_id,
            AttendanceRecord.status == AttendanceStatus.ABSENT,
            AttendanceRecord.is_justified.is_(False),
        )
    ).scalar_one()
    return {"total_absences": total_absences, "unjustified_absences": unjustified}


# ---------- Discipline ----------

@router.get("/students/{student_id}/discipline", response_model=list[DisciplinaryRecordOut])
def list_discipline(
    student_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("discipline.view")),
):
    return db.execute(
        select(DisciplinaryRecord).where(DisciplinaryRecord.student_id == student_id).order_by(DisciplinaryRecord.record_date.desc())
    ).scalars().all()


@router.post("/discipline", response_model=DisciplinaryRecordOut, status_code=201)
def create_discipline_record(
    payload: DisciplinaryRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("discipline.record")),
):
    student = db.get(Student, payload.student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Élève introuvable.")

    record = DisciplinaryRecord(**payload.model_dump(), recorded_by_id=current_user.id)
    db.add(record)
    db.flush()

    record_audit(
        db, user=current_user, school_id=student.school_id, action="discipline.create",
        entity_type="DisciplinaryRecord", entity_id=str(record.id),
        new_value={"type": payload.record_type.value, "severity": payload.severity.value},
    )
    db.commit()
    db.refresh(record)
    return record
