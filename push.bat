@echo off
setlocal enabledelayedexpansion

echo.
echo  +-----------------------------------+
echo  ^|    GIT PUSHer - Quick Launcher   ^|
echo  +-----------------------------------+
echo.

set "SCRIPT_DIR=%~dp0"
set "PYTHON=python"

where python >nul 2>&1
if errorlevel 1 (
    if exist "C:\Users\pranj\AppData\Local\Python\bin\python3.exe" (
        set "PYTHON=C:\Users\pranj\AppData\Local\Python\bin\python3.exe"
    ) else (
        echo  [ERROR] Python not found in PATH.
        pause
        exit /b 1
    )
)

if not exist "%SCRIPT_DIR%venv\Scripts\activate.bat" (
    echo  [SETUP] Creating virtual environment...
    %PYTHON% -m venv "%SCRIPT_DIR%venv"
    call "%SCRIPT_DIR%venv\Scripts\activate.bat"
    echo  [SETUP] Installing dependencies...
    pip install -q -r "%SCRIPT_DIR%requirements.txt"
) else (
    call "%SCRIPT_DIR%venv\Scripts\activate.bat"
)

rem Tesseract is a separate Windows application, not a Python package. Install it
rem automatically through the Windows Package Manager when it is not available.
set "TESSERACT_EXE="
where tesseract >nul 2>&1
if not errorlevel 1 (
    for /f "delims=" %%T in ('where tesseract') do if "!TESSERACT_EXE!"=="" set "TESSERACT_EXE=%%T"
) else if exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
    set "TESSERACT_EXE=C:\Program Files\Tesseract-OCR\tesseract.exe"
    set "PATH=C:\Program Files\Tesseract-OCR;!PATH!"
)

if "!TESSERACT_EXE!"=="" (
    echo  [SETUP] Installing the OCR engine. This may take a minute...
    where winget >nul 2>&1
    if errorlevel 1 (
        echo  [WARNING] Windows Package Manager was not found. OCR scans will be skipped.
        echo            Install App Installer from the Microsoft Store, then run this again.
    ) else (
        winget install --id UB-Mannheim.TesseractOCR --exact --silent --accept-package-agreements --accept-source-agreements
        if exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
            set "TESSERACT_EXE=C:\Program Files\Tesseract-OCR\tesseract.exe"
            set "PATH=C:\Program Files\Tesseract-OCR;!PATH!"
            echo  [OK] OCR engine installed and ready.
        ) else (
            echo  [WARNING] OCR engine could not be installed. The Git push will still work; screen scans will be skipped.
            echo            Try running this launcher as Administrator, then run it again.
        )
    )
)

if not "!TESSERACT_EXE!"=="" set "TESSERACT_PATH=!TESSERACT_EXE!"

if "%~1"=="" (
    echo  Usage:
    echo    push.bat [project_path] [options]
    echo.
    echo  Examples:
    echo    push.bat .
    echo    push.bat C:\MyProject -m "feat: new feature"
    echo    push.bat C:\MyProject --private --branch develop
    echo.
    set /p "PROJECT_PATH=  Enter project path (or . for current dir): "
    set /p "COMMIT_MSG=  Commit message (leave blank for auto): "

    if "!COMMIT_MSG!"=="" (
        python "%SCRIPT_DIR%gitpusher.py" "!PROJECT_PATH!"
    ) else (
        python "%SCRIPT_DIR%gitpusher.py" "!PROJECT_PATH!" -m "!COMMIT_MSG!"
    )
) else (
    python "%SCRIPT_DIR%gitpusher.py" %*
)

echo.
pause
