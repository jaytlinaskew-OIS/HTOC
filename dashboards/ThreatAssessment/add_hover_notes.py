from pathlib import Path
import sys,os,site,json,zipfile,sqlite3,shutil,datetime,hashlib,re,copy
sys.stdout.reconfigure(encoding='utf-8');lib=Path(os.environ['LOCALAPPDATA'])/'HTOC/IWDashboard/lib';sys.path.insert(0,str(lib));site.addsitedir(str(lib))
from pbix_mcp import server as api
from pbix_mcp.report_binding import compile_visual_binding
from pbix_mcp.formats.model_reader import ModelReader
from pbix_mcp.formats.datamodel_roundtrip import decompress_datamodel
from pbix_mcp.formats.abf_rebuild import read_metadata_sqlite
import openpyxl
root=Path(r'\\cscso1fsappv01\home\jaskew\HTOC\dashboards\ThreatAssessment');target=Path(r'Z:\HTOC\Data_Analytics\Data\Threat Assessment Scores\ThreatAssessI_W\Dashobard.pbix');before=hashlib.sha256(target.read_bytes()).digest()
T='Unreported I&W';R='Reported I&W (5 days)'
def check(s):
 r=json.loads(s);assert r.get('success'),r;return r
with zipfile.ZipFile(target) as z:
 original_layout=json.loads(z.read('Report/Layout').decode('utf-16-le'));c=sqlite3.connect(':memory:');c.deserialize(read_metadata_sqlite(decompress_datamodel(z.read('DataModel'))));queries=dict(c.execute('SELECT t.Name,p.QueryDefinition FROM Partition p JOIN [Table] t ON p.TableID=t.ID WHERE t.ModelID=1').fetchall());c.close()
reader=ModelReader(str(target));data=reader.get_table(T);rows=[dict(zip(data['columns'],r)) for r in data['rows']]
for r in rows:
 value=r.get('GTI Verdict');r['GTI Verdict']='Unknown' if value is None else str(value).lower().removeprefix('verdict_').replace('_',' ').title()
schema=json.loads((root/'POWERBI/UnreportedIW.SemanticModel/model.bim').read_text())['model']['tables'][0]['columns'];types={'string':'String','double':'Double','int64':'Int64','dateTime':'DateTime'}
columns=[{'name':c['name'],'data_type':types[c['dataType']]} for c in schema]
assert {c['name'] for c in columns}==set(data['columns'])
# For each reported Indicator, use the newest source note in the five-day window.
today=datetime.date(2026,10,21);start=today-datetime.timedelta(days=4);reported={}
for f in sorted(target.parent.glob('ThreatAssessI_W_*.xlsx'),reverse=True):
 m=re.fullmatch(r'ThreatAssessI_W_(\d{8})\.xlsx',f.name)
 if not m:continue
 try:day=datetime.datetime.strptime(m[1],'%Y%m%d').date()
 except ValueError:continue
 if not start<=day<=today:continue
 wb=openpyxl.load_workbook(f,read_only=True,data_only=True)
 for s in wb:
  if s.title.strip().lower()!='i&w_yes':continue
  it=iter(s.values);headers=list(next(it,[]))
  for vals in it:
   r=dict(zip(headers,vals));ind=str(r.get('Indicator') or '').strip()
   if ind and ind not in reported:reported[ind]=str(r.get('Explanation') or 'No source assessment notes were provided.')
 wb.close()
rrows=[{'Indicator':k,'Explanation':reported[k]} for k in sorted(reported)]
rquery=(root/'automation/ReportedLast5Days.pq').read_text(encoding='utf-8')
rquery=rquery.replace('Table.AddColumn(Recent, "Reported Indicators"','Table.AddColumn(Table.Sort(Recent,{{"File Date",Order.Descending}}), "Reported Indicators"')
rquery=rquery.replace('#table(type table [Indicator = text], {})','#table(type table [Indicator = text, Explanation = text], {})')
rquery=rquery.replace('Table.SelectColumns(Promoted,{"Indicator"})','Table.SelectColumns(Promoted,{"Indicator","Explanation"},MissingField.UseNull)')
rquery=rquery.replace('Table.Distinct(Combined,{"Indicator"})','Table.Distinct(Table.Buffer(Combined),{"Indicator"})')
uquery='let\n Data = ('+queries[T]+'),\n Display = Table.TransformColumns(Data,{{"GTI Verdict", each if _ = null then "Unknown" else Text.Proper(Text.Replace(Text.Replace(Text.Lower(Text.From(_)),"verdict_",""),"_"," ")), type text}})\nin Display'
work=root/'POWERBI/Dashobard.hover-notes.pbix';shutil.copy2(target,work)
check(api.pbix_open(str(work),'hover_edit'));updates={T:{'columns':columns,'rows':rows},R:{'columns':[{'name':'Indicator','data_type':'String'},{'name':'Explanation','data_type':'String'}],'rows':rrows}}
api._rebuild_preserving_calc('hover_edit',api._ensure_open('hover_edit'),table_updates=updates)
for table,q in {**queries,T:uquery,R:rquery}.items():check(api.pbix_set_partition_m('hover_edit',table,q))
check(api.pbix_datamodel_modify_metadata('hover_edit','DELETE FROM Annotation WHERE ID NOT IN (SELECT MIN(ID) FROM Annotation GROUP BY ObjectID,ObjectType,Name COLLATE NOCASE)'))
check(api.pbix_datamodel_modify_metadata('hover_edit',"UPDATE Model SET DefaultPowerBIDataSourceVersion=2,SourceQueryCulture='en-US' WHERE ID=1"))
check(api.pbix_save('hover_edit',overwrite=True,backup=False));check(api.pbix_close('hover_edit',force=True))
with zipfile.ZipFile(work) as z:parts={i.filename:z.read(i.filename) for i in z.infolist()}
layout=json.loads(parts['Report/Layout'].decode('utf-16-le'));main=layout['sections'][0];main['height']=564
old={json.loads(v['config'])['name']:v for v in main['visualContainers']};visuals=[v for name,v in old.items() if name not in {'explanation','kpi_0_meaning','kpi_3_meaning'}]
def lit(v):
 s='true' if v is True else 'false' if v is False else str(v)+'D' if isinstance(v,(int,float)) else "'"+v.replace("'","''")+"'"
 return {'expr':{'Literal':{'Value':s}}}
def title(s,text):s.setdefault('vcObjects',{}).setdefault('title',[{'properties':{}}])[0]['properties']['text']=lit(text)
def compile(s):
 def resolver(e,p,m):return None if m else 'Double' if p in ['PRISM Score','VirusTotal Malicious Score'] else 'DateTime' if p=='Last Observed' else 'String'
 resolver.summarize_by=lambda e,p:2;resolver.data_category=lambda e,p:None
 q,dt=compile_visual_binding(s,resolver);return json.dumps(q),json.dumps(dt)
def table_visual(name,table,fields,x,y,w,h,heading,widths):
 selects=[{'Column':{'Expression':{'SourceRef':{'Source':'t'}},'Property':col},'Name':table+'.'+col} for col in fields]
 s={'visualType':'tableEx','projections':{'Values':[{'queryRef':a['Name']} for a in selects]},'prototypeQuery':{'Version':2,'From':[{'Name':'t','Entity':table,'Type':0}],'Select':selects},'vcObjects':copy.deepcopy(json.loads(old['queue']['config'])['singleVisual'].get('vcObjects',{})),'objects':{'grid':[{'properties':{'textSize':lit(10)}}],'values':[{'properties':{'wordWrap':lit(True)}}],'columnWidth':[{'selector':{'metadata':table+'.'+col},'properties':{'value':lit(widths[col])}} for col in fields]}}
 title(s,heading);q,dt=compile(s)
 return {'x':x,'y':y,'width':w,'height':h,'query':q,'dataTransforms':dt,'filters':'[]','config':json.dumps({'name':name,'singleVisual':s},ensure_ascii=False)}
# Tags form the second part of the Indicator details, with enough room to wrap.
visuals.append(table_visual('indicator_tags',T,['Indicator','Tags'],252,208,852,128,'Indicator Tags',{'Indicator':112,'Tags':700}))
positions={'dashboard_title':(16,8,420,50),'dashboard_subtitle':(16,62,420,30),'overview_asof':(904,8,200,78),'kpi_0':(452,8,160,78),'kpi_3':(628,8,176,78),'reported_last5days':(16,100,220,236),'queue':(252,100,852,92),'indicator_tags':(252,208,852,128),'severity':(16,352,352,132),'severity_meaning':(16,490,352,58),'verdict':(384,352,352,132),'verdict_meaning':(384,490,352,58),'prism':(752,352,352,132),'prism_meaning':(752,490,352,58)}
titles={'overview_asof':'Data Date','kpi_0':'I&W Indicators','kpi_3':'Highest PRISM Score','severity':'Indicators by Priority','verdict':'GTI Verdict','prism':'PRISM Score by Indicator','queue':'Indicator Details','reported_last5days':'Reported I&W — Last 5 Days'}
current_tip='ReportSectionIWCurrentNotes';reported_tip='ReportSectionIWReportedNotes'
for v in visuals:
 c=json.loads(v['config']);name=c['name'];s=c['singleVisual'];v.update(zip(['x','y','width','height'],positions[name]))
 if name in titles:title(s,titles[name])
 for entry in s.get('objects',{}).get('general',[]):
  for para in entry.get('properties',{}).get('paragraphs',[]):
   for run in para.get('textRuns',[]):run['value']=re.sub(r'\bitems\b','Indicators',re.sub(r'\bitem\b','Indicator',run.get('value',''),flags=re.I),flags=re.I)
 if name=='dashboard_subtitle':
  s['objects']['general'][0]['properties']['paragraphs'][0]['textRuns'][0]['value']='Hover over an Indicator for its assessment notes.'
  s['objects']['general'][0]['properties']['paragraphs'][0]['textRuns'][0]['textStyle']['fontSize']='11pt'
 if name in ['queue','prism','indicator_tags','reported_last5days']:
  s.setdefault('vcObjects',{})['visualTooltip']=[{'properties':{'show':lit(True),'type':lit('Canvas'),'section':lit(reported_tip if name=='reported_last5days' else current_tip)}}]
 if name=='queue':
  widths={'Indicator':112,'Severity':64,'PRISM Score':80,'GTI Verdict':98,'VirusTotal Malicious Score':160,'Last Observed':110,'OpDiv':170}
  s['objects']['columnWidth']=[{'selector':{'metadata':p['queryRef']},'properties':{'value':lit(widths[p['queryRef'].rsplit('.',1)[-1]])}} for p in s['projections']['Values']]
 v['config']=json.dumps(c,ensure_ascii=False)
main['visualContainers']=visuals
names={json.loads(v['config'])['name'] for v in visuals};cfg=json.loads(main.get('config','{}'));cfg['relationships']=[r for r in cfg.get('relationships',[]) if r['source'] in names and r['target'] in names];main['config']=json.dumps(cfg)
# Match native tooltip pages found in the user's Desktop-authored exports.
layout['sections']=[main]
for idx,(pname,table,heading) in enumerate([(current_tip,T,'Source Assessment Notes'),(reported_tip,R,'Reported Indicator Assessment')],1):
 tip=table_visual('notes_'+str(idx),table,['Indicator','Explanation'],8,8,624,304,heading,{'Indicator':110,'Explanation':474})
 layout['sections'].append({'name':pname,'displayName':heading,'ordinal':idx,'filters':'[]','config':json.dumps({'visibility':1,'type':1}),'displayOption':3,'width':640,'height':320,'visualContainers':[tip]})
for page in layout['sections']:
 for i,v in enumerate(page['visualContainers']):
  c=json.loads(v['config']);v['z']=i*1000;v['tabOrder']=(i+1)*1000;c['layouts']=[{'id':0,'position':{k:v[k] for k in ['x','y','z','width','height','tabOrder']}}];v['config']=json.dumps(c,ensure_ascii=False)
  assert v['x']+v['width']<=page['width'] and v['y']+v['height']<=page['height']
 for i,v in enumerate(page['visualContainers']):
  for b in page['visualContainers'][:i]:assert not(min(v['x']+v['width'],b['x']+b['width'])>max(v['x'],b['x']) and min(v['y']+v['height'],b['y']+b['height'])>max(v['y'],b['y']))
assert len([p for p in layout['sections'] if json.loads(p.get('config','{}')).get('visibility',0)!=1])==1
parts['Report/Layout']=json.dumps(layout,ensure_ascii=False).encode('utf-16-le');parts.pop('SecurityBindings',None)
with zipfile.ZipFile(work,'w',zipfile.ZIP_DEFLATED) as z:
 for n,b in parts.items():z.writestr(n,b)
with zipfile.ZipFile(work) as z:assert z.testzip() is None
check(api.pbix_open(str(work),'hover_check'));health=check(api.pbix_doctor('hover_check'));assert '\u274c' not in health['message'];metrics=check(api.pbix_evaluate_dax('hover_check','Unreported Indicators,Highest PRISM',apply_default_filters=False));print('Metrics:',metrics.get('results'));check(api.pbix_close('hover_check',force=True))
r=ModelReader(str(work));actual=r.get_table(T);assert actual['rows'][0][actual['columns'].index('GTI Verdict')]=='Suspicious';notes=r.get_table(R);assert len(notes['rows'])==6 and 'Explanation' in notes['columns']
assert hashlib.sha256(target.read_bytes()).digest()==before
backup=target.with_name('Dashobard.before-hover-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'.pbix');assert not backup.exists();shutil.copy2(target,backup)
staging=target.with_name('Dashobard.hover-staging.tmp');assert not staging.exists();shutil.copy2(work,staging);os.replace(staging,target)
(root/'automation/ReportedLast5Days.pq').write_text(rquery,encoding='utf-8')
(root/'POWERBI/hover_notes_validation.json').write_text(json.dumps({'visiblePages':1,'hiddenTooltipPages':2,'currentVerdict':'Suspicious','reportedIndicatorsWithNotes':6,'tooltipVisuals':['queue','prism','indicator_tags','reported_last5days'],'nativeTooltipFormatMatched':True,'desktopHoverInteractionTested':False},indent=2),encoding='utf-8')
print('Saved updated dashboard with standardized titles, readable GTI values, Tags, and native Indicator hover notes.')
