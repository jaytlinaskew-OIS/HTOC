@echo off
setlocal EnableExtensions EnableDelayedExpansion
REM I^&W Spreadsheet - Batch Script
REM This script executes the I^&W Spreadsheet Python script for automated scheduling

echo [%date% %time%] Starting I^&W Spreadsheet...

REM Set the Python executable path
set "PYTHON_EXE=\\10.1.4.22\data\HTOC\Data_Analytics\Py\python.exe"

REM Set the script path
set "WORK_DIR=Z:\HTOC\HTOC Reports\I&W Reports\5. I&W Staging\I&W Report Processing Scripts\Spreadsheet_scripts"
set "SCRIPT_PATH=%WORK_DIR%\I&W_Spreadsheet.py"

REM Set the log directory
set "LOG_DIR=Z:\HTOC\HTOC Reports\I&W Reports\5. I&W Staging\logs"

REM Create log directory if it doesn't exist
if not exist "%LOG_DIR%" (
    mkdir "%LOG_DIR%"
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to create log directory. Error level: %ERRORLEVEL%
        pause
        exit /b 1
    )
)

REM Set log file with timestamp
set "LOG_FILE=%LOG_DIR%\iw_spreadsheet_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%.log"

REM Change to working directory (quoted to handle &)
pushd "%WORK_DIR%" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to change to working directory. Error level: %ERRORLEVEL%
    pause
    exit /b 1
)

REM Check if Python executable exists
if not exist "%PYTHON_EXE%" (
    echo [ERROR] Python executable not found at %PYTHON_EXE%
    echo [%date% %time%] ERROR: Python executable not found >> "%LOG_FILE%" 2>nul
    popd >nul
    pause
    exit /b 1
)

REM Check if script exists
if not exist "%SCRIPT_PATH%" (
    echo [ERROR] Script not found at %SCRIPT_PATH%
    echo [%date% %time%] ERROR: Script not found >> "%LOG_FILE%" 2>nul
    popd >nul
    pause
    exit /b 1
)

echo [%date% %time%] Installing/updating required packages...

REM Clean up any corrupted pandas remnants
"%PYTHON_EXE%" -m pip uninstall -y pandas 2>nul

REM Remove corrupted directories using simple Windows commands
rmdir /s /q "%USERPROFILE%\AppData\Roaming\Python\Python311\site-packages\~andas" 2>nul
rmdir /s /q "%USERPROFILE%\AppData\Roaming\Python\Python311\site-packages\pandas" 2>nul

REM Install required packages with warnings suppressed
"%PYTHON_EXE%" -m pip install --quiet --upgrade --trusted-host pypi.org --trusted-host files.pythonhosted.org --disable-pip-version-check --no-warn-script-location pandas openpyxl requests urllib3 pytz 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install required packages. Error level: %ERRORLEVEL%
    echo [%date% %time%] ERROR: Failed to install required packages >> "%LOG_FILE%" 2>nul
    popd >nul
    pause
    exit /b 1
)

echo [%date% %time%] Executing I^&W Spreadsheet script...

REM Execute the Python script and capture output
set "TEMP_OUT=%LOG_DIR%\temp_output.log"
"%PYTHON_EXE%" "%SCRIPT_PATH%" > "%TEMP_OUT%" 2>&1
set "SCRIPT_EXIT_CODE=%ERRORLEVEL%"

REM Check exit code
if %SCRIPT_EXIT_CODE% EQU 0 (
    echo [%date% %time%] I^&W Spreadsheet completed successfully
    echo [%date% %time%] I^&W Spreadsheet completed successfully >> "%LOG_FILE%" 2>nul
) else (
    echo [%date% %time%] I^&W Spreadsheet failed with error code %SCRIPT_EXIT_CODE%
    echo [%date% %time%] I^&W Spreadsheet failed with error code %SCRIPT_EXIT_CODE% >> "%LOG_FILE%" 2>nul
)

type "%TEMP_OUT%" >> "%LOG_FILE%" 2>nul
if exist "%TEMP_OUT%" del "%TEMP_OUT%" >nul 2>&1

echo [%date% %time%] I^&W Spreadsheet batch script completed
popd >nul
exit /b %SCRIPT_EXIT_CODE%
