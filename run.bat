@echo off
setlocal enabledelayedexpansion
title Connectly - Contact Book Web Application
color 0A

:: Ensure working directory is the script directory
cd /d "%~dp0"

cls
echo ======================================================================
echo                     CONNECTLY CONTACT BOOK
echo ======================================================================
echo.

:: 1. Check Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    where py >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] Python was not found in your system PATH.
        echo Please install Python 3.10+ from https://python.org and check "Add Python to PATH".
        echo.
        pause
        exit /b 1
    ) else (
        set "PY_CMD=py"
    )
) else (
    set "PY_CMD=python"
)

:: 2. Create virtual environment if missing
if not exist "venv\Scripts\python.exe" (
    echo [*] Setting up virtual environment for the first time...
    !PY_CMD! -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [*] Virtual environment created successfully.
    echo.
)

:: 3. Install / check requirements
echo [*] Checking dependencies...
".\venv\Scripts\pip.exe" install -r requirements.txt --disable-pip-version-check --quiet
if %errorlevel% neq 0 (
    echo [WARNING] Dependency install had warnings, continuing...
)

:: 4. Launch browser asynchronously after 2 seconds
start /b cmd /c "timeout /t 2 /nobreak >nul & start http://127.0.0.1:5000"

echo.
echo ======================================================================
echo  Connectly server is starting at:
echo  -> http://127.0.0.1:5000
echo.
echo  Your default browser will open automatically in a moment.
echo  (Press Ctrl+C in this terminal window to stop the server)
echo ======================================================================
echo.

:: 5. Run Flask application
".\venv\Scripts\python.exe" app.py

pause
