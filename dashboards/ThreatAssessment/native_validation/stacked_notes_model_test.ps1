$ErrorActionPreference='Stop'
[Reflection.Assembly]::LoadFrom('C:\Program Files\Microsoft Power BI Desktop\bin\Microsoft.PowerBI.Tabular.dll')|Out-Null
[Reflection.Assembly]::LoadFrom('C:\Program Files\Microsoft Power BI Desktop\bin\Microsoft.PowerBI.AdomdClient.dll')|Out-Null
$engine=Get-CimInstance Win32_Process -Filter "Name='msmdsrv.exe'"|Where-Object {$_.ParentProcessId -eq 90340}|Select-Object -First 1
$match=[regex]::Match($engine.CommandLine,'-s\s+"([^"]+)"');$portFile=Join-Path $match.Groups[1].Value 'msmdsrv.port.txt';$port=([IO.File]::ReadAllText($portFile)).Replace([string][char]0,'').Trim()
$server=New-Object Microsoft.AnalysisServices.Tabular.Server;$connection=$null
try {
 $server.Connect('Data Source=localhost:'+$port);$database=$server.Databases|Where-Object {$_.Model.Tables.Contains('Unreported I&W')}|Select-Object -First 1
 $connection=New-Object Microsoft.AnalysisServices.AdomdClient.AdomdConnection;$connection.ConnectionString='Data Source=localhost:'+$port+';Initial Catalog='+$database.ID;$connection.Open();$cmd=$connection.CreateCommand()
 $cmd.CommandText='EVALUATE ROW("Indicators",COUNTROWS(''Unreported I&W''),"Indicators with Notes",COUNTROWS(FILTER(''Unreported I&W'',LEN(''Unreported I&W''[Explanation])>0)),"Highest PRISM",[Highest PRISM])'
 $reader=$cmd.ExecuteReader();while($reader.Read()){for($i=0;$i -lt $reader.FieldCount;$i++){Write-Output ($reader.GetName($i)+'='+$reader.GetValue($i))}};$reader.Close()
} finally {if($null -ne $connection){$connection.Close()};$server.Disconnect()}
