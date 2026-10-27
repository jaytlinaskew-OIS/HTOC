param([Parameter(Mandatory=$true)][string]$InputPath,[Parameter(Mandatory=$true)][string]$OutputPath)
$ErrorActionPreference='Stop'
$taskWord=$null;$taskDoc=$null
try{
 $taskWord=New-Object -ComObject Word.Application
 $taskWord.Visible=$false;$taskWord.DisplayAlerts=0
 if($taskWord.Documents.Count -ne 0){throw 'Refusing to use a Word instance with existing documents'}
 $taskDoc=$taskWord.Documents.Open($InputPath,$false,$true,$false)
 $taskDoc.Repaginate()
 $taskDoc.ExportAsFixedFormat($OutputPath,17)
 Write-Output ('Native Word rendered PDF: '+$OutputPath)
}finally{
 if($null -ne $taskDoc){[object]$taskNoSave=0;$taskDoc.Close([ref]$taskNoSave);[void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($taskDoc)}
 if($null -ne $taskWord){[object]$taskNoSave=0;$taskWord.Quit([ref]$taskNoSave);[void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($taskWord)}
}

