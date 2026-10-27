param([ValidateSet('Ensure','Stop')][string]$Action,[string]$DisplayFile,[string]$ProcessState)
$ErrorActionPreference='Stop'
[Console]::OutputEncoding=New-Object System.Text.UTF8Encoding($false)
$owned=$null
if(Test-Path -LiteralPath $ProcessState){
 $saved=Get-Content -LiteralPath $ProcessState -Raw | ConvertFrom-Json
 $process=Get-Process -Id $saved.pid -ErrorAction SilentlyContinue
 if($null -ne $process -and $process.ProcessName -eq 'PBIDesktop' -and $process.StartTime.ToUniversalTime().Ticks.ToString() -eq $saved.start_ticks){
  $details=Get-CimInstance Win32_Process -Filter ('ProcessId='+$process.Id)
  if($details.CommandLine -like ('*"'+$DisplayFile+'"*')){$owned=$process}
 }
}
if($Action -eq 'Stop'){
 if($null -ne $owned){Stop-Process -Id $owned.Id -Force; Wait-Process -Id $owned.Id -Timeout 12 -ErrorAction SilentlyContinue}
 Remove-Item -LiteralPath $ProcessState -ErrorAction SilentlyContinue
 @{status='stopped-owned-display'} | ConvertTo-Json -Compress
 exit 0
}
if($null -ne $owned){@{status='already-open';pid=$owned.Id}|ConvertTo-Json -Compress;exit 0}
# Only this recorded process may be restarted. Other Power BI windows are never closed.
$p=Start-Process -FilePath 'C:\Program Files\Microsoft Power BI Desktop\bin\PBIDesktop.exe' -ArgumentList ('"'+$DisplayFile+'"') -WindowStyle Hidden -PassThru
$state=@{pid=$p.Id;start_ticks=$p.StartTime.ToUniversalTime().Ticks.ToString();file=$DisplayFile}
$state|ConvertTo-Json|Set-Content -LiteralPath $ProcessState -Encoding UTF8
@{status='opened';pid=$p.Id}|ConvertTo-Json -Compress
