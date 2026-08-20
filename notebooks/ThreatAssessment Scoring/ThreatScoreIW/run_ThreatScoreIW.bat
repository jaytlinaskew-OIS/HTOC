@echo off
setlocal EnableExtensions EnableDelayedExpansion
REM ============================================================================
REM ThreatScoreIW - Task Scheduler launcher (strict exit codes, headless-safe)
REM ============================================================================

if not exist "C:\Temp" mkdir "C:\Temp" >nul 2>&1
echo [%date% %time%] bat started from: %~dp0 > "C:\Temp\threatscoreiw_debug.txt" 2>&1

if not defined HTOC_SHARE_ROOT set "HTOC_SHARE_ROOT=\\cscso1fsappv01\data\HTOC"

REM Prefer local Python 3.13; fall back to share Python.
if not defined PYTHON_EXE (
    py -3.13 --version >nul 2>&1
    if "!ERRORLEVEL!"=="0" (
        for /f "delims=" %%p in ('py -3.13 -c "import sys; print(sys.executable)"') do set "PYTHON_EXE=%%p"
    ) else (
        set "PYTHON_EXE=%HTOC_SHARE_ROOT%\JA\Python313\python.exe"
    )
)

set "WORK_DIR=%~dp0"
set "SCRIPT_PATH=%WORK_DIR%ThreatScoreIW.py"
set "LOG_DIR=%WORK_DIR%logs"
set "OUTPUT_DIR=%HTOC_SHARE_ROOT%\Data_Analytics\Data\Threat Assessment Scores\ThreatAssessI_W"
set "WHEELHOUSE=%HTOC_SHARE_ROOT%\JA\wheelhouse"
set "SUCCESS_MARKER=PIPELINE_OK"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
forfiles /p "%LOG_DIR%" /m "*.log" /d -14 /c "cmd /c del /q @path" >nul 2>&1

for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd"') do set "TODAY_STR=%%i"
set "_TS_RAW=%TIME: =0%"
set "NOW_STR=%_TS_RAW:~0,2%%_TS_RAW:~3,2%%_TS_RAW:~6,2%"
set "TS=%TODAY_STR%_%NOW_STR%"
set "LOG_FILE=%LOG_DIR%\threatscoreiw_%TS%.log"
set "TEMP_OUT=%LOG_DIR%\temp_output_%TS%.log"
set "EXPECTED_FILE=%OUTPUT_DIR%\ThreatAssessI_W_%TODAY_STR%.xlsx"

for /f %%i in ('powershell -NoProfile -Command "[int][double]::Parse((Get-Date -UFormat %%s))"') do set "RUN_START_EPOCH=%%i"

call :log START   ThreatScoreIW
call :log CONFIG  Python: %PYTHON_EXE%
call :log CONFIG  Script: %SCRIPT_PATH%
call :log CONFIG  Log:    %LOG_FILE%
call :log CONFIG  Expect: %EXPECTED_FILE%
call :log RUN     Connecting data share...
call "%~dp0..\..\ensure_htoc_data_share.bat" >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    call :log ERROR   Cannot reach HTOC data share %HTOC_SHARE_ROOT%
    exit /b 3
)
call :log CHECK   Data share OK (%HTOC_SHARE_ROOT%)
set "PYTHONPATH=%HTOC_SHARE_ROOT%\Data_Analytics\threatconnect;%PYTHONPATH%"

if not exist "%PYTHON_EXE%" (
    call :log ERROR   Python not found: %PYTHON_EXE%
    exit /b 1
)
if not exist "%SCRIPT_PATH%" (
    call :log ERROR   Script not found: %SCRIPT_PATH%
    exit /b 1
)

set "PYTHONUSERBASE=C:\Users\jaskew\AppData\Roaming\Python"
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"
set "TMP=C:\Temp"
set "TEMP=C:\Temp"
if not exist "%TMP%" mkdir "%TMP%" >nul 2>&1
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%" >nul 2>&1

pushd "%WORK_DIR%" >nul 2>&1
if errorlevel 1 (
    call :log ERROR   Failed to pushd WORK_DIR: %WORK_DIR%
    exit /b 1
)

REM ── Dependencies (wheelhouse first, then PyPI) ─────────────────────────────
set "PKGS=pandas openpyxl xlsxwriter requests urllib3 pytz"
set "PIP_FLAGS=--user --disable-pip-version-check --no-warn-script-location --no-cache-dir --timeout 120 --retries 10"
set "PIP_TRUST=--trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host pypi.python.org"
set "PIP_OK=0"

call :log RUN     Installing packages...
if exist "%WHEELHOUSE%" (
    "%PYTHON_EXE%" -m pip install --user --no-index --find-links="%WHEELHOUSE%" %PKGS% > "%TEMP_OUT%" 2>&1
    if "!ERRORLEVEL!"=="0" set "PIP_OK=1"
)
if "!PIP_OK!"=="0" (
    "%PYTHON_EXE%" -m pip install %PIP_FLAGS% %PIP_TRUST% %PKGS% > "%TEMP_OUT%" 2>&1
    if "!ERRORLEVEL!"=="0" set "PIP_OK=1"
)
type "%TEMP_OUT%" >> "%LOG_FILE%" 2>nul
if not "!PIP_OK!"=="1" (
    call :log ERROR   Package install failed from wheelhouse and PyPI
    popd >nul
    exit /b 1
)
call :log CHECK   Packages OK

REM ── Run script ─────────────────────────────────────────────────────────────
call :log RUN     Launching ThreatScoreIW.py...
"%PYTHON_EXE%" -u "%SCRIPT_PATH%" > "%TEMP_OUT%" 2>&1
set "SCRIPT_EXIT_CODE=!ERRORLEVEL!"
popd >nul 2>&1

if not defined SCRIPT_EXIT_CODE set "SCRIPT_EXIT_CODE=1"
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

findstr /C:"%SUCCESS_MARKER%" "%TEMP_OUT%" >nul 2>&1
if not "!ERRORLEVEL!"=="0" (
    call :log ERROR   Python exit 0 but missing success marker %SUCCESS_MARKER%
    goto :finish
)

if not exist "!EXPECTED_FILE!" (
    call :log ERROR   Expected Excel missing: !EXPECTED_FILE!
    goto :finish
)

for /f %%i in ('powershell -NoProfile -Command "(Get-Item -LiteralPath '!EXPECTED_FILE!').LastWriteTimeUtc | ForEach-Object { [int][double]::Parse(($_ | Get-Date -UFormat %%s)) }"') do set "EXCEL_MTIME_EPOCH=%%i"
if not defined EXCEL_MTIME_EPOCH (
    call :log ERROR   Could not read Excel LastWriteTime
    goto :finish
)
if !EXCEL_MTIME_EPOCH! LSS !RUN_START_EPOCH! (
    set /a SKEW=!RUN_START_EPOCH!-!EXCEL_MTIME_EPOCH!
    if !SKEW! GTR 60 (
        call :log ERROR   Excel file is stale ^(mtime before run start by !SKEW!s^)
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
