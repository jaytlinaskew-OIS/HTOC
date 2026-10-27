$ErrorActionPreference='Stop'
[Reflection.Assembly]::LoadFrom('C:\Program Files\Microsoft Power BI Desktop\bin\Microsoft.PowerBI.Tabular.dll') | Out-Null
[Reflection.Assembly]::LoadFrom('C:\Program Files\Microsoft Power BI Desktop\bin\Microsoft.PowerBI.AdomdClient.dll') | Out-Null
$taskPort=([IO.File]::ReadAllText('C:\Users\jaskew\AppData\Local\Microsoft\Power BI Desktop\AnalysisServicesWorkspaces\AnalysisServicesWorkspace_72c52f4d-8dbd-408c-8d08-922cd726c00d\Data\msmdsrv.port.txt')).Replace([string][char]0,'').Trim()
$taskState=Get-Content -LiteralPath 'C:\Users\jaskew\AppData\Local\HTOC\IWDashboard\native_tests\partner_tiles_state.json' -Raw | ConvertFrom-Json
$taskServer=New-Object Microsoft.AnalysisServices.Tabular.Server;$taskServer.Connect('Data Source=localhost:'+$taskPort)
if($taskServer.Databases.Count -ne 1){throw 'Expected only the test model'}
$taskDB=$taskServer.Databases[0]
$taskConnection=New-Object Microsoft.AnalysisServices.AdomdClient.AdomdConnection;$taskConnection.ConnectionString='Data Source=localhost:'+$taskPort+';Initial Catalog='+$taskDB.ID;$taskConnection.Open()
try{
 foreach($taskPartnerProperty in $taskState.expected.PSObject.Properties){
  $taskPartner=$taskPartnerProperty.Name;$taskExpected=@($taskPartnerProperty.Value)
  $taskCommand=$taskConnection.CreateCommand();$taskCommand.CommandText='EVALUATE CALCULATETABLE(SELECTCOLUMNS(''Unreported I&W'',"Indicator",''Unreported I&W''[Indicator],"Score",''Unreported I&W''[PRISM Score]),''Indicator Partners''[Partner]="'+$taskPartner+'")'
  $taskReader=$taskCommand.ExecuteReader();$taskActual=@{}
  while($taskReader.Read()){$taskActual[[string]$taskReader.GetValue(0)]=[double]$taskReader.GetValue(1)};$taskReader.Close()
  if($taskActual.Count -ne $taskExpected.Count){throw ('Wrong partner count: '+$taskPartner)}
  foreach($taskRow in $taskExpected){if(-not $taskActual.ContainsKey($taskRow.Indicator) -or $taskActual[$taskRow.Indicator] -ne $taskRow.Score){throw ('Indicator/score mismatch for '+$taskPartner+': '+$taskRow.Indicator)}}
  $taskCommand.CommandText='EVALUATE CALCULATETABLE(ROW("Count",[Unreported Indicators],"PRISM",[Highest PRISM]),''Indicator Partners''[Partner]="'+$taskPartner+'")'
  $taskReader=$taskCommand.ExecuteReader();if(-not $taskReader.Read()){throw 'Missing measures'}
  $taskCount=[int]$taskReader.GetValue(0);$taskMax=[double]$taskReader.GetValue(1);$taskReader.Close();$taskExpectedMax=($taskExpected | Measure-Object -Property Score -Maximum).Maximum
  if($taskCount -ne $taskExpected.Count -or $taskMax -ne $taskExpectedMax){throw ('Wrong partner measure: '+$taskPartner)}
  Write-Output ($taskPartner+': exact Indicator/score matches passed; count='+$taskCount+'; highest PRISM='+$taskMax)
 }
 foreach($taskTable in @('Unreported I&W','Snapshot','Reported I&W (5 days)','Indicator Partners')){
  $taskCommand=$taskConnection.CreateCommand();$taskCommand.CommandText='EVALUATE '''+$taskTable+'''';$taskReader=$taskCommand.ExecuteReader();$taskRows=0
  while($taskReader.Read()){$taskRows++;for($taskIndex=0;$taskIndex -lt $taskReader.FieldCount;$taskIndex++){$taskValue=$taskReader.GetValue($taskIndex)}};$taskReader.Close();Write-Output ($taskTable+': native read passed; rows='+$taskRows)
 }
 Write-Output 'All six partner cross-filter cases passed in Power BI native engine.'
}finally{$taskConnection.Close();$taskServer.Disconnect()}
