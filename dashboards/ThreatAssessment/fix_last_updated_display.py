from pathlib import Path
import os,sys,site,json,zipfile,copy,hashlib,tempfile,sqlite3,shutil
lib=Path(os.environ['LOCALAPPDATA'])/'HTOC/IWDashboard/lib';sys.path.insert(0,str(lib));site.addsitedir(str(lib))
from pbix_mcp import server as api
from pbix_mcp.formats.model_reader import ModelReader
from pbix_mcp.formats.datamodel_roundtrip import decompress_datamodel
from pbix_mcp.formats.abf_rebuild import list_abf_files,read_metadata_sqlite
from pbix_mcp.report_binding import compile_visual_binding
from restore_blank_dictionary import restore_blank_dictionary
p=Path(r'Z:\HTOC\Data_Analytics\Data\Threat Assessment Scores\ThreatAssessI_W\Dashboard\Dashobard.pbix');raw=p.read_bytes();work=Path(tempfile.mkdtemp(prefix='htoc_last_updated_fix_'));candidate=work/'Dashobard.pbix';shutil.copyfile(p,candidate)
with zipfile.ZipFile(p) as z:infos={i.filename:copy.copy(i) for i in z.infolist()};parts={n:z.read(n) for n in infos}
def ok(s):
 r=json.loads(s)
 if not r.get('success'):raise RuntimeError(str(r)[:900])
 return r
alias='iw_compact_updated';ok(api.pbix_open(str(candidate),alias))
try:
 ok(api.pbix_datamodel_add_measure(alias,'Snapshot','Last Updated Display','"Last updated: " & IF(ISBLANK([Last Refresh]), "Not available", FORMAT([Last Refresh], "dd MMM yyyy HH:mm"))',description='One-line display of the last data load time.',data_type='String'))
 info=api._ensure_open(alias);dm=(Path(info['work_dir'])/'DataModel').read_bytes()
finally:ok(api.pbix_close(alias,force=True))
donor=Path(os.environ['LOCALAPPDATA'])/'HTOC/IWDashboard/native_tests/partner_autofit_final.pbix';parts['DataModel']=restore_blank_dictionary(dm,donor)
d=json.loads(parts['Report/Layout'].decode('utf-16-le'));before=copy.deepcopy(d);page=d['sections'][0];v=next(x for x in page['visualContainers'] if json.loads(x['config'])['name']=='last_updated_timestamp');c=json.loads(v['config']);v['x']=904;v['width']=200
for layout in c['layouts']:layout['position'].update({'x':904,'width':200})
lit=lambda x:{'expr':{'Literal':{'Value':x}}};sv=c['singleVisual'];sv['projections']['Values']=[{'queryRef':'Snapshot.Last Updated Display'}];sel=sv['prototypeQuery']['Select'][0];sel['Measure']['Property']='Last Updated Display';sel['Name']='Snapshot.Last Updated Display';sv['objects']['wordWrap']=[{'properties':{'show':lit('false')}}];sv['objects']['labels'][0]['properties']['fontSize']=lit('8D');q,t=compile_visual_binding(sv,lambda e,p,is_measure:'String');v['config']=json.dumps(c,ensure_ascii=False);v['query']=json.dumps(q,ensure_ascii=False);v['dataTransforms']=json.dumps(t,ensure_ascii=False)
page['visualContainers']=[x for x in page['visualContainers'] if json.loads(x['config'])['name']!='last_updated_label'];cfg=json.loads(page['config']);cfg['relationships']=[r for r in cfg.get('relationships',[]) if r.get('source')!='last_updated_label' and r.get('target')!='last_updated_label'];page['config']=json.dumps(cfg,ensure_ascii=False)
old={json.loads(x['config'])['name']:x for x in before['sections'][0]['visualContainers']}
for x in page['visualContainers']:
 name=json.loads(x['config'])['name']
 if name!='last_updated_timestamp':assert x==old[name],name
assert d['sections'][1:]==before['sections'][1:]
parts['Report/Layout']=json.dumps(d,ensure_ascii=False).encode('utf-16-le');parts.pop('SecurityBindings',None);infos.pop('SecurityBindings',None);infos['DataModel'].compress_type=zipfile.ZIP_STORED
with zipfile.ZipFile(candidate,'w') as z:
 for n,b in parts.items():z.writestr(infos[n],b)
with zipfile.ZipFile(candidate) as z:assert z.testzip() is None
oldm=ModelReader(str(p));newm=ModelReader(str(candidate))
for table in ['Unreported I&W','Snapshot','Reported I&W (5 days)','Indicator Partners']:assert oldm.get_table(table)==newm.get_table(table),table
abf=decompress_datamodel(parts['DataModel']);names={f['FileName'].lower() for f in list_abf_files(abf)};db=sqlite3.connect(':memory:');db.deserialize(read_metadata_sqlite(abf));missing=[r[0] for r in db.execute('select FileName from StorageFile') if r[0] and r[0].lower() not in names];db.close();assert not missing,missing
state={'candidate':str(candidate),'work':str(work),'original_sha256':hashlib.sha256(raw).hexdigest()};(work/'state.json').write_text(json.dumps(state,indent=2));print(json.dumps(state))
