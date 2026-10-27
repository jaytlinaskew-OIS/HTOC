param([int]$PreviewPid=67028)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName System.Drawing
Add-Type @"
using System; using System.Runtime.InteropServices; public class DrawerInput { [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h); [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow(); [DllImport("user32.dll")] public static extern bool GetCursorPos(out POINT p); [DllImport("user32.dll")] public static extern bool SetCursorPos(int x,int y); [DllImport("user32.dll")] public static extern void keybd_event(byte v,byte s,uint f,UIntPtr e); [DllImport("user32.dll")] public static extern void mouse_event(uint f,uint x,uint y,uint d,UIntPtr e); public struct POINT {public int X; public int Y;} }
"@
function Snapshot { if($null -ne $script:window){$script:nodes=$script:window.FindAll([Windows.Automation.TreeScope]::Descendants,[Windows.Automation.Condition]::TrueCondition)}else{$script:nodes=@()} }
$deadline=(Get-Date).AddSeconds(70)
do {
 $script:window=[Windows.Automation.AutomationElement]::RootElement.FindAll([Windows.Automation.TreeScope]::Children,[Windows.Automation.Condition]::TrueCondition) | Where-Object {$_.Current.ProcessId -eq $PreviewPid} | Select-Object -First 1
 Snapshot
 $ready=$script:nodes | Where-Object {$_.Current.Name -match '^Showing [48] of 8 Indicators'}
 if(-not $ready){Start-Sleep -Seconds 2}
} while(-not $ready -and (Get-Date) -lt $deadline)
if(-not $ready){throw 'Dashboard did not finish rendering'}
$old=[DrawerInput]::GetForegroundWindow();$point=New-Object DrawerInput+POINT;[DrawerInput]::GetCursorPos([ref]$point)|Out-Null
function ClickBookmark([string]$prefix){
 Snapshot
 $button=$script:nodes | Where-Object {$_.Current.Name -like ($prefix+'*')} | Sort-Object {$_.Current.BoundingRectangle.Height} | Select-Object -First 1
 if($null -eq $button){throw ('Button missing: '+$prefix)}
 [DrawerInput]::SetForegroundWindow([IntPtr]$script:window.Current.NativeWindowHandle)|Out-Null;Start-Sleep -Milliseconds 350
 Snapshot; $button=$script:nodes | Where-Object {$_.Current.Name -like ($prefix+'*')} | Sort-Object {$_.Current.BoundingRectangle.Height} | Select-Object -First 1; $r=$button.Current.BoundingRectangle
 [DrawerInput]::SetCursorPos([int]($r.Left+$r.Width/2),[int]($r.Top+$r.Height/2+4))|Out-Null
 [DrawerInput]::keybd_event(17,0,0,[UIntPtr]::Zero);Start-Sleep -Milliseconds 70
 [DrawerInput]::mouse_event(2,0,0,0,[UIntPtr]::Zero);Start-Sleep -Milliseconds 80;[DrawerInput]::mouse_event(4,0,0,0,[UIntPtr]::Zero);Start-Sleep -Milliseconds 100
 [DrawerInput]::keybd_event(17,0,2,[UIntPtr]::Zero);Start-Sleep -Milliseconds 1000;Snapshot
 $want=if($prefix -like '*Collapse*'){'Bookmark Show reported I&W'}else{'Bookmark Collapse the reported I&W'}
 $end=(Get-Date).AddSeconds(15)
 while(-not ($script:nodes | Where-Object {$_.Current.Name -like ($want+'*')}) -and (Get-Date) -lt $end){Start-Sleep -Milliseconds 500;Snapshot}
}
function Picture([string]$name){
 [DrawerInput]::SetForegroundWindow([IntPtr]$script:window.Current.NativeWindowHandle)|Out-Null;[DrawerInput]::SetCursorPos(10,10)|Out-Null;Start-Sleep -Milliseconds 350
 $r=$script:window.Current.BoundingRectangle;$b=New-Object Drawing.Bitmap ([int]$r.Width),([int]$r.Height);$g=[Drawing.Graphics]::FromImage($b)
 try {$g.CopyFromScreen([int]$r.Left,[int]$r.Top,0,0,$b.Size);$b.Save(('C:\Users\jaskew\AppData\Local\Temp\htoc_reported_drawer_2tc4os3y\'+$name+'.png'))} finally {$g.Dispose();$b.Dispose()}
}
try {
 'Initial bookmarks:';$script:nodes | Where-Object {$_.Current.Name -like 'Bookmark *'} | ForEach-Object {$_.Current.Name}
 if($script:nodes | Where-Object {$_.Current.Name -like 'Bookmark Collapse the reported I&W*'}){ClickBookmark 'Bookmark Collapse the reported I&W'}
 Picture 'collapsed'
 $hrsa=$script:nodes | Where-Object {$_.Current.Name -eq 'Partner HRSA. Partner Block Area 1.'} | Sort-Object {$_.Current.BoundingRectangle.Left} | Select-Object -First 1
 if(-not ($script:nodes | Where-Object {$_.Current.Name -eq 'Showing 4 of 8 Indicators · HRSA'})){$hrsa.GetCurrentPattern([Windows.Automation.TogglePattern]::Pattern).Toggle()};Start-Sleep -Milliseconds 1800;Snapshot
 if(-not ($script:nodes | Where-Object {$_.Current.Name -eq 'Showing 4 of 8 Indicators · HRSA'})){throw 'Partner filter failed'}
 ClickBookmark 'Bookmark Show reported I&W'
 if(-not ($script:nodes | Where-Object {$_.Current.Name -like 'Bookmark Collapse the reported I&W*'})){throw 'Close control did not appear'}
 if(-not ($script:nodes | Where-Object {$_.Current.Name -eq 'Showing 4 of 8 Indicators · HRSA'})){throw 'Opening reset partner filter'}
 $script:nodes | Where-Object {$_.Current.Name -match '130.12.182.224|Reported I&W|Bookmark '} | ForEach-Object {$_.Current.Name}
 Picture 'expanded'
 $cms=$script:nodes | Where-Object {$_.Current.Name -eq 'Partner CMS. Partner Block Area 1.' -and -not $_.Current.IsOffscreen} | Sort-Object {$_.Current.BoundingRectangle.Left} -Descending | Select-Object -First 1
 $cms.GetCurrentPattern([Windows.Automation.TogglePattern]::Pattern).Toggle();$end=(Get-Date).AddSeconds(12)
 do {Start-Sleep -Milliseconds 500;Snapshot;$cmsSelected=$script:nodes | Where-Object {$_.Current.Name -eq 'Showing 3 of 8 Indicators · CMS'}} while(-not $cmsSelected -and (Get-Date) -lt $end)
 if(-not $cmsSelected){throw 'Changing partner in expanded layout failed'}
 ClickBookmark 'Bookmark Collapse the reported I&W'
 if(-not ($script:nodes | Where-Object {$_.Current.Name -like 'Bookmark Show reported I&W*'})){throw 'Open control did not reappear'}
 if(-not ($script:nodes | Where-Object {$_.Current.Name -eq 'Showing 3 of 8 Indicators · CMS'})){throw 'Closing reset partner filter'}
 'Drawer open/close and partner-filter preservation PASSED'
} finally {
 [DrawerInput]::keybd_event(17,0,2,[UIntPtr]::Zero);[DrawerInput]::SetCursorPos($point.X,$point.Y)|Out-Null;[DrawerInput]::SetForegroundWindow($old)|Out-Null
}
