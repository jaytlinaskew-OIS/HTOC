@echo off
setlocal EnableExtensions EnableDelayedExpansion
REM I^&W Document Expanded Spreadsheet Generator - Batch Script

REM ── Config ──────────────────────────────────────────────────────────────────
set "PYTHON_EXE=\\10.1.4.22\data\HTOC\Data_Analytics\Py\python.exe"

REM Point to the actual folder that contains the .py
set "WORK_DIR=Z:\HTOC\HTOC Reports\I&W Reports\5. I&W Staging\I&W Report Processing Scripts\Expanded Scripts"
set "SCRIPT_PATH=%WORK_DIR%\I&W_Document_expanded_spreadsheet.py"

set "LOG_DIR=Z:\HTOC\HTOC Reports\I&W Reports\5. I&W Staging\logs"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

REM ── Stable timestamp ────────────────────────────────────────────────────────
for /f "tokens=2-4 delims=/.- " %%a in ('echo %date%') do (
  set "MM=%%a"
  set "DD=%%b"
  set "YYYY=%%c"
)
set "HH=%time:~0,2%"
if "%HH:~0,1%"==" " set "HH=0%HH:~1,1%"
set "MN=%time:~3,2%"
set "SS=%time:~6,2%"
set "STAMP=%YYYY%%MM%%DD%_%HH%%MN%%SS%"
set "LOG_FILE=%LOG_DIR%\iw_expanded_spreadsheet_%STAMP%.log"

echo [%date% %time%] Starting I^&W Document Expanded Spreadsheet Generator...

REM ── Move to working directory ───────────────────────────────────────────────
pushd "%WORK_DIR%" 2>nul
if errorlevel 1 (
    echo ERROR: Failed to change to working directory: %WORK_DIR%
    >>"%LOG_FILE%" echo [%date% %time%] ERROR: Failed to change to working directory: %WORK_DIR%
    pause
    exit /b 1
)

REM ── Sanity checks ───────────────────────────────────────────────────────────
if not exist "%PYTHON_EXE%" (
    echo ERROR: Python executable not found at %PYTHON_EXE%
    >>"%LOG_FILE%" echo [%date% %time%] ERROR: Python executable not found at %PYTHON_EXE%
    popd & pause & exit /b 1
)
if not exist "%SCRIPT_PATH%" (
    echo ERROR: Script not found at "%SCRIPT_PATH%"
    >>"%LOG_FILE%" echo [%date% %time%] ERROR: Script not found at "%SCRIPT_PATH%"
    popd & pause & exit /b 1
)

REM ── Install required packages (safe if already installed) ──────────────────
echo [%date% %time%] Installing required packages...
"%PYTHON_EXE%" -m pip install --quiet --user --disable-pip-version-check --no-warn-script-location ^
  --trusted-host pypi.org --trusted-host files.pythonhosted.org ^
  pandas openpyxl pytz requests urllib3 >nul 2>&1
if errorlevel 1 (
    echo ERROR: Failed to install required packages
    >>"%LOG_FILE%" echo [%date% %time%] ERROR: Failed to install required packages
    popd & pause & exit /b 1
)

echo [%date% %time%] Executing I^&W Expanded Spreadsheet Generator script...

set "TEMP_OUT=%LOG_DIR%\temp_output_%STAMP%.log"
"%PYTHON_EXE%" "%SCRIPT_PATH%" > "%TEMP_OUT" 2>&1
set "PY_EXIT=%ERRORLEVEL%"

if "%PY_EXIT%"=="0" (
    echo [%date% %time%] I^&W Expanded Spreadsheet Generator completed successfully
    >>"%LOG_FILE%" echo [%date% %time%] I^&W Expanded Spreadsheet Generator completed successfully
) else (
    echo [%date% %time%] I^&W Expanded Spreadsheet Generator failed with error code %PY_EXIT%
    >>"%LOG_FILE%" echo [%date% %time%] I^&W Expanded Spreadsheet Generator failed with error code %PY_EXIT%
)

type "%TEMP_OUT%" >> "%LOG_FILE%" 2>nul
del "%TEMP_OUT%" 2>nul

echo [%date% %time%] I^&W Expanded Spreadsheet Generator batch script completed
popd
pause
exit /b %PY_EXIT%
