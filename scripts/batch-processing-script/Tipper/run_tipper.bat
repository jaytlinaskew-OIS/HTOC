@echo off
REM ─── Configuration ────────────────────────────────────────────────────────────
set "SCRIPT_DIR=C:\Users\jaskew\Documents\project_repository\scripts\batch-processing-script\Tipper"
set "LOG_FILE=%SCRIPT_DIR%\TipperRunLogs.json"
set "OUTPUT_LOG=%SCRIPT_DIR%\TipperRunOutput.log"

pushd "%SCRIPT_DIR%"

REM ─── Grab an ISO8601 timestamp ───────────────────────────────────────────────
for /f "delims=" %%T in ('
    powershell -NoProfile -Command "Get-Date -Format yyyy-MM-ddTHH:mm:ss"
') do set "TSTAMP=%%T"

REM ─── Log Start ────────────────────────────────────────────────────────────────
>> "%LOG_FILE%" echo {"timestamp":"%TSTAMP%","event":"Start","exitCode":null}

REM ─── Ensure required packages are installed to the user site ────────────────
"C:\Program Files\Python313\python.exe" -m pip install --upgrade --quiet --user ^
    pandas pytz numpy requests >> "%OUTPUT_LOG%" 2>&1
if %ERRORLEVEL% neq 0 (
    set "EXIT_CODE=%ERRORLEVEL%"
    for /f "delims=" %%T in ('
        powershell -NoProfile -Command "Get-Date -Format yyyy-MM-ddTHH:mm:ss"
    ') do set "TSTAMP=%%T"
    >> "%LOG_FILE%" echo {"timestamp":"%TSTAMP%","event":"PipInstallFailed","exitCode":%EXIT_CODE%}
    popd
    exit /b %EXIT_CODE%
)

REM ─── Run the Python script and capture its output ────────────────────────────
"C:\Program Files\Python313\python.exe" main.py >> "%OUTPUT_LOG%" 2>&1
set "EXIT_CODE=%ERRORLEVEL%"

REM ─── Grab a fresh timestamp and Log End ───────────────────────────────────────
for /f "delims=" %%T in ('
    powershell -NoProfile -Command "Get-Date -Format yyyy-MM-ddTHH:mm:ss"
') do set "TSTAMP=%%T"
>> "%LOG_FILE%" echo {"timestamp":"%TSTAMP%","event":"End","exitCode":%EXIT_CODE%}

popd
exit /b %EXIT_CODE%
