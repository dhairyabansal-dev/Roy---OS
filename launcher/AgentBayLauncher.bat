@echo off
setlocal
cd /d "%~dp0.."
set "PYTHON_EXE="
if exist ".venv\Scripts\python.exe" set "PYTHON_EXE=.venv\Scripts\python.exe"
if not defined PYTHON_EXE if exist "venv\Scripts\python.exe" set "PYTHON_EXE=venv\Scripts\python.exe"
if not defined PYTHON_EXE set "PYTHON_EXE=python"
if /i "%PYTHON_EXE%"=="python" where python >nul 2>&1
if /i "%PYTHON_EXE%"=="python" if errorlevel 1 (
  echo [ERROR] Python was not found. Install Python 3.11+ or create .venv\Scripts\python.exe.
  pause
  exit /b 1
)
"%PYTHON_EXE%" scripts\launch_agent_bay.py
if errorlevel 1 (
  echo [ERROR] Agent Bay failed to start. See data\agent_bay_server.log.
  pause
  exit /b 1
)
endlocal