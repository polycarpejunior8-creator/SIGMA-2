"""
Journal d'audit (cf §14). Volontairement en LECTURE SEULE : aucune route de
modification ou de suppression n'est exposée, conformément au cahier des charges.
"""
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import require_permission
from app.database import get_db
from app.models.audit import AuditLog
from app.models.user import User
from app.schemas.audit import AuditLogOut

router = APIRouter(prefix="/api/audit-logs", tags=["Audit"])


@router.get("", response_model=list[AuditLogOut])
def list_audit_logs(
    school_id: uuid.UUID,
    entity_type: str | None = Query(default=None),
    user_id: uuid.UUID | None = Query(default=None),
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("audit.view")),
):
    stmt = select(AuditLog).where(AuditLog.school_id == school_id).order_by(AuditLog.created_at.desc()).limit(limit)
    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    if user_id:
        stmt = stmt.where(AuditLog.user_id == user_id)
    return db.execute(stmt).scalars().all()
