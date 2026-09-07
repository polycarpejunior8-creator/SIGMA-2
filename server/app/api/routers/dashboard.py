"""
Tableau de bord direction (cf §36). Version MVP : indicateurs de base calculés à la volée.
Les alertes intelligentes plus avancées (§37) et l'analytique comparative (§38) sont prévues
pour la V1/V2 (cf cahier des charges §53-54) et pourront être ajoutées comme service séparé
sans toucher au reste de l'architecture.
"""
import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models.academic import ClassGroup
from app.models.assessment import Grade, GradeStatus
from app.models.finance import Payment, Invoice
from app.models.organization import AcademicYear
from app.models.student import Student, StudentStatus
from app.models.user import User

router = APIRouter(prefix="/api/dashboard", tags=["Tableau de bord"])


class DashboardOut(BaseModel):
    active_students: int
    classes_count: int
    average_grade: float | None
    total_collected: float
    total_due: float
    unpaid_amount: float


@router.get("/{school_id}", response_model=DashboardOut)
def get_dashboard(school_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    active_students = db.execute(
        select(func.count()).select_from(Student).where(Student.school_id == school_id, Student.status == StudentStatus.ACTIVE)
    ).scalar_one()

    current_year = db.execute(
        select(AcademicYear).where(AcademicYear.school_id == school_id, AcademicYear.is_current.is_(True))
    ).scalar_one_or_none()

    classes_count = 0
    if current_year:
        classes_count = db.execute(
            select(func.count()).select_from(ClassGroup).where(ClassGroup.academic_year_id == current_year.id)
        ).scalar_one()

    avg_grade = db.execute(
        select(func.avg(Grade.score)).where(Grade.status.in_([GradeStatus.VALIDATED, GradeStatus.LOCKED, GradeStatus.PUBLISHED]))
    ).scalar_one()

    total_collected = db.execute(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.is_cancelled.is_(False))
    ).scalar_one()

    total_due = db.execute(select(func.coalesce(func.sum(Invoice.amount_due), 0))).scalar_one()

    return DashboardOut(
        active_students=active_students,
        classes_count=classes_count,
        average_grade=round(float(avg_grade), 2) if avg_grade is not None else None,
        total_collected=float(total_collected),
        total_due=float(total_due),
        unpaid_amount=max(float(total_due) - float(total_collected), 0),
    )
