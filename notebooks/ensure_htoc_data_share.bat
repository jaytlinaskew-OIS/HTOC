@echo off
REM ============================================================================
REM Establish SMB access to the HTOC data share for Task Scheduler
REM (run whether logged on or not / session 0).
REM
REM Use the hostname, not \\10.1.4.22 — IP forces NTLM and fails logged-off
REM even though \\cscso1fsappv01\home already works. Same volume (CSCSO1FSAPPV01).
REM Do NOT setlocal: HTOC_SHARE_ROOT must remain in the caller.
REM ============================================================================
if not defined HTOC_DATA_ROOT set "HTOC_DATA_ROOT=\\cscso1fsappv01\data"
if not defined HTOC_SHARE_ROOT set "HTOC_SHARE_ROOT=%HTOC_DATA_ROOT%\HTOC"

if exist "%HTOC_SHARE_ROOT%\Data_Analytics\threatconnect\ThreatConnect.py" (
    echo SHARE_OK %HTOC_SHARE_ROOT%
    exit /b 0
)

echo SHARE_MAP net use %HTOC_DATA_ROOT%
net use "%HTOC_DATA_ROOT%" /persistent:no
if exist "%HTOC_SHARE_ROOT%\Data_Analytics\threatconnect\ThreatConnect.py" (
    echo SHARE_OK %HTOC_SHARE_ROOT%
    exit /b 0
)

echo SHARE_REMAP delete+retry %HTOC_DATA_ROOT%
net use "%HTOC_DATA_ROOT%" /delete /y >nul 2>&1
net use "%HTOC_DATA_ROOT%" /persistent:no
if exist "%HTOC_SHARE_ROOT%\Data_Analytics\threatconnect\ThreatConnect.py" (
    echo SHARE_OK %HTOC_SHARE_ROOT%
    exit /b 0
)

echo SHARE_FAIL cannot reach %HTOC_SHARE_ROOT% (hostname SMB). Logged-off tasks cannot use \\10.1.4.22.
exit /b 3
