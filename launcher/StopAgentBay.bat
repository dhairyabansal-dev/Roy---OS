@echo off
setlocal
cd /d "%~dp0.."
set "PYTHON_EXE="
if exist ".venv\Scripts\python.exe" set "PYTHON_EXE=.venv\Scripts\python.exe"
if not defined PYTHON_EXE if exist "venv\Scripts\python.exe" set "PYTHON_EXE=venv\Scripts\python.exe"
if not defined PYTHON_EXE set "PYTHON_EXE=python"
"%PYTHON_EXE%" scripts\stop_agent_bay.py
if errorlevel 1 pause
endlocal