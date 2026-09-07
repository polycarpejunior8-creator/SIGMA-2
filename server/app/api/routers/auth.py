"""
Authentification (cf doc2 §4) :
LOGIN -> mot de passe -> authentification -> chargement des postes ->
calcul des permissions -> calcul des périmètres -> génération de l'interface.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.authorization import get_user_permission_codes
from app.core.deps import get_current_user
from app.core.security import create_access_token, verify_password
from app.database import get_db
from app.models.user import User, UserPost, Post
from app.schemas.auth import Token, UserMe

router = APIRouter(prefix="/api/auth", tags=["Authentification"])

MAX_FAILED_ATTEMPTS = 5


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.email == form_data.username)).scalar_one_or_none()

    invalid_credentials = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Email ou mot de passe incorrect.",
    )

    if user is None:
        raise invalid_credentials

    now = datetime.now(timezone.utc)
    if user.locked_until and user.locked_until > now:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Compte temporairement verrouillé suite à plusieurs échecs de connexion.",
        )

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Compte désactivé.")

    if not verify_password(form_data.password, user.hashed_password):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
            from datetime import timedelta
            user.locked_until = now + timedelta(minutes=15)
        db.commit()
        raise invalid_credentials

    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = now
    db.commit()

    token = create_access_token(subject=str(user.id))
    return Token(access_token=token)


@router.get("/me", response_model=UserMe)
def read_current_user(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    permissions = sorted(get_user_permission_codes(db, current_user))
    post_names = db.execute(
        select(Post.name).join(UserPost, UserPost.post_id == Post.id).where(UserPost.user_id == current_user.id)
    ).scalars().all()

    return UserMe(
        id=current_user.id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        school_id=current_user.school_id,
        is_superadmin=current_user.is_superadmin,
        permissions=permissions,
        posts=list(post_names),
    )
