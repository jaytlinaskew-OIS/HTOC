@echo off
setlocal EnableExtensions EnableDelayedExpansion
REM ============================================================================
REM NextObservedIndicatorV4.0 - Task Scheduler launcher (test outputs)
REM Does NOT replace existing "Next Observed Daily Reports" tasks.
REM ============================================================================

if not exist "C:\Temp" mkdir "C:\Temp" >nul 2>&1
echo [%date% %time%] bat started from: %~dp0 > "C:\Temp\noi_v4_debug.txt" 2>&1

if not defined HTOC_SHARE_ROOT set "HTOC_SHARE_ROOT=\\cscso1fsappv01\data\HTOC"
if not defined NOI_V4_SAVE_DIR set "NOI_V4_SAVE_DIR=%HTOC_SHARE_ROOT%\JA\NextObserveV4Test"

if not defined PYTHON_EXE (
    py -3.13 --version >nul 2>&1
    if "!ERRORLEVEL!"=="0" (
        for /f "delims=" %%p in ('py -3.13 -c "import sys; print(sys.executable)"') do set "PYTHON_EXE=%%p"
    ) else (
        set "PYTHON_EXE=%HTOC_SHARE_ROOT%\JA\Python313\python.exe"
    )
)

set "WORK_DIR=%~dp0"
set "SCRIPT_PATH=%WORK_DIR%NextObservedIndicatorV4.0.py"
set "LOG_DIR=%WORK_DIR%logs"
set "WHEELHOUSE=%HTOC_SHARE_ROOT%\JA\wheelhouse"
set "SUCCESS_MARKER=PIPELINE_OK"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
forfiles /p "%LOG_DIR%" /m "*.log" /d -14 /c "cmd /c del /q @path" >nul 2>&1

for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd"') do set "TODAY_STR=%%i"
set "_TS_RAW=%TIME: =0%"
set "NOW_STR=%_TS_RAW:~0,2%%_TS_RAW:~3,2%%_TS_RAW:~6,2%"
set "TS=%TODAY_STR%_%NOW_STR%"
set "LOG_FILE=%LOG_DIR%\noi_v4_%TS%.log"
set "TEMP_OUT=%LOG_DIR%\temp_output_%TS%.log"

for /f %%i in ('powershell -NoProfile -Command "[int][double]::Parse((Get-Date -UFormat %%s))"') do set "RUN_START_EPOCH=%%i"

call :log START   NextObservedIndicatorV4.0
call :log CONFIG  Python: %PYTHON_EXE%
call :log CONFIG  Script: %SCRIPT_PATH%
call :log CONFIG  Save:   %NOI_V4_SAVE_DIR%
call :log CONFIG  Log:    %LOG_FILE%
call :log RUN     Connecting data share...
call "%~dp0..\..\ensure_htoc_data_share.bat" >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    call :log ERROR   Cannot reach HTOC data share %HTOC_SHARE_ROOT%
    exit /b 3
)
call :log CHECK   Data share OK (%HTOC_SHARE_ROOT%)
if not exist "%NOI_V4_SAVE_DIR%" mkdir "%NOI_V4_SAVE_DIR%"

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

pushd "%WORK_DIR%" >nul 2>&1
if errorlevel 1 (
    call :log ERROR   Failed to pushd WORK_DIR
    exit /b 1
)

set "PKGS=pandas numpy scikit-learn openpyxl"
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
    call :log ERROR   Package install failed
    popd >nul
    exit /b 1
)
call :log CHECK   Packages OK

call :log RUN     Launching NextObservedIndicatorV4.0.py...
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
    call :log ERROR   Missing success marker %SUCCESS_MARKER%
    goto :finish
)

REM Require at least one CSV written under SAVE_DIR during this run
set "FRESH_COUNT=0"
for /f %%i in ('powershell -NoProfile -Command "$d='%NOI_V4_SAVE_DIR%'; if (Test-Path -LiteralPath $d) { (Get-ChildItem -LiteralPath $d -Recurse -Filter '*.csv' | Where-Object { $_.LastWriteTimeUtc -ge (Get-Date).ToUniversalTime().AddHours(-6) }).Count } else { 0 }"') do set "FRESH_COUNT=%%i"
if "!FRESH_COUNT!"=="0" (
    call :log ERROR   No fresh CSV outputs found under %NOI_V4_SAVE_DIR%
    goto :finish
)

call :log SUCCESS Script completed successfully
call :log OUTPUT  Fresh CSV files: !FRESH_COUNT!
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
