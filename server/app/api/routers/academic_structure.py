import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_permission
from app.database import get_db
from app.models.academic import Level, Stream, ClassGroup, Subject, TeacherAssignment
from app.models.user import User
from app.schemas.academic import (
    LevelCreate, LevelOut, StreamCreate, StreamOut,
    ClassGroupCreate, ClassGroupOut, SubjectCreate, SubjectOut,
    TeacherAssignmentCreate, TeacherAssignmentOut,
)

router = APIRouter(prefix="/api", tags=["Structure académique"])


# ---------- Niveaux ----------

@router.get("/schools/{school_id}/levels", response_model=list[LevelOut])
def list_levels(school_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.execute(select(Level).where(Level.school_id == school_id).order_by(Level.order_index)).scalars().all()


@router.post("/levels", response_model=LevelOut, status_code=201)
def create_level(payload: LevelCreate, db: Session = Depends(get_db), _: User = Depends(require_permission("classes.manage"))):
    level = Level(**payload.model_dump())
    db.add(level)
    db.commit()
    db.refresh(level)
    return level


# ---------- Séries ----------

@router.get("/levels/{level_id}/streams", response_model=list[StreamOut])
def list_streams(level_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.execute(select(Stream).where(Stream.level_id == level_id)).scalars().all()


@router.post("/streams", response_model=StreamOut, status_code=201)
def create_stream(payload: StreamCreate, db: Session = Depends(get_db), _: User = Depends(require_permission("classes.manage"))):
    stream = Stream(**payload.model_dump())
    db.add(stream)
    db.commit()
    db.refresh(stream)
    return stream


# ---------- Classes ----------

@router.get("/academic-years/{year_id}/classes", response_model=list[ClassGroupOut])
def list_classes(year_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.execute(select(ClassGroup).where(ClassGroup.academic_year_id == year_id)).scalars().all()


@router.post("/classes", response_model=ClassGroupOut, status_code=201)
def create_class(payload: ClassGroupCreate, db: Session = Depends(get_db), _: User = Depends(require_permission("classes.manage"))):
    class_group = ClassGroup(**payload.model_dump())
    db.add(class_group)
    db.commit()
    db.refresh(class_group)
    return class_group


# ---------- Matières ----------

@router.get("/schools/{school_id}/subjects", response_model=list[SubjectOut])
def list_subjects(school_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.execute(select(Subject).where(Subject.school_id == school_id)).scalars().all()


@router.post("/subjects", response_model=SubjectOut, status_code=201)
def create_subject(payload: SubjectCreate, db: Session = Depends(get_db), _: User = Depends(require_permission("subjects.manage"))):
    subject = Subject(**payload.model_dump())
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return subject


# ---------- Affectations enseignants ----------

@router.get("/classes/{class_id}/teacher-assignments", response_model=list[TeacherAssignmentOut])
def list_teacher_assignments(class_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.execute(select(TeacherAssignment).where(TeacherAssignment.class_id == class_id)).scalars().all()


@router.post("/teacher-assignments", response_model=TeacherAssignmentOut, status_code=201)
def create_teacher_assignment(
    payload: TeacherAssignmentCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("teacher_assignments.manage")),
):
    assignment = TeacherAssignment(**payload.model_dump())
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment
