"""
Amorçage de la base de données SIGMA :
  1. Crée toutes les tables (via SQLAlchemy metadata — pour Alembic, voir /alembic).
  2. Insère le catalogue de permissions.
  3. Crée une Organisation + École + Année scolaire par défaut.
  4. Crée un Poste "Administrateur système" (toutes permissions, portée établissement)
     et un utilisateur superadmin.
  5. Crée quelques données de démonstration (niveaux, classes, matières, poste Enseignant
     scopé, poste Comptable) pour illustrer le moteur RBAC/Scopes dès le premier démarrage.

Utilisation :
    python -m app.seed
"""
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.core.permissions_catalog import PERMISSIONS_CATALOG
from app.core.security import hash_password
from app.database import Base, engine, SessionLocal
import app.models  # noqa: F401  (assure que tous les modèles sont enregistrés dans Base.metadata)
from app.models.organization import Organization, School, AcademicYear, AcademicPeriod
from app.models.user import User, Permission, Post, PostPermission, PermissionScope, UserPost, ScopeType
from app.models.academic import Level, Stream, ClassGroup, Subject, TeacherAssignment


def create_tables():
    Base.metadata.create_all(bind=engine)
    print("✔ Tables créées (ou déjà existantes).")


def seed_permissions(db: Session) -> dict[str, Permission]:
    existing = {p.code: p for p in db.execute(select(Permission)).scalars().all()}
    created = 0
    for item in PERMISSIONS_CATALOG:
        if item["code"] not in existing:
            perm = Permission(**item)
            db.add(perm)
            existing[item["code"]] = perm
            created += 1
    db.flush()
    print(f"✔ Catalogue de permissions : {created} créées, {len(existing) - created} déjà présentes.")
    return existing


def seed_org_and_school(db: Session) -> School:
    org = db.execute(select(Organization).where(Organization.name == settings.SEED_ORG_NAME)).scalar_one_or_none()
    if org is None:
        org = Organization(name=settings.SEED_ORG_NAME)
        db.add(org)
        db.flush()
        print(f"✔ Organisation créée : {org.name}")

    school = db.execute(select(School).where(School.organization_id == org.id)).scalars().first()
    if school is None:
        school = School(
            organization_id=org.id,
            name=settings.SEED_ORG_NAME,
            code="ECOLE-001",
            language="fr",
            currency="XAF",
            grading_system="20",
        )
        db.add(school)
        db.flush()
        print(f"✔ École créée : {school.name} ({school.code})")

    year = db.execute(
        select(AcademicYear).where(AcademicYear.school_id == school.id, AcademicYear.is_current.is_(True))
    ).scalars().first()
    if year is None:
        year = AcademicYear(
            school_id=school.id,
            label="2026/2027",
            start_date=date(2026, 9, 1),
            end_date=date(2027, 7, 15),
            is_current=True,
        )
        db.add(year)
        db.flush()

        periods = [
            ("Trimestre 1", 1, date(2026, 9, 1), date(2026, 12, 15)),
            ("Trimestre 2", 2, date(2027, 1, 5), date(2027, 3, 25)),
            ("Trimestre 3", 3, date(2027, 4, 5), date(2027, 7, 15)),
        ]
        for label, idx, start, end in periods:
            db.add(AcademicPeriod(academic_year_id=year.id, label=label, order_index=idx, start_date=start, end_date=end))
        db.flush()
        print(f"✔ Année scolaire créée : {year.label} (avec 3 trimestres)")

    return school


def seed_superadmin(db: Session, school: School, permissions: dict[str, Permission]):
    admin = db.execute(select(User).where(User.email == settings.SEED_ADMIN_EMAIL)).scalar_one_or_none()
    if admin is not None:
        print("✔ Utilisateur administrateur déjà présent, rien à faire.")
        return

    admin = User(
        school_id=school.id,
        email=settings.SEED_ADMIN_EMAIL,
        hashed_password=hash_password(settings.SEED_ADMIN_PASSWORD),
        first_name="Admin",
        last_name="SIGMA",
        is_superadmin=True,
        is_active=True,
    )
    db.add(admin)
    db.flush()

    post = Post(
        school_id=school.id,
        name="Administrateur système",
        description="Poste technique disposant de toutes les permissions, sans restriction de périmètre.",
        is_system=True,
    )
    db.add(post)
    db.flush()

    for perm in permissions.values():
        db.add(PostPermission(post_id=post.id, permission_id=perm.id))
    db.flush()

    db.add(UserPost(user_id=admin.id, post_id=post.id))
    db.flush()

    print(f"✔ Superadministrateur créé : {settings.SEED_ADMIN_EMAIL} / {settings.SEED_ADMIN_PASSWORD}")
    print("  ⚠ Changez ce mot de passe dès la première connexion.")


def seed_demo_academic_structure(db: Session, school: School, permissions: dict[str, Permission]):
    """
    Crée un exemple concret illustrant le moteur RBAC/Scopes :
      - Niveau "3e" avec deux classes (3e A, 3e B)
      - Matière "Mathématiques"
      - Poste "Enseignant" avec la permission grades.enter restreinte à 3e A + Mathématiques
      - Poste "Comptable" avec les permissions finance.* portée établissement entière
    """
    year = db.execute(select(AcademicYear).where(AcademicYear.school_id == school.id, AcademicYear.is_current.is_(True))).scalar_one()

    level = db.execute(select(Level).where(Level.school_id == school.id, Level.name == "3e")).scalar_one_or_none()
    if level is None:
        level = Level(school_id=school.id, name="3e", order_index=9)
        db.add(level)
        db.flush()

        class_a = ClassGroup(academic_year_id=year.id, level_id=level.id, name="3e A")
        class_b = ClassGroup(academic_year_id=year.id, level_id=level.id, name="3e B")
        db.add_all([class_a, class_b])
        db.flush()
        print("✔ Démo : niveau 3e + classes 3e A / 3e B créées.")

    subject = db.execute(select(Subject).where(Subject.school_id == school.id, Subject.code == "MATH")).scalar_one_or_none()
    if subject is None:
        subject = Subject(school_id=school.id, code="MATH", name="Mathématiques", default_coefficient=4)
        db.add(subject)
        db.flush()
        print("✔ Démo : matière Mathématiques créée.")

    class_a = db.execute(select(ClassGroup).where(ClassGroup.academic_year_id == year.id, ClassGroup.name == "3e A")).scalar_one()

    teacher_post = db.execute(select(Post).where(Post.school_id == school.id, Post.name == "Enseignant (démo)")).scalar_one_or_none()
    if teacher_post is None:
        teacher_post = Post(
            school_id=school.id,
            name="Enseignant (démo)",
            description="Exemple : peut saisir les notes de Mathématiques en 3e A uniquement.",
        )
        db.add(teacher_post)
        db.flush()

        pp = PostPermission(post_id=teacher_post.id, permission_id=permissions["grades.enter"].id)
        db.add(pp)
        db.flush()
        db.add(PermissionScope(post_permission_id=pp.id, scope_type=ScopeType.CLASS, scope_id=class_a.id))
        db.add(PermissionScope(post_permission_id=pp.id, scope_type=ScopeType.SUBJECT, scope_id=subject.id))

        pp_view = PostPermission(post_id=teacher_post.id, permission_id=permissions["grades.view"].id)
        db.add(pp_view)
        db.flush()
        db.add(PermissionScope(post_permission_id=pp_view.id, scope_type=ScopeType.CLASS, scope_id=class_a.id))

        db.flush()
        print("✔ Démo : poste 'Enseignant (démo)' créé avec permission scopée (3e A + Mathématiques).")

    accountant_post = db.execute(select(Post).where(Post.school_id == school.id, Post.name == "Comptable (démo)")).scalar_one_or_none()
    if accountant_post is None:
        accountant_post = Post(
            school_id=school.id,
            name="Comptable (démo)",
            description="Exemple : accès complet au module Finance, portée établissement entière.",
        )
        db.add(accountant_post)
        db.flush()
        for code in ["finance.view_payments", "finance.record_payment", "finance.print_receipt", "finance.view_cash_register"]:
            db.add(PostPermission(post_id=accountant_post.id, permission_id=permissions[code].id))
        db.flush()
        print("✔ Démo : poste 'Comptable (démo)' créé (Finance, portée établissement).")


def main():
    create_tables()
    db = SessionLocal()
    try:
        permissions = seed_permissions(db)
        school = seed_org_and_school(db)
        seed_superadmin(db, school, permissions)
        seed_demo_academic_structure(db, school, permissions)
        db.commit()
        print("\n✅ Amorçage terminé avec succès.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
