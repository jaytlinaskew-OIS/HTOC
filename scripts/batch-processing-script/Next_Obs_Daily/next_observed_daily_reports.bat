@echo off
setlocal EnableDelayedExpansion

REM ─── Work in this script’s folder ─────────────────────────────────────────────
cd /d "%~dp0"

REM ─── Configuration ────────────────────────────────────────────────────────────
set "SCRIPT=%~dp0src\main.py"
set "LOG_FILE=%~dp0run_log.json"
set "OUTPUT_FILE=%~dp0output.log"

REM Require local Python 3.13; exit if unavailable to avoid pip 22.3.1 issues
set "PYTHON_EXE="
py -3.13 -c "import sys" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
  set "PYTHON_EXE=py -3.13"
) else (
  echo [ERROR] Python 3.13 not found. Install from Microsoft Store or python.org.>> "%OUTPUT_FILE%"
  echo [HINT] After install, ensure 'py -3.13' works in a new terminal.>> "%OUTPUT_FILE%"
  exit /b 1
)

REM Ensure packages install/load from user profile (not systemprofile)
set "PYTHONUSERBASE=%USERPROFILE%\AppData\Roaming\Python"
set "PYTHONPATH=%PYTHONUSERBASE%\Python313\site-packages;%PYTHONPATH%"

REM ─── Ensure log file is initialized as JSON array ─────────────────────────────
if not exist "%LOG_FILE%" (
    echo [ > "%LOG_FILE%"
    echo ] >> "%LOG_FILE%"
)

REM ─── Get ISO‑8601 timestamp ───────────────────────────────────────────────────
for /f "tokens=2 delims==." %%A in ('wmic os get localdatetime /value') do set dt=%%A
set "timestamp=%dt:~0,4%-%dt:~4,2%-%dt:~6,2%T%dt:~8,2%:%dt:~10,2%:%dt:~12,2%"

REM ─── Install required packages ────────────────────────────────────────────────
%PYTHON_EXE% -m pip install --quiet --user --retries 5 --timeout 60 --no-warn-script-location ^
  --trusted-host pypi.org --trusted-host files.pythonhosted.org ^
  pandas openpyxl >> "%OUTPUT_FILE%" 2>&1

if errorlevel 1 (
  for /f "usebackq delims=" %%L in ("%OUTPUT_FILE%") do (
      set "LINE=%%L"
      set "LINE=!LINE:\=\\!"
      set "OUTPUT=!LINE!"
  )
  goto :write_log
)

REM ─── Run the Python script ────────────────────────────────────────────────────
%PYTHON_EXE% "%SCRIPT%" >> "%OUTPUT_FILE%" 2>&1

REM ─── Capture last line of output and escape backslashes ───────────────────────
for /f "usebackq delims=" %%L in ("%OUTPUT_FILE%") do (
    set "OUTPUT=%%L"

)

:write_log

REM ─── Append new entry to JSON array properly ──────────────────────────────────
powershell -Command ^
  "$path = '%LOG_FILE%';" ^
  "$json = Get-Content $path -Raw | ConvertFrom-Json;" ^
  "$newEntry = [PSCustomObject]@{ timestamp = '%timestamp%'; output = '%OUTPUT%' };" ^
  "$json += $newEntry;" ^
  "$json | ConvertTo-Json -Depth 5 | Set-Content $path -Encoding UTF8"

endlocal
