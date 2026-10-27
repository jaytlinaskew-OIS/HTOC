$ErrorActionPreference='Stop'
Add-Type -AssemblyName WindowsBase
$taskRoot='\\cscso1fsappv01\home\jaskew\HTOC\dashboards\ThreatAssessment\native_validation'
$taskFile=Join-Path $taskRoot 'native_packaged.pbix'
$taskPackage=[System.IO.Packaging.Package]::Open($taskFile,[IO.FileMode]::Open,[IO.FileAccess]::ReadWrite)
try {
 $taskUri=New-Object Uri('/Report/Layout',[UriKind]::Relative)
 $taskPart=$taskPackage.GetPart($taskUri)
 $taskStream=$taskPart.GetStream([IO.FileMode]::Create,[IO.FileAccess]::Write)
 try {$taskBytes=[IO.File]::ReadAllBytes((Join-Path $taskRoot 'current-layout.bin'));$taskStream.Write($taskBytes,0,$taskBytes.Length)} finally {$taskStream.Dispose()}
 $taskBinding=New-Object Uri('/SecurityBindings',[UriKind]::Relative)
 if($taskPackage.PartExists($taskBinding)){$taskPackage.DeletePart($taskBinding)}
} finally {$taskPackage.Close()}
Write-Output 'Saved test candidate with native WindowsBase Packaging.'
