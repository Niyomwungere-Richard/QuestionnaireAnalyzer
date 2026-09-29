@echo off
setlocal
REM ============================================================
REM  Construction de l'executable Windows - ETAPE 15
REM  (ETAPE 17 : utilise l'environnement virtuel venv\)
REM
REM  Utilisation :
REM      build.bat
REM
REM  Resultat :
REM      dist\AnalyseurQuestionnaire.exe
REM ============================================================

cd /d "%~dp0"

echo.
echo ============================================================
echo   CONSTRUCTION DE L'EXECUTABLE WINDOWS
echo ============================================================
echo.

REM ------------------------------------------------------------
REM ETAPE 17 : on utilise l'environnement virtuel du projet s'il
REM existe (venv\), sinon on retombe sur Python global.
REM ------------------------------------------------------------
set "PYTHON=%~dp0venv\Scripts\python.exe"
if exist "%PYTHON%" goto :python_trouve

echo [INFO] venv\ introuvable -> utilisation du Python global.
echo        Lancez setup.bat pour creer l'environnement virtuel.
set "PYTHON=python"

:python_trouve
echo [INFO] Python utilise : %PYTHON%
echo.

REM Verifier PyInstaller
"%PYTHON%" -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] PyInstaller n'est pas installe.
    echo          Lancez : setup.bat
    echo          ou      : pip install pyinstaller
    pause
    exit /b 1
)

echo [1/3] Nettoyage des builds precedents...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo [2/3] Construction de l'exe (peut durer 1-3 minutes)...
"%PYTHON%" -m PyInstaller --noconfirm AnalyseurQuestionnaire.spec
if errorlevel 1 (
    echo.
    echo [ERREUR] La construction a echoue.
    pause
    exit /b 1
)

echo [3/3] Verification du resultat...
if not exist dist\AnalyseurQuestionnaire.exe (
    echo [ERREUR] L'executable n'a pas ete genere.
    pause
    exit /b 1
)

for %%A in (dist\AnalyseurQuestionnaire.exe) do set TAILLE=%%~zA
echo.
echo ============================================================
echo   SUCCES
echo ============================================================
echo   Fichier : dist\AnalyseurQuestionnaire.exe
echo   Taille  : %TAILLE% octets
echo.
echo   POUR DEPLOYER SUR UN AUTRE POSTE :
echo     1. Copier AnalyseurQuestionnaire.exe
echo     2. Sur le SERVEUR : ajouter le fichier .env (cle API)
echo     3. Double-cliquer pour lancer
echo ============================================================
echo.
pause
