# -*- mode: python ; coding: utf-8 -*-
"""
Fichier de construction PyInstaller - ETAPE 16 (installateur).

Genere "Installateur.exe" qui contient le programme lui-meme :
double-cliquer sur Installateur.exe installe l'application.

    1. Construire d'abord le programme :
         python -m PyInstaller --noconfirm AnalyseurQuestionnaire.spec
    2. Puis l'installateur :
         python -m PyInstaller --noconfirm Installateur.spec

RESULTAT : dist/Installateur.exe  (~55 Mo, autonome)

Le programme (AnalyseurQuestionnaire.exe) est embarque en tant que
DONNEE ; l'installateur le copie dans le dossier choisi.
"""

import os

NOM_EXE = "Installateur"
ENTREE = "installateur.py"

# Le programme a installer DOIT deja etre construit
PROGRAMME = os.path.join("dist", "AnalyseurQuestionnaire.exe")

if not os.path.exists(PROGRAMME):
    raise SystemExit(
        "ERREUR : introuvable {0}\n"
        "Construisez d'abord le programme :\n"
        "    python -m PyInstaller --noconfirm "
        "AnalyseurQuestionnaire.spec".format(PROGRAMME)
    )

block_cipher = None

EXCLUS = [
    "tkinter.test",
    "unittest",
    "pydoc",
    "doctest",
]

# Le programme est embarque comme donnee, extrait dans _MEIPASS
DONNEES = [(PROGRAMME, ".")]

# Le fichier .env (cle API) est embarque s'il existe AU MOMENT de la
# construction : l'installation le copiera automatiquement a cote du
# programme, sans le redemander a chaque installation ni a chaque
# demarrage.
# ATTENTION SECURITE : la cle se retrouve DANS Installateur.exe.
# Ne diffusez cet installateur qu'aux machines de confiance.
FICHIER_ENV = ".env"
if os.path.exists(FICHIER_ENV):
    DONNEES.append((FICHIER_ENV, "."))
    print("  + .env embarque dans l'installateur")
else:
    print("  AVERTISSEMENT : .env absent, il faudra le fournir "
          "manuellement (option --env= ou bouton Choisir...).")

analyse = Analysis(
    [ENTREE],
    pathex=[],
    binaries=[],
    datas=DONNEES,
    hiddenimports=[
        "tkinter",
        "tkinter.filedialog",
        "tkinter.messagebox",
        "tkinter.ttk",
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
    # L'installateur n'a PAS besoin de console
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
