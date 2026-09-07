"""
SIGMA SERVER — point d'entrée de l'API.

Démarrage (développement) :
    uvicorn app.main:app --host 0.0.0.0 --port 8000

En production (exécutable autonome), voir deployment/pyinstaller/launcher.py qui
définit SIGMA_WEBAPP_DIR pour servir le frontend compilé directement depuis ce serveur,
sans dépendance à Node.js sur la machine cible.
"""
import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.api.routers import (
    auth, organizations, users, posts, delegations, audit,
    academic_structure, students, assessments, finance, dashboard,
    attendance, honor_boards, timetable, hr, communication, report_cards,
)

app = FastAPI(
    title="SIGMA — Système Intégré de Gestion et Management Académique",
    description="API centrale du serveur SIGMA (cf cahier des charges v2.0).",
    version="0.1.0-mvp",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(organizations.router)
app.include_router(users.router)
app.include_router(posts.router)
app.include_router(delegations.router)
app.include_router(audit.router)
app.include_router(academic_structure.router)
app.include_router(students.router)
app.include_router(assessments.router)
app.include_router(finance.router)
app.include_router(dashboard.router)
app.include_router(attendance.router)
app.include_router(honor_boards.router)
app.include_router(timetable.router)
app.include_router(hr.router)
app.include_router(communication.router)
app.include_router(report_cards.router)


@app.get("/api/health", tags=["Santé"])
def health_check():
    return {"status": "ok", "service": "SIGMA Server"}


# ---------------------------------------------------------------------------
# Frontend statique (build React) — utilisé uniquement quand SIGMA_WEBAPP_DIR
# pointe vers un dossier existant (cas de l'exécutable autonome packagé avec
# PyInstaller). En développement avec `npm run dev`, cette variable n'est pas
# définie et le frontend est servi séparément par Vite : ce bloc est ignoré.
# ---------------------------------------------------------------------------
_webapp_dir = os.environ.get("SIGMA_WEBAPP_DIR")
if _webapp_dir and Path(_webapp_dir).is_dir():
    webapp_path = Path(_webapp_dir)
    assets_path = webapp_path / "assets"

    if assets_path.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets_path)), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_spa(full_path: str, request: Request):
        """
        Sert index.html pour toute route non-API, pour que le routage côté
        client (React Router) fonctionne même en accès direct par URL
        (ex: rechargement de page sur /students/123).
        """
        if full_path.startswith("api/"):
            return {"detail": "Not Found"}, 404

        candidate = webapp_path / full_path
        if full_path and candidate.is_file():
            return FileResponse(str(candidate))

        index_file = webapp_path / "index.html"
        return FileResponse(str(index_file))
