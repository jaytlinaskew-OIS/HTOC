$ErrorActionPreference='Stop'
$taskApp=$PSScriptRoot
$taskPython='C:\Users\jaskew\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$taskOutput=Join-Path $taskApp 'managed-task-output.log'
if((Test-Path -LiteralPath $taskOutput) -and (Get-Item -LiteralPath $taskOutput).Length -gt 262144){Move-Item -LiteralPath $taskOutput -Destination ($taskOutput+'.old') -Force}
# Windows PowerShell 5 treats benign Python stderr warnings as errors. Preserve the Python exit code.
$ErrorActionPreference='Continue'
& $taskPython (Join-Path $taskApp 'managed_refresh.py') --config (Join-Path $taskApp 'managed-config.json') 2>&1 | Out-File -LiteralPath $taskOutput -Encoding utf8 -Append
exit $LASTEXITCODE
