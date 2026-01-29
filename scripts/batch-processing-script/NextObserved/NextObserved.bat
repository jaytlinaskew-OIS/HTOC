@echo off
setlocal EnableDelayedExpansion

REM ─── Work in this script’s folder ────────────────────────────────────────────
cd /d "%~dp0"

REM ─── Configuration ────────────────────────────────────────────────────────────
set "PYTHON_EXE=py -3.13"
set "LOG_FILE=%~dp0run_log.json"
set "OUTPUT_FILE=%~dp0output.log"
set "PYTHONUSERBASE=C:\Users\jaskew\AppData\Roaming\Python"

REM ─── Get ISO‑8601 timestamp ──────────────────────────────────────────────────
for /f "tokens=2 delims==." %%A in ('wmic os get localdatetime /value') do set dt=%%A
set "timestamp=%dt:~0,4%-%dt:~4,2%-%dt:~6,2%T%dt:~8,2%:%dt:~10,2%:%dt:~12,2%"

REM ─── Install required packages ────────────────────────────────────────────────
echo Installing required packages...  >> "%OUTPUT_FILE%" 2>&1
%PYTHON_EXE% -m pip install --user pandas pytz python-dateutil numpy scikit-learn lifelines openpyxl >> "%OUTPUT_FILE%" 2>&1
if errorlevel 1 (
  echo WARNING: Package installation encountered errors  >> "%OUTPUT_FILE%" 2>&1
)

REM ─── Run the Python script and capture all output ─────────────────────────────
%PYTHON_EXE% "%~dp0main.py" >> "%OUTPUT_FILE%" 2>&1

REM ─── Grab the last line of output ─────────────────────────────────────────────
for /f "usebackq delims=" %%L in ("%OUTPUT_FILE%") do set "OUTPUT=%%L"

REM ─── Write the JSON log ───────────────────────────────────────────────────────
(
  echo {
  echo   "timestamp":"%timestamp%",
  echo   "output":"!OUTPUT!"
  echo }
) > "%LOG_FILE%"

endlocal
