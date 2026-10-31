@echo off
REM Double-clickable Windows 10/11 Launcher for OpenMRR Studio
REM Automatically creates .venv and installs dependencies on first launch if needed.
setlocal
cd /d "%~dp0\.."
set "PYTHONPATH=%CD%\src;%PYTHONPATH%"

if exist ".venv\Scripts\python.exe" goto :launch

where uv >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OpenMRR Studio] First-time setup via uv...
    uv sync --extra desktop
    if exist ".venv\Scripts\python.exe" goto :launch
)

set "SYS_PY="
where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    py -3.12 -c "import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)" >nul 2>nul && set "SYS_PY=py -3.12"
    if not defined SYS_PY py -3.13 -c "import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)" >nul 2>nul && set "SYS_PY=py -3.13"
    if not defined SYS_PY py -3.11 -c "import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)" >nul 2>nul && set "SYS_PY=py -3.11"
    if not defined SYS_PY py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)" >nul 2>nul && set "SYS_PY=py -3"
)
if not defined SYS_PY (
    python -c "import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)" >nul 2>nul && set "SYS_PY=python"
)

if not defined SYS_PY (
    echo [OpenMRR Studio] Python 3.11 or newer was not found on this PC.
    echo Please install Python 3.12 from https://www.python.org/downloads/windows/
    echo ^(Check "Add python.exe to PATH" during installation^), then double-click this launcher again.
    pause
    exit /b 1
)

echo [OpenMRR Studio] First-time setup: creating local .venv and installing packages (~1 minute)...
%SYS_PY% -m venv .venv
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\pip.exe" install -e ".[desktop]" || ".venv\Scripts\pip.exe" install -e "."

:launch
".venv\Scripts\python.exe" -m openmrr.desktop_app %*
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [OpenMRR Studio] Process exited with code %ERRORLEVEL%.
    pause
)
endlocal
