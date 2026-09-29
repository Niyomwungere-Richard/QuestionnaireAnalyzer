@echo off
setlocal enabledelayedexpansion
REM ============================================================
REM  Creation de l'ENVIRONNEMENT VIRTUEL du projet - ETAPE 17
REM
REM  Utilisation :
REM      setup.bat
REM
REM  Resultat :
REM      venv\Scripts\python.exe   Python ISOLE de ce projet
REM      + toutes les dependances de requirements.txt
REM
REM  Pourquoi un environnement virtuel ?
REM      - les paquets du projet ne melangent pas avec les autres
REM      - le projet est reproductible sur une autre machine
REM      - une mise a jour globale ne peut pas casser le projet
REM
REM  Apres : utilisez  venv\Scripts\python  au lieu de  python
REM           (build.bat le fait deja automatiquement)
REM ============================================================

cd /d "%~dp0"

echo.
echo ============================================================
echo   CREATION DE L'ENVIRONNEMENT VIRTUEL
echo ============================================================
echo.

REM --- 1. Localiser Python -------------------------------------
set "PYTHON="

python --version >nul 2>&1
if not errorlevel 1 set "PYTHON=python"

if not defined PYTHON (
    py -3 --version >nul 2>&1
    if not errorlevel 1 set "PYTHON=py -3"
)

if not defined PYTHON (
    echo [ERREUR] Python 3 introuvable dans le PATH.
    echo.
    echo          1. Installez Python 3.10 ou superieur
    echo             https://www.python.org/downloads/
    echo          2. Cochez "Add python.exe to PATH"
    echo          3. Relancez setup.bat
    echo.
    pause
    exit /b 1
)

echo [1/4] Python trouve : 
for /f "delims=" %%i in ('%PYTHON% --version') do echo        %%i

REM --- 2. Creer le venv ----------------------------------------
if exist "venv\Scripts\python.exe" goto :venv_existe
echo [2/4] Creation de venv\ - une trentaine de secondes...
%PYTHON% -m venv venv
if not exist "venv\Scripts\python.exe" (
    echo.
    echo [ERREUR] La creation de l'environnement a echoue.
    pause
    exit /b 1
)
goto :venv_ok

:venv_existe
echo [2/4] Environnement virtuel deja present : venv\

:venv_ok
set "VPY=%~dp0venv\Scripts\python.exe"

REM --- 3. Installer les dependances ----------------------------
echo [3/4] Installation des dependances (requirements.txt)...
"%VPY%" -m pip install --upgrade pip >nul 2>&1
"%VPY%" -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [ERREUR] L'installation des dependances a echoue.
    pause
    exit /b 1
)

REM --- 4. Verification ----------------------------------------
echo.
echo [4/4] Verification des modules...
set "OK=1"
for %%M in (fitz docx openai dotenv reportlab PIL) do (
    "%VPY%" -c "import %%M" >nul 2>&1
    if errorlevel 1 (
        echo        [MANQUANT] %%M
        set "OK=0"
    ) else (
        echo        [OK] %%M
    )
)

if "%OK%"=="0" (
    echo.
    echo [ERREUR] Certains modules sont manquants.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   SUCCES
echo ============================================================
echo   Environnement : %~dp0venv
echo   Python isole  : venv\Scripts\python.exe
echo.
echo   UTILISER LE PROJET :
echo       venv\Scripts\python.exe main.py
echo       venv\Scripts\python.exe test_integration.py
echo.
echo   CONSTRUIRE LES EXE (utilise deja le venv) :
echo       build.bat
echo       build_installer.bat
echo ============================================================
echo.
pause
