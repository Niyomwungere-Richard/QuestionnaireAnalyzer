@echo off
REM ============================================================
REM  Construction de l'INSTALLATEUR Windows - ETAPE 16
REM
REM  Utilisation :
REM      build_installer.bat
REM
REM  Resultat :
REM      dist\AnalyseurQuestionnaire.exe   (le programme)
REM      dist\Installateur.exe             (l'installateur)
REM ============================================================

echo.
echo ============================================================
echo   CONSTRUCTION DE L'INSTALLATEUR WINDOWS
echo ============================================================
echo.

set "PYTHON=%~dp0venv\Scripts\python.exe"
if exist "%PYTHON%" goto :python_trouve

echo [INFO] venv\ introuvable -> utilisation du Python global.
set "PYTHON=python"

:python_trouve
echo [INFO] Python utilise : %PYTHON%
echo.

"%PYTHON%" -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] PyInstaller n'est pas installe.
    echo          Lancez : setup.bat
    pause
    exit /b 1
)

REM --- 1. Le programme doit exister ---
if not exist dist\AnalyseurQuestionnaire.exe (
    echo [1/3] Programme absent - construction...
    "%PYTHON%" -m PyInstaller --noconfirm AnalyseurQuestionnaire.spec
    if errorlevel 1 (
        echo [ERREUR] Construction du programme echouee.
        pause
        exit /b 1
    )
) else (
    echo [1/3] Programme deja construit : dist\AnalyseurQuestionnaire.exe
)

REM --- 2. L'installateur embarque le programme ---
echo [2/3] Construction de l'installateur (peut durer 1-3 minutes)...
"%PYTHON%" -m PyInstaller --noconfirm Installateur.spec
if errorlevel 1 (
    echo.
    echo [ERREUR] La construction de l'installateur a echoue.
    pause
    exit /b 1
)

REM --- 3. Verification ---
echo [3/3] Verification...
if not exist dist\Installateur.exe (
    echo [ERREUR] Installateur.exe n'a pas ete genere.
    pause
    exit /b 1
)

for %%A in (dist\Installateur.exe) do set TAILLE=%%~zA
for %%A in (dist\AnalyseurQuestionnaire.exe) do set TAILLE2=%%~zA

echo.
echo ============================================================
echo   SUCCES
echo ============================================================
echo   Programme    : dist\AnalyseurQuestionnaire.exe  (%TAILLE2% o)
echo   Installateur : dist\Installateur.exe            (%TAILLE% o)
echo.
echo   POUR INSTALLER SUR UN AUTRE POSTE :
echo     1. Copier Installateur.exe (il contient tout, .env inclus)
echo     2. Double-cliquer dessus
echo     3. Choisir le dossier + les options
echo     4. Le .env embarque est copie automatiquement ;
echo        un autre .env peut etre choisi manuellement
echo        (il sera utilise en priorite, sans doublon)
echo ============================================================
echo.
pause
