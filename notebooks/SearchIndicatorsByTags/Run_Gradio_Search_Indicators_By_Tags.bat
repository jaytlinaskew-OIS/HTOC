@echo off
setlocal
cd /d "%~dp0"

echo Loading Gradio Search UI...

if not exist "Z:\HTOC\Data_Analytics\Data\Threat Assessment Scores\SearchScripts\Gradio\requirements.txt" (
    echo requirements.txt not found in "%cd%"
    pause
    exit /b 1
)

py -m pip install -q -r "Z:\HTOC\Data_Analytics\Data\Threat Assessment Scores\SearchScripts\Gradio\requirements.txt"
if errorlevel 1 (
    echo Failed to install requirements.
    pause
    exit /b 1
)

py "Z:\HTOC\Data_Analytics\Data\Threat Assessment Scores\SearchScripts\Gradio\gradio_search_indicators.py"
if errorlevel 1 (
    echo Failed to launch Gradio app.
)

pause
