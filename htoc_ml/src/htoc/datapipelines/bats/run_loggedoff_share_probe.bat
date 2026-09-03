@echo off
setlocal EnableExtensions EnableDelayedExpansion
REM Fast session-0 probe: share access + ThreatConnect import + obs files.
REM Invoked via Task Scheduler so it matches "run whether logged on or not".

if not exist "C:\Temp" mkdir "C:\Temp" >nul 2>&1
set "LOG=C:\Temp\htoc_loggedoff_probe.log"
echo ===== %date% %time% probe start ===== > "%LOG%"

if not defined HTOC_SHARE_ROOT set "HTOC_SHARE_ROOT=\\cscso1fsappv01\data\HTOC"
call "%~dp0ensure_htoc_data_share.bat" >> "%LOG%" 2>&1
if errorlevel 1 (
    echo PROBE_FAIL share >> "%LOG%"
    echo PROBE_FAIL share
    exit /b 3
)

py -3.13 -c "import os,sys; r=os.environ.get('HTOC_SHARE_ROOT', r'\\cscso1fsappv01\data\HTOC'); sys.path.insert(0, os.path.join(r,'Data_Analytics','threatconnect')); from ThreatConnect import ThreatConnect; d=os.path.join(r,r'Data_Analytics\Data\OpDiv_Observations'); n=len([f for f in os.listdir(d) if f.startswith('htoc_opdiv_obs_d')]); print('import_ok'); print('obs_csv', n); print('PROBE_OK')" >> "%LOG%" 2>&1
if errorlevel 1 (
    echo PROBE_FAIL python >> "%LOG%"
    echo PROBE_FAIL python
    exit /b 2
)
findstr /C:"PROBE_OK" "%LOG%" >nul
if errorlevel 1 (
    echo PROBE_FAIL marker >> "%LOG%"
    exit /b 2
)
echo ===== %date% %time% probe ok ===== >> "%LOG%"
type "%LOG%"
exit /b 0
