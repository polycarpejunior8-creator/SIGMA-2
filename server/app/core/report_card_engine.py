"""
Calcul des données d'un bulletin (cf §22-23) : moyenne par matière, moyenne générale,
rang dans la classe. La génération du PDF proprement dite est dans `report_card_pdf.py`.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.academic import Subject, TeacherAssignment
from app.models.assessment import Assessment, Grade, GradeStatus
from app.models.student import ClassMembership, Student

VALID_GRADE_STATUSES = [GradeStatus.VALIDATED, GradeStatus.LOCKED, GradeStatus.PUBLISHED]


def compute_subject_average(db: Session, student_id: uuid.UUID, subject_id: uuid.UUID, period_id: uuid.UUID) -> float | None:
    stmt = (
        select(Grade.score, Assessment.coefficient, Assessment.max_score)
        .join(Assessment, Assessment.id == Grade.assessment_id)
        .where(
            Grade.student_id == student_id,
            Assessment.subject_id == subject_id,
            Assessment.academic_period_id == period_id,
            Grade.status.in_(VALID_GRADE_STATUSES),
            Grade.is_absent.is_(False),
            Grade.score.is_not(None),
        )
    )
    rows = db.execute(stmt).all()
    if not rows:
        return None

    total_weighted, total_coeff = 0.0, 0.0
    for score, coeff, max_score in rows:
        normalized = (float(score) / float(max_score)) * 20
        total_weighted += normalized * float(coeff)
        total_coeff += float(coeff)
    return total_weighted / total_coeff if total_coeff else None


def compute_report_card(db: Session, student_id: uuid.UUID, class_id: uuid.UUID, period_id: uuid.UUID) -> dict:
    """
    Retourne :
        {
          "subjects": [{"subject": Subject, "average": float|None, "coefficient": float}],
          "overall_average": float|None,
          "rank": int|None,
          "class_size": int,
        }
    """
    subjects = db.execute(
        select(Subject)
        .join(TeacherAssignment, TeacherAssignment.subject_id == Subject.id)
        .where(TeacherAssignment.class_id == class_id)
        .distinct()
    ).scalars().all()

    subject_rows = []
    total_weighted, total_coeff = 0.0, 0.0
    for subject in subjects:
        avg = compute_subject_average(db, student_id, subject.id, period_id)
        coeff = float(subject.default_coefficient)
        subject_rows.append({"subject": subject, "average": avg, "coefficient": coeff})
        if avg is not None:
            total_weighted += avg * coeff
            total_coeff += coeff

    overall_average = round(total_weighted / total_coeff, 2) if total_coeff else None

    # Rang dans la classe : recalcul de la moyenne générale de chaque élève de la classe.
    classmates = db.execute(
        select(ClassMembership.student_id).where(ClassMembership.class_id == class_id)
    ).scalars().all()

    averages = []
    for classmate_id in classmates:
        tw, tc = 0.0, 0.0
        for subject in subjects:
            avg = compute_subject_average(db, classmate_id, subject.id, period_id)
            if avg is not None:
                tw += avg * float(subject.default_coefficient)
                tc += float(subject.default_coefficient)
        if tc:
            averages.append((classmate_id, tw / tc))

    averages.sort(key=lambda x: x[1], reverse=True)
    rank = next((i + 1 for i, (sid, _) in enumerate(averages) if sid == student_id), None)

    return {
        "subjects": subject_rows,
        "overall_average": overall_average,
        "rank": rank,
        "class_size": len(classmates),
    }
