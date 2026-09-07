"""
Délégations temporaires (cf §13) : un responsable absent peut déléguer une autorisation
précise pour une période donnée. La permission expire automatiquement (vérifié par le
moteur d'autorisation à chaque requête, pas besoin de job planifié).
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import record_audit
from app.core.deps import get_current_user, require_permission
from app.database import get_db
from app.models.user import Delegation, Permission, User
from app.schemas.user import DelegationCreate, DelegationOut

router = APIRouter(prefix="/api/delegations", tags=["Délégations"])


@router.get("", response_model=list[DelegationOut])
def list_delegations(school_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.execute(select(Delegation).where(Delegation.school_id == school_id)).scalars().all()


@router.post("", response_model=DelegationOut, status_code=201)
def create_delegation(
    payload: DelegationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("delegations.manage")),
):
    if payload.end_at <= payload.start_at:
        raise HTTPException(status_code=400, detail="La date de fin doit être postérieure à la date de début.")

    permission = db.execute(select(Permission).where(Permission.code == payload.permission_code)).scalar_one_or_none()
    if permission is None:
        raise HTTPException(status_code=400, detail="Permission inconnue.")

    delegation = Delegation(
        school_id=payload.school_id,
        granted_by_id=current_user.id,
        granted_to_id=payload.granted_to_id,
        permission_id=permission.id,
        scope_type=payload.scope_type,
        scope_id=payload.scope_id,
        reason=payload.reason,
        start_at=payload.start_at,
        end_at=payload.end_at,
    )
    db.add(delegation)
    db.flush()

    record_audit(
        db, user=current_user, school_id=payload.school_id, action="delegation.create",
        entity_type="Delegation", entity_id=str(delegation.id),
        new_value={
            "granted_to_id": str(payload.granted_to_id),
            "permission_code": payload.permission_code,
            "start_at": payload.start_at.isoformat(),
            "end_at": payload.end_at.isoformat(),
        },
    )
    db.commit()
    db.refresh(delegation)
    return delegation


@router.post("/{delegation_id}/revoke", response_model=DelegationOut)
def revoke_delegation(
    delegation_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("delegations.manage")),
):
    delegation = db.get(Delegation, delegation_id)
    if delegation is None:
        raise HTTPException(status_code=404, detail="Délégation introuvable.")

    delegation.is_revoked = True
    record_audit(
        db, user=current_user, school_id=delegation.school_id, action="delegation.revoke",
        entity_type="Delegation", entity_id=str(delegation.id),
    )
    db.commit()
    db.refresh(delegation)
    return delegation
