from pathlib import Path
import sys,os,site,json,zipfile,sqlite3,shutil,datetime,hashlib,re
sys.stdout.reconfigure(encoding='utf-8');lib=Path(os.environ['LOCALAPPDATA'])/'HTOC/IWDashboard/lib';sys.path.insert(0,str(lib));site.addsitedir(str(lib))
from pbix_mcp import server as api
from pbix_mcp.report_binding import compile_visual_binding
from pbix_mcp.formats.model_reader import ModelReader
from pbix_mcp.formats.datamodel_roundtrip import decompress_datamodel
from pbix_mcp.formats.abf_rebuild import read_metadata_sqlite
import openpyxl
root=Path(r'\\cscso1fsappv01\home\jaskew\HTOC\dashboards\ThreatAssessment')
target=Path(r'Z:\HTOC\Data_Analytics\Data\Threat Assessment Scores\ThreatAssessI_W\Dashobard.pbix');before=hashlib.sha256(target.read_bytes()).digest()
end=datetime.date(2026,10,21);start=end-datetime.timedelta(days=4);indicators=[];sources=[]
for f in sorted(target.parent.glob('ThreatAssessI_W_*.xlsx')):
 m=re.fullmatch(r'ThreatAssessI_W_(\d{8})\.xlsx',f.name)
 if not m:continue
 try:day=datetime.datetime.strptime(m[1],'%Y%m%d').date()
 except ValueError:continue
 if not start<=day<=end:continue
 sources.append(f.name);w=openpyxl.load_workbook(f,read_only=True,data_only=True)
 for s in w:
  if s.title.strip().lower()!='i&w_yes':continue
  it=iter(s.values);headers=list(next(it,[]))
  if 'Indicator' not in headers:raise ValueError(f'{f.name}: missing Indicator header in I&W_Yes')
  i=headers.index('Indicator')
  for r in it:
   if r[i] is not None and str(r[i]).strip():indicators.append(str(r[i]).strip())
 w.close()
unique=sorted(set(indicators),key=str.casefold);table='Reported I&W (5 days)'
query=r'''let
    SourceFolder = "\\cscso1fsappv01\data\HTOC\Data_Analytics\Data\Threat Assessment Scores\ThreatAssessI_W",
    Today = Date.From(DateTime.LocalNow()),
    WindowStart = Date.AddDays(Today, -4),
    Files = Folder.Contents(SourceFolder),
    Candidates = Table.SelectRows(Files, each let n = [Name], d = Text.Middle(n,16,8) in Text.Length(n) = 29 and Text.Start(n,16) = "ThreatAssessI_W_" and Text.End(n,5) = ".xlsx" and Text.Select(d,{"0".."9"}) = d and [Attributes]?[Hidden]? <> true),
    Dated = Table.AddColumn(Candidates, "File Date", each let d = Text.Middle([Name],16,8) in try #date(Number.FromText(Text.Start(d,4)),Number.FromText(Text.Middle(d,4,2)),Number.FromText(Text.End(d,2))) otherwise null, type date),
    Recent = Table.SelectRows(Dated, each [File Date] <> null and [File Date] >= WindowStart and [File Date] <= Today),
    Extracted = Table.AddColumn(Recent, "Reported Indicators", each let
        Book = Excel.Workbook([Content],null,true),
        Sheets = Table.SelectRows(Book, each [Kind] = "Sheet" and Text.Lower(Text.Trim([Item])) = "i&w_yes"),
        Empty = #table(type table [Indicator = text], {}),
        Promoted = if Table.IsEmpty(Sheets) then Empty else Table.PromoteHeaders(Sheets{0}[Data],[PromoteAllScalars=true]),
        Selected = if not Table.HasColumns(Promoted,"Indicator") then error "An I&W_Yes sheet is missing the Indicator header." else Table.SelectColumns(Promoted,{"Indicator"}),
        Trimmed = Table.TransformColumns(Selected,{{"Indicator", each if _ = null then null else Text.Trim(Text.From(_)), type text}}),
        Clean = Table.SelectRows(Trimmed, each [Indicator] <> null and [Indicator] <> "")
        in Clean),
    Combined = if Table.IsEmpty(Extracted) then #table(type table [Indicator = text], {}) else Table.Combine(Extracted[Reported Indicators]),
    Unique = Table.Distinct(Combined,{"Indicator"}),
    Sorted = Table.Sort(Unique,{{"Indicator",Order.Ascending}})
in Sorted'''
(root/'automation/ReportedLast5Days.pq').write_text(query,encoding='utf-8')
work=root/'POWERBI/Dashobard.with-reported.pbix';shutil.copy2(target,work)
def check(text):
 r=json.loads(text);assert r.get('success'),r;return r
check(api.pbix_open(str(work),'reported_update'))
payload={'columns':[{'name':'Indicator','data_type':'String'}],'rows':[{'Indicator':v} for v in unique]}
print(check(api.pbix_set_table_data('reported_update',table,json.dumps(payload)))['message'])
check(api.pbix_set_partition_m('reported_update',table,query))
check(api.pbix_datamodel_modify_metadata('reported_update','DELETE FROM Annotation WHERE ID NOT IN (SELECT MIN(ID) FROM Annotation GROUP BY ObjectID,ObjectType,Name COLLATE NOCASE)'))
check(api.pbix_datamodel_modify_metadata('reported_update',"UPDATE Model SET DefaultPowerBIDataSourceVersion=2,SourceQueryCulture='en-US' WHERE ID=1"))
check(api.pbix_save('reported_update',overwrite=True,backup=False));check(api.pbix_close('reported_update',force=True))
with zipfile.ZipFile(work) as z:parts={i.filename:z.read(i.filename) for i in z.infolist()}
l=json.loads(parts['Report/Layout'].decode('utf-16-le'));page=l['sections'][0]
removed={'kpi_1','kpi_1_meaning'};visuals=[v for v in page['visualContainers'] if json.loads(v['config'])['name'] not in removed]
# Match the existing card style, but present only the reported indicator column.
with zipfile.ZipFile(target) as z:old=json.loads(z.read('Report/Layout').decode('utf-16-le'))
card=next(v for v in old['sections'][0]['visualContainers'] if json.loads(v['config'])['name']=='kpi_1')
vc=json.loads(card['config'])['singleVisual'].get('vcObjects',{});vc['title'][0]['properties']['text']={'expr':{'Literal':{'Value':"'Reported I&W — last 5 days'"}}}
ref=table+'.Indicator';field={'Column':{'Expression':{'SourceRef':{'Source':'r'}},'Property':'Indicator'}}
sv={'visualType':'tableEx','projections':{'Values':[{'queryRef':ref}]},'prototypeQuery':{'Version':2,'From':[{'Name':'r','Entity':table,'Type':0}],'Select':[{**field,'Name':ref}],'OrderBy':[{'Direction':1,'Expression':field}]},'vcObjects':vc,'objects':{'grid':[{'properties':{'textSize':{'expr':{'Literal':{'Value':'11D'}}},'rowPadding':{'expr':{'Literal':{'Value':'1D'}}}}}],'columnHeaders':[{'properties':{'fontSize':{'expr':{'Literal':{'Value':'11D'}}}}}],'total':[{'properties':{'totals':{'expr':{'Literal':{'Value':'false'}}}}}]}}
def resolve(e,p,m):return None if m else 'String'
resolve.summarize_by=lambda e,p:2;resolve.data_category=lambda e,p:None
q,dt=compile_visual_binding(sv,resolve)
v={'x':544,'y':116,'width':504,'height':162,'query':json.dumps(q),'dataTransforms':json.dumps(dt),'filters':'[]','config':json.dumps({'name':'reported_last5days','singleVisual':sv},ensure_ascii=False)};visuals.append(v)
for i,v in enumerate(visuals):
 v['z']=i*1000;v['tabOrder']=(i+1)*1000;c=json.loads(v['config']);c['layouts']=[{'id':0,'position':{k:v[k] for k in ['x','y','z','width','height','tabOrder']}}];v['config']=json.dumps(c,ensure_ascii=False)
page['visualContainers']=visuals;names={json.loads(v['config'])['name'] for v in visuals};cfg=json.loads(page.get('config','{}'));cfg['relationships']=[r for r in cfg.get('relationships',[]) if r['source'] in names and r['target'] in names]
data_names=[json.loads(v['config'])['name'] for v in visuals if 'query' in v];cfg['relationships'] += [{'source':a,'target':b,'type':3} for a in data_names for b in data_names if a!=b and (a=='reported_last5days' or b=='reported_last5days')];page['config']=json.dumps(cfg)
for i,v in enumerate(visuals):
 assert v['x']+v['width']<=1600 and v['y']+v['height']<=900
 for b in visuals[:i]:assert not (min(v['x']+v['width'],b['x']+b['width'])>max(v['x'],b['x']) and min(v['y']+v['height'],b['y']+b['height'])>max(v['y'],b['y']))
parts['Report/Layout']=json.dumps(l,ensure_ascii=False).encode('utf-16-le');parts.pop('SecurityBindings',None)
with zipfile.ZipFile(work,'w',zipfile.ZIP_DEFLATED) as z:
 for n,b in parts.items():z.writestr(n,b)
with zipfile.ZipFile(work) as z:
 assert z.testzip() is None;c=sqlite3.connect(':memory:');c.deserialize(read_metadata_sqlite(decompress_datamodel(z.read('DataModel'))))
 assert not c.execute('SELECT ObjectID,ObjectType,Name FROM Annotation GROUP BY ObjectID,ObjectType,Name COLLATE NOCASE HAVING COUNT(*)>1').fetchall();assert c.execute('SELECT DefaultPowerBIDataSourceVersion FROM Model').fetchone()[0]==2;c.close()
stored=ModelReader(str(work)).get_table(table);assert stored['columns']==['Indicator'];actual=[r[0] for r in stored['rows']];assert sorted(actual)==unique;assert len(actual)==len(set(actual))
check(api.pbix_open(str(work),'reported_final'));health=check(api.pbix_doctor('reported_final'));assert '\u274c' not in health['message'];check(api.pbix_close('reported_final',force=True))
assert hashlib.sha256(target.read_bytes()).digest()==before
backup=target.with_name('Dashobard.before-reported-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'.pbix');assert not backup.exists();shutil.copy2(target,backup)
staging=target.with_name('Dashobard.reported-staging.tmp');assert not staging.exists();shutil.copy2(work,staging);os.replace(staging,target)
(root/'POWERBI/reported_list_validation.json').write_text(json.dumps({'windowStart':str(start),'windowEnd':str(end),'sourceFiles':sources,'reportedSourceRows':len(indicators),'uniqueIndicators':unique,'highPriorityCardRemoved':True,'pages':1,'queryRefreshesWindowUsingCurrentDate':True},indent=2),encoding='utf-8')
print('Updated',target,'with',len(unique),'unique reported indicators; high-priority card removed.')
