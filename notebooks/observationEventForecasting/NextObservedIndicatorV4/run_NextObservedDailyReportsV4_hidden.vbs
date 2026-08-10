' Hidden launcher for Task Scheduler — no console window.
Option Explicit
Dim sh, bat, rc, cmd
Set sh = CreateObject("WScript.Shell")
bat = "\\cscso1fsappv01\home\jaskew\HTOC\notebooks\observationEventForecasting\NextObservedIndicatorV4\run_NextObservedDailyReportsV4.bat"
cmd = "cmd.exe /c call """ & bat & """"
rc = sh.Run(cmd, 0, True)
If rc < 0 Then
  rc = 1
End If
WScript.Quit rc
