# SIGMA — Compilation en exécutable Windows (Setup_SIGMA.exe)

Ce dossier contient tout ce qu'il faut pour transformer SIGMA en un installateur Windows
unique, conformément à la vision du cahier des charges (§22 — service système sans fenêtre
CMD, §29 — `Setup_SIGMA.exe` en une seule commande).

## Vue d'ensemble du pipeline

```
client/ (React)  ──npm run build──▶  client/dist/  ─┐
                                                       │
server/ (FastAPI) ──PyInstaller──▶  dist/SigmaServer/ ─┼──▶  dist_staging/  ──Inno Setup──▶  Setup_SIGMA.exe
                                                       │
PostgreSQL portable (téléchargé)  ────────────────────┤
NSSM (téléchargé)                 ────────────────────┘
```

- **`launcher.py`** : remplace `uvicorn app.main:app` en développement. C'est lui qui devient
  `SigmaServer.exe`. Il initialise PostgreSQL au premier lancement, le démarre, prépare le
  schéma de base de données, puis lance le serveur API (qui sert aussi le frontend compilé).
- **`sigma-server.spec`** : configuration PyInstaller qui fige `launcher.py` + tout le backend
  Python en un exécutable autonome (aucune installation de Python requise sur la machine cible).
- **`installer.iss`** : script Inno Setup qui assemble tout (exécutable + PostgreSQL portable +
  frontend + NSSM) en un seul `Setup_SIGMA.exe`, et enregistre SIGMA comme service Windows.

## Option A — Compilation automatique (recommandée)

Le workflow `.github/workflows/build-windows-installer.yml` fait tout automatiquement sur un
runner Windows gratuit de GitHub Actions :

1. Poussez ce dépôt sur GitHub.
2. Le build se déclenche automatiquement sur chaque push vers `main`, ou manuellement depuis
   l'onglet **Actions** → **Build SIGMA Windows Installer** → **Run workflow**.
3. Une fois terminé (~10-15 minutes), téléchargez `Setup_SIGMA.exe` depuis l'onglet **Actions**
   → le run correspondant → section **Artifacts**.
4. Pour une vraie publication versionnée, poussez un tag (`git tag v1.0.0 && git push --tags`) :
   une **Release GitHub** est créée automatiquement avec `Setup_SIGMA.exe` joint.

⚠️ Le workflow télécharge PostgreSQL portable depuis une URL versionnée d'EnterpriseDB
(`PG_ZIP_URL` en haut du fichier workflow). Si ce lien casse (erreur 404 dans les logs du job),
récupérez le lien à jour sur https://www.enterprisedb.com/download-postgresql-binaries et
mettez à jour la variable.

## Option B — Compilation locale sur une machine Windows

Si vous préférez compiler vous-même (ou tester avant de pousser sur GitHub) :

```powershell
# 1. Frontend
cd client
npm install
npm run build
cd ..

# 2. Backend → exécutable
cd server
pip install -r requirements.txt
pip install pyinstaller
cd ..
pyinstaller deployment\pyinstaller\sigma-server.spec --distpath dist --workpath build --noconfirm

# 3. Télécharger PostgreSQL portable (binaires zip, PAS l'installeur .exe classique)
#    depuis https://www.enterprisedb.com/download-postgresql-binaries
#    Décompressez-le pour obtenir un dossier "pgsql\"

# 4. Télécharger NSSM depuis https://nssm.cc/download, extrayez nssm.exe (dossier win64)

# 5. Assembler le dossier de staging
mkdir deployment\inno-setup\dist_staging
xcopy /E /I dist\SigmaServer\* deployment\inno-setup\dist_staging\
xcopy /E /I <chemin_vers>\pgsql deployment\inno-setup\dist_staging\pgsql
mkdir deployment\inno-setup\dist_staging\webapp
xcopy /E /I client\dist\* deployment\inno-setup\dist_staging\webapp\
copy <chemin_vers>\nssm.exe deployment\inno-setup\dist_staging\nssm.exe

# 6. Installer Inno Setup (https://jrsoftware.org/isdl.php), puis compiler :
cd deployment\inno-setup
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss

# → Setup_SIGMA.exe apparaît dans deployment\inno-setup\Output\
```

## Ce qui se passe à l'installation

1. `Setup_SIGMA.exe` copie les fichiers dans `C:\Program Files\SIGMA`.
2. Il enregistre `SigmaServer.exe` comme service Windows (`SIGMAServer`, démarrage
   automatique) via NSSM.
3. Au premier démarrage du service, `launcher.py` :
   - initialise une base PostgreSQL locale (dossier `C:\ProgramData\SIGMA\pgdata`), avec un
     mot de passe généré aléatoirement, accessible **uniquement en local** (`127.0.0.1`,
     jamais exposé sur le réseau de l'établissement — seul le serveur SIGMA y accède) ;
   - génère un fichier de configuration (`C:\ProgramData\SIGMA\.env`) avec une clé secrète
     aléatoire et affiche/enregistre les identifiants du compte administrateur initial dans
     les journaux (`C:\ProgramData\SIGMA\logs\`) ;
   - crée le schéma de base de données et le catalogue de permissions.
4. Le navigateur s'ouvre automatiquement sur `http://localhost:8000`.
5. Aux démarrages suivants (y compris après redémarrage de Windows), le service redémarre
   automatiquement — aucune fenêtre CMD n'apparaît (cf §22).

## Désinstallation

Le désinstalleur arrête et retire le service, puis supprime les fichiers du programme.
**Les données** (base de données, identifiants, journaux) dans `C:\ProgramData\SIGMA` ne sont
**jamais supprimées automatiquement**, pour éviter toute perte accidentelle de dossiers
d'élèves ou de paiements. Supprimez ce dossier manuellement si vous êtes certain de ne plus en
avoir besoin (après avoir vérifié vos sauvegardes).

## Limites connues de cette première version du packaging

- Un seul établissement par installation (pas de sélection multi-instance à l'installation).
- Pas encore de mécanisme de sauvegarde automatique programmée depuis l'installateur lui-même
  (cf §26 du cahier des charges — `pg_dump` peut être planifié manuellement via le Planificateur
  de tâches Windows en ciblant `pgsql\bin\pg_dump.exe`, en attendant une intégration native).
- Le port HTTP (8000) et le port PostgreSQL interne (5433) sont fixes ; en cas de conflit avec
  un autre logiciel, ils ne sont pas encore configurables depuis l'installateur.
- Cette chaîne de compilation n'a pas pu être testée de bout en bout dans l'environnement où ce
  code a été écrit (pas de machine Windows disponible). Voir la note de validation à la racine
  du dépôt.
