@echo off
setlocal EnableExtensions EnableDelayedExpansion
REM ============================================================================
REM Threat Assessment Scoring Daily - Batch Script
REM ============================================================================

REM ── Debug: confirm bat is executing (remove once working) ────────────────────
if not exist "C:\Temp" mkdir "C:\Temp" >nul 2>&1
echo [%date% %time%] bat started from: %~dp0 > "C:\Temp\prism_debug.txt" 2>&1

REM ── Configuration ───────────────────────────────────────────────────────────
if not defined HTOC_SHARE_ROOT set "HTOC_SHARE_ROOT=\\10.1.4.22\data\HTOC"

REM Prefer local Python 3.13 (faster than loading from network share).
REM PYTHON_CMD = full command used to invoke Python (may include flags).
REM PYTHON_EXE = path used for the existence check (must be a real file path).
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
set "SCRIPT_PATH=%WORK_DIR%threat_assessment_scoring_daily.py"
set "LOG_DIR=%WORK_DIR%logs"
set "OUTPUT_DIR=%HTOC_SHARE_ROOT%\Data_Analytics\Data\Threat Assessment Scores"
set "EXPECTED_FILE=%OUTPUT_DIR%\Threat_Assessment_Scores.xlsx"

REM ── Create log directory ────────────────────────────────────────────────────
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

REM ── Purge logs older than 14 days ───────────────────────────────────────────
forfiles /p "%LOG_DIR%" /m "*.log" /d -14 /c "cmd /c del /q @path" >nul 2>&1

REM ── Timestamp ───────────────────────────────────────────────────────────────
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd"') do set "TODAY_STR=%%i"
set "_TS_RAW=%TIME: =0%"
set "NOW_STR=%_TS_RAW:~0,2%%_TS_RAW:~3,2%%_TS_RAW:~6,2%"
set "TS=%TODAY_STR%_%NOW_STR%"
set "LOG_FILE=%LOG_DIR%\threat_assessment_daily_%TS%.log"
set "TEMP_OUT=%LOG_DIR%\temp_output_%TS%.log"

call :log START   Threat Assessment Scoring Daily
call :log CONFIG  Python: %PYTHON_CMD%
call :log CONFIG  Script: %SCRIPT_PATH%
call :log CONFIG  Log:    %LOG_FILE%

REM ── Pre-flight checks ───────────────────────────────────────────────────────
call :log CHECK   Verifying Python executable...
if not exist "%PYTHON_EXE%" (
    call :log ERROR   Python not found: %PYTHON_EXE%
    echo [ERROR] Python not found: "%PYTHON_EXE%"
    pause & exit /b 1
)
call :log CHECK   Python OK (%PYTHON_EXE%)

call :log CHECK   Verifying script...
if not exist "%SCRIPT_PATH%" (
    call :log ERROR   Script not found: %SCRIPT_PATH%
    echo [ERROR] Script not found: "%SCRIPT_PATH%"
    pause & exit /b 1
)
call :log CHECK   Script OK

REM ── Ensure Python finds user-installed packages in non-interactive sessions ────
set "PYTHONUSERBASE=C:\Users\jaskew\AppData\Roaming\Python"

REM ── Force local TEMP (avoids network share instability) ─────────────────────
set "TMP=C:\Temp"
set "TEMP=C:\Temp"
if not exist "%TMP%" mkdir "%TMP%" >nul 2>&1


REM ── Run the script ──────────────────────────────────────────────────────────
call :log RUN     Launching threat_assessment_scoring_daily.py...
pushd "%WORK_DIR%" >nul 2>&1

%PYTHON_CMD% -u "%SCRIPT_PATH%" > "%TEMP_OUT%" 2>&1
set "SCRIPT_EXIT_CODE=!ERRORLEVEL!"

popd >nul
call :log RUN     Script exited with code !SCRIPT_EXIT_CODE!

REM ── Append full script output to log ────────────────────────────────────────
echo. >> "%LOG_FILE%"
echo ---- script output ---- >> "%LOG_FILE%"
type "%TEMP_OUT%" >> "%LOG_FILE%" 2>nul
echo ---- end output ---- >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

REM ── Result handling ─────────────────────────────────────────────────────────
if "!SCRIPT_EXIT_CODE!"=="0" (
    call :log SUCCESS Script completed successfully

    dir "!EXPECTED_FILE!" >nul 2>&1
    if "!ERRORLEVEL!"=="0" (
        for %%a in ("!EXPECTED_FILE!") do set /a SIZE_KB=%%~za / 1024
        call :log OUTPUT  Excel file confirmed - !SIZE_KB! KB
    ) else (
        call :log WARN    Script succeeded but Excel file not found
    )
) else (
    call :log ERROR   Script failed with exit code !SCRIPT_EXIT_CODE! - see log for details
    echo [ERROR] Script failed. Review log: "%LOG_FILE%"
)

REM ── Clean up temp output ────────────────────────────────────────────────────
if exist "%TEMP_OUT%" del "%TEMP_OUT%" >nul 2>&1
call :log END     Batch complete

if "!SCRIPT_EXIT_CODE!"=="0" (
    exit 0
) else (
    pause
    exit /b !SCRIPT_EXIT_CODE!
)

REM ── :log subroutine ─────────────────────────────────────────────────────────
:log
set "_T=%TIME: =0%"
echo [%TODAY_STR% %_T:~0,8%] %*
echo [%TODAY_STR% %_T:~0,8%] %*>> "%LOG_FILE%" 2>nul
exit /b 0
