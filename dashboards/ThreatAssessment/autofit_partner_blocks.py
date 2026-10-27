from pathlib import Path
import os,sys,site,json,copy,zipfile,hashlib,shutil,sqlite3
lib=Path(os.environ['LOCALAPPDATA'])/'HTOC/IWDashboard/lib';sys.path.insert(0,str(lib));site.addsitedir(str(lib))
from pbix_mcp import server as api
from pbix_mcp.formats.model_reader import ModelReader
from pbix_mcp.formats.datamodel_roundtrip import decompress_datamodel
from pbix_mcp.formats.abf_rebuild import list_abf_files,read_metadata_sqlite
from pbix_mcp.report_binding import compile_visual_binding
p=Path(r'Z:\HTOC\Data_Analytics\Data\Threat Assessment Scores\ThreatAssessI_W\Dashboard\Dashobard.pbix');raw=p.read_bytes();m=ModelReader(str(p));work=Path(os.environ['LOCALAPPDATA'])/'HTOC/IWDashboard/native_tests';candidate=work/'partner_autofit_test.pbix'
with zipfile.ZipFile(p) as z:infos={i.filename:copy.copy(i) for i in z.infolist()};parts={n:z.read(n) for n in infos}
shutil.copyfile(p,candidate)
def ok(s):
 r=json.loads(s)
 if not r.get('success'):raise RuntimeError(str(r)[:1000])
 return r
alias='iw_autofit';ok(api.pbix_open(str(candidate),alias))
try:
 ok(api.pbix_datamodel_add_measure(alias,'Indicator Partners','Partner Block Area','1',format_string='0',description='Assigns equal area to each partner block; block area does not represent Indicator count.',data_type='Int64'))
 info=api._ensure_open(alias);dm=(Path(info['work_dir'])/'DataModel').read_bytes()
finally:ok(api.pbix_close(alias,force=True))
parts['DataModel']=dm
d=json.loads(parts['Report/Layout'].decode('utf-16-le'));before=copy.deepcopy(d);page=d['sections'][0]
lit=lambda v:{'expr':{'Literal':{'Value':v}}};txt=lambda v:lit("'"+v.replace("'","''")+"'");solid=lambda v:{'solid':{'color':txt(v)}}
for v in page['visualContainers']:
 c=json.loads(v['config'])
 if c['name']=='severity':
  vc=c['singleVisual']['vcObjects'];sv={'visualType':'treemap','projections':{'Group':[{'queryRef':'Indicator Partners.Partner','active':True}],'Values':[{'queryRef':'Indicator Partners.Partner Block Area'}]},'prototypeQuery':{'Version':2,'From':[{'Name':'p','Entity':'Indicator Partners','Type':0}],'Select':[{'Column':{'Expression':{'SourceRef':{'Source':'p'}},'Property':'Partner'},'Name':'Indicator Partners.Partner'},{'Measure':{'Expression':{'SourceRef':{'Source':'p'}},'Property':'Partner Block Area'},'Name':'Indicator Partners.Partner Block Area'}],'OrderBy':[{'Direction':1,'Expression':{'Column':{'Expression':{'SourceRef':{'Source':'p'}},'Property':'Partner'}}}]},'objects':{'legend':[{'properties':{'show':lit('false')}}],'dataPoint':[{'properties':{'fill':solid('#303366')}}],'categoryLabels':[{'properties':{'show':lit('true'),'color':solid('#D9D9D9'),'fontSize':lit('12D'),'fontFamily':txt('Segoe UI Semibold')}}],'labels':[{'properties':{'show':lit('false')}}],'layout':[{'properties':{'tilingMethod':txt('stableSquarified'),'innerPadding':lit('6D'),'outerPadding':lit('2D')}}]},'vcObjects':vc}
  c['singleVisual']=sv;q,t=compile_visual_binding(sv,lambda e,p,is_measure:'Int64' if is_measure else 'String');v['config']=json.dumps(c,ensure_ascii=False);v['query']=json.dumps(q,ensure_ascii=False);v['dataTransforms']=json.dumps(t,ensure_ascii=False)
 elif c['name']=='severity_meaning':
  ps=c['singleVisual']['objects']['general'][0]['properties']['paragraphs'];ps[0]['textRuns'][0]['value']='Select a partner block to filter Indicator Details and PRISM scores. Blocks resize automatically as partners are added.'
  for para in ps:
   for run in para['textRuns'][1:]:run['value']=''
  v['config']=json.dumps(c,ensure_ascii=False)
cfg=json.loads(page['config']);cfg['relationships']=[r for r in cfg.get('relationships',[]) if not (r.get('source')=='severity' and r.get('target') in ['indicator_hover_column','prism'])]
for target in ['indicator_hover_column','prism']:cfg['relationships'].append({'source':'severity','target':target,'type':1})
page['config']=json.dumps(cfg,ensure_ascii=False)
for help_page in d['sections']:
 if help_page['name']=='HelpIWPriorityGraph':
  for hv in help_page['visualContainers']:
   hc=json.loads(hv['config'])
   if hc['name'].endswith('_body'):
    ps=hc['singleVisual']['objects']['general'][0]['properties']['paragraphs'];ps[0]['textRuns'][0]['value']='Each block represents one partner. Blocks share the available space equally and automatically shrink and rearrange as partners are added. Block size does not represent the number of Indicators. Select a partner to filter Indicator Details and PRISM scores.';hv['config']=json.dumps(hc,ensure_ascii=False)
for a,b in zip(before['sections'],d['sections']):
 if a['name']=='ReportSection1':
  for va,vb in zip(a['visualContainers'],b['visualContainers']):
   if json.loads(va['config'])['name'] not in ['severity','severity_meaning']:assert va==vb
 elif a['name']!='HelpIWPriorityGraph':assert a==b
parts['Report/Layout']=json.dumps(d,ensure_ascii=False).encode('utf-16-le');parts.pop('SecurityBindings',None);infos.pop('SecurityBindings',None);infos['DataModel'].compress_type=zipfile.ZIP_STORED
with zipfile.ZipFile(candidate,'w') as z:
 for n,b in parts.items():z.writestr(infos[n],b)
with zipfile.ZipFile(candidate) as z:assert z.testzip() is None
new=ModelReader(str(candidate))
for table in ['Unreported I&W','Snapshot','Reported I&W (5 days)','Indicator Partners']:assert new.get_table(table)==m.get_table(table),table
abf=decompress_datamodel(dm);names={f['FileName'].lower() for f in list_abf_files(abf)};db=sqlite3.connect(':memory:');db.deserialize(read_metadata_sqlite(abf));missing=[r[0] for r in db.execute('select FileName from StorageFile') if r[0] and r[0].lower() not in names];db.close();assert not missing,missing
state={'original_sha256':hashlib.sha256(raw).hexdigest(),'candidate':str(candidate)};(work/'partner_autofit_state.json').write_text(json.dumps(state,indent=2));print('Built equal-area auto-fitting partner chart. Existing data, layout and theme preserved.')
