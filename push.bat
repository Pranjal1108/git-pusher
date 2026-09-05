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
