@echo off
cd /d "%~dp0"
if exist .venv\Scripts\python.exe (
    start "" ".venv\Scripts\python.exe" "android_launcher.py"
) else (
    start "" python "android_launcher.py"
)

