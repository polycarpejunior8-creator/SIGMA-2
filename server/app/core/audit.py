"""
Aide à l'écriture dans le journal d'audit (cf §14).
Appelé explicitement par les routeurs pour toute opération sensible
(modification de paiement, de note, de permission, suppression, etc.).
"""
from sqlalchemy.orm import Session

from app.models.audit import AuditLog
from app.models.user import User


def record_audit(
    db: Session,
    *,
    user: User | None,
    school_id,
    action: str,
    entity_type: str,
    entity_id: str | None = None,
    old_value: dict | None = None,
    new_value: dict | None = None,
    ip_address: str | None = None,
    device_label: str | None = None,
    notes: str | None = None,
) -> AuditLog:
    entry = AuditLog(
        school_id=school_id,
        user_id=user.id if user else None,
        user_label=user.full_name if user else "Système",
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        old_value=old_value,
        new_value=new_value,
        ip_address=ip_address,
        device_label=device_label,
        notes=notes,
    )
    db.add(entry)
    db.flush()
    return entry
