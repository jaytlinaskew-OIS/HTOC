$ErrorActionPreference='Stop'
$taskSource=$PSScriptRoot
$taskApp='C:\Users\jaskew\AppData\Local\Packages\OpenAI.Codex_2p2nqsd0c76g0\LocalCache\Local\HTOC\IWDashboard'
$taskName='HTOC I&W Dashboard - Update Data'
$taskBackup=Join-Path $taskApp ('Deprecated\before-managed-automation-'+(Get-Date).ToString('yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $taskBackup -Force | Out-Null
$old=Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if($null -ne $old){Export-ScheduledTask -TaskName $taskName | Set-Content -LiteralPath (Join-Path $taskBackup 'previous-task.xml') -Encoding UTF8}
foreach($name in @('run_refresh.ps1','managed_refresh.py','display_window.ps1','validate_desktop.ps1','run_managed_refresh.ps1','manage_display.ps1')){
 $existing=Join-Path $taskApp $name
 if(Test-Path -LiteralPath $existing){Copy-Item -LiteralPath $existing -Destination (Join-Path $taskBackup $name)}
}
foreach($name in @('managed_refresh.py','display_window.ps1','validate_desktop.ps1','run_managed_refresh.ps1','manage_display.ps1')){Copy-Item -LiteralPath (Join-Path $taskSource $name) -Destination (Join-Path $taskApp $name) -Force}
# Retire the old entry point as well, so it cannot accidentally update the old PBIX location.
Copy-Item -LiteralPath (Join-Path $taskApp 'run_managed_refresh.ps1') -Destination (Join-Path $taskApp 'run_refresh.ps1') -Force
$taskAction=New-ScheduledTaskAction -Execute 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe' -Argument ('-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "'+(Join-Path $taskApp 'run_managed_refresh.ps1')+'"')
$taskUser=[Security.Principal.WindowsIdentity]::GetCurrent().Name
$taskTriggers=@((New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 1)),(New-ScheduledTaskTrigger -AtLogOn -User $taskUser))
$taskPrincipal=New-ScheduledTaskPrincipal -UserId $taskUser -LogonType Interactive -RunLevel Limited
$taskSettings=New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 5) -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName $taskName -Action $taskAction -Trigger $taskTriggers -Principal $taskPrincipal -Settings $taskSettings -Description 'Checks daily I&W workbooks every minute and refreshes a separately managed Power BI display. Preserves editable original; validates models before replacing the display.' -Force | Out-Null
$taskDashboard='\\cscso1fsappv01\data\HTOC\Data_Analytics\Data\Threat Assessment Scores\ThreatAssessI_W\Dashboard'
$taskShell=New-Object -ComObject WScript.Shell
foreach($pair in @(@('Open Live I&W Dashboard.lnk','Start'),@('Pause Live I&W Dashboard.lnk','Pause'))){
 $link=$taskShell.CreateShortcut((Join-Path $taskDashboard $pair[0]));$link.TargetPath='C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe';$link.Arguments='-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "'+(Join-Path $taskApp 'manage_display.ps1')+'" -Action '+$pair[1];$link.WorkingDirectory=$taskApp;$link.WindowStyle=7;$link.IconLocation='C:\Program Files\Microsoft Power BI Desktop\bin\PBIDesktop.exe,0';$link.Description=if($pair[1] -eq 'Start'){'Start the automatically updated display copy'}else{'Pause automatic updates and close only the managed display'};$link.Save()
}
Start-ScheduledTask -TaskName $taskName
Get-ScheduledTask -TaskName $taskName | Select-Object TaskName,State
