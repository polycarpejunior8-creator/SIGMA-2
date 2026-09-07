"""
Dépendances FastAPI réutilisables : utilisateur courant, garde-fous de permissions.
"""
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.authorization import ScopeContext, user_has_permission
from app.core.security import decode_access_token
from app.database import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Identifiants invalides ou session expirée.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None or "sub" not in payload:
        raise credentials_exception

    user = db.get(User, UUID(payload["sub"]))
    if user is None or not user.is_active:
        raise credentials_exception
    return user


def require_permission(permission_code: str, context: ScopeContext | None = None):
    """
    Fabrique une dépendance FastAPI qui refuse la requête (403) si l'utilisateur courant
    ne possède pas `permission_code` (éventuellement restreint par `context`).

    Pour les vérifications à périmètre dynamique (ex: dépend de l'ID de la classe dans l'URL),
    préférez appeler `user_has_permission(...)` directement dans le corps du routeur.
    """

    def _dependency(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        if not user_has_permission(db, current_user, permission_code, context):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission refusée : {permission_code}",
            )
        return current_user

    return _dependency


def require_superadmin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_superadmin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Réservé à l'administrateur système.")
    return current_user
