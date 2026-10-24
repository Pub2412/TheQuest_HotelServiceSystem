@echo off
title The Quest Hotel - Android Launcher
where python >nul 2>nul
if errorlevel 1 (
    echo Python is required to open the launcher.
    pause
    exit /b 1
)
python "%~dp0android_launcher.py"
