# SIGMA — Système Intégré de Gestion et Management Académique

MVP fonctionnel implémentant une large partie du cahier des charges v2.0 :
- Moteur RBAC/Scopes (Postes + Permissions + Périmètres + Délégations temporaires)
- Journal d'audit immuable
- Module Élèves (dossier, famille, historique de scolarité sans écrasement)
- Module Académique (niveaux/séries/classes/matières, évaluations et notes avec cycle de
  validation DRAFT → SUBMITTED → CHECKED → VALIDATED → LOCKED → PUBLISHED)
- Emploi du temps avec détection automatique de conflits (enseignant/classe/salle)
- Vie scolaire : présences/absences avec justification, discipline (observations, sanctions,
  récompenses)
- Tableaux d'honneur automatiques et entièrement configurables (seuils + pondération)
- Génération de bulletins PDF (moyenne par matière, moyenne générale, rang)
- Module Finance (tarifs, factures, paiements avec reçus numérotés, annulation au lieu de
  suppression)
- Module RH & Paie (contrats, congés avec workflow d'approbation, fiches de paie)
- Module Communication (annonces internes ; SMS/Email/Push prévus mais non branchés à un
  fournisseur externe)
- Tableau de bord direction (indicateurs de base)

Stack : **FastAPI + PostgreSQL + SQLAlchemy** (backend) / **React + TypeScript + Vite** (frontend),
conforme à l'architecture technique recommandée dans le cahier des charges.

---

## ⚠️ Prérequis

Vous avez besoin de **Docker** et **Docker Compose** installés sur votre machine, avec un accès
Internet (pour télécharger PostgreSQL, les dépendances Python et les paquets npm au premier
démarrage).

---

## 🚀 Démarrage rapide

```bash
# 1. Cloner / copier le projet, puis se placer à la racine (dossier contenant docker-compose.yml)

# 2. Copier le fichier d'environnement backend
cp server/.env.example server/.env

# 3. (optionnel) copier le fichier d'environnement frontend
cp client/.env.example client/.env

# 4. Démarrer toute la stack (PostgreSQL + API + interface web)
docker compose up --build
```

Cela démarre :
- **PostgreSQL** sur le port `5432`
- **API SIGMA** (FastAPI) sur `http://localhost:8000` — documentation interactive sur
  `http://localhost:8000/docs`
- **Interface web** (React) sur `http://localhost:5173`

## 🌱 Initialiser la base de données (première fois uniquement)

Une fois les conteneurs démarrés, dans un **autre terminal** :

```bash
docker compose exec server python -m app.seed
```

Ce script :
1. Crée toutes les tables.
2. Insère le catalogue complet des permissions.
3. Crée une Organisation + École + Année scolaire 2026/2027 (avec 3 trimestres) par défaut.
4. Crée un compte **administrateur système** :
   - Email : `admin@sigma.local`
   - Mot de passe : `Admin123!`
   - ⚠️ À changer immédiatement en production (modifiable dans `server/.env` avant le premier
     lancement du seed, ou depuis l'écran Utilisateurs ensuite).
5. Crée des données de démonstration illustrant le moteur RBAC/Scopes : un niveau "3e" avec
   deux classes (3e A / 3e B), une matière "Mathématiques", un poste "Enseignant (démo)"
   limité à la saisie des notes de Mathématiques en 3e A uniquement, et un poste
   "Comptable (démo)" avec accès complet au module Finance.

Connectez-vous ensuite sur `http://localhost:5173` avec le compte administrateur.

---

## 💿 Compiler en installateur Windows (Setup_SIGMA.exe)

SIGMA peut être compilé en un installateur Windows unique — serveur + PostgreSQL embarqué +
frontend, enregistré comme service Windows au démarrage automatique — conformément à la
vision du cahier des charges (§22, §29). Voir **`deployment/README.md`** pour le détail complet
(compilation automatique via GitHub Actions, ou compilation locale sur une machine Windows).

## 🏗️ Architecture du dépôt

```
sigma/
├── docker-compose.yml
├── .github/workflows/build-windows-installer.yml  # Compilation auto en Setup_SIGMA.exe
├── deployment/                 # Packaging Windows (voir deployment/README.md)
│   ├── pyinstaller/            # launcher.py + spec PyInstaller
│   └── inno-setup/             # Script installateur (installer.iss)
├── server/                    # API FastAPI
│   ├── app/
│   │   ├── main.py            # Point d'entrée FastAPI
│   │   ├── config.py          # Configuration (.env)
│   │   ├── database.py        # Connexion SQLAlchemy
│   │   ├── seed.py            # Amorçage de la base
│   │   ├── models/            # Modèles SQLAlchemy (une table = un fichier logique)
│   │   ├── schemas/           # Schémas Pydantic (entrée/sortie API)
│   │   ├── core/
│   │   │   ├── authorization.py   # ⭐ MOTEUR RBAC/SCOPES (le cœur du système)
│   │   │   ├── security.py        # JWT + hachage de mots de passe
│   │   │   ├── deps.py            # Dépendances FastAPI (current_user, require_permission)
│   │   │   ├── audit.py           # Aide à l'écriture du journal d'audit
│   │   │   └── permissions_catalog.py  # Catalogue des permissions du système
│   │   └── api/routers/       # Un routeur par module métier
│   ├── alembic/                # Migrations de base de données (cf plus bas)
│   └── requirements.txt
└── client/                     # Interface web React + TypeScript
    └── src/
        ├── api/client.ts       # Client Axios (injection du JWT)
        ├── context/AuthContext.tsx
        ├── hooks/useScopeOptions.ts
        ├── pages/
        │   ├── admin/          # Postes & permissions, utilisateurs, délégations, audit
        │   ├── academic/       # Classes, matières, évaluations, notes
        │   ├── students/       # Dossier élève
        │   └── finance/        # Paiements & reçus
        └── App.tsx
```

## 🧠 Le moteur RBAC/Scopes (le point le plus important)

C'est l'implémentation directe de la **règle d'or** du cahier des charges (§55) :

> Les fonctionnalités doivent être séparées de l'autorisation d'y accéder.

Concrètement (`server/app/core/authorization.py`) :

- Le développeur code des **Permissions** fixes (`grades.enter`, `finance.record_payment`, …).
- L'établissement crée des **Postes** entièrement configurables (ex: "Censeur", "Comptable")
  depuis l'écran **Postes & permissions** — sans jamais toucher au code.
- Chaque association Poste ↔ Permission peut être restreinte par un ou plusieurs
  **Périmètres** : campus, niveau, série, classe, matière, période, ou "ses propres dossiers".
  - Plusieurs périmètres du même type = **OU** (ex: 3e A **ou** 3e B).
  - Des périmètres de types différents = **ET** (ex: classe 3e A **et** matière Mathématiques).
  - Aucun périmètre = portée sur tout l'établissement.
- Les **Délégations temporaires** (§13) fonctionnent comme un Poste ponctuel qui expire
  automatiquement à la date de fin, sans job planifié : la vérification se fait à chaque requête.

Chaque routeur sensible appelle soit la dépendance simple `require_permission(code)` (portée
établissement), soit directement `user_has_permission(db, user, code, ScopeContext(...))` quand
le périmètre dépend de la ressource ciblée (c'est le cas du module Notes : voir
`server/app/api/routers/assessments.py`).

## 📝 Migrations de base de données

Pour la première installation, `python -m app.seed` suffit (il crée les tables via
`Base.metadata.create_all`). Pour un usage en production avec un historique de migrations
propre, générez la première révision Alembic avant de lancer le seed :

```bash
docker compose exec server alembic revision --autogenerate -m "initial schema"
docker compose exec server alembic upgrade head
docker compose exec server python -m app.seed   # sans recréer les tables si déjà migrées
```

## 🔜 Ce qui n'est pas encore implémenté (prochaines étapes suggérées)

Conformément au découpage MVP → V1 → V2 du cahier des charges (§52-54), le cœur des Blocs 1
à 7 est maintenant couvert. Reste notamment :
- Branchement réel des canaux SMS/Email/Push (le modèle `Announcement` est prêt, il manque
  l'intégration d'un fournisseur comme Twilio ou un serveur SMTP)
- Portails dédiés Parent/Enseignant/Élève en lecture seule (les données existent déjà via
  l'API ; il s'agit surtout d'écrans front simplifiés et d'un contrôle de périmètre par
  défaut adapté à ces profils)
- Mode offline réel + synchronisation Cloud (§41-42) — l'architecture le permet (base
  PostgreSQL locale par établissement) mais le moteur de synchronisation n'est pas écrit
- Multi-établissements/multi-campus dans l'interface (le modèle de données le supporte déjà :
  `Organization` → `School` → `Campus`, mais l'UI suppose un seul établissement par connexion)
- Intégration Mobile Money réelle pour les paiements (le champ `PaymentMethod.MOBILE_MONEY`
  existe déjà, il manque le webhook du fournisseur)
- Tests automatisés (aucun test n'a pu être exécuté dans l'environnement de génération de ce
  code, faute d'accès réseau pour installer les dépendances — voir note ci-dessous)
- Progression réelle dans le calcul des tableaux d'honneur (actuellement fixée à 0 faute de
  comparaison avec la période précédente — cf `app/core/honor_board_engine.py`)

---

## Note sur la validation de ce code

Ce projet a été écrit dans un environnement sans accès aux registres de paquets (PyPI/npm),
qui n'a donc pas pu exécuter `pip install` / `npm install` ni lancer le serveur ou les tests
en conditions réelles. Chaque fichier Python a été vérifié syntaxiquement (`python -m py_compile`)
et l'ensemble a été relu avec soin, mais je vous recommande de :
1. Lancer `docker compose up --build` et vérifier que les trois services démarrent sans erreur.
2. Tester le scénario de démonstration créé par le seed (connexion admin, puis création d'un
   utilisateur avec le poste "Enseignant (démo)" pour vérifier qu'il ne voit bien que 3e A).
3. Me signaler toute erreur d'exécution rencontrée — je pourrai la corriger immédiatement.
