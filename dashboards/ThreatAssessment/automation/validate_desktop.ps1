param([Parameter(Mandatory=$true)][string]$Candidate,[Parameter(Mandatory=$true)][string]$Expected)
$ErrorActionPreference='Stop'
[Console]::OutputEncoding=New-Object System.Text.UTF8Encoding($false)
$bin='C:\Program Files\Microsoft Power BI Desktop\bin'
[Reflection.Assembly]::LoadFrom((Join-Path $bin 'Microsoft.PowerBI.Tabular.dll')) | Out-Null
[Reflection.Assembly]::LoadFrom((Join-Path $bin 'Microsoft.PowerBI.AdomdClient.dll')) | Out-Null
$expectedData=Get-Content -LiteralPath $Expected -Raw | ConvertFrom-Json
$preview=Start-Process -FilePath (Join-Path $bin 'PBIDesktop.exe') -ArgumentList ('"'+$Candidate+'"') -WindowStyle Hidden -PassThru
$started=$preview.StartTime
$server=$null; $connection=$null; $lastError='Power BI did not finish loading'
try {
 $deadline=(Get-Date).AddSeconds(110)
 while((Get-Date) -lt $deadline) {
  Start-Sleep -Seconds 2
  $engine=Get-CimInstance Win32_Process -Filter "Name='msmdsrv.exe'" | Where-Object {$_.ParentProcessId -eq $preview.Id} | Select-Object -First 1
  if($null -eq $engine){continue}
  $match=[regex]::Match($engine.CommandLine,'-s\s+"([^"]+)"')
  if(-not $match.Success){$match=[regex]::Match($engine.CommandLine,'-s\s+(\S+)')}
  if(-not $match.Success){continue}
  $portFile=Join-Path $match.Groups[1].Value 'msmdsrv.port.txt'
  if(-not (Test-Path -LiteralPath $portFile)){continue}
  $port=([IO.File]::ReadAllText($portFile)).Replace([string][char]0,'').Trim()
  try {
   $server=New-Object Microsoft.AnalysisServices.Tabular.Server
   $server.Connect('Data Source=localhost:'+$port)
   $database=$server.Databases | Where-Object {$_.Model.Tables.Contains('Unreported I&W')} | Select-Object -First 1
   if($null -eq $database){$server.Disconnect(); $server=$null; continue}
   $connection=New-Object Microsoft.AnalysisServices.AdomdClient.AdomdConnection
   $connection.ConnectionString='Data Source=localhost:'+$port+';Initial Catalog='+$database.ID
   $connection.Open();$command=$connection.CreateCommand()
   $command.CommandText='EVALUATE ROW("current",COUNTROWS(''Unreported I&W''),"reported",COUNTROWS(''Reported I&W (5 days)''),"links",COUNTROWS(''Indicator Partners''),"highest",[Highest PRISM],"context",[Indicator Filter Context])'
   $reader=$command.ExecuteReader(); $got=@{}
   if($reader.Read()){for($i=0;$i -lt $reader.FieldCount;$i++){$name=$reader.GetName($i).Trim('[',']');$value=$reader.GetValue($i);$got[$name]=if($value -is [DBNull]){$null}else{$value}}}
   $reader.Close()
   foreach($key in @('current','reported','links')){if([int]$got[$key] -ne [int]$expectedData.$key){throw "Native $key count differs"}}
   if($null -eq $got['highest'] -or [double]$got['highest'] -ne [double]$expectedData.highest){throw 'Native PRISM differs'}
   if($expectedData.current -eq 0 -and ($null -eq $got['highest'] -or [double]$got['highest'] -ne 0)){throw 'Empty snapshot must display PRISM 0'}
   $command.CommandText='EVALUATE ADDCOLUMNS(VALUES(''Indicator Partners''[Partner]),"Expected",CALCULATE(DISTINCTCOUNT(''Indicator Partners''[Indicator])),"Actual",CALCULATE([Unreported Indicators]))'
   $reader=$command.ExecuteReader()
   while($reader.Read()){if([int]$reader.GetValue(1) -ne [int]$reader.GetValue(2)){throw 'Partner relationship does not filter Indicators'}}
   $reader.Close()
   @{status='passed';counts=$got;partner_filter='passed'} | ConvertTo-Json -Compress -Depth 6
   exit 0
  } catch {$lastError=$_.Exception.Message}
  finally {if($null -ne $connection){$connection.Close();$connection=$null};if($null -ne $server){$server.Disconnect();$server=$null}}
 }
 throw ('Native Power BI validation failed: '+$lastError)
} finally {
 $owned=Get-Process -Id $preview.Id -ErrorAction SilentlyContinue
 if($null -ne $owned -and $owned.StartTime -eq $started){Stop-Process -Id $owned.Id -Force}
}
