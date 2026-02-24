@echo off
setlocal EnableExtensions EnableDelayedExpansion
REM ============================================================================
REM I&W Expanded Spreadsheet - Batch Script (Enterprise-hardened, original-style behavior)
REM - Robust timestamp (no spaces/colons)
REM - Logs everything (pip + script)
REM - Uses local TEMP for pip (C:\Temp) to avoid network-drive flakiness
REM - pip: timeout/retries/no-cache + trusted-host
REM - Optional offline wheelhouse fallback
REM ============================================================================
echo [%date% %time%] Starting I^&W Expanded Spreadsheet...

REM ── Set the Python executable path ──────────────────────────────────────────
set "PYTHON_EXE=Z:\HTOC\JA\Python313\python.exe"

REM ── Set script + working directory ─────────────────────────────────────────
set "SCRIPT_PATH=Z:\HTOC\HTOC Reports\I&W Reports\5. I&W Staging\I&W Report Processing Scripts\Expanded Scripts\I&W_Document_expanded_spreadsheet.py"
set "WORK_DIR=Z:\HTOC\HTOC Reports\I&W Reports\5. I&W Staging\I&W Report Processing Scripts\Expanded Scripts"

REM ── Set log directory ──────────────────────────────────────────────────────
set "LOG_DIR=Z:\HTOC\HTOC Reports\I&W Reports\5. I&W Staging\logs"

REM ── Optional offline wheelhouse folder (create once) ───────────────────────
set "WHEELHOUSE=Z:\HTOC\JA\wheelhouse"

REM ── Set spreadsheet output directory ────────────────────────────────────────────────────────────────────
set "OUTPUT_DIR=Z:\HTOC\HTOC Reports\I&W Reports\5. I&W Staging\Expanded Reports"

REM ── Create log directory if it doesn't exist ───────────────────────────────
if not exist "%LOG_DIR%" (
    mkdir "%LOG_DIR%"
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to create log directory. Error level: %ERRORLEVEL%
        pause
        exit /b 1
    )
)

REM ── Safe timestamp (avoids spaces/colons) ───────────────────────────────────
set "YYYY=%date:~-4,4%"
set "MM=%date:~-10,2%"
set "DD=%date:~-7,2%"
set "HH=%time:~0,2%"
if "%HH:~0,1%"==" " set "HH=0%HH:~1,1%"
set "NN=%time:~3,2%"
set "SS=%time:~6,2%"
set "TS=%YYYY%%MM%%DD%_%HH%%NN%%SS%"

REM ── Log files ──────────────────────────────────────────────────────────────
set "LOG_FILE=%LOG_DIR%\iw_expanded_spreadsheet_%TS%.log"
set "TEMP_OUT=%LOG_DIR%\temp_output_%TS%.log"

echo [%date% %time%] Log file: "%LOG_FILE%"
echo [%date% %time%] Starting I^&W Expanded Spreadsheet...> "%LOG_FILE%" 2>nul
echo [%date% %time%] Log file: "%LOG_FILE%">> "%LOG_FILE%" 2>nul

REM ── Change to working directory (quoted handles &) ─────────────────────────
pushd "%WORK_DIR%" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to change to working directory. Error level: %ERRORLEVEL%
    echo [%date% %time%] ERROR: Failed to change to working directory >> "%LOG_FILE%" 2>nul
    pause
    exit /b 1
)

REM ── Sanity checks ───────────────────────────────────────────────────────────
if not exist "%PYTHON_EXE%" (
    echo [ERROR] Python executable not found at %PYTHON_EXE%
    echo [%date% %time%] ERROR: Python executable not found >> "%LOG_FILE%" 2>nul
    popd >nul
    pause
    exit /b 1
)

if not exist "%SCRIPT_PATH%" (
    echo [ERROR] Script not found at "%SCRIPT_PATH%"
    echo [%date% %time%] ERROR: Script not found at "%SCRIPT_PATH%">> "%LOG_FILE%" 2>nul
    popd
    pause
    exit /b 1
)

REM ── Force local TEMP for pip (reduces Z:\ network instability) ─────────────
set "TMP=C:\Temp"
set "TEMP=C:\Temp"
if not exist "%TMP%" mkdir "%TMP%" >nul 2>&1

REM ── Package installation settings ──────────────────────────────────────────
set "PIP_FLAGS=--quiet --user --disable-pip-version-check --no-warn-script-location --timeout 120 --retries 20 --no-cache-dir"
set "PIP_TRUST=--trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host pypi.python.org"
set "PKGS=pandas openpyxl requests urllib3 pytz"

REM ── Install required packages (show output like original) ──────────────────
echo [%date% %time%] Installing required packages...
echo [%date% %time%] Installing required packages...>> "%LOG_FILE%" 2>nul

REM Try wheelhouse first if it exists (offline, faster, more reliable)
if exist "%WHEELHOUSE%" (
    echo [%date% %time%] Attempting install from wheelhouse ^(offline^)
    echo [%date% %time%] Attempting install from wheelhouse>> "%LOG_FILE%" 2>nul
    
    "%PYTHON_EXE%" -m pip install --user --no-index --find-links="%WHEELHOUSE%" %PKGS% > "%TEMP_OUT%" 2>&1
    set "PIP_EXIT=!ERRORLEVEL!"
    
    type "%TEMP_OUT%"
    type "%TEMP_OUT%" >> "%LOG_FILE%" 2>nul
    
    if "!PIP_EXIT!"=="0" (
        echo.
        echo ========================================================================================================
        echo [SUCCESS] Packages installed from WHEELHOUSE ^(offline^)
        echo ========================================================================================================
        echo.
        echo [%date% %time%] SUCCESS: Packages installed from wheelhouse>> "%LOG_FILE%" 2>nul
        goto :pip_done
    )
    
    REM Check if packages were already satisfied from wheelhouse attempt
    findstr /C:"Requirement already satisfied" "%TEMP_OUT%" >nul
    set "FINDSTR_EXIT=!ERRORLEVEL!"
    
    if "!FINDSTR_EXIT!"=="0" (
        echo.
        echo ========================================================================================================
        echo [SUCCESS] Packages already installed ^(satisfied from cache^)
        echo ========================================================================================================
        echo.
        echo [%date% %time%] SUCCESS: Packages already satisfied>> "%LOG_FILE%" 2>nul
        goto :pip_done
    )
    
    echo [WARNING] Wheelhouse install failed. Error level: !PIP_EXIT!
    echo [WARNING] Falling back to online PyPI installation...
    echo [%date% %time%] WARNING: Wheelhouse failed, trying PyPI>> "%LOG_FILE%" 2>nul
    echo.
)

REM Attempt online install from PyPI (either wheelhouse doesn't exist or failed)
echo [%date% %time%] Attempting install from PyPI ^(online^)...
echo [%date% %time%] Attempting install from PyPI>> "%LOG_FILE%" 2>nul

"%PYTHON_EXE%" -m pip install %PIP_FLAGS% %PIP_TRUST% %PKGS% > "%TEMP_OUT%" 2>&1
set "PIP_EXIT=!ERRORLEVEL!"

type "%TEMP_OUT%"
type "%TEMP_OUT%" >> "%LOG_FILE%" 2>nul

if "!PIP_EXIT!"=="0" (
    echo.
    echo ========================================================================================================
    echo [SUCCESS] Packages installed from PyPI ^(online^)
    echo ========================================================================================================
    echo.
    echo [%date% %time%] SUCCESS: Packages installed from PyPI>> "%LOG_FILE%" 2>nul
    
    REM Download packages to wheelhouse for future offline use
    echo [INFO] Caching packages to wheelhouse for future offline use...
    echo [%date% %time%] Caching packages to wheelhouse>> "%LOG_FILE%" 2>nul
    
    REM Create wheelhouse directory if it doesn't exist
    if not exist "%WHEELHOUSE%" (
        mkdir "%WHEELHOUSE%" 2>nul
        if not exist "%WHEELHOUSE%" (
            echo [WARNING] Could not create wheelhouse directory
            echo [%date% %time%] WARNING: Could not create wheelhouse directory>> "%LOG_FILE%" 2>nul
            goto :pip_done
        )
    )
    
    REM Download packages to wheelhouse
    "%PYTHON_EXE%" -m pip download --dest="%WHEELHOUSE%" %PKGS% > "%TEMP_OUT%" 2>&1
    set "DOWNLOAD_EXIT=!ERRORLEVEL!"
    
    if "!DOWNLOAD_EXIT!"=="0" (
        echo [SUCCESS] Packages cached to wheelhouse successfully
        echo [%date% %time%] SUCCESS: Packages cached to wheelhouse>> "%LOG_FILE%" 2>nul
    ) else (
        echo [WARNING] Failed to cache packages to wheelhouse ^(Error: !DOWNLOAD_EXIT!^)
        echo [%date% %time%] WARNING: Failed to cache to wheelhouse. Error: !DOWNLOAD_EXIT!>> "%LOG_FILE%" 2>nul
    )
    
    goto :pip_done
)

REM If we get here, PyPI also failed - check if packages were already satisfied
findstr /C:"Requirement already satisfied" "%TEMP_OUT%" >nul
set "FINDSTR_EXIT=!ERRORLEVEL!"

if "!FINDSTR_EXIT!"=="0" (
    echo.
    echo ========================================================================================================
    echo [SUCCESS] Packages already installed ^(satisfied from cache^)
    echo ========================================================================================================
    echo.
    echo [%date% %time%] SUCCESS: Packages already satisfied>> "%LOG_FILE%" 2>nul
    
    REM Try to cache to wheelhouse if not already there (optional, non-fatal)
    if not exist "%WHEELHOUSE%" (
        mkdir "%WHEELHOUSE%" 2>nul
    )
    
    if exist "%WHEELHOUSE%" (
        echo [INFO] Updating wheelhouse cache...
        "%PYTHON_EXE%" -m pip download --dest="%WHEELHOUSE%" %PKGS% >nul 2>&1
        if !ERRORLEVEL!==0 (
            echo [INFO] Wheelhouse cache updated
            echo [%date% %time%] INFO: Wheelhouse cache updated>> "%LOG_FILE%" 2>nul
        )
    )
    
    goto :pip_done
)

REM Both wheelhouse and PyPI failed
echo.
echo ========================================================================================================
echo [ERROR] Package installation failed from all sources
echo ========================================================================================================
echo [ERROR] Both wheelhouse and PyPI installation failed. Error level: !PIP_EXIT!
echo [%date% %time%] ERROR: All package installation attempts failed. Error level: !PIP_EXIT!>> "%LOG_FILE%" 2>nul
del "%TEMP_OUT%" >nul 2>&1
popd >nul
pause
exit /b 1

:pip_done
del "%TEMP_OUT%" >nul 2>&1

REM ── Execute the Python script and capture output ────────────────────────────
echo.
echo ========================================================================================================
echo EXECUTING I^&W EXPANDED SPREADSHEET SCRIPT
echo ========================================================================================================
echo [%date% %time%] Executing I^&W Expanded Spreadsheet script...
echo [%date% %time%] Executing I^&W Expanded Spreadsheet script...>> "%LOG_FILE%" 2>nul

"%PYTHON_EXE%" "%SCRIPT_PATH%" > "%TEMP_OUT%" 2>&1
set "SCRIPT_EXIT_CODE=!ERRORLEVEL!"

REM ── Display and log script output ───────────────────────────────────────────
type "%TEMP_OUT%"
echo ========================================================================================================
type "%TEMP_OUT%" >> "%LOG_FILE%" 2>nul

REM ── Detailed success/failure handling (like original) ───────────────────────
echo.
if "!SCRIPT_EXIT_CODE!"=="0" (
    echo ========================================================================================================
    echo [SUCCESS] I^&W Expanded Spreadsheet completed successfully
    echo ========================================================================================================
    echo.
    
    REM Parse output for record counts
    set "RECORD_COUNT=0"
    set "INDICATORS_FOUND=Unknown"
    
    for /f "tokens=*" %%a in ('findstr /C:"Retrieved" /C:"indicators ready" /C:"Final filtered dataset" "%TEMP_OUT%"') do (
        echo [INFO] %%a
        set "LINE=%%a"
    )
    
    REM Check if no records
    findstr /C:"No indicators met the filtering criteria" "%TEMP_OUT%" >nul
    set "NO_RECORDS=!ERRORLEVEL!"
    
    if "!NO_RECORDS!"=="0" (
        echo.
        echo --------------------------------------------------------------------------------------------------------
        echo RESULT: No indicators met filtering criteria
        echo --------------------------------------------------------------------------------------------------------
        echo Excel File: NOT CREATED ^(no records to export^)
        echo --------------------------------------------------------------------------------------------------------
    ) else (
        REM Check for Excel file creation
        echo.
        echo --------------------------------------------------------------------------------------------------------
        if exist "%OUTPUT_DIR%\*.xlsx" (
            REM Find the most recent Excel file
            for /f "delims=" %%f in ('dir /b /od "%OUTPUT_DIR%\*.xlsx" 2^>nul') do set "LATEST_FILE=%%f"
            
            if defined LATEST_FILE (
                echo RESULT: Excel spreadsheet created successfully
                echo --------------------------------------------------------------------------------------------------------
                echo File Name: !LATEST_FILE!
                echo Location:  "%OUTPUT_DIR%\"
                
                REM Get file size
                for %%a in ("%OUTPUT_DIR%\!LATEST_FILE!") do set "FILE_SIZE=%%~za"
                
                REM Convert bytes to KB
                set /a SIZE_KB=!FILE_SIZE! / 1024
                echo File Size: !SIZE_KB! KB ^(!FILE_SIZE! bytes^)
                echo --------------------------------------------------------------------------------------------------------
            ) else (
                echo RESULT: Excel file status unknown
                echo --------------------------------------------------------------------------------------------------------
                echo Excel File: Unable to verify
                echo --------------------------------------------------------------------------------------------------------
            )
        ) else (
            echo RESULT: No Excel file found in output directory
            echo --------------------------------------------------------------------------------------------------------
            echo Excel File: NOT CREATED
            echo Output Dir: "%OUTPUT_DIR%"
            echo --------------------------------------------------------------------------------------------------------
        )
    )
    echo.
    
    if exist "%OUTPUT_DIR%\*.xlsx" (
        echo [%date% %time%] I^&W Expanded Spreadsheet completed successfully
        echo [%date% %time%] SUCCESS: I^&W Expanded Spreadsheet completed successfully>> "%LOG_FILE%" 2>nul
    ) else (
        echo [%date% %time%] I^&W Expanded Spreadsheet completed - No spreadsheet created
        echo [%date% %time%] INFO: No spreadsheet created>> "%LOG_FILE%" 2>nul
    )
) else (
    echo ========================================================================================================
    echo [ERROR] I^&W Expanded Spreadsheet failed
    echo ========================================================================================================
    echo Error Code: !SCRIPT_EXIT_CODE!
    echo ========================================================================================================
    echo.
    echo [%date% %time%] I^&W Expanded Spreadsheet failed with error code !SCRIPT_EXIT_CODE!
    echo [%date% %time%] ERROR: I^&W Expanded Spreadsheet failed with error code !SCRIPT_EXIT_CODE!>> "%LOG_FILE%" 2>nul

    set "ERROR_LOG=%LOG_DIR%\error_iw_expanded_spreadsheet_%TS%.log"
    (
        echo [%date% %time%] FAILURE DETAILS - Error Code: !SCRIPT_EXIT_CODE!
        echo Script Path: "%SCRIPT_PATH%"
        echo Working Directory: "%WORK_DIR%"
        echo Python Executable: %PYTHON_EXE%
        echo Wheelhouse: "%WHEELHOUSE%"
        echo ======== ERROR OUTPUT ========
        type "%TEMP_OUT%"
        echo ==============================
    ) > "%ERROR_LOG%" 2>nul

    echo [%date% %time%] Error details written to: "%ERROR_LOG%"
    echo [%date% %time%] Error log created: "%ERROR_LOG%">> "%LOG_FILE%" 2>nul
)

del "%TEMP_OUT%" >nul 2>&1

REM ── Final status ─────────────────────────────────────────────────────────────────────────────────────────
if "!SCRIPT_EXIT_CODE!"=="0" (
    echo ========================================================================================================
    echo [%date% %time%] Batch script completed successfully
    echo Log file: "%LOG_FILE%"
    echo ========================================================================================================
    echo [%date% %time%] Batch script completed successfully>> "%LOG_FILE%" 2>nul
) else (
    echo ========================================================================================================
    echo [%date% %time%] Batch script completed with errors
    echo Log file: "%LOG_FILE%"
    echo ========================================================================================================
    echo [%date% %time%] Batch script completed with errors>> "%LOG_FILE%" 2>nul
)

popd
pause
exit /b !SCRIPT_EXIT_CODE!
