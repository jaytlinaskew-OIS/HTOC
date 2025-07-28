@echo off
setlocal EnableDelayedExpansion

REM ─── Work in this script’s folder ─────────────────────────────────────────────
cd /d "%~dp0"

REM ─── Configuration ────────────────────────────────────────────────────────────
set "PYTHON_EXE=\\10.1.4.22\data\HTOC\Data_Analytics\Py\python.exe"
set "SCRIPT=%~dp0src\main.py"
set "LOG_FILE=%~dp0run_log.json"
set "OUTPUT_FILE=%~dp0output.log"

REM ─── Ensure log file is initialized as JSON array ─────────────────────────────
if not exist "%LOG_FILE%" (
    echo [ > "%LOG_FILE%"
    echo ] >> "%LOG_FILE%"
)

REM ─── Get ISO‑8601 timestamp ───────────────────────────────────────────────────
for /f "tokens=2 delims==." %%A in ('wmic os get localdatetime /value') do set dt=%%A
set "timestamp=%dt:~0,4%-%dt:~4,2%-%dt:~6,2%T%dt:~8,2%:%dt:~10,2%:%dt:~12,2%"

REM ─── Install required packages ────────────────────────────────────────────────
"%PYTHON_EXE%" -m pip install --quiet --user ^
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
"%PYTHON_EXE%" "%SCRIPT%" >> "%OUTPUT_FILE%" 2>&1

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
