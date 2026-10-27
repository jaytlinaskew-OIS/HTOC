$ErrorActionPreference='Stop'
Add-Type -AssemblyName WindowsBase
$taskRoot='\\cscso1fsappv01\home\jaskew\HTOC\dashboards\ThreatAssessment\native_validation'
$taskPackage=[IO.Packaging.Package]::Open((Join-Path $taskRoot 'native_repaired.pbix'),[IO.FileMode]::Open,[IO.FileAccess]::ReadWrite)
try {
 $taskPart=$taskPackage.GetPart((New-Object Uri('/DataModel',[UriKind]::Relative)))
 $taskStream=$taskPart.GetStream([IO.FileMode]::Create,[IO.FileAccess]::Write)
 try {$taskBytes=[IO.File]::ReadAllBytes((Join-Path $taskRoot 'repaired.abf'));$taskStream.Write($taskBytes,0,$taskBytes.Length)} finally {$taskStream.Dispose()}
} finally {$taskPackage.Close()}
Write-Output 'Repaired candidate packaged natively.'
