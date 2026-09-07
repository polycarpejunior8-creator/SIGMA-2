"""
Génération de bulletins PDF (cf §23).
"""
import io
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import require_permission
from app.core.report_card_engine import compute_report_card
from app.core.report_card_pdf import generate_report_card_pdf
from app.database import get_db
from app.models.academic import ClassGroup
from app.models.organization import AcademicPeriod, School
from app.models.student import ClassMembership, Student
from app.models.user import User

router = APIRouter(prefix="/api", tags=["Bulletins"])


@router.get("/students/{student_id}/report-card")
def get_report_card_pdf(
    student_id: uuid.UUID,
    academic_period_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("report_cards.generate")),
):
    student = db.get(Student, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Élève introuvable.")

    period = db.get(AcademicPeriod, academic_period_id)
    if period is None:
        raise HTTPException(status_code=404, detail="Période introuvable.")

    membership = db.execute(
        select(ClassMembership)
        .join(ClassGroup, ClassGroup.id == ClassMembership.class_id)
        .where(ClassMembership.student_id == student_id, ClassGroup.academic_year_id == period.academic_year_id)
    ).scalars().first()
    if membership is None:
        raise HTTPException(status_code=404, detail="Aucune inscription de classe trouvée pour cette année scolaire.")

    class_group = db.get(ClassGroup, membership.class_id)
    school = db.get(School, student.school_id)

    data = compute_report_card(db, student_id, class_group.id, period.id)

    pdf_bytes = generate_report_card_pdf(
        school_name=school.name,
        student_name=student.full_name,
        matricule=student.matricule,
        class_name=class_group.name,
        period_label=period.label,
        subject_rows=data["subjects"],
        overall_average=data["overall_average"],
        rank=data["rank"],
        class_size=data["class_size"],
    )

    filename = f"bulletin_{student.matricule}_{period.label.replace(' ', '_')}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
