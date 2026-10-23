@echo off
title The Quest Hotel - Customer Portal
cls

echo ======================================================================
echo   THE QUEST HOTEL - CUSTOMER WEBSITE PORTAL
echo   "We shall never deny a guest, even the most ridiculous request"
echo ======================================================================
echo.

cd /d "%~dp0"

REM 1. Check if local virtual environment exists
if exist ".venv\Scripts\python.exe" (
    echo [INFO] Activating virtual environment (.venv)...
    call .venv\Scripts\activate.bat
    python run.py
    pause
    exit /b 0
)

REM 2. Check if parent virtual environment exists
if exist "..\TheQuest_Company_DesktopApp\.venv\Scripts\python.exe" (
    echo [INFO] Using workspace virtual environment...
    call ..\TheQuest_Company_DesktopApp\.venv\Scripts\activate.bat
    python run.py
    pause
    exit /b 0
)

REM 3. Fallback to system Python
echo [INFO] Running with System Python...
python run.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Application failed to launch.
    echo Please make sure dependencies are installed:
    echo     pip install -r requirements.txt
    echo.
    pause
)
