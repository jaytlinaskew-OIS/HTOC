from pathlib import Path
import json, re, datetime, urllib.request, sys, os, zipfile
ROOT=Path(r'\\cscso1fsappv01\home\jaskew\HTOC\dashboards\ThreatAssessment')
SOURCE=r'\\cscso1fsappv01\data\HTOC\Data_Analytics\Data\Threat Assessment Scores\ThreatAssessI_W'
BASE='https://developer.microsoft.com/json-schemas/fabric/item/'
REPORT=ROOT/'UnreportedIW.Report'
MODEL=ROOT/'UnreportedIW.SemanticModel'
def write(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def schema(kind,version='2.0.0'):
    return BASE+'report/definition/'+kind+'/'+version+'/schema.json'
write(ROOT/'UnreportedIW.pbip',{'version':'1.0','artifacts':[{'report':{'path':'UnreportedIW.Report'}}],'settings':{'enableAutoRecovery':True}})
write(REPORT/'definition.pbir',{'$schema':BASE+'report/definitionProperties/2.0.0/schema.json','version':'4.0','datasetReference':{'byPath':{'path':'../UnreportedIW.SemanticModel'}}})
write(MODEL/'definition.pbism',{'$schema':BASE+'semanticModel/definitionProperties/1.0.0/schema.json','version':'1.0','settings':{'qnaEnabled':False}})
# Filename date, rather than modification time, determines the current snapshot.
latest=r'''let
    Files = Folder.Contents(SourceFolder),
    Candidates = Table.SelectRows(Files, each
        let n = [Name], d = Text.Middle(n, 14, 8)
        in Text.Length(n) = 27 and Text.Start(n, 14) = "ThreatAssessI_W_"
            and Text.End(n, 5) = ".xlsx" and Text.Select(d, {"0".."9"}) = d
            and [Attributes]?[Hidden]? <> true),
    Dated = Table.AddColumn(Candidates, "Snapshot Date", each
        let d = Text.Middle([Name],14,8)
        in try #date(Number.FromText(Text.Start(d,4)),Number.FromText(Text.Middle(d,4,2)),Number.FromText(Text.End(d,2))) otherwise null, type date),
    Valid = Table.SelectRows(Dated, each [Snapshot Date] <> null),
    Sorted = Table.Sort(Valid, {{"Snapshot Date", Order.Descending}, {"Name", Order.Descending}}),
    Latest = if Table.IsEmpty(Sorted) then error "No valid ThreatAssessI_W_YYYYMMDD.xlsx snapshot found in SourceFolder." else Sorted{0}
in Latest'''
# The prefix has 15 characters; generate positions from the actual prefix to avoid drift.
prefix='ThreatAssessI_W_'
latest=latest.replace('Text.Middle(n, 14, 8)',f'Text.Middle(n, {len(prefix)}, 8)').replace('Text.Length(n) = 27',f'Text.Length(n) = {len(prefix)+13}').replace('Text.Start(n, 14)',f'Text.Start(n, {len(prefix)})').replace('Text.Middle([Name],14,8)',f'Text.Middle([Name],{len(prefix)},8)')
textcols=['Indicator','Host IP','Indicator Type','GTI Verdict','GTI Severity','Partners','incidents/events','Threat Actor','Tagging Boost Reason','Severity','Explanation','Associated Groups','Tags','OpDiv']
numcols=['VirusTotal Malicious Score','GTI Threat Score','Mandiant','Observation Yearly Count','ThreatConnect Rating','Observation Penalty Multiplier','Botnet Flag','False Positives','Tagging Boost','CAL Score','ThreatConnect Score','PRISM Score']
allcols=['Indicator','Host IP','Last Observed','Indicator Type','VirusTotal Malicious Score','GTI Verdict','GTI Threat Score','GTI Severity','Mandiant','Observation Yearly Count','ThreatConnect Rating','Observation Penalty Multiplier','Botnet Flag','False Positives','Partners','incidents/events','Threat Actor','Tagging Boost','Tagging Boost Reason','CAL Score','ThreatConnect Score','PRISM Score','Severity','Explanation','Associated Groups','Tags','OpDiv']
mcols=json.dumps(allcols,ensure_ascii=False)
transforms=',\n        '.join('{'+json.dumps(c)+', each if _ = null then null else Number.From(_, "en-US"), type number}' for c in numcols)
texttransforms=',\n        '.join('{'+json.dumps(c)+', each if _ = null then null else Text.From(_, "en-US"), type text}' for c in textcols)
load=r'''let
    Workbook = Excel.Workbook(LatestFile[Content], null, true),
    NoSheets = Table.SelectRows(Workbook, each [Kind] = "Sheet" and Text.Lower(Text.Trim([Item])) = "i&w_no"),
    Raw = if Table.RowCount(NoSheets) <> 1 then error "Latest workbook must contain exactly one I&W_No worksheet. No fallback to a prior snapshot or reported worksheet is allowed." else NoSheets{0}[Data],
    Headers = Table.PromoteHeaders(Raw, [PromoteAllScalars=true]),
    Checked = if not Table.HasColumns(Headers, {"Indicator", "PRISM Score", "Severity"}) then error "I&W_No is missing required Indicator, PRISM Score, or Severity headers." else Headers,
    WithStatus = if Table.HasColumns(Checked, "Reported I&W?") then Checked else Table.AddColumn(Checked, "Reported I&W?", each "No", type text),
    Unreported = Table.SelectRows(WithStatus, each
        let v = Record.Field(_, "Reported I&W?"), s = if v = null then "" else Text.Lower(Text.Trim(Text.From(v)))
        in List.Contains({"", "no", "n", "false", "0", "unreported", "not reported"}, s)),
    Nonblank = Table.SelectRows(Unreported, each [Indicator] <> null and Text.Trim(Text.From([Indicator])) <> ""),
    Selected = Table.SelectColumns(Nonblank, COLUMNS, MissingField.UseNull),
    Numbers = Table.TransformColumns(Selected, {NUMBERS}),
    Texts = Table.TransformColumns(Numbers, {TEXTS}),
    Dates = Table.TransformColumns(Texts, {{"Last Observed", each if _ = null or _ = "" then null else DateTime.From(_, "en-US"), type datetime}}),
    Severity = Table.TransformColumns(Dates, {{"Severity", each if _ = null or Text.Trim(_) = "" then "Unknown" else Text.Proper(Text.Trim(_)), type text}}),
    Rank = Table.AddColumn(Severity, "Severity Rank", each if [Severity] = "Critical" then 1 else if [Severity] = "High" then 2 else if [Severity] = "Medium" then 3 else if [Severity] = "Low" then 4 else if [Severity] = "Informational" then 5 else 6, Int64.Type),
    Status = Table.AddColumn(Rank, "Reported I&W?", each "No", type text),
    Snapshot = Table.AddColumn(Status, "Snapshot Date", each LatestFile[Snapshot Date], type date),
    File = Table.AddColumn(Snapshot, "Source File", each LatestFile[Name], type text)
in File'''.replace('COLUMNS',mcols).replace('NUMBERS',transforms).replace('TEXTS',texttransforms)
metadata='''let
    Result = #table({"Snapshot Date", "Source File", "File Modified", "Refreshed At", "Unreported Rows"}, {{LatestFile[Snapshot Date], LatestFile[Name], LatestFile[Date modified], DateTime.LocalNow(), Table.RowCount(UnreportedSnapshot)}}),
    Typed = Table.TransformColumnTypes(Result, {{"Snapshot Date", type date}, {"Source File", type text}, {"File Modified", type datetime}, {"Refreshed At", type datetime}, {"Unreported Rows", Int64.Type}})
in Typed'''
expressions=[{'name':'SourceFolder','kind':'m','expression':'"'+SOURCE+'" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]'}, {'name':'LatestFile','kind':'m','expression':latest},{'name':'UnreportedSnapshot','kind':'m','expression':load}]
def column(name,typ='string',**kwargs):
    return {'name':name,'dataType':typ,'sourceColumn':name,'summarizeBy':'none',**kwargs}
cols=[column(c,'double' if c in numcols else 'dateTime' if c=='Last Observed' else 'string',**({'formatString':'#,0.0'} if c in numcols else {'formatString':'yyyy-MM-dd HH:mm'} if c=='Last Observed' else {})) for c in allcols]
next(c for c in cols if c['name']=='Severity')['sortByColumn']='Severity Rank'
cols += [column('Severity Rank','int64',isHidden=True),column('Reported I&W?'),column('Snapshot Date','dateTime',formatString='yyyy-MM-dd'),column('Source File')]
measures=[
 ('Unreported Indicators',"COALESCE(DISTINCTCOUNT('Unreported I&W'[Indicator]), 0)",'#,0'),
 ('High or Critical',"COALESCE(CALCULATE([Unreported Indicators], KEEPFILTERS('Unreported I&W'[Severity] IN {\"High\", \"Critical\"})), 0)",'#,0'),
 ('Average PRISM',"AVERAGE('Unreported I&W'[PRISM Score])",'#,0.0'),
 ('Highest PRISM',"MAX('Unreported I&W'[PRISM Score])",'#,0'),
 ('Unreported Records',"COUNTROWS('Unreported I&W')",'#,0'),
 ('Average VT Malicious',"AVERAGE('Unreported I&W'[VirusTotal Malicious Score])",'#,0.0'),
]
tables=[{'name':'Unreported I&W','columns':cols,'measures':[{'name':n,'expression':e,'formatString':fmt,'displayFolder':'Unreported I&W'} for n,e,fmt in measures],'partitions':[{'name':'Latest unreported snapshot','mode':'import','source':{'type':'m','expression':'let Source = UnreportedSnapshot in Source'}}]},
 {'name':'Snapshot','columns':[column('Snapshot Date','dateTime',formatString='yyyy-MM-dd'),column('Source File'),column('File Modified','dateTime',formatString='yyyy-MM-dd HH:mm'),column('Refreshed At','dateTime',formatString='yyyy-MM-dd HH:mm'),column('Unreported Rows','int64')], 'measures':[{'name':'Snapshot As Of','expression':"MAX('Snapshot'[Snapshot Date])",'formatString':'dd MMM yyyy'},{'name':'Source Modified','expression':"MAX('Snapshot'[File Modified])",'formatString':'dd MMM yyyy HH:mm'},{'name':'Last Refresh','expression':"MAX('Snapshot'[Refreshed At])",'formatString':'dd MMM yyyy HH:mm'}], 'partitions':[{'name':'Snapshot metadata','mode':'import','source':{'type':'m','expression':metadata}}]}]
model={'name':'UnreportedIW','compatibilityLevel':1567,'model':{'culture':'en-US','defaultPowerBIDataSourceVersion':'powerBI_V3','sourceQueryCulture':'en-US','expressions':expressions,'tables':tables,'annotations':[{'name':'PBI_QueryOrder','value':json.dumps(['SourceFolder','LatestFile','UnreportedSnapshot','Unreported I&W','Snapshot'])},{'name':'PBI_ProTooling','value':'["DevMode"]'}]}}
write(MODEL/'model.bim',model)
# Also expose the exact query for review or reuse in an existing report.
(ROOT/'LatestUnreported.pq').write_text('section Section1;\n\n'+'\n\n'.join('shared '+json.dumps(e['name'])+' = '+e['expression']+';' for e in expressions).replace('shared "','shared #"'),encoding='utf-8')
# PBIR report definitions and native Power BI visuals.
write(REPORT/'definition/version.json',{'$schema':schema('versionMetadata','1.0.0'),'version':'4.0.0'})
write(REPORT/'definition/report.json',{'$schema':schema('report'),'themeCollection':{},'settings':{'useStylableVisualContainerHeader':True}})
write(REPORT/'definition/pages/pages.json',{'$schema':schema('pagesMetadata','1.0.0'),'pageOrder':['overview'],'activePageName':'overview'})
T='Unreported I&W'
def literal(v):
    if isinstance(v,bool): v='true' if v else 'false'
    elif isinstance(v,(int,float)): v=str(v)+'D'
    else: v="'"+str(v).replace("'","''")+"'"
    return {'expr':{'Literal':{'Value':v}}}
def color(v): return {'solid':{'color':literal(v)}}
def obj(**props): return [{'properties':props}]
def fld(name,measure=False,table=T):
    return {('Measure' if measure else 'Column'):{'Expression':{'SourceRef':{'Entity':table}},'Property':name}}
def proj(name,measure=False,table=T):
    return {'field':fld(name,measure,table),'queryRef':table+'.'+name,'nativeQueryRef':name}
def visual(page,name,typ,x,y,w,h,title,roles=None,objects=None,sort=None):
    config={'visualType':typ,'visualContainerObjects':{'title':obj(show=literal(True),text=literal(title),fontColor=color('#18324D'),fontSize=literal(13),bold=literal(True)), 'background':obj(show=literal(True),color=color('#FFFFFF'),transparency=literal(0)), 'border':obj(show=literal(True),color=color('#DDE5ED'),radius=literal(8))},'drillFilterOtherVisuals':True}
    if roles:
        config['query']={'queryState':{r:{'projections':p} for r,p in roles.items()}}
        if sort: config['query']['sortDefinition']={'sort':[{'field':sort[0],'direction':sort[1]}],'isDefaultSort':False}
    if objects: config['objects']=objects
    result={'$schema':schema('visualContainer'),'name':name,'position':{'x':x,'y':y,'z':y*10+x,'width':w,'height':h,'tabOrder':y*10+x},'visual':config}
    write(REPORT/f'definition/pages/{page}/visuals/{name}/visual.json',result)
    return result
for page,title in [('overview','Unreported I&W dashboard')]:
    write(REPORT/f'definition/pages/{page}/page.json',{'$schema':schema('page'),'name':page,'displayName':title,'displayOption':'FitToPage','width':1600,'height':1200,'objects':{'background':obj(color=color('#F2F5F9'),transparency=literal(0))}})
    visual(page,page+'_heading','textbox',24,16,1552,60,'',objects={'general':obj(paragraphs=[{'textRuns':[{'value':title,'textStyle':{'fontFamily':'Segoe UI','fontSize':'26pt','fontWeight':'bold','color':'#18324D'}}]}])})
    visual(page,page+'_scope','textbox',24,80,1552,45,'',objects={'general':obj(paragraphs=[{'textRuns':[{'value':'Latest snapshot. Unreported I&W only. Select a chart or filter to narrow the indicator list.','textStyle':{'fontFamily':'Segoe UI','fontSize':'12pt','color':'#53677C'}}]}])})
    for i,(c,title) in enumerate([('Severity','Severity'),('Indicator Type','Indicator type'),('Indicator','Indicator')]):
        visual(page,page+'_filter_'+str(i),'slicer',24+392*i,136,376,95,title,{'Values':[proj(c)]},objects={'data':obj(mode=literal('Dropdown'))})
    visual(page,page+'_asof','card',1200,136,376,95,'Snapshot date',{'Values':[proj('Snapshot As Of',True,'Snapshot')]},objects={'labels':obj(fontSize=literal(22),color=color('#18324D')),'categoryLabels':obj(show=literal(False))})
for i,(m,title) in enumerate([('Unreported Indicators','Unreported indicators'),('High or Critical','High or critical'),('Average PRISM','Average PRISM score'),('Highest PRISM','Highest PRISM score')]):
    visual('overview','kpi_'+str(i),'card',24+i*392,247,376,126,title,{'Values':[proj(m,True)]},objects={'labels':obj(fontSize=literal(36),color=color('#087F8C')),'categoryLabels':obj(show=literal(False))})
visual('overview','severity','clusteredBarChart',24,389,504,278,'Indicators by severity',{'Category':[proj('Severity')],'Y':[proj('Unreported Indicators',True)]},sort=(fld('Severity'), 'Ascending'))
visual('overview','verdict','clusteredBarChart',544,389,504,278,'Indicators by GTI verdict',{'Category':[proj('GTI Verdict')],'Y':[proj('Unreported Indicators',True)]},sort=(fld('Unreported Indicators',True),'Descending'))
visual('overview','prism','clusteredBarChart',1064,389,512,278,'PRISM score by indicator',{'Category':[proj('Indicator')],'Y':[proj('Highest PRISM',True)]},sort=(fld('Highest PRISM',True),'Descending'))
summary=['Indicator','Severity','PRISM Score','ThreatConnect Score','CAL Score','GTI Threat Score','GTI Verdict','VirusTotal Malicious Score','Last Observed','Partners','OpDiv','Threat Actor','Botnet Flag','False Positives','Tagging Boost Reason']
visual('overview','queue','tableEx',24,683,1552,257,'Unreported indicator queue',{'Values':[proj(c) for c in summary]},sort=(fld('PRISM Score'),'Descending'),objects={'grid':obj(textSize=literal(11))})
visual('overview','modified','card',24,1131,760,53,'Source file modified',{'Values':[proj('Source Modified',True,'Snapshot')]},objects={'labels':obj(fontSize=literal(14)),'categoryLabels':obj(show=literal(False))})
visual('overview','refreshed','card',800,1131,776,53,'Last refresh (local time)',{'Values':[proj('Last Refresh',True,'Snapshot')]},objects={'labels':obj(fontSize=literal(14)),'categoryLabels':obj(show=literal(False))})
visual('overview','explanation','tableEx',24,956,1552,159,'Scoring explanation and context',{'Values':[proj('Indicator'),proj('Explanation'),proj('Tags'),proj('Associated Groups')]},objects={'grid':obj(textSize=literal(11)),'values':obj(wordWrap=literal(True))})
# Explicit alternate import query, and instructions tied to the actual artifact.
(ROOT/'LatestUnreported.pq').write_text('let\n    SourceFolder = '+expressions[0]['expression']+',\n    LatestFile = '+latest+',\n    UnreportedSnapshot = '+load+'\nin\n    UnreportedSnapshot\n',encoding='utf-8')
(ROOT/'README.txt').write_text('''UNREPORTED I&W POWER BI DASHBOARD

Open UnreportedIW.pbip in current Power BI Desktop. Keep the project folders together.
If Desktop requires it, enable Power BI Project (PBIP) and enhanced report format (PBIR) in Options > Preview features and restart Desktop.
Select Refresh. If prompted for the network folder, choose Windows authentication with an account permitted to read it. Credentials are not included in this project.

Scope
The newest strictly named ThreatAssessI_W_YYYYMMDD.xlsx file is chosen by its filename date. ORIG, PreNewFilters, temporary files and differently named backups are excluded. Only the I&W_No worksheet is read. No I&W_Yes records are imported. If Reported I&W? exists, explicitly reported or unknown status values are excluded. Blank or absent status is treated as unreported because the record is on I&W_No. A missing I&W_No sheet or missing required headers causes a visible refresh failure. An empty current sheet stays empty; it never reuses an older nonempty file.

The source Severity and PRISM scores are preserved; no scoring thresholds are invented. High or critical means the source Severity equals High or Critical. Counts are distinct indicator values within the current filters. Average PRISM averages source rows; duplicates are retained for inspection. Category counts can overlap if an indicator has multiple source rows. OpDiv and Partners retain their original comma-separated values. Blank scores remain blank. File and refresh timestamps are local times of the refresh machine.

Refresh
The source parameter SourceFolder uses the UNC equivalent of the supplied Z: drive:
'''+SOURCE+'''
Every refresh selects the latest dated file again. This is an Import model; files appearing in the folder do not refresh an open report by themselves. In Power BI Desktop, use Home > Refresh. For unattended refresh, publish to Power BI Service and configure an on-premises data gateway with read access to this UNC folder, then set a refresh schedule after the daily export finishes. Service publishing and gateway/schedule configuration have not been performed.
To change the source, use Transform data > Manage parameters > SourceFolder.

Page
One page contains severity/type/indicator filters, snapshot date, four metrics, severity and verdict charts, PRISM scores, the unreported indicator queue, scoring explanations, source context and refresh timestamps. The detail tables scroll horizontally to show additional evidence columns.

This deliverable is a Power BI Project, not a PBIX binary. After opening and refreshing successfully, use Save As to save a PBIX if needed. LatestUnreported.pq provides the query for an existing report.

Validation
See validation.json for source inspection and schema-validation results. File/schema validation does not replace opening and refreshing in Power BI Desktop.
''',encoding='utf-8')
print('Built',ROOT)
print('Source accessible',Path(SOURCE).is_dir())
print('Filename prefix length',len(prefix),'expected total',len(prefix)+13)
