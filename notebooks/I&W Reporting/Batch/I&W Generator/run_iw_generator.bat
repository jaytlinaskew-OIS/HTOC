@echo off
REM I^&W Report Generator - Batch Script
REM This script executes the I^&W Generator Python script for automated scheduling

echo [%date% %time%] Starting I^&W Report Generator...

REM Set the Python executable path
set "PYTHON_EXE=\\10.1.4.22\data\HTOC\Data_Analytics\Py\python.exe"

REM Set the script path
set "SCRIPT_PATH=Z:\HTOC\HTOC Reports\I&W Reports\5. I&W Staging\I&W Report Processing Scripts\Spreadsheet_scripts\I&W_Generator.py"

REM Set the working directory
set "WORK_DIR=Z:\HTOC\HTOC Reports\I&W Reports\5. I&W Staging\I&W Report Processing Scripts\Spreadsheet_scripts"

REM Set the log directory
set "LOG_DIR=Z:\HTOC\HTOC Reports\I&W Reports\5. I&W Staging\logs"

REM Create log directory if it doesn't exist
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

REM Set log file with timestamp
set "LOG_FILE=%LOG_DIR%\iw_generator_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%.log"

REM Change to working directory
cd /d "%WORK_DIR%"

REM Check if Python executable exists
if not exist "%PYTHON_EXE%" (
    echo ERROR: Python executable not found at %PYTHON_EXE%
    echo [%date% %time%] ERROR: Python executable not found >> "%LOG_FILE%"
    pause
    exit /b 1
)

REM Check if script exists
if not exist "%SCRIPT_PATH%" (
    echo ERROR: Script not found at %SCRIPT_PATH%
    echo [%date% %time%] ERROR: Script not found >> "%LOG_FILE%"
    pause
    exit /b 1
)

echo [%date% %time%] Installing/updating required packages...

REM Clean up any corrupted packages first
"%PYTHON_EXE%" -m pip uninstall -y pandas 2>nul

REM Remove corrupted directories using simple Windows commands
rmdir /s /q "%USERPROFILE%\AppData\Roaming\Python\Python311\site-packages\~andas" 2>nul
rmdir /s /q "%USERPROFILE%\AppData\Roaming\Python\Python311\site-packages\pandas" 2>nul

REM Install required packages with warnings suppressed
"%PYTHON_EXE%" -m pip install --quiet --upgrade --trusted-host pypi.org --trusted-host files.pythonhosted.org --disable-pip-version-check --no-warn-script-location pandas openpyxl requests python-docx 2>nul || (
    echo ERROR: Failed to install required packages
    echo [%date% %time%] ERROR: Failed to install required packages >> "%LOG_FILE%"
    pause
    exit /b 1
)

echo [%date% %time%] Executing I^&W Generator script...

REM Execute the Python script and capture output
"%PYTHON_EXE%" "%SCRIPT_PATH%" > "%LOG_DIR%\temp_output.log" 2>&1

REM Check exit code
if %ERRORLEVEL% EQU 0 (
    echo [%date% %time%] I^&W Generator completed successfully
    echo [%date% %time%] I^&W Generator completed successfully >> "%LOG_FILE%"
    type "%LOG_DIR%\temp_output.log" >> "%LOG_FILE%"
) else (
    echo [%date% %time%] I^&W Generator failed with error code %ERRORLEVEL%
    echo [%date% %time%] I^&W Generator failed with error code %ERRORLEVEL% >> "%LOG_FILE%"
    type "%LOG_DIR%\temp_output.log" >> "%LOG_FILE%"
)

REM Clean up temporary output file
if exist "%LOG_DIR%\temp_output.log" del "%LOG_DIR%\temp_output.log"

echo [%date% %time%] I^&W Report Generator batch script completed

REM Keep window open
pause

REM Exit with the same code as the Python script
exit /b %ERRORLEVEL%