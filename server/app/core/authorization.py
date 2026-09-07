"""
MOTEUR D'AUTORISATION SIGMA (RBAC + Scopes).

C'est l'implémentation directe de la "règle d'or" du cahier des charges (§55) :
    "Les fonctionnalités doivent être séparées de l'autorisation d'y accéder."

Pour chaque requête sensible, on répond à la question :

    Utilisateur -> Quel(s) poste(s) ? -> Quelle permission ? -> Quel périmètre ? -> AUTORISER / REFUSER

Fonctionnement des périmètres (cf §12) :
  - Une PostPermission sans aucun PermissionScope => portée sur tout l'établissement.
  - Plusieurs PermissionScope du MÊME type (ex: deux classes) => relation OU.
  - Des PermissionScope de types DIFFÉRENTS (ex: classe ET matière) => relation ET.

Une délégation (§13) fonctionne comme une PostPermission ponctuelle et expirante :
elle est prise en compte exactement comme un poste, mais seulement pendant sa fenêtre
temporelle et si elle n'a pas été révoquée.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User, UserPost, PostPermission, PermissionScope, Permission, Delegation, ScopeType


@dataclass
class ScopeContext:
    """
    Représente le périmètre concret de la ressource ciblée par une action donnée.
    Tous les champs sont optionnels : seuls ceux pertinents pour l'action sont renseignés
    par le routeur qui appelle le moteur.
    """
    campus_id: UUID | None = None
    level_id: UUID | None = None
    stream_id: UUID | None = None
    class_id: UUID | None = None
    subject_id: UUID | None = None
    period_id: UUID | None = None
    owner_user_id: UUID | None = None  # pour le scope OWN : le "propriétaire" de la ressource

    def value_for(self, scope_type: ScopeType) -> UUID | None:
        return {
            ScopeType.CAMPUS: self.campus_id,
            ScopeType.LEVEL: self.level_id,
            ScopeType.STREAM: self.stream_id,
            ScopeType.CLASS: self.class_id,
            ScopeType.SUBJECT: self.subject_id,
            ScopeType.PERIOD: self.period_id,
        }.get(scope_type)


def _scope_set_matches(scope_rows: list[PermissionScope], context: ScopeContext | None, requesting_user_id: UUID) -> bool:
    """
    Vérifie qu'un ensemble de PermissionScope (issus d'UNE SEULE PostPermission ou délégation)
    est satisfait par le contexte fourni.
    Aucune ligne => portée établissement entière => toujours vrai.
    """
    if not scope_rows:
        return True

    if context is None:
        # Une permission scopée existe, mais l'appelant n'a fourni aucun contexte à vérifier :
        # on refuse par prudence (on ne peut pas prouver que la ressource est dans le périmètre).
        return False

    # Regrouper par type de scope
    by_type: dict[ScopeType, list[UUID | None]] = {}
    for row in scope_rows:
        by_type.setdefault(row.scope_type, []).append(row.scope_id)

    for scope_type, allowed_ids in by_type.items():
        if scope_type == ScopeType.SCHOOL:
            continue  # équivalent à "aucune restriction" pour ce type
        if scope_type == ScopeType.OWN:
            if context.owner_user_id is None or context.owner_user_id != requesting_user_id:
                return False
            continue

        target_value = context.value_for(scope_type)
        if target_value is None or target_value not in allowed_ids:
            return False

    return True


def user_has_permission(
    db: Session,
    user: User,
    permission_code: str,
    context: ScopeContext | None = None,
) -> bool:
    """
    Point d'entrée principal du moteur d'autorisation.
    Retourne True si `user` peut exécuter `permission_code` sur la ressource décrite par `context`.
    """
    if user.is_superadmin:
        return True

    now = datetime.now(timezone.utc)

    # 1. Vérifier via les postes de l'utilisateur
    stmt = (
        select(PostPermission)
        .join(Permission, PostPermission.permission_id == Permission.id)
        .join(UserPost, UserPost.post_id == PostPermission.post_id)
        .where(UserPost.user_id == user.id, Permission.code == permission_code)
    )
    post_permissions = db.execute(stmt).scalars().unique().all()

    for pp in post_permissions:
        if _scope_set_matches(pp.scopes, context, user.id):
            return True

    # 2. Vérifier via les délégations actives
    stmt_del = (
        select(Delegation)
        .join(Permission, Delegation.permission_id == Permission.id)
        .where(
            Delegation.granted_to_id == user.id,
            Permission.code == permission_code,
            Delegation.is_revoked.is_(False),
            Delegation.start_at <= now,
            Delegation.end_at >= now,
        )
    )
    delegations = db.execute(stmt_del).scalars().unique().all()

    for delegation in delegations:
        # Une délégation porte un seul (scope_type, scope_id) — on le traite comme un ensemble à 1 ligne.
        fake_row = PermissionScope(scope_type=delegation.scope_type, scope_id=delegation.scope_id)
        scope_rows = [] if delegation.scope_type == ScopeType.SCHOOL else [fake_row]
        if _scope_set_matches(scope_rows, context, user.id):
            return True

    return False


def get_user_permission_codes(db: Session, user: User) -> set[str]:
    """
    Retourne l'ensemble des codes de permission accordés à l'utilisateur, tous périmètres
    confondus. Utile pour construire le menu de l'interface côté frontend (cf doc2 §4 - Auth).
    Ne remplace jamais une vérification fine avec ScopeContext pour une action d'écriture précise.
    """
    if user.is_superadmin:
        stmt = select(Permission.code)
        return set(db.execute(stmt).scalars().all())

    now = datetime.now(timezone.utc)

    stmt = (
        select(Permission.code)
        .join(PostPermission, PostPermission.permission_id == Permission.id)
        .join(UserPost, UserPost.post_id == PostPermission.post_id)
        .where(UserPost.user_id == user.id)
    )
    codes = set(db.execute(stmt).scalars().all())

    stmt_del = (
        select(Permission.code)
        .join(Delegation, Delegation.permission_id == Permission.id)
        .where(
            Delegation.granted_to_id == user.id,
            Delegation.is_revoked.is_(False),
            Delegation.start_at <= now,
            Delegation.end_at >= now,
        )
    )
    codes |= set(db.execute(stmt_del).scalars().all())

    return codes
