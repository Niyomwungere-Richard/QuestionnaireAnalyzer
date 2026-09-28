@echo off
REM ============================================================
REM  Construction de l'executable Windows - ETAPE 15
REM
REM  Utilisation :
REM      build.bat
REM
REM  Resultat :
REM      dist\AnalyseurQuestionnaire.exe
REM ============================================================

echo.
echo ============================================================
echo   CONSTRUCTION DE L'EXECUTABLE WINDOWS
echo ============================================================
echo.

REM Python utilise par le projet
set PYTHON=C:\Users\ZEBRA\AppData\Local\Programs\Python\Python314\python.exe

REM Verifier PyInstaller
"%PYTHON%" -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] PyInstaller n'est pas installe.
    echo          Lancez : pip install pyinstaller
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
