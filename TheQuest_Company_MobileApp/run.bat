@echo off
title The Quest Hotel - Mobile Application Portal
color 0B

echo ======================================================================
echo   THE QUEST HOTEL - MOBILE MANAGEMENT SYSTEM PORTAL
echo   "We shall never deny a guest, even the most ridiculous request"
echo ======================================================================
echo.

:: Detect Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not found in your system PATH.
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)

:: Activate Virtual Environment if available in parent or current dir
if exist "..\.venv\Scripts\activate.bat" (
    echo [INFO] Activating project virtual environment: ..\.venv
    call "..\.venv\Scripts\activate.bat"
) else if exist ".venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment: .venv
    call ".venv\Scripts\activate.bat"
)

:: Launch runner script
echo [INFO] Starting The Quest Mobile Portal on port 5001...
python run.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Server terminated with an error code.
    pause
)
