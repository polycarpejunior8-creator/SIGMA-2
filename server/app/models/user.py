"""
Moteur d'habilitation SIGMA : Utilisateurs, Postes, Permissions, Périmètres (Scopes), Délégations.

C'est le cœur architectural du logiciel (cf cahier des charges §11 à §13 et §55 - "Règle d'or") :
    Les fonctionnalités sont séparées de l'autorisation d'y accéder.

Principe :
  - Permission        : une action possible dans le logiciel (ex: "grades.enter").
  - Post (Poste)       : un rôle configurable par l'établissement (ex: "Censeur").
  - PostPermission     : associe un Poste à une Permission.
  - PermissionScope    : restreint une PostPermission à un périmètre précis
                         (campus / niveau / série / classe / matière / période / soi-même).
                         Plusieurs lignes du même type = OR. Des types différents = AND.
                         Aucune ligne = portée sur tout l'établissement.
  - UserPost           : un utilisateur peut cumuler plusieurs postes (cf §11 exemple Mme Ngo).
  - Delegation         : autorisation temporaire, expirant automatiquement (cf §13).
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import String, Boolean, ForeignKey, DateTime, Enum, UniqueConstraint, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import UUIDPKMixin, TimestampMixin


class ScopeType(str, enum.Enum):
    SCHOOL = "school"        # tout l'établissement
    CAMPUS = "campus"
    LEVEL = "level"          # niveau (ex: 3e)
    STREAM = "stream"        # série / filière
    CLASS = "class"          # classe précise (ex: 3e A)
    SUBJECT = "subject"      # matière
    PERIOD = "period"        # période (trimestre)
    OWN = "own"              # ses propres dossiers uniquement


class User(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "users"

    school_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("schools.id", ondelete="CASCADE"))

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    first_name: Mapped[str] = mapped_column(String(150), nullable=False)
    last_name: Mapped[str] = mapped_column(String(150), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superadmin: Mapped[bool] = mapped_column(Boolean, default=False)  # bypass total (admin technique SIGMA)

    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_login_attempts: Mapped[int] = mapped_column(default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    posts: Mapped[list["UserPost"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class Permission(Base, UUIDPKMixin, TimestampMixin):
    """
    Catalogue des permissions disponibles dans SIGMA (cf §11.2).
    Le code suit la convention "module.action", ex: "grades.validate", "finance.record_payment".
    Ce catalogue est fourni par le développeur ; les Postes qui les combinent sont eux
    entièrement configurables par l'établissement.
    """
    __tablename__ = "permissions"

    code: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    module: Mapped[str] = mapped_column(String(100), nullable=False)  # students / academic / finance / admin ...
    label_fr: Mapped[str] = mapped_column(String(255), nullable=False)
    label_en: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class Post(Base, UUIDPKMixin, TimestampMixin):
    """Un poste de responsabilité configurable par l'établissement (ex: "Censeur", "Comptable")."""
    __tablename__ = "posts"
    __table_args__ = (UniqueConstraint("school_id", "name", name="uq_post_name_per_school"),)

    school_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("schools.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)  # poste créé au seed, non supprimable

    post_permissions: Mapped[list["PostPermission"]] = relationship(back_populates="post", cascade="all, delete-orphan")


class PostPermission(Base, UUIDPKMixin, TimestampMixin):
    """Association Poste <-> Permission, éventuellement restreinte par des PermissionScope."""
    __tablename__ = "post_permissions"
    __table_args__ = (UniqueConstraint("post_id", "permission_id", name="uq_post_permission"),)

    post_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"))
    permission_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("permissions.id", ondelete="CASCADE"))

    post: Mapped["Post"] = relationship(back_populates="post_permissions")
    permission: Mapped["Permission"] = relationship()
    scopes: Mapped[list["PermissionScope"]] = relationship(back_populates="post_permission", cascade="all, delete-orphan")


class PermissionScope(Base, UUIDPKMixin, TimestampMixin):
    """Une contrainte de périmètre sur une PostPermission (cf §12)."""
    __tablename__ = "permission_scopes"

    post_permission_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("post_permissions.id", ondelete="CASCADE"))
    scope_type: Mapped[ScopeType] = mapped_column(Enum(ScopeType), nullable=False)
    # scope_id référence l'entité correspondante (campus/niveau/série/classe/matière/période).
    # Nul pour scope_type == OWN (n'a pas besoin de cible).
    scope_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    post_permission: Mapped["PostPermission"] = relationship(back_populates="scopes")


class UserPost(Base, UUIDPKMixin, TimestampMixin):
    """Attribution d'un poste à un utilisateur (cumul possible, cf §11 exemple Mme Ngo)."""
    __tablename__ = "user_posts"
    __table_args__ = (UniqueConstraint("user_id", "post_id", name="uq_user_post"),)

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    post_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"))

    user: Mapped["User"] = relationship(back_populates="posts")
    post: Mapped["Post"] = relationship()


class Delegation(Base, UUIDPKMixin, TimestampMixin):
    """
    Délégation temporaire d'une permission à un utilisateur, sur un périmètre donné,
    avec expiration automatique (cf §13).
    """
    __tablename__ = "delegations"

    school_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("schools.id", ondelete="CASCADE"))
    granted_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    granted_to_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    permission_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("permissions.id"))

    scope_type: Mapped[ScopeType] = mapped_column(Enum(ScopeType), default=ScopeType.SCHOOL)
    scope_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)

    granted_by: Mapped["User"] = relationship(foreign_keys=[granted_by_id])
    granted_to: Mapped["User"] = relationship(foreign_keys=[granted_to_id])
    permission: Mapped["Permission"] = relationship()

    def is_currently_active(self, now: datetime) -> bool:
        return (not self.is_revoked) and self.start_at <= now <= self.end_at

    @property
    def permission_code(self) -> str:
        return self.permission.code
