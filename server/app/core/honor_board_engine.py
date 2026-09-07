"""
Moteur de calcul des tableaux d'honneur (cf §24).

Étapes :
  1. Déterminer la population d'élèves concernée (classe, niveau, ou établissement entier).
  2. Calculer pour chaque élève : moyenne pondérée par coefficient (sur les notes VALIDATED/
     LOCKED/PUBLISHED de la période), absences injustifiées, solde de points de discipline.
  3. Filtrer selon les seuils d'éligibilité de la règle (HonorBoardRule).
  4. Calculer le score pondéré des élèves éligibles et les classer.
"""
import uuid
from datetime import date

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.assessment import Assessment, Grade, GradeStatus
from app.models.attendance import AttendanceRecord, AttendanceStatus
from app.models.discipline import DisciplinaryRecord, DisciplinarySeverity
from app.models.honor_board import HonorBoardRule, HonorBoardScopeType
from app.models.organization import AcademicPeriod
from app.models.student import ClassMembership
from app.models.academic import ClassGroup


VALID_GRADE_STATUSES = [GradeStatus.VALIDATED, GradeStatus.LOCKED, GradeStatus.PUBLISHED]


def _students_in_scope(db: Session, scope_type: HonorBoardScopeType, class_id: uuid.UUID | None, level_id: uuid.UUID | None) -> list[uuid.UUID]:
    if scope_type == HonorBoardScopeType.CLASS:
        stmt = select(ClassMembership.student_id).where(ClassMembership.class_id == class_id)
    elif scope_type == HonorBoardScopeType.LEVEL:
        stmt = (
            select(ClassMembership.student_id)
            .join(ClassGroup, ClassGroup.id == ClassMembership.class_id)
            .where(ClassGroup.level_id == level_id)
        )
    else:  # SCHOOL : tous les élèves actuellement inscrits dans une classe
        stmt = select(ClassMembership.student_id)
    return list(db.execute(stmt).scalars().unique().all())


def _weighted_average(db: Session, student_id: uuid.UUID, period_id: uuid.UUID) -> float | None:
    """Moyenne pondérée par coefficient, cf §22 (moteur de calcul configurable)."""
    stmt = (
        select(Grade.score, Assessment.coefficient, Assessment.max_score)
        .join(Assessment, Assessment.id == Grade.assessment_id)
        .where(
            Grade.student_id == student_id,
            Assessment.academic_period_id == period_id,
            Grade.status.in_(VALID_GRADE_STATUSES),
            Grade.is_absent.is_(False),
            Grade.score.is_not(None),
        )
    )
    rows = db.execute(stmt).all()
    if not rows:
        return None

    total_weighted = 0.0
    total_coeff = 0.0
    for score, coeff, max_score in rows:
        normalized = (float(score) / float(max_score)) * 20  # ramené sur 20 pour uniformiser
        total_weighted += normalized * float(coeff)
        total_coeff += float(coeff)

    return total_weighted / total_coeff if total_coeff else None


def _unjustified_absences(db: Session, student_id: uuid.UUID, period_start: date, period_end: date) -> int:
    stmt = select(func.count()).select_from(AttendanceRecord).where(
        AttendanceRecord.student_id == student_id,
        AttendanceRecord.status == AttendanceStatus.ABSENT,
        AttendanceRecord.is_justified.is_(False),
        AttendanceRecord.record_date >= period_start,
        AttendanceRecord.record_date <= period_end,
    )
    return db.execute(stmt).scalar_one()


def _discipline_points(db: Session, student_id: uuid.UUID, period_start: date, period_end: date) -> tuple[float, bool]:
    """Retourne (somme des points, a_une_sanction_grave)."""
    stmt = select(DisciplinaryRecord).where(
        DisciplinaryRecord.student_id == student_id,
        DisciplinaryRecord.record_date >= period_start,
        DisciplinaryRecord.record_date <= period_end,
    )
    records = db.execute(stmt).scalars().all()
    total = sum(float(r.points) for r in records)
    has_high_severity = any(r.severity == DisciplinarySeverity.HIGH for r in records)
    return total, has_high_severity


def compute_honor_board(
    db: Session,
    rule: HonorBoardRule,
    period: AcademicPeriod,
    scope_type: HonorBoardScopeType,
    class_id: uuid.UUID | None,
    level_id: uuid.UUID | None,
) -> list[dict]:
    """
    Calcule et retourne la liste triée des élèves éligibles, sous forme de dicts prêts
    à être persistés en HonorBoardEntry.
    """
    student_ids = _students_in_scope(db, scope_type, class_id, level_id)

    candidates = []
    for student_id in student_ids:
        average = _weighted_average(db, student_id, period.id)
        if average is None:
            continue  # pas assez de notes validées pour être évalué

        unjustified = _unjustified_absences(db, student_id, period.start_date, period.end_date)
        discipline_points, has_high_severity = _discipline_points(db, student_id, period.start_date, period.end_date)

        if rule.min_average is not None and average < float(rule.min_average):
            continue
        if rule.max_unjustified_absences is not None and unjustified > rule.max_unjustified_absences:
            continue
        if rule.disallow_high_severity_sanction and has_high_severity:
            continue

        candidates.append({
            "student_id": student_id,
            "average": round(average, 2),
            "unjustified_absences": unjustified,
            "discipline_points": discipline_points,
            "average_normalized": average / 20 * 100,
            "attendance_normalized": max(0, 100 - unjustified * 5),
            "discipline_normalized": max(0, 100 + discipline_points),
        })

    # Score pondéré (cf §24 : ex. 70% moyenne + 15% discipline + 10% assiduité + 5% progression).
    # La progression nécessiterait la comparaison avec la période précédente ; fixée à 0 pour ce MVP.
    for c in candidates:
        c["score"] = round(
            c["average_normalized"] * float(rule.weight_average) / 100
            + c["discipline_normalized"] * float(rule.weight_discipline) / 100
            + c["attendance_normalized"] * float(rule.weight_attendance) / 100,
            2,
        )

    candidates.sort(key=lambda c: c["score"], reverse=True)

    if rule.max_winners:
        candidates = candidates[: rule.max_winners]

    for i, c in enumerate(candidates, start=1):
        c["rank"] = i

    return candidates
