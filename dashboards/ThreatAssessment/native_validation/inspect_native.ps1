[Reflection.Assembly]::LoadFrom('C:\Program Files\Microsoft Power BI Desktop\bin\Microsoft.PowerBI.Tabular.dll') | Out-Null
[Microsoft.AnalysisServices.ImageLoadInfo].GetProperties() | ForEach-Object { $_.Name+' '+$_.PropertyType.FullName }
