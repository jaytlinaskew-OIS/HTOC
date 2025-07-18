@echo off
REM ─── Configuration ────────────────────────────────────────────────────────────
set "SCRIPT_DIR=C:\Users\jaskew\Documents\project_repository\scripts\batch-processing-script\Tipper"
set "LOG_FILE=%SCRIPT_DIR%\TipperRunLogs.json"
set "OUTPUT_LOG=%SCRIPT_DIR%\TipperRunOutput.log"

pushd "%SCRIPT_DIR%"

REM ─── 0) Initialize JSON array ────────────────────────────────────────────────
> "%LOG_FILE%" echo [
 
REM ─── 1) Log “Start” (first element, with comma) ──────────────────────────────
for /f "delims=" %%T in (
  'powershell -NoProfile -Command "Get-Date -Format yyyy-MM-ddTHH:mm:ss"'
) do set "TSTAMP=%%T"
>> "%LOG_FILE%" echo     {"timestamp":"%TSTAMP%","event":"Start","exitCode":null},

REM ─── 2) Pip install check (if failure, second element, with comma) ───────────
"C:\Program Files\Python313\python.exe" -m pip install --upgrade --quiet --user ^
    pandas pytz numpy requests xlsxwriter openpyxl >> "%OUTPUT_LOG%" 2>&1
if %ERRORLEVEL% neq 0 (
    for /f "delims=" %%T in (
      'powershell -NoProfile -Command "Get-Date -Format yyyy-MM-ddTHH:mm:ss"'
    ) do set "TSTAMP=%%T"
    >> "%LOG_FILE%" echo     {"timestamp":"%TSTAMP%","event":"PipInstallFailed","exitCode":%ERRORLEVEL%},
    popd
    exit /b %ERRORLEVEL%
)

REM ─── 3) Run main.py and then log final “End” (last element, NO comma) ─────────
"C:\Program Files\Python313\python.exe" main.py >> "%OUTPUT_LOG%" 2>&1
set "EXIT_CODE=%ERRORLEVEL%"
for /f "delims=" %%T in (
  'powershell -NoProfile -Command "Get-Date -Format yyyy-MM-ddTHH:mm:ss"'
) do set "TSTAMP=%%T"
>> "%LOG_FILE%" echo     {"timestamp":"%TSTAMP%","event":"End","exitCode":%EXIT_CODE%}

REM ─── 4) Close JSON array ─────────────────────────────────────────────────────
>> "%LOG_FILE%" echo ]

popd
exit /b %EXIT_CODE%
