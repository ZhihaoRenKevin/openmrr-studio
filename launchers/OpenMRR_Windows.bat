@echo off
REM Double-clickable Windows 10/11 Launcher for OpenMRR Studio v3.0 (Auto-detects CUDA GPU vs CPU)
setlocal
cd /d "%~dp0\.."
set "PYTHONPATH=%CD%\src;%PYTHONPATH%"

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m openmrr.desktop_app
) else (
    where uv >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        uv run python -m openmrr.desktop_app
    ) else (
        python -m openmrr.desktop_app
    )
)
endlocal
