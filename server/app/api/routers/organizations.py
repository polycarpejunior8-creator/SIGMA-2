import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_permission
from app.database import get_db
from app.models.organization import School, Campus, AcademicYear, AcademicPeriod
from app.models.user import User
from app.schemas.organization import (
    SchoolCreate, SchoolOut, CampusCreate, CampusOut,
    AcademicYearCreate, AcademicYearOut, AcademicPeriodCreate, AcademicPeriodOut,
)

router = APIRouter(prefix="/api", tags=["Établissements"])


# ---------- Écoles ----------

@router.get("/schools", response_model=list[SchoolOut])
def list_schools(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.execute(select(School)).scalars().all()


@router.post("/schools", response_model=SchoolOut, status_code=201)
def create_school(payload: SchoolCreate, db: Session = Depends(get_db), _: User = Depends(require_permission("schools.manage"))):
    school = School(**payload.model_dump())
    db.add(school)
    db.commit()
    db.refresh(school)
    return school


# ---------- Campus ----------

@router.get("/schools/{school_id}/campuses", response_model=list[CampusOut])
def list_campuses(school_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.execute(select(Campus).where(Campus.school_id == school_id)).scalars().all()


@router.post("/campuses", response_model=CampusOut, status_code=201)
def create_campus(payload: CampusCreate, db: Session = Depends(get_db), _: User = Depends(require_permission("schools.manage"))):
    campus = Campus(**payload.model_dump())
    db.add(campus)
    db.commit()
    db.refresh(campus)
    return campus


# ---------- Années scolaires ----------

@router.get("/schools/{school_id}/academic-years", response_model=list[AcademicYearOut])
def list_academic_years(school_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.execute(select(AcademicYear).where(AcademicYear.school_id == school_id)).scalars().all()


@router.post("/academic-years", response_model=AcademicYearOut, status_code=201)
def create_academic_year(payload: AcademicYearCreate, db: Session = Depends(get_db), _: User = Depends(require_permission("academic_years.manage"))):
    if payload.is_current:
        db.query(AcademicYear).filter(AcademicYear.school_id == payload.school_id).update({"is_current": False})
    year = AcademicYear(**payload.model_dump())
    db.add(year)
    db.commit()
    db.refresh(year)
    return year


@router.post("/academic-years/{year_id}/archive", response_model=AcademicYearOut)
def archive_academic_year(year_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(require_permission("academic_years.manage"))):
    """Une année clôturée devient archivée et protégée en écriture (cf §9)."""
    year = db.get(AcademicYear, year_id)
    if year is None:
        raise HTTPException(status_code=404, detail="Année scolaire introuvable.")
    year.is_archived = True
    year.is_current = False
    db.commit()
    db.refresh(year)
    return year


# ---------- Périodes académiques ----------

@router.get("/academic-years/{year_id}/periods", response_model=list[AcademicPeriodOut])
def list_periods(year_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.execute(select(AcademicPeriod).where(AcademicPeriod.academic_year_id == year_id)).scalars().all()


@router.post("/academic-periods", response_model=AcademicPeriodOut, status_code=201)
def create_period(payload: AcademicPeriodCreate, db: Session = Depends(get_db), _: User = Depends(require_permission("academic_years.manage"))):
    period = AcademicPeriod(**payload.model_dump())
    db.add(period)
    db.commit()
    db.refresh(period)
    return period


@router.post("/academic-periods/{period_id}/toggle-grading", response_model=AcademicPeriodOut)
def toggle_grading(period_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(require_permission("academic_years.manage"))):
    """Ouvre/ferme la saisie des notes pour la période (verrou global, cf §21)."""
    period = db.get(AcademicPeriod, period_id)
    if period is None:
        raise HTTPException(status_code=404, detail="Période introuvable.")
    period.is_open_for_grading = not period.is_open_for_grading
    db.commit()
    db.refresh(period)
    return period
