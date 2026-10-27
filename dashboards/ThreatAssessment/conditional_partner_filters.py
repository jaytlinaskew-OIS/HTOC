from pathlib import Path
import os,sys,site,json,copy,zipfile,hashlib,shutil,sqlite3
lib=Path(os.environ['LOCALAPPDATA'])/'HTOC/IWDashboard/lib';sys.path.insert(0,str(lib));site.addsitedir(str(lib))
from pbix_mcp import server as api
from pbix_mcp.formats.model_reader import ModelReader
from pbix_mcp.formats.datamodel_roundtrip import decompress_datamodel
from pbix_mcp.formats.abf_rebuild import list_abf_files,read_metadata_sqlite
from pbix_mcp.report_binding import compile_visual_binding
p=Path(r'Z:\HTOC\Data_Analytics\Data\Threat Assessment Scores\ThreatAssessI_W\Dashboard\Dashobard.pbix');raw=p.read_bytes();m=ModelReader(str(p));work=Path(os.environ['LOCALAPPDATA'])/'HTOC/IWDashboard/native_tests';candidate=work/'conditional_partner_filters_test.pbix'
with zipfile.ZipFile(p) as z:infos={i.filename:copy.copy(i) for i in z.infolist()};parts={n:z.read(n) for n in infos}
shutil.copyfile(p,candidate)
def ok(s):
 r=json.loads(s)
 if not r.get('success'):raise RuntimeError(str(r)[:1000])
 return r
area='VAR IndicatorCount = CALCULATE(DISTINCTCOUNT(\'Unreported I&W\'[Indicator]), REMOVEFILTERS()) RETURN IF(IndicatorCount > 1, 1, BLANK())'
guidance='''VAR IndicatorCount = CALCULATE(DISTINCTCOUNT('Unreported I&W'[Indicator]), REMOVEFILTERS())
VAR PartnersText = CALCULATE(CONCATENATEX(VALUES('Indicator Partners'[Partner]), 'Indicator Partners'[Partner], ", ", 'Indicator Partners'[Partner], ASC), REMOVEFILTERS())
RETURN SWITCH(TRUE(), IndicatorCount = 0, "No Indicators are available.", IndicatorCount = 1, "Partners: " & PartnersText & ". Only one Indicator is available; partner filtering is off.", "Select a partner block to filter Indicator Details and PRISM scores. Blocks resize automatically as partners are added.")'''
alias='iw_single_behavior';ok(api.pbix_open(str(candidate),alias))
try:
 ok(api.pbix_datamodel_modify_measure(alias,'Partner Block Area',new_expression=area))
 ok(api.pbix_datamodel_add_measure(alias,'Indicator Partners','Partner Panel Guidance',guidance,description='Shows non-interactive partner text for one Indicator and filter instructions for multiple Indicators.',data_type='String'))
 info=api._ensure_open(alias);dm=(Path(info['work_dir'])/'DataModel').read_bytes()
finally:ok(api.pbix_close(alias,force=True))
from restore_blank_dictionary import restore_blank_dictionary
dm=restore_blank_dictionary(dm,work/'partner_autofit_final.pbix')
parts['DataModel']=dm;d=json.loads(parts['Report/Layout'].decode('utf-16-le'));before=copy.deepcopy(d)
lit=lambda v:{'expr':{'Literal':{'Value':v}}};txt=lambda v:lit("'"+v.replace("'","''")+"'");solid=lambda v:{'solid':{'color':txt(v)}}
for v in d['sections'][0]['visualContainers']:
 c=json.loads(v['config'])
 if c['name']=='severity_meaning':
  vc=c['singleVisual']['vcObjects'];vc['visualTooltip']=[{'properties':{'show':lit('false')}}]
  sv={'visualType':'card','projections':{'Values':[{'queryRef':'Indicator Partners.Partner Panel Guidance'}]},'prototypeQuery':{'Version':2,'From':[{'Name':'p','Entity':'Indicator Partners','Type':0}],'Select':[{'Measure':{'Expression':{'SourceRef':{'Source':'p'}},'Property':'Partner Panel Guidance'},'Name':'Indicator Partners.Partner Panel Guidance'}]},'objects':{'labels':[{'properties':{'fontSize':lit('8D'),'color':solid('#D9D9D9'),'fontFamily':txt('Segoe UI')}}],'categoryLabels':[{'properties':{'show':lit('false')}}],'wordWrap':[{'properties':{'show':lit('true')}}]},'vcObjects':vc}
  c['singleVisual']=sv;q,t=compile_visual_binding(sv,lambda e,p,is_measure:'String');v['config']=json.dumps(c,ensure_ascii=False);v['query']=json.dumps(q,ensure_ascii=False);v['dataTransforms']=json.dumps(t,ensure_ascii=False)
for page in d['sections']:
 if page['name']=='HelpIWPriorityGraph':
  for v in page['visualContainers']:
   c=json.loads(v['config'])
   if c['name'].endswith('_body'):
    ps=c['singleVisual']['objects']['general'][0]['properties']['paragraphs'];ps[0]['textRuns'][0]['value']='With multiple Indicators, select a partner block to filter Indicator Details and PRISM scores. Blocks resize as partners are added. With only one Indicator, partner names are shown as plain text and there are no filter blocks to click.';v['config']=json.dumps(c,ensure_ascii=False)
for a,b in zip(before['sections'],d['sections']):
 if a['name']=='ReportSection1':
  for va,vb in zip(a['visualContainers'],b['visualContainers']):
   if json.loads(va['config'])['name']!='severity_meaning':assert va==vb
 elif a['name']!='HelpIWPriorityGraph':assert a==b
parts['Report/Layout']=json.dumps(d,ensure_ascii=False).encode('utf-16-le');parts.pop('SecurityBindings',None);infos.pop('SecurityBindings',None);infos['DataModel'].compress_type=zipfile.ZIP_STORED
with zipfile.ZipFile(candidate,'w') as z:
 for n,b in parts.items():z.writestr(infos[n],b)
with zipfile.ZipFile(candidate) as z:assert z.testzip() is None
new=ModelReader(str(candidate))
for table in ['Unreported I&W','Snapshot','Reported I&W (5 days)','Indicator Partners']:assert new.get_table(table)==m.get_table(table),table
abf=decompress_datamodel(dm);names={f['FileName'].lower() for f in list_abf_files(abf)};db=sqlite3.connect(':memory:');db.deserialize(read_metadata_sqlite(abf));missing=[r[0] for r in db.execute('select FileName from StorageFile') if r[0] and r[0].lower() not in names];db.close();assert not missing,missing
state={'original_sha256':hashlib.sha256(raw).hexdigest(),'candidate':str(candidate)};(work/'conditional_partner_state.json').write_text(json.dumps(state,indent=2));print('Built conditional partner behavior; production dataset still contains all eight Indicators.')

