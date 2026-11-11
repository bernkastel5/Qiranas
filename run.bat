@echo off
cd /d "%~dp0"
".venv\Scripts\python.exe" main.py
if %errorlevel% neq 0 (
    echo.
    echo Qiranas exited with error code %errorlevel%.
    pause
)
