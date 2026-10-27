param([int]$PreviewPid=90900,[string]$Action,[string]$Expected,[string]$Capture)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName System.Drawing
Add-Type @"
using System; using System.Runtime.InteropServices; public class StackedInput { [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h); [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow(); [DllImport("user32.dll")] public static extern bool GetCursorPos(out POINT p); [DllImport("user32.dll")] public static extern bool SetCursorPos(int x,int y); [DllImport("user32.dll")] public static extern void keybd_event(byte v,byte s,uint f,UIntPtr e); [DllImport("user32.dll")] public static extern void mouse_event(uint f,uint x,uint y,uint d,UIntPtr e); public struct POINT {public int X; public int Y;} }
"@
$state=Get-Content -LiteralPath '\\cscso1fsappv01\home\jaskew\HTOC\dashboards\ThreatAssessment\fullheight_drawers_state.json' -Raw|ConvertFrom-Json
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
WaitPattern 'Showing * of 8 Indicators*' 30
$old=[StackedInput]::GetForegroundWindow();$point=New-Object StackedInput+POINT;[StackedInput]::GetCursorPos([ref]$point)|Out-Null
try {
 ClickControl ('Bookmark '+$Action) ('Bookmark '+$Expected+'*')
 Start-Sleep -Seconds 2;WaitPattern ('Bookmark '+$Expected+'*')
 if($Capture){Picture $Capture}
 Snapshot;$script:nodes|Where-Object {$_.Current.Name -like 'Bookmark *' -or $_.Current.Name -like 'Showing *'}|ForEach-Object {$_.Current.Name}
}finally{[StackedInput]::keybd_event(17,0,2,[UIntPtr]::Zero);[StackedInput]::SetCursorPos($point.X,$point.Y)|Out-Null;[StackedInput]::SetForegroundWindow($old)|Out-Null}
