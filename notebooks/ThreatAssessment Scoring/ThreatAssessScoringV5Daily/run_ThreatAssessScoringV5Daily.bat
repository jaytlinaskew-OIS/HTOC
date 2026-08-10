@echo off
setlocal EnableExtensions EnableDelayedExpansion
REM ============================================================================
REM ThreatAssessScoringV5Daily - Task Scheduler launcher (strict exit codes)
REM ============================================================================

if not exist "C:\Temp" mkdir "C:\Temp" >nul 2>&1
echo [%date% %time%] bat started from: %~dp0 > "C:\Temp\threatassess_v5daily_debug.txt" 2>&1

if not defined HTOC_SHARE_ROOT set "HTOC_SHARE_ROOT=\\10.1.4.22\data\HTOC"

if not defined PYTHON_CMD (
    py -3.13 --version >nul 2>&1
    if "!ERRORLEVEL!"=="0" (
        set "PYTHON_CMD=py -3.13"
        for /f "delims=" %%p in ('py -3.13 -c "import sys; print(sys.executable)"') do set "PYTHON_EXE=%%p"
    ) else (
        set "PYTHON_EXE=%HTOC_SHARE_ROOT%\JA\Python313\python.exe"
        set "PYTHON_CMD=%HTOC_SHARE_ROOT%\JA\Python313\python.exe"
    )
)

set "WORK_DIR=%~dp0"
set "SCRIPT_PATH=%WORK_DIR%ThreatAssessScoringV5Daily.py"
set "LOG_DIR=%WORK_DIR%logs"
set "OUTPUT_DIR=%HTOC_SHARE_ROOT%\Data_Analytics\Data\Threat Assessment Scores"
set "EXPECTED_FILE=%OUTPUT_DIR%\Threat_Assessment_Scores.xlsx"
set "SUCCESS_MARKER=PIPELINE_OK"
set "NOWORK_MARKER=PIPELINE_OK_NOWORK"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
forfiles /p "%LOG_DIR%" /m "*.log" /d -14 /c "cmd /c del /q @path" >nul 2>&1

for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd"') do set "TODAY_STR=%%i"
set "_TS_RAW=%TIME: =0%"
set "NOW_STR=%_TS_RAW:~0,2%%_TS_RAW:~3,2%%_TS_RAW:~6,2%"
set "TS=%TODAY_STR%_%NOW_STR%"
set "LOG_FILE=%LOG_DIR%\threatassess_v5daily_%TS%.log"
set "TEMP_OUT=%LOG_DIR%\temp_output_%TS%.log"

REM Epoch seconds at run start (for Excel freshness check)
for /f %%i in ('powershell -NoProfile -Command "[int][double]::Parse((Get-Date -UFormat %%s))"') do set "RUN_START_EPOCH=%%i"

call :log START   ThreatAssessScoringV5Daily
call :log CONFIG  Python: %PYTHON_CMD%
call :log CONFIG  Script: %SCRIPT_PATH%
call :log CONFIG  Log:    %LOG_FILE%

if not defined PYTHON_EXE (
    call :log ERROR   PYTHON_EXE not resolved
    exit /b 1
)
if not exist "%PYTHON_EXE%" (
    call :log ERROR   Python not found: %PYTHON_EXE%
    exit /b 1
)
call :log CHECK   Python OK (%PYTHON_EXE%)

if not exist "%SCRIPT_PATH%" (
    call :log ERROR   Script not found: %SCRIPT_PATH%
    exit /b 1
)
call :log CHECK   Script OK

set "PYTHONUSERBASE=C:\Users\jaskew\AppData\Roaming\Python"
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"
set "TMP=C:\Temp"
set "TEMP=C:\Temp"
if not exist "%TMP%" mkdir "%TMP%" >nul 2>&1

call :log RUN     Launching ThreatAssessScoringV5Daily.py...
pushd "%WORK_DIR%" >nul 2>&1
if errorlevel 1 (
    call :log ERROR   Failed to pushd WORK_DIR: %WORK_DIR%
    exit /b 1
)

REM Prefer concrete python.exe so ERRORLEVEL is reliable (avoid bare "py -3.13" tokenization issues)
"%PYTHON_EXE%" -u "%SCRIPT_PATH%" > "%TEMP_OUT%" 2>&1
set "SCRIPT_EXIT_CODE=!ERRORLEVEL!"
popd >nul 2>&1

if not defined SCRIPT_EXIT_CODE (
    set "SCRIPT_EXIT_CODE=1"
    call :log ERROR   SCRIPT_EXIT_CODE was empty after Python run; treating as failure
)
call :log RUN     Script exited with code !SCRIPT_EXIT_CODE!

echo. >> "%LOG_FILE%"
echo ---- script output ---- >> "%LOG_FILE%"
type "%TEMP_OUT%" >> "%LOG_FILE%" 2>nul
echo ---- end output ---- >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

set "FINAL_EXIT=1"

if not "!SCRIPT_EXIT_CODE!"=="0" (
    call :log ERROR   Script failed with exit code !SCRIPT_EXIT_CODE!
    goto :finish
)

findstr /C:"%NOWORK_MARKER%" "%TEMP_OUT%" >nul 2>&1
if "!ERRORLEVEL!"=="0" (
    call :log SUCCESS No-work success marker found ^(%NOWORK_MARKER%^)
    set "FINAL_EXIT=0"
    goto :finish
)

findstr /C:"%SUCCESS_MARKER%" "%TEMP_OUT%" >nul 2>&1
if not "!ERRORLEVEL!"=="0" (
    call :log ERROR   Python exit 0 but missing success marker %SUCCESS_MARKER% in output
    goto :finish
)

if not exist "!EXPECTED_FILE!" (
    call :log ERROR   Python exit 0 but Excel output missing: !EXPECTED_FILE!
    goto :finish
)

REM Fail if Excel was not rewritten during this run (stale file = silent no-op)
for /f %%i in ('powershell -NoProfile -Command "(Get-Item -LiteralPath '!EXPECTED_FILE!').LastWriteTimeUtc | ForEach-Object { [int][double]::Parse(($_ | Get-Date -UFormat %%s)) }"') do set "EXCEL_MTIME_EPOCH=%%i"
if not defined EXCEL_MTIME_EPOCH (
    call :log ERROR   Could not read Excel LastWriteTime
    goto :finish
)
set /a EXCEL_AGE=!RUN_START_EPOCH!-!EXCEL_MTIME_EPOCH!
if !EXCEL_MTIME_EPOCH! LSS !RUN_START_EPOCH! (
    set /a SKEW=!RUN_START_EPOCH!-!EXCEL_MTIME_EPOCH!
    if !SKEW! GTR 60 (
        call :log ERROR   Excel file is stale ^(mtime before run start by !SKEW!s^). Script claimed success but did not rewrite output.
        call :log ERROR   RUN_START_EPOCH=!RUN_START_EPOCH! EXCEL_MTIME_EPOCH=!EXCEL_MTIME_EPOCH!
        goto :finish
    ) else (
        call :log WARN    Excel mtime !SKEW!s before run start ^(within 60s grace^)
    )
)

for %%a in ("!EXPECTED_FILE!") do set /a SIZE_KB=%%~za / 1024
call :log SUCCESS Script completed successfully
call :log OUTPUT  Excel confirmed - !SIZE_KB! KB ^(fresh^)
set "FINAL_EXIT=0"

:finish
if exist "%TEMP_OUT%" del "%TEMP_OUT%" >nul 2>&1
call :log END     Batch complete with exit !FINAL_EXIT!
exit /b !FINAL_EXIT!

:log
set "_T=%TIME: =0%"
echo [%TODAY_STR% %_T:~0,8%] %*
echo [%TODAY_STR% %_T:~0,8%] %*>> "%LOG_FILE%" 2>nul
exit /b 0
