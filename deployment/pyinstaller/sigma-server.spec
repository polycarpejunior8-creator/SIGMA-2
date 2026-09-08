# -*- mode: python ; coding: utf-8 -*-
import os

SERVER_DIR = os.path.join(SPECPATH, "..", "..", "server")
LAUNCHER_SCRIPT = os.path.join(SPECPATH, "launcher.py")

block_cipher = None

a = Analysis(
    [LAUNCHER_SCRIPT],
    pathex=[SERVER_DIR],
    binaries=[],
    datas=[],
    hiddenimports=[
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        "passlib.handlers.bcrypt",
        "jose.backends.cryptography_backend",
        "psycopg2",
        "email_validator",
        "dotenv",
        "app.main",
        "app.seed",
        "app.models",
        "app.api.routers.auth",
        "app.api.routers.organizations",
        "app.api.routers.users",
        "app.api.routers.posts",
        "app.api.routers.delegations",
        "app.api.routers.audit",
        "app.api.routers.academic_structure",
        "app.api.routers.students",
        "app.api.routers.assessments",
        "app.api.routers.finance",
        "app.api.routers.dashboard",
        "app.api.routers.attendance",
        "app.api.routers.honor_boards",
        "app.api.routers.timetable",
        "app.api.routers.hr",
        "app.api.routers.communication",
        "app.api.routers.report_cards",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="SigmaServer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="SigmaServer",
)
