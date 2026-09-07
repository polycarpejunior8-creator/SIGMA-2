import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.audit import record_audit
from app.core.deps import get_current_user, require_permission
from app.database import get_db
from app.models.academic import ClassGroup
from app.models.student import Student, Guardian, StudentGuardian, ClassMembership
from app.models.user import User
from app.schemas.student import (
    StudentCreate, StudentOut, StudentDetailOut, StudentUpdate,
    EnrollmentCreate, ClassMembershipOut,
)

router = APIRouter(prefix="/api/students", tags=["Élèves"])


@router.get("", response_model=list[StudentOut])
def list_students(
    school_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("students.view")),
):
    return db.execute(select(Student).where(Student.school_id == school_id)).scalars().all()


@router.get("/{student_id}", response_model=StudentDetailOut)
def get_student(
    student_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("students.view")),
):
    stmt = (
        select(Student)
        .options(selectinload(Student.guardians).selectinload(StudentGuardian.guardian))
        .where(Student.id == student_id)
    )
    student = db.execute(stmt).scalar_one_or_none()
    if student is None:
        raise HTTPException(status_code=404, detail="Élève introuvable.")

    out = StudentDetailOut.model_validate(student)
    out.guardians = [
        {
            "id": sg.guardian.id,
            "first_name": sg.guardian.first_name,
            "last_name": sg.guardian.last_name,
            "phone": sg.guardian.phone,
            "email": sg.guardian.email,
            "relationship_type": sg.relationship_type,
            "is_primary_contact": sg.is_primary_contact,
            "can_pickup": sg.can_pickup,
        }
        for sg in student.guardians
    ]
    return out


@router.post("", response_model=StudentOut, status_code=201)
def create_student(
    payload: StudentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("students.create")),
):
    existing = db.execute(
        select(Student).where(Student.school_id == payload.school_id, Student.matricule == payload.matricule)
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Ce matricule existe déjà dans cet établissement.")

    data = payload.model_dump(exclude={"guardians"})
    student = Student(**data)
    db.add(student)
    db.flush()

    for g in payload.guardians:
        guardian = Guardian(
            school_id=payload.school_id,
            first_name=g.first_name,
            last_name=g.last_name,
            phone=g.phone,
            email=g.email,
            profession=g.profession,
            address=g.address,
        )
        db.add(guardian)
        db.flush()
        db.add(StudentGuardian(
            student_id=student.id, guardian_id=guardian.id,
            relationship_type=g.relationship_type,
            is_primary_contact=g.is_primary_contact,
            can_pickup=g.can_pickup,
        ))

    record_audit(
        db, user=current_user, school_id=student.school_id, action="student.create",
        entity_type="Student", entity_id=str(student.id),
        new_value={"matricule": student.matricule, "name": student.full_name},
    )
    db.commit()
    db.refresh(student)
    return student


@router.patch("/{student_id}", response_model=StudentOut)
def update_student(
    student_id: uuid.UUID,
    payload: StudentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("students.edit")),
):
    student = db.get(Student, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Élève introuvable.")

    old_value = {"status": student.status.value}
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(student, field, value)

    record_audit(
        db, user=current_user, school_id=student.school_id, action="student.update",
        entity_type="Student", entity_id=str(student.id), old_value=old_value,
        new_value=payload.model_dump(exclude_unset=True, mode="json"),
    )
    db.commit()
    db.refresh(student)
    return student


# ---------- Inscriptions / historique de classe (cf §16) ----------

@router.post("/enroll", response_model=ClassMembershipOut, status_code=201)
def enroll_student(
    payload: EnrollmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("students.create")),
):
    """
    Inscrit un élève dans une classe pour une année scolaire. Ne modifie jamais une
    inscription existante d'une autre année : une nouvelle ligne est toujours créée,
    ce qui permet de conserver l'historique complet, y compris en cas de redoublement.
    """
    class_group = db.get(ClassGroup, payload.class_id)
    if class_group is None:
        raise HTTPException(status_code=404, detail="Classe introuvable.")

    student = db.get(Student, payload.student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Élève introuvable.")

    existing = db.execute(
        select(ClassMembership).where(
            ClassMembership.student_id == payload.student_id,
            ClassMembership.class_id == payload.class_id,
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Cet élève est déjà inscrit dans cette classe.")

    membership = ClassMembership(
        student_id=payload.student_id, class_id=payload.class_id, enrolled_at=payload.enrolled_at
    )
    db.add(membership)

    record_audit(
        db, user=current_user, school_id=student.school_id, action="student.enroll",
        entity_type="ClassMembership", entity_id=str(payload.student_id),
        new_value={"class_id": str(payload.class_id)},
    )
    db.commit()
    db.refresh(membership)
    return membership


@router.get("/{student_id}/history", response_model=list[ClassMembershipOut])
def student_history(
    student_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("students.view")),
):
    """Historique scolaire complet de l'élève, toutes années confondues (cf §16)."""
    return db.execute(
        select(ClassMembership).where(ClassMembership.student_id == student_id).order_by(ClassMembership.enrolled_at)
    ).scalars().all()


@router.get("/by-class/{class_id}", response_model=list[StudentOut])
def list_students_in_class(
    class_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("students.view")),
):
    """Liste des élèves inscrits dans une classe (utilisé notamment par la saisie des notes)."""
    stmt = (
        select(Student)
        .join(ClassMembership, ClassMembership.student_id == Student.id)
        .where(ClassMembership.class_id == class_id)
    )
    return db.execute(stmt).scalars().all()
