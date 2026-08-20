@echo off
setlocal EnableExtensions EnableDelayedExpansion
REM ============================================================================
REM Next Observed Daily Reports V4 - consolidates NextObserveV4Test forecasts
REM Does NOT replace the production "Next Observed Daily Reports" task.
REM ============================================================================

if not exist "C:\Temp" mkdir "C:\Temp" >nul 2>&1
echo [%date% %time%] bat started from: %~dp0 > "C:\Temp\noi_v4_daily_reports_debug.txt" 2>&1

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
set "SCRIPT_PATH=%WORK_DIR%next_observed_daily_reports_v4.py"
set "LOG_DIR=%WORK_DIR%logs"
set "SUCCESS_MARKER=PIPELINE_OK"
set "NOWORK_MARKER=PIPELINE_OK_NOWORK"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
forfiles /p "%LOG_DIR%" /m "noi_v4_daily_*.log" /d -14 /c "cmd /c del /q @path" >nul 2>&1

for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd"') do set "TODAY_STR=%%i"
set "_TS_RAW=%TIME: =0%"
set "NOW_STR=%_TS_RAW:~0,2%%_TS_RAW:~3,2%%_TS_RAW:~6,2%"
set "TS=%TODAY_STR%_%NOW_STR%"
set "LOG_FILE=%LOG_DIR%\noi_v4_daily_%TS%.log"
set "TEMP_OUT=%LOG_DIR%\temp_daily_%TS%.log"

call :log START   Next Observed Daily Reports V4
call :log CONFIG  Python: %PYTHON_EXE%
call :log CONFIG  Script: %SCRIPT_PATH%
call :log CONFIG  Data:   %NOI_V4_SAVE_DIR%
call :log RUN     Connecting data share...
call "%~dp0..\..\ensure_htoc_data_share.bat" >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    call :log ERROR   Cannot reach HTOC data share %HTOC_SHARE_ROOT%
    exit /b 3
)
call :log CHECK   Data share OK (%HTOC_SHARE_ROOT%)

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

"%PYTHON_EXE%" -m pip install --user --disable-pip-version-check --quiet pandas openpyxl >nul 2>&1

call :log RUN     Launching next_observed_daily_reports_v4.py...
"%PYTHON_EXE%" -u "%SCRIPT_PATH%" > "%TEMP_OUT%" 2>&1
set "SCRIPT_EXIT_CODE=!ERRORLEVEL!"
popd >nul 2>&1

if not defined SCRIPT_EXIT_CODE set "SCRIPT_EXIT_CODE=1"
call :log RUN     Script exited with code !SCRIPT_EXIT_CODE!

echo. >> "%LOG_FILE%"
echo ---- script output ---- >> "%LOG_FILE%"
type "%TEMP_OUT%" >> "%LOG_FILE%" 2>nul
echo ---- end output ---- >> "%LOG_FILE%"

set "FINAL_EXIT=1"
if not "!SCRIPT_EXIT_CODE!"=="0" (
    call :log ERROR   Script failed with exit code !SCRIPT_EXIT_CODE!
    goto :finish
)

findstr /C:"%NOWORK_MARKER%" "%TEMP_OUT%" >nul 2>&1
if "!ERRORLEVEL!"=="0" (
    call :log SUCCESS No-work success ^(%NOWORK_MARKER%^)
    set "FINAL_EXIT=0"
    goto :finish
)

findstr /C:"%SUCCESS_MARKER%" "%TEMP_OUT%" >nul 2>&1
if not "!ERRORLEVEL!"=="0" (
    call :log ERROR   Missing success marker %SUCCESS_MARKER%
    goto :finish
)

set "EXPECTED=%NOI_V4_SAVE_DIR%\Full Daily Reports\full_daily_report_%TODAY_STR%.csv"
if not exist "!EXPECTED!" (
    call :log ERROR   Expected report missing: !EXPECTED!
    goto :finish
)

call :log SUCCESS Report confirmed: !EXPECTED!
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
