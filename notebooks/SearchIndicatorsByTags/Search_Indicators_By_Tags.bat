@echo off
setlocal
cd /d "%~dp0"

echo Loading...

set "REQUIREMENTS_TXT=Z:\HTOC\Data_Analytics\Data\Threat Assessment Scores\SearchScripts\requirements.txt"

rem Local wheelhouse: install from wheels here first, then PyPI if needed.
set "WHEELHOUSE=Z:\HTOC\JA\wheelhouse"
if not exist "%WHEELHOUSE%" mkdir "%WHEELHOUSE%" 2>nul

rem Prefer wheels from wheelhouse (also writes cache when downloading from PyPI).
set "PIP_FIND_LINKS=%WHEELHOUSE%"

rem Optional: download wheels into wheelhouse only (for offline use), then exit:
rem   run_search_indicators_by_tags.bat populate
if /i "%~1"=="populate" goto :populate_wheels

rem Try installing from the wheelhouse first.
rem On the first run (or after wheelhouse updates), this will likely fail, so we
rem then download the required wheels into the wheelhouse and retry.
py -m pip install -q -r "%REQUIREMENTS_TXT%" --find-links "%WHEELHOUSE%" --prefer-binary --no-index >nul 2>&1
if errorlevel 1 (
    rem Download wheels into the wheelhouse (so future runs are faster/offline).
    py -m pip download -q -r "%REQUIREMENTS_TXT%" -d "%WHEELHOUSE%" --find-links "%WHEELHOUSE%" --prefer-binary --only-binary=:all: >nul 2>&1
    if errorlevel 1 (
        rem If download fails (e.g. no network), fall back to regular install.
        py -m pip install -q -r "%REQUIREMENTS_TXT%" --find-links "%WHEELHOUSE%" --prefer-binary >nul 2>&1
    ) else (
        py -m pip install -q -r "%REQUIREMENTS_TXT%" --find-links "%WHEELHOUSE%" --prefer-binary --no-index >nul 2>&1
    )
)

rem Also ensure tabulate/openpyxl are present in the wheelhouse.
py -m pip install -q tabulate openpyxl --find-links "%WHEELHOUSE%" --prefer-binary --no-index >nul 2>&1
if errorlevel 1 (
    py -m pip download -q tabulate openpyxl -d "%WHEELHOUSE%" --find-links "%WHEELHOUSE%" --prefer-binary --only-binary=:all: >nul 2>&1
    if errorlevel 1 (
        py -m pip install -q tabulate openpyxl --find-links "%WHEELHOUSE%" --prefer-binary >nul 2>&1
    ) else (
        py -m pip install -q tabulate openpyxl --find-links "%WHEELHOUSE%" --prefer-binary --no-index >nul 2>&1
    )
)

rem Interactive tag search only (no prior clutter).
cls
py "Z:\HTOC\Data_Analytics\Data\Threat Assessment Scores\SearchScripts\search_indicators_by_tags.py" --interactive --show-scores-records

pause
goto :eof

:populate_wheels
py -m pip download -q -r "%REQUIREMENTS_TXT%" -d "%WHEELHOUSE%" --find-links "%WHEELHOUSE%" --only-binary=:all: >nul 2>&1
if errorlevel 1 (
    echo pip download failed.
    pause
    exit /b 1
)
exit /b 0
