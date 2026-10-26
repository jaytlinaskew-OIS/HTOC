from pathlib import Path
import sys,os,json,re,datetime,zipfile,hashlib
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,str(Path(os.environ['TEMP'])/'htoc-pbix-tools'))
import site
site.addsitedir(str(Path(os.environ['TEMP'])/'htoc-pbix-tools'))
from pbix_mcp.builder import PBIXBuilder
from pbix_mcp.formats.datamodel_roundtrip import decompress_datamodel
from pbix_mcp.formats.abf_rebuild import read_metadata_sqlite,list_abf_files
from pbix_mcp import server as api
import openpyxl
ROOT=Path(r'\\cscso1fsappv01\home\jaskew\HTOC\dashboards\ThreatAssessment\POWERBI')
ORIGINAL=Path(r'Z:\HTOC\Data_Analytics\Data\Threat Assessment Scores\ThreatAssessI_W\Dashobard.pbix')
model=json.loads((ROOT/'UnreportedIW.SemanticModel/model.bim').read_text(encoding='utf-8'))['model']
source=ORIGINAL.parent
files=sorted(p for p in source.glob('*.xlsx') if re.fullmatch(r'ThreatAssessI_W_\d{8}\.xlsx',p.name))
latest=files[-1]; day=datetime.datetime.strptime(latest.stem[-8:],'%Y%m%d')
wb=openpyxl.load_workbook(latest,read_only=True,data_only=True)
sheet=wb['I&W_No']; it=iter(sheet.values); headers=list(next(it))
raw=[dict(zip(headers,row)) for row in it if row[0] is not None and str(row[0]).strip()]
raw=[r for r in raw if str(r.get('Reported I&W?') or '').strip().lower() in ['','no','n','false','0','unreported','not reported']]
wb.close()
table=model['tables'][0]
rows=[]
for r in raw:
 out={}
 for c in table['columns']:
  name=c['name'];v=r.get(name)
  if name=='Severity':v=(str(v).strip().title() if v is not None and str(v).strip() else 'Unknown')
  elif name=='Severity Rank':v={'critical':1,'high':2,'medium':3,'low':4,'informational':5}.get(str(r.get('Severity','')).lower(),6)
  elif name=='Reported I&W?':v='No'
  elif name=='Snapshot Date':v=day
  elif name=='Source File':v=latest.name
  elif v is not None and c['dataType']=='double':v=float(v)
  elif v is not None and c['dataType']=='dateTime' and not isinstance(v,datetime.datetime):v=datetime.datetime.fromisoformat(str(v))
  elif v is not None and c['dataType']=='string':v=str(v)
  out[name]=v
 rows.append(out)
meta=[{'Snapshot Date':day,'Source File':latest.name,'File Modified':datetime.datetime.fromtimestamp(latest.stat().st_mtime),'Refreshed At':datetime.datetime.now(),'Unreported Rows':len(rows)}]
with zipfile.ZipFile(ORIGINAL) as z:
 blank={i.filename:z.read(i.filename) for i in z.infolist()}
 abf=decompress_datamodel(blank['DataModel'])
 bf=list_abf_files(abf)
 print('Original ABF members',[(i['FileName'],i['Size']) for i in bf])
 def extract(match):
  found=[i for i in bf if match(i['FileName'])]
  if not found:return None
  i=found[0];return abf[i['m_cbOffsetHeader']:i['m_cbOffsetHeader']+i['Size']]
 builder=PBIXBuilder('Unreported I&W')
 builder._source_metadata=read_metadata_sqlite(abf)
 builder._source_db_xml=extract(lambda n:n.endswith('.db.xml'))
 builder._source_cryptkey=extract(lambda n:n.endswith('.CryptKey.bin'))
 print('Preserving source metadata era, db xml:',bool(builder._source_db_xml),'key:',bool(builder._source_cryptkey))
typemap={'string':'String','double':'Double','int64':'Int64','dateTime':'DateTime'}
for t,rs in zip(model['tables'],[rows,meta]):
 builder.add_table(t['name'],[{'name':c['name'],'data_type':typemap[c['dataType']]} for c in t['columns']],rows=rs)
 for m in t['measures']:
  builder.add_measure(t['name'],m['name'],m['expression'],format_string=m.get('formatString'))
visuals=[];pdefs=[]
for f in (ROOT/'UnreportedIW.Report/definition/pages/overview/visuals').glob('*/visual.json'):
 p=json.loads(f.read_text());pdefs.append(p)
pdefs.sort(key=lambda p:(p['position']['y'],p['position']['x']))
for p in pdefs:
 v=p['visual'];cfg={}
 if v.get('query'):
  roles={}
  for role,state in v['query']['queryState'].items():
   fields=[]
   for pr in state['projections']:
    field=pr['field'];kind=next(iter(field));spec=field[kind]
    fields.append({'measure':spec['Property']} if kind=='Measure' else {'table':spec['Expression']['SourceRef']['Entity'],'column':spec['Property']})
   roles[role]=fields
  cfg['roles']=roles
  if v['query'].get('sortDefinition'):
   so=v['query']['sortDefinition']['sort'][0];sp=next(iter(so['field'].values()));cfg['sort']={'by':sp['Property'],'direction':'desc' if so['direction']=='Descending' else 'asc'}
 pos=p['position']
 visuals.append({'type':v['visualType'],'name':p['name'],'config':cfg,'objects':v.get('objects',{}),'x':pos['x'],'y':pos['y'],'width':pos['width'],'height':pos['height']})
builder.add_page('Unreported I&W',visuals=visuals)
builder.save(str(ROOT/'native_generated.pbix'))
# Keep the provided PBIX's shell, theme, schema version and settings; replace its data model and single report page.
with zipfile.ZipFile(ROOT/'native_generated.pbix') as z:
 generated={i.filename:z.read(i.filename) for i in z.infolist()}
layout=json.loads(generated['Report/Layout'].decode('utf-16-le'))
original_layout=json.loads(blank['Report/Layout'].decode('utf-16-le'))
layout['resourcePackages']=original_layout['resourcePackages']
layout['config']=original_layout['config']
layout['layoutOptimization']=original_layout.get('layoutOptimization',0)
page=layout['sections'][0];page.update({'id':0,'width':1600,'height':1200,'displayOption':1,'config':json.dumps({'objects':{'background':[{'properties':{'color':{'solid':{'color':{'expr':{'Literal':{'Value':"'#F2F5F9'"}}}}},'transparency':{'expr':{'Literal':{'Value':'0D'}}}}}]}})})
for container,p in zip(page['visualContainers'],pdefs):
 c=json.loads(container['config']);c['singleVisual']['vcObjects']=p['visual'].get('visualContainerObjects',{})
 if p['visual']['visualType']=='textbox':
  c['singleVisual']['vcObjects']={}
 container['config']=json.dumps(c,ensure_ascii=False)
blank['DataModel']=generated['DataModel'];blank['Report/Layout']=json.dumps(layout,ensure_ascii=False).encode('utf-16-le');blank.pop('SecurityBindings',None)
# Remove the stale DiagramLayout referencing the empty database; Desktop regenerates the diagram.
blank.pop('DiagramLayout',None)
candidate=ROOT/'Dashobard.updated.pbix'
with zipfile.ZipFile(candidate,'w',zipfile.ZIP_DEFLATED) as z:
 for n,b in blank.items():z.writestr(n,b)
print(api.pbix_open(str(candidate),'iw_edit'))
exprs={e['name']:e['expression'] for e in model['expressions']}
query=(ROOT/'LatestUnreported.pq').read_text(encoding='utf-8')
print(api.pbix_set_partition_m('iw_edit','Unreported I&W',query))
# Independent, self-contained metadata query keeps file provenance available even on empty snapshots.
metadata_query='let\n SourceFolder = '+exprs['SourceFolder']+',\n LatestFile = '+exprs['LatestFile']+',\n UnreportedSnapshot = '+exprs['UnreportedSnapshot']+',\n Result = '+model['tables'][1]['partitions'][0]['source']['expression']+'\nin Result'
print(api.pbix_set_partition_m('iw_edit','Snapshot',metadata_query))
print(api.pbix_datamodel_modify_metadata('iw_edit', 'DELETE FROM Annotation WHERE ID NOT IN (SELECT MIN(ID) FROM Annotation GROUP BY ObjectID,ObjectType,Name COLLATE NOCASE)'))
print(api.pbix_datamodel_modify_metadata('iw_edit', "UPDATE Model SET DefaultPowerBIDataSourceVersion=2, SourceQueryCulture='en-US' WHERE ID=1"))
print(api.pbix_save('iw_edit',overwrite=True,backup=False))
print(api.pbix_doctor('iw_edit'))
print(api.pbix_evaluate_dax('iw_edit','Unreported Indicators,High or Critical,Average PRISM,Highest PRISM',apply_default_filters=False))
print(api.pbix_get_table_data('iw_edit','Unreported I&W',max_rows=3))
print('Candidate',str(candidate),'bytes',candidate.stat().st_size)
(ROOT/'pbix_build_source.json').write_text(json.dumps({'originalSHA256':hashlib.sha256(ORIGINAL.read_bytes()).hexdigest(),'latestFile':latest.name,'unreportedRows':len(rows),'reportPages':1,'visuals':len(visuals)},indent=2),encoding='utf-8')
