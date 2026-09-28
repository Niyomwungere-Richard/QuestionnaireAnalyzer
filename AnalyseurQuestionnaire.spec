# -*- mode: python ; coding: utf-8 -*-
"""
Fichier de construction PyInstaller - ETAPE 15.

Genere un EXE AUTONOME Windows a partir de main.py.

    pyinstaller AnalyseurQuestionnaire.spec

Parametres reglables ci-dessous :
    CONSOLE = True   -> une fenetre noire affiche les logs (utile
                        pour deboguer et voir travailler le serveur)
    CONSOLE = False  -> ONLY l'interface graphique (rendu plus propre)

IMPORTANT - Ce qui N'EST PAS embarque dans l'exe :
    - .env (cle API)  : a placer A COTE du .exe sur le serveur
    - config.json     : cree automatiquement au premier lancement
    - documents/      : crees automatiquement (preparer_dossiers)
    - reports/        : crees automatiquement
"""

import sys

# ============================================================
# REGLAGES
# ============================================================

# True  = fenetre console visible (logs serveur)
# False = interface graphique seule
CONSOLE = True

# Nom de l'executable genere
NOM_EXE = "AnalyseurQuestionnaire"

# Fichier d'entree
ENTREE = "main.py"


# ============================================================
# CONSTRUCTION (ne pas modifier ci-dessous)
# ============================================================

block_cipher = None

# Modules a exclure pour reduire la taille
EXCLUS = [
    # Modules de test (inutiles dans l'exe)
    "test_analysis",
    "test_ai_analysis",
    "test_documents",
    "test_env",
    "test_file_transfer",
    "test_grok",
    "test_integration",
    "test_multi_clients",
    "test_report",
    # Modules de dev rarement necessaires
    "tkinter.test",
    "unittest",
    "pydoc",
    "doctest",
]

# Fichiers de donnees a embarquer (aucun obligatoire :
# documents/ et reports/ sont crees au lancement)
DONNEES = []

analyse = Analysis(
    [ENTREE],
    pathex=[],
    binaries=[],
    datas=DONNEES,
    hiddenimports=[
        # Certains paquets necessitent un coup de pouce
        "tkinter",
        "tkinter.filedialog",
        "tkinter.messagebox",
        "tkinter.ttk",
        "PIL.Image",
        "PIL.ImageTk",
        "dotenv",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=EXCLUS,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(analyse.pure, analyse.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    analyse.scripts,
    analyse.binaries,
    analyse.zipfiles,
    analyse.datas,
    [],
    name=NOM_EXE,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=CONSOLE,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
