import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import record_audit
from app.core.deps import get_current_user, require_permission
from app.core.security import hash_password
from app.database import get_db
from app.models.user import User, UserPost, Post
from app.schemas.user import UserCreate, UserOut, UserUpdate, UserPostAssign

router = APIRouter(prefix="/api/users", tags=["Utilisateurs"])


@router.get("", response_model=list[UserOut])
def list_users(
    school_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("users.view")),
):
    return db.execute(select(User).where(User.school_id == school_id)).scalars().all()


@router.post("", response_model=UserOut, status_code=201)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users.create")),
):
    existing = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Un utilisateur avec cet email existe déjà.")

    data = payload.model_dump(exclude={"password", "post_ids"})
    user = User(**data, hashed_password=hash_password(payload.password))
    db.add(user)
    db.flush()

    for post_id in payload.post_ids:
        db.add(UserPost(user_id=user.id, post_id=post_id))

    record_audit(
        db, user=current_user, school_id=user.school_id, action="user.create",
        entity_type="User", entity_id=str(user.id), new_value={"email": user.email},
    )
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users.edit")),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")

    old_value = {"is_active": user.is_active, "first_name": user.first_name, "last_name": user.last_name}
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)

    record_audit(
        db, user=current_user, school_id=user.school_id, action="user.update",
        entity_type="User", entity_id=str(user.id), old_value=old_value,
        new_value=payload.model_dump(exclude_unset=True),
    )
    db.commit()
    db.refresh(user)
    return user


@router.post("/assign-post", status_code=204)
def assign_post(
    payload: UserPostAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("posts.manage")),
):
    exists = db.execute(
        select(UserPost).where(UserPost.user_id == payload.user_id, UserPost.post_id == payload.post_id)
    ).scalar_one_or_none()
    if exists:
        return
    user = db.get(User, payload.user_id)
    db.add(UserPost(user_id=payload.user_id, post_id=payload.post_id))
    record_audit(
        db, user=current_user, school_id=user.school_id if user else None, action="user.assign_post",
        entity_type="UserPost", entity_id=str(payload.user_id), new_value={"post_id": str(payload.post_id)},
    )
    db.commit()


@router.post("/revoke-post", status_code=204)
def revoke_post(
    payload: UserPostAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("posts.manage")),
):
    link = db.execute(
        select(UserPost).where(UserPost.user_id == payload.user_id, UserPost.post_id == payload.post_id)
    ).scalar_one_or_none()
    if link is None:
        raise HTTPException(status_code=404, detail="Association introuvable.")
    user = db.get(User, payload.user_id)
    db.delete(link)
    record_audit(
        db, user=current_user, school_id=user.school_id if user else None, action="user.revoke_post",
        entity_type="UserPost", entity_id=str(payload.user_id), old_value={"post_id": str(payload.post_id)},
    )
    db.commit()
