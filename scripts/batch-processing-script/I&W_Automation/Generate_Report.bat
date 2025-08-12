@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM ─── Work in this script’s folder ───────────────────────────────────────────
cd /d "%~dp0"

REM ─── Configuration ──────────────────────────────────────────────────────────
set "PYTHON_EXE=\\10.1.4.22\data\HTOC\Data_Analytics\Py\python.exe"
set "SCRIPT=Z:\HTOC\HTOC Reports\I&W Reports\5. I&W Staging\I&W Report Processing Scripts\scripts\main.py"

REM ─── Install required packages (safe if already installed) ──────────────────
"%PYTHON_EXE%" -m pip install --quiet --user ^
  --trusted-host pypi.org --trusted-host files.pythonhosted.org ^
  pandas openpyxl python-docx charset-normalizer requests

REM ─── Verify script exists ───────────────────────────────────────────────────
if not exist "%SCRIPT%" (
  echo [ERROR] Script not found: "%SCRIPT%"
  pause
  exit /b 1
)

REM ─── Run the Python script ──────────────────────────────────────────────────
"%PYTHON_EXE%" "%SCRIPT%"

pause
endlocal
