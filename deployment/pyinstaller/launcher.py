"""
SIGMA SERVER — lanceur autonome (utilisé pour produire SigmaServer.exe via PyInstaller).

Rôle de ce script (cf cahier des charges §22 — "le serveur ne doit pas nécessiter
l'ouverture d'une fenêtre CMD" et §29 — installation en un clic) :

  1. Au premier démarrage : initialise une instance PostgreSQL embarquée locale
     (dossier de données sous %ProgramData%\\SIGMA), avec un mot de passe et une
     clé secrète générés aléatoirement.
  2. À chaque démarrage : lance PostgreSQL (écoute uniquement sur 127.0.0.1 —
     inaccessible depuis le réseau, seul le serveur SIGMA lui-même y accède,
     conformément à la règle "les clients ne parlent jamais directement à la
     base" cf §55 du document d'architecture).
  3. Crée/complète le schéma de base de données et le catalogue de permissions
     (idempotent, cf app/seed.py).
  4. Démarre le serveur API + sert le frontend compilé (cf app/main.py).
  5. À l'arrêt (service Windows stoppé via NSSM), arrête proprement PostgreSQL.

Ce fichier est le point d'entrée déclaré dans sigma-server.spec (PyInstaller).
Il n'est PAS destiné à être exécuté directement en développement : utilisez
`uvicorn app.main:app --reload` pour ça (voir README.md).
"""
import os
import secrets
import signal
import subprocess
import sys
import time
from pathlib import Path


def _app_dir() -> Path:
    """Dossier contenant l'exécutable (ou ce script, en mode non-figé)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


APP_DIR = _app_dir()
PG_BIN_DIR = APP_DIR / "pgsql" / "bin"
WEBAPP_DIR = APP_DIR / "webapp"

DATA_ROOT = Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData")) / "SIGMA"
PG_DATA_DIR = DATA_ROOT / "pgdata"
PG_LOG_FILE = DATA_ROOT / "logs" / "postgres.log"
SERVER_LOG_FILE = DATA_ROOT / "logs" / "server.log"
ENV_FILE = DATA_ROOT / ".env"

PG_PORT = 5433          # port dédié, différent du port Postgres par défaut (5432)
PG_SUPERUSER = "sigma"
HTTP_PORT = int(os.environ.get("SIGMA_HTTP_PORT", "8000"))

_pg_process: subprocess.Popen | None = None


def log(message: str) -> None:
    line = f"[SIGMA Launcher] {message}"
    print(line, flush=True)


def _run(args: list[str], **kwargs) -> subprocess.CompletedProcess:
    log("→ " + " ".join(str(a) for a in args))
    return subprocess.run(args, check=True, **kwargs)


def ensure_directories() -> None:
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    (DATA_ROOT / "logs").mkdir(parents=True, exist_ok=True)


def is_first_run() -> bool:
    return not (PG_DATA_DIR / "PG_VERSION").exists()


def generate_env_file(pg_password: str) -> None:
    secret_key = secrets.token_hex(32)
    admin_password = secrets.token_urlsafe(12)

    content = f"""# Généré automatiquement au premier démarrage de SIGMA — ne pas partager.
DATABASE_URL=postgresql+psycopg2://{PG_SUPERUSER}:{pg_password}@127.0.0.1:{PG_PORT}/sigma
SECRET_KEY={secret_key}
ACCESS_TOKEN_EXPIRE_MINUTES=480
CORS_ORIGINS=http://localhost:{HTTP_PORT}
SEED_ORG_NAME=Mon Établissement
SEED_ADMIN_EMAIL=admin@sigma.local
SEED_ADMIN_PASSWORD={admin_password}
"""
    ENV_FILE.write_text(content, encoding="utf-8")
    log(f"Fichier de configuration créé : {ENV_FILE}")
    log("=" * 70)
    log("IDENTIFIANTS DE PREMIÈRE CONNEXION (à changer immédiatement) :")
    log(f"  URL      : http://localhost:{HTTP_PORT}")
    log(f"  Email    : admin@sigma.local")
    log(f"  Mot de passe : {admin_password}")
    log("Ces identifiants sont aussi enregistrés dans :")
    log(f"  {ENV_FILE}")
    log("=" * 70)


def initialize_postgres() -> str:
    """Initialise un nouveau cluster PostgreSQL. Retourne le mot de passe généré."""
    log("Premier démarrage détecté : initialisation de PostgreSQL…")
    PG_DATA_DIR.parent.mkdir(parents=True, exist_ok=True)

    pg_password = secrets.token_urlsafe(24)
    pwfile = DATA_ROOT / "_pwfile.tmp"
    pwfile.write_text(pg_password, encoding="utf-8")

    try:
        _run([
            str(PG_BIN_DIR / "initdb.exe"),
            "-D", str(PG_DATA_DIR),
            "-U", PG_SUPERUSER,
            "-A", "password",
            "--pwfile", str(pwfile),
            "-E", "UTF8",
            "--locale=C",
        ])
    finally:
        pwfile.unlink(missing_ok=True)

    # Écoute UNIQUEMENT sur 127.0.0.1 : jamais exposé au réseau local (cf §55).
    conf_path = PG_DATA_DIR / "postgresql.conf"
    with open(conf_path, "a", encoding="utf-8") as f:
        f.write(f"\nlisten_addresses = '127.0.0.1'\nport = {PG_PORT}\n")

    generate_env_file(pg_password)

    # Démarre temporairement pour créer la base "sigma", puis on relance normalement.
    _start_postgres_process()
    wait_for_postgres_ready()
    _run([
        str(PG_BIN_DIR / "createdb.exe"),
        "-h", "127.0.0.1", "-p", str(PG_PORT), "-U", PG_SUPERUSER, "sigma",
    ], env={**os.environ, "PGPASSWORD": pg_password})
    stop_postgres()

    return pg_password


def _start_postgres_process() -> None:
    global _pg_process
    log("Démarrage de PostgreSQL (127.0.0.1:%d)…" % PG_PORT)
    _pg_process = subprocess.Popen([
        str(PG_BIN_DIR / "pg_ctl.exe"),
        "start",
        "-D", str(PG_DATA_DIR),
        "-l", str(PG_LOG_FILE),
        "-w",  # attend que le serveur soit prêt avant de rendre la main
        "-t", "60",
    ])
    _pg_process.wait()


def wait_for_postgres_ready(timeout_seconds: int = 30) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        result = subprocess.run(
            [str(PG_BIN_DIR / "pg_isready.exe"), "-h", "127.0.0.1", "-p", str(PG_PORT)],
            capture_output=True,
        )
        if result.returncode == 0:
            return
        time.sleep(1)
    raise RuntimeError("PostgreSQL n'a pas démarré à temps.")


def stop_postgres() -> None:
    log("Arrêt de PostgreSQL…")
    subprocess.run([
        str(PG_BIN_DIR / "pg_ctl.exe"), "stop", "-D", str(PG_DATA_DIR), "-m", "fast",
    ])


def handle_shutdown(signum, frame):
    log(f"Signal d'arrêt reçu ({signum}) — arrêt propre en cours…")
    stop_postgres()
    sys.exit(0)


def main() -> None:
    ensure_directories()

    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
    if hasattr(signal, "SIGBREAK"):
        signal.signal(signal.SIGBREAK, handle_shutdown)  # CTRL_BREAK envoyé par NSSM sous Windows

    first_run = is_first_run()

    if first_run:
        initialize_postgres()

    _start_postgres_process()

    try:
        wait_for_postgres_ready()
    except RuntimeError:
        log("ERREUR : PostgreSQL n'a pas pu démarrer. Consultez " + str(PG_LOG_FILE))
        sys.exit(1)

    # Charge la configuration (.env) générée lors de l'initialisation, puis
    # importe l'application seulement APRÈS avoir positionné les variables
    # d'environnement (app.config les lit au moment de l'import).
    from dotenv import load_dotenv
    load_dotenv(ENV_FILE)
    os.environ["SIGMA_WEBAPP_DIR"] = str(WEBAPP_DIR)

    log("Initialisation du schéma de base de données et du catalogue de permissions…")
    try:
        from app import seed
        seed.main()
    except Exception as exc:  # noqa: BLE001
        log(f"ERREUR lors de l'initialisation de la base : {exc}")
        stop_postgres()
        sys.exit(1)

    log(f"Démarrage du serveur SIGMA sur http://0.0.0.0:{HTTP_PORT} …")
    import uvicorn
    try:
        uvicorn.run("app.main:app", host="0.0.0.0", port=HTTP_PORT, log_level="info")
    finally:
        stop_postgres()


if __name__ == "__main__":
    main()
