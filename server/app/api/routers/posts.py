"""
Gestion des Postes de responsabilité et de leur matrice de permissions (cf §11, §12).
C'est ici que l'établissement configure QUI peut faire QUOI, SUR QUEL PÉRIMÈTRE —
sans jamais toucher au code (cf §55, règle d'or).
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.audit import record_audit
from app.core.deps import get_current_user, require_permission
from app.database import get_db
from app.models.user import Post, PostPermission, PermissionScope, Permission, User
from app.schemas.user import PostCreate, PostOut, PostUpdate, PermissionOut

router = APIRouter(prefix="/api", tags=["Postes & Permissions"])


def _load_post(db: Session, post_id: uuid.UUID) -> Post:
    stmt = (
        select(Post)
        .options(selectinload(Post.post_permissions).selectinload(PostPermission.scopes),
                 selectinload(Post.post_permissions).selectinload(PostPermission.permission))
        .where(Post.id == post_id)
    )
    post = db.execute(stmt).scalar_one_or_none()
    if post is None:
        raise HTTPException(status_code=404, detail="Poste introuvable.")
    return post


def _apply_permission_matrix(db: Session, post: Post, assignments: list, permission_by_code: dict[str, Permission]):
    # Repart de zéro : supprime la matrice existante puis reconstruit (transaction unique).
    for pp in list(post.post_permissions):
        db.delete(pp)
    db.flush()

    for item in assignments:
        perm = permission_by_code.get(item.permission_code)
        if perm is None:
            raise HTTPException(status_code=400, detail=f"Permission inconnue : {item.permission_code}")
        pp = PostPermission(post_id=post.id, permission_id=perm.id)
        db.add(pp)
        db.flush()
        for scope in item.scopes:
            db.add(PermissionScope(post_permission_id=pp.id, scope_type=scope.scope_type, scope_id=scope.scope_id))
    db.flush()


@router.get("/permissions", response_model=list[PermissionOut])
def list_permissions(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """Catalogue complet des permissions disponibles (utilisé par l'UI pour construire la matrice)."""
    return db.execute(select(Permission).order_by(Permission.module, Permission.code)).scalars().all()


@router.get("/schools/{school_id}/posts", response_model=list[PostOut])
def list_posts(school_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    stmt = (
        select(Post)
        .options(selectinload(Post.post_permissions).selectinload(PostPermission.scopes),
                 selectinload(Post.post_permissions).selectinload(PostPermission.permission))
        .where(Post.school_id == school_id)
    )
    return db.execute(stmt).scalars().unique().all()


@router.post("/posts", response_model=PostOut, status_code=201)
def create_post(
    payload: PostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("posts.manage")),
):
    existing = db.execute(
        select(Post).where(Post.school_id == payload.school_id, Post.name == payload.name)
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Un poste avec ce nom existe déjà dans cet établissement.")

    post = Post(school_id=payload.school_id, name=payload.name, description=payload.description)
    db.add(post)
    db.flush()

    permission_by_code = {p.code: p for p in db.execute(select(Permission)).scalars().all()}
    _apply_permission_matrix(db, post, payload.permissions, permission_by_code)

    record_audit(
        db, user=current_user, school_id=post.school_id, action="post.create",
        entity_type="Post", entity_id=str(post.id), new_value={"name": post.name},
    )
    db.commit()
    return _load_post(db, post.id)


@router.patch("/posts/{post_id}", response_model=PostOut)
def update_post(
    post_id: uuid.UUID,
    payload: PostUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("posts.manage")),
):
    post = _load_post(db, post_id)
    if post.is_system:
        raise HTTPException(status_code=403, detail="Ce poste système ne peut pas être modifié.")

    if payload.name is not None:
        post.name = payload.name
    if payload.description is not None:
        post.description = payload.description

    if payload.permissions is not None:
        permission_by_code = {p.code: p for p in db.execute(select(Permission)).scalars().all()}
        _apply_permission_matrix(db, post, payload.permissions, permission_by_code)

    record_audit(
        db, user=current_user, school_id=post.school_id, action="post.update",
        entity_type="Post", entity_id=str(post.id),
    )
    db.commit()
    return _load_post(db, post.id)


@router.delete("/posts/{post_id}", status_code=204)
def delete_post(
    post_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("posts.manage")),
):
    post = db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Poste introuvable.")
    if post.is_system:
        raise HTTPException(status_code=403, detail="Ce poste système ne peut pas être supprimé.")

    record_audit(
        db, user=current_user, school_id=post.school_id, action="post.delete",
        entity_type="Post", entity_id=str(post.id), old_value={"name": post.name},
    )
    db.delete(post)
    db.commit()
