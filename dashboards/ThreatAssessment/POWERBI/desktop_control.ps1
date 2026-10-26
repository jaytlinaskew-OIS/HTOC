param([string]$Action='inspect',[string]$Target='',[string]$Value='')
Add-Type -AssemblyName UIAutomationClient
$taskP=Get-Process PBIDesktop | Sort-Object StartTime -Descending | Select-Object -First 1
$taskC=New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ProcessIdProperty,$taskP.Id)
$taskWs=[System.Windows.Automation.AutomationElement]::RootElement.FindAll([System.Windows.Automation.TreeScope]::Children,$taskC)
if($Action -eq 'inspect') {
 foreach($w in $taskWs){Write-Output ('WINDOW: '+$w.Current.Name);$w.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)|ForEach-Object {if($_.Current.Name -and -not $_.Current.IsOffscreen){'{0} | {1} | {2}' -f $_.Current.ControlType.ProgrammaticName,$_.Current.AutomationId,$_.Current.Name}}|Select-Object -First 1000};exit
}
$taskMatches=@(foreach($w in $taskWs){$w.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)|Where-Object {($_.Current.Name -eq $Target -or $_.Current.AutomationId -eq $Target) -and -not $_.Current.IsOffscreen}})
if($taskMatches.Count -eq 0){throw ('No visible control: '+$Target)}
$taskE=$taskMatches[-1];$pat=$null
switch($Action){
 'click' {if($taskE.TryGetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern,[ref]$pat)){$pat.Invoke()}elseif($taskE.TryGetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern,[ref]$pat)){$pat.Select()}else{throw 'No click pattern'}}
 'set' {if($taskE.TryGetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern,[ref]$pat)){$pat.SetValue($Value)}else{throw 'No value pattern'}}
 'toggle' {if($taskE.TryGetCurrentPattern([System.Windows.Automation.TogglePattern]::Pattern,[ref]$pat)){if($pat.Current.ToggleState -ne [System.Windows.Automation.ToggleState]::On){$pat.Toggle()};Write-Output $pat.Current.ToggleState}else{throw 'No toggle pattern'}}
}
Write-Output ($Action+': '+$Target)


