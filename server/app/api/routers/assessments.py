"""
Évaluations et notes (cf §20-22). Contrairement aux autres routeurs qui utilisent
`require_permission` (contrôle simple, portée établissement), ce module illustre
l'usage COMPLET du moteur RBAC/Scopes : chaque action de saisie/validation vérifie
que l'utilisateur a bien la permission POUR LA CLASSE ET LA MATIÈRE CONCERNÉES,
et pas seulement la permission générique.
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import record_audit
from app.core.authorization import ScopeContext, user_has_permission
from app.core.deps import get_current_user
from app.database import get_db
from app.models.academic import ClassGroup
from app.models.assessment import Assessment, Grade, GradeStatus
from app.models.organization import AcademicPeriod
from app.models.user import User
from app.schemas.assessment import (
    AssessmentCreate, AssessmentOut, GradeBulkUpsert, GradeOut, GradeStatusTransition,
)

router = APIRouter(prefix="/api", tags=["Évaluations & Notes"])


def _assessment_scope(assessment: Assessment) -> ScopeContext:
    return ScopeContext(
        class_id=assessment.class_id,
        subject_id=assessment.subject_id,
        period_id=assessment.academic_period_id,
    )


def _require(db: Session, user: User, code: str, context: ScopeContext | None = None):
    if not user_has_permission(db, user, code, context):
        raise HTTPException(status_code=403, detail=f"Permission refusée : {code} (hors de votre périmètre)")


@router.post("/assessments", response_model=AssessmentOut, status_code=201)
def create_assessment(
    payload: AssessmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    context = ScopeContext(class_id=payload.class_id, subject_id=payload.subject_id, period_id=payload.academic_period_id)
    _require(db, current_user, "grades.enter", context)

    period = db.get(AcademicPeriod, payload.academic_period_id)
    if period is None:
        raise HTTPException(status_code=404, detail="Période académique introuvable.")
    if not period.is_open_for_grading:
        raise HTTPException(status_code=423, detail="La saisie des notes est fermée pour cette période.")

    assessment = Assessment(**payload.model_dump(), created_by_id=current_user.id)
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return assessment


@router.get("/classes/{class_id}/assessments", response_model=list[AssessmentOut])
def list_assessments(class_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    context = ScopeContext(class_id=class_id)
    _require(db, current_user, "grades.view", context)
    return db.execute(select(Assessment).where(Assessment.class_id == class_id)).scalars().all()


@router.put("/assessments/{assessment_id}/grades", response_model=list[GradeOut])
def upsert_grades(
    assessment_id: uuid.UUID,
    payload: GradeBulkUpsert,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Saisie groupée des notes (cf §21 - PC/tablette/smartphone/import Excel côté client)."""
    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Évaluation introuvable.")

    _require(db, current_user, "grades.enter", _assessment_scope(assessment))

    period = db.get(AcademicPeriod, assessment.academic_period_id)
    if not period.is_open_for_grading:
        raise HTTPException(status_code=423, detail="La saisie des notes est fermée pour cette période.")

    existing = {g.student_id: g for g in assessment.grades}
    results = []
    for item in payload.grades:
        grade = existing.get(item.student_id)
        if grade is None:
            grade = Grade(assessment_id=assessment.id, student_id=item.student_id)
            db.add(grade)
        if grade.status == GradeStatus.LOCKED:
            raise HTTPException(status_code=423, detail="Cette note est verrouillée et ne peut plus être modifiée.")
        grade.score = item.score
        grade.is_absent = item.is_absent
        if grade.status == GradeStatus.DRAFT:
            pass  # reste en brouillon jusqu'à soumission explicite
        results.append(grade)

    db.commit()
    for g in results:
        db.refresh(g)
    return results


@router.post("/grades/{grade_id}/transition", response_model=GradeOut)
def transition_grade(
    grade_id: uuid.UUID,
    payload: GradeStatusTransition,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Fait avancer une note dans son cycle de vie :
    DRAFT -> SUBMITTED -> CHECKED -> VALIDATED -> LOCKED -> PUBLISHED (cf doc2 §10).
    Chaque transition a sa propre permission requise.
    """
    grade = db.get(Grade, grade_id)
    if grade is None:
        raise HTTPException(status_code=404, detail="Note introuvable.")

    assessment = db.get(Assessment, grade.assessment_id)
    context = _assessment_scope(assessment)

    transition_permission = {
        GradeStatus.SUBMITTED: "grades.enter",
        GradeStatus.CHECKED: "grades.validate",
        GradeStatus.VALIDATED: "grades.validate",
        GradeStatus.LOCKED: "grades.lock",
        GradeStatus.PUBLISHED: "report_cards.publish",
    }.get(payload.new_status)

    if transition_permission is None:
        raise HTTPException(status_code=400, detail="Transition invalide.")

    _require(db, current_user, transition_permission, context)

    old_status = grade.status
    grade.status = payload.new_status
    now = datetime.now(timezone.utc)
    if payload.new_status == GradeStatus.SUBMITTED:
        grade.submitted_at = now
    if payload.new_status == GradeStatus.VALIDATED:
        grade.validated_at = now
        grade.validated_by_id = current_user.id

    record_audit(
        db, user=current_user, school_id=None, action=f"grade.transition.{payload.new_status.value}",
        entity_type="Grade", entity_id=str(grade.id),
        old_value={"status": old_status.value}, new_value={"status": payload.new_status.value},
    )
    db.commit()
    db.refresh(grade)
    return grade
