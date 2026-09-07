"""
Module Élèves : dossier élève, famille, historique de scolarité (cf §15, §16).
"""
import enum
import uuid
from datetime import date

from sqlalchemy import String, ForeignKey, Date, Enum, Boolean, UniqueConstraint, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import UUIDPKMixin, TimestampMixin


class Gender(str, enum.Enum):
    M = "M"
    F = "F"


class StudentStatus(str, enum.Enum):
    PRE_ENROLLED = "pre_enrolled"       # préinscription
    ACTIVE = "active"                    # inscrit
    TRANSFERRED = "transferred"          # transféré vers un autre établissement
    GRADUATED = "graduated"              # diplômé / sorti en fin de cursus
    WITHDRAWN = "withdrawn"              # abandon
    EXCLUDED = "excluded"                # exclu


class MembershipStatus(str, enum.Enum):
    ACTIVE = "active"
    REPEATED = "repeated"       # a redoublé cette classe
    TRANSFERRED = "transferred"
    WITHDRAWN = "withdrawn"
    PROMOTED = "promoted"       # passé dans la classe supérieure


class Student(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "students"
    __table_args__ = (UniqueConstraint("school_id", "matricule", name="uq_student_matricule_per_school"),)

    school_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("schools.id", ondelete="CASCADE"))
    matricule: Mapped[str] = mapped_column(String(50), nullable=False)

    first_name: Mapped[str] = mapped_column(String(150), nullable=False)
    last_name: Mapped[str] = mapped_column(String(150), nullable=False)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    place_of_birth: Mapped[str | None] = mapped_column(String(255), nullable=True)
    gender: Mapped[Gender | None] = mapped_column(Enum(Gender), nullable=True)
    nationality: Mapped[str | None] = mapped_column(String(100), nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[StudentStatus] = mapped_column(Enum(StudentStatus), default=StudentStatus.PRE_ENROLLED)

    guardians: Mapped[list["StudentGuardian"]] = relationship(back_populates="student", cascade="all, delete-orphan")
    memberships: Mapped[list["ClassMembership"]] = relationship(back_populates="student", cascade="all, delete-orphan")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class Guardian(Base, UUIDPKMixin, TimestampMixin):
    """Parent / tuteur / personne autorisée (cf §15 - Famille)."""
    __tablename__ = "guardians"

    school_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("schools.id", ondelete="CASCADE"))
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # accès portail parent

    first_name: Mapped[str] = mapped_column(String(150), nullable=False)
    last_name: Mapped[str] = mapped_column(String(150), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    profession: Mapped[str | None] = mapped_column(String(150), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)

    students: Mapped[list["StudentGuardian"]] = relationship(back_populates="guardian", cascade="all, delete-orphan")


class StudentGuardian(Base, UUIDPKMixin, TimestampMixin):
    """Lien élève <-> responsable, avec le type de relation et les droits associés."""
    __tablename__ = "student_guardians"
    __table_args__ = (UniqueConstraint("student_id", "guardian_id", name="uq_student_guardian"),)

    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"))
    guardian_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("guardians.id", ondelete="CASCADE"))

    relationship_type: Mapped[str] = mapped_column(String(50), nullable=False)  # père / mère / tuteur / autre
    is_primary_contact: Mapped[bool] = mapped_column(Boolean, default=False)
    can_pickup: Mapped[bool] = mapped_column(Boolean, default=True)

    student: Mapped["Student"] = relationship(back_populates="guardians")
    guardian: Mapped["Guardian"] = relationship(back_populates="students")


class ClassMembership(Base, UUIDPKMixin, TimestampMixin):
    """
    Inscription d'un élève dans une classe pour une année scolaire donnée.
    Une nouvelle ligne est créée chaque année (y compris en cas de redoublement),
    sans jamais écraser l'historique (cf §16).
    """
    __tablename__ = "class_memberships"
    __table_args__ = (UniqueConstraint("student_id", "class_id", name="uq_student_class"),)

    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"))
    class_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("classes.id", ondelete="CASCADE"))

    status: Mapped[MembershipStatus] = mapped_column(Enum(MembershipStatus), default=MembershipStatus.ACTIVE)
    enrolled_at: Mapped[date] = mapped_column(Date, nullable=False)
    left_at: Mapped[date | None] = mapped_column(Date, nullable=True)

    student: Mapped["Student"] = relationship(back_populates="memberships")
    class_group: Mapped["object"] = relationship("ClassGroup", back_populates="memberships")
