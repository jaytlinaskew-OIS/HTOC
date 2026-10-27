param([int]$PreviewPid=90340)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName System.Drawing
Add-Type @"
using System; using System.Runtime.InteropServices; public class StackedInput { [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h); [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow(); [DllImport("user32.dll")] public static extern bool GetCursorPos(out POINT p); [DllImport("user32.dll")] public static extern bool SetCursorPos(int x,int y); [DllImport("user32.dll")] public static extern void keybd_event(byte v,byte s,uint f,UIntPtr e); [DllImport("user32.dll")] public static extern void mouse_event(uint f,uint x,uint y,uint d,UIntPtr e); public struct POINT {public int X; public int Y;} }
"@
$state=Get-Content -LiteralPath '\\cscso1fsappv01\home\jaskew\HTOC\dashboards\ThreatAssessment\stacked_rails_state.json' -Raw|ConvertFrom-Json
function Snapshot {
 $script:window=[Windows.Automation.AutomationElement]::RootElement.FindAll([Windows.Automation.TreeScope]::Children,[Windows.Automation.Condition]::TrueCondition)|Where-Object {$_.Current.ProcessId -eq $PreviewPid}|Select-Object -First 1
 $script:nodes=if($null -ne $script:window){$script:window.FindAll([Windows.Automation.TreeScope]::Descendants,[Windows.Automation.Condition]::TrueCondition)}else{@()}
}
function WaitPattern([string]$pattern,[int]$seconds=20){
 $end=(Get-Date).AddSeconds($seconds)
 do {Snapshot;$found=$script:nodes|Where-Object {$_.Current.Name -like $pattern};if(-not $found){Start-Sleep -Milliseconds 500}}while(-not $found -and (Get-Date) -lt $end)
 if(-not $found){throw ('Expected UI missing: '+$pattern)}
}
function ClickControl([string]$prefix,[string]$expected){
 [StackedInput]::SetForegroundWindow([IntPtr]$script:window.Current.NativeWindowHandle)|Out-Null;Start-Sleep -Milliseconds 400
 if([StackedInput]::GetForegroundWindow() -ne [IntPtr]$script:window.Current.NativeWindowHandle){$script:window.SetFocus();Start-Sleep -Milliseconds 400}
 if([StackedInput]::GetForegroundWindow() -ne [IntPtr]$script:window.Current.NativeWindowHandle){throw 'Preview cannot receive input; unlock Windows before running the click test'}
 Snapshot
 $b=$script:nodes|Where-Object {$_.Current.Name -like ($prefix+'*')}|Sort-Object {$_.Current.BoundingRectangle.Height}|Select-Object -First 1
 if($null -eq $b){throw ('Control missing: '+$prefix)}
 $r=$b.Current.BoundingRectangle;[StackedInput]::SetCursorPos([int]($r.Left+$r.Width/2),[int]($r.Top+$r.Height/2+4))|Out-Null
 try {[StackedInput]::keybd_event(17,0,0,[UIntPtr]::Zero);Start-Sleep -Milliseconds 120;[StackedInput]::mouse_event(2,0,0,0,[UIntPtr]::Zero);Start-Sleep -Milliseconds 80;[StackedInput]::mouse_event(4,0,0,0,[UIntPtr]::Zero);Start-Sleep -Milliseconds 120}finally{[StackedInput]::keybd_event(17,0,2,[UIntPtr]::Zero)}
 WaitPattern $expected
}
function SelectPartner([string]$partner,[string]$context){
 Snapshot;$b=$script:nodes|Where-Object {$_.Current.Name -eq ('Partner '+$partner+'. Partner Block Area 1.')}|Select-Object -First 1
 if($null -eq $b){throw ('Partner missing: '+$partner)}
 $b.GetCurrentPattern([Windows.Automation.TogglePattern]::Pattern).Toggle();WaitPattern $context
}
function Picture([string]$name){
 [StackedInput]::SetForegroundWindow([IntPtr]$script:window.Current.NativeWindowHandle)|Out-Null;[StackedInput]::SetCursorPos(10,10)|Out-Null;Start-Sleep -Milliseconds 350
 $r=$script:window.Current.BoundingRectangle;$b=New-Object Drawing.Bitmap ([int]$r.Width),([int]$r.Height);$g=[Drawing.Graphics]::FromImage($b)
 try {$g.CopyFromScreen([int]$r.Left,[int]$r.Top,0,0,$b.Size);$b.Save((Join-Path $state.work ($name+'.png')))}finally{$g.Dispose();$b.Dispose()}
}
WaitPattern 'Showing 8 of 8 Indicators*All partners' 70
$old=[StackedInput]::GetForegroundWindow();$point=New-Object StackedInput+POINT;[StackedInput]::GetCursorPos([ref]$point)|Out-Null
try {
 Snapshot
 $initialNotes=$script:nodes|Where-Object {$_.Current.Name -match '^Indicator Assessment Notes\s*$' -and $_.Current.ControlType -eq [Windows.Automation.ControlType]::Group}|Select-Object -First 1
 $initialNoteNodes=$initialNotes.FindAll([Windows.Automation.TreeScope]::Descendants,[Windows.Automation.Condition]::TrueCondition)
 $initialNoteRows=@($initialNoteNodes|Where-Object {$_.Current.Name -like 'Select Row *'})
 if($initialNoteRows.Count -ne 1 -or $initialNoteRows[0].Current.Name -notlike '*103.214.44.138*'){throw 'Notes must default to the one highest-scoring Indicator'}
 'Default assessment: one row, 103.214.44.138'
 Picture 'both-collapsed'
 ClickControl 'Bookmark Expand Partners' 'Bookmark Collapse Partners*'
 SelectPartner 'HRSA' 'Showing 4 of 8 Indicators*HRSA'
 ClickControl 'Bookmark Collapse Partners' 'Bookmark Expand Partners*'
 WaitPattern 'Showing 4 of 8 Indicators*HRSA'
 ClickControl 'Bookmark Expand reported I&W' 'Bookmark Collapse reported I&W*'
 WaitPattern 'Showing 4 of 8 Indicators*HRSA'
 ClickControl 'Bookmark Expand Partners' 'Bookmark Collapse Partners*'
 SelectPartner 'CMS' 'Showing 3 of 8 Indicators*CMS'
 Picture 'both-expanded'
 # Use a detail row's native selection pattern to filter the notes independently.
 Snapshot;$rows=@($script:nodes|Where-Object {$_.Current.Name -match '^Select Row (\S+) High '});$row=$rows|Select-Object -Last 1
 if($null -eq $row){throw 'No Indicator detail row found'}
 $selectedIndicator=[regex]::Match($row.Current.Name,'^Select Row (\S+) High ').Groups[1].Value
 $patterns=@($row.GetSupportedPatterns()|ForEach-Object {$_.ProgrammaticName});'Row patterns: '+($patterns -join ', ')
 if($patterns -contains 'SelectionItemPatternIdentifiers.Pattern'){$row.GetCurrentPattern([Windows.Automation.SelectionItemPattern]::Pattern).Select()}
 else {
  [StackedInput]::SetForegroundWindow([IntPtr]$script:window.Current.NativeWindowHandle)|Out-Null;Start-Sleep -Milliseconds 300;$r=$row.Current.BoundingRectangle
  [StackedInput]::SetCursorPos([int]($r.Left+40),[int]($r.Top+$r.Height/2))|Out-Null;[StackedInput]::mouse_event(2,0,0,0,[UIntPtr]::Zero);Start-Sleep -Milliseconds 80;[StackedInput]::mouse_event(4,0,0,0,[UIntPtr]::Zero)
 }
 Start-Sleep -Seconds 2;Snapshot
 $notes=$script:nodes|Where-Object {$_.Current.Name -match '^Indicator Assessment Notes\s*$' -and $_.Current.ControlType -eq [Windows.Automation.ControlType]::Group}|Select-Object -First 1
 if($null -eq $notes){throw 'Assessment notes visual not rendered'}
 $notesNames=@($notes.FindAll([Windows.Automation.TreeScope]::Descendants,[Windows.Automation.Condition]::TrueCondition)|ForEach-Object {$_.Current.Name})
 if(-not ($notesNames -match [regex]::Escape($selectedIndicator))){throw 'Selected Indicator notes are not present'}
 if(@($notesNames|Where-Object {$_ -like 'Select Row *'}).Count -ne 1){throw 'More than one assessment displayed'}
 'Selected Indicator notes present: '+$selectedIndicator
 Picture 'selected-assessment'
 $afterSelectionContext=($script:nodes|Where-Object {$_.Current.Name -like 'Showing * of 8 Indicators*'}|Select-Object -First 1).Current.Name
 ClickControl 'Bookmark Collapse reported I&W' 'Bookmark Expand reported I&W*'
 WaitPattern $afterSelectionContext
 ClickControl 'Bookmark Collapse Partners' 'Bookmark Expand Partners*'
 WaitPattern $afterSelectionContext
 @{status='passed';states_tested=4;partner_filter_persisted=$true;selected_indicator=$selectedIndicator;assessment_notes_present=$true}|ConvertTo-Json -Compress|Set-Content -LiteralPath (Join-Path $state.work 'native-validation.json') -Encoding utf8
 'Four drawer states, partner-filter persistence, and assessment selection PASSED'
}finally{[StackedInput]::keybd_event(17,0,2,[UIntPtr]::Zero);[StackedInput]::SetCursorPos($point.X,$point.Y)|Out-Null;[StackedInput]::SetForegroundWindow($old)|Out-Null}
