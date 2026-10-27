from pathlib import Path
import os,sys,site,json,zipfile,copy,hashlib,tempfile,shutil
lib=Path(os.environ['LOCALAPPDATA'])/'HTOC/IWDashboard/lib';sys.path.insert(0,str(lib));site.addsitedir(str(lib))
from pbix_mcp import server as api
from pbix_mcp.formats.model_reader import ModelReader
from pbix_mcp.report_binding import compile_visual_binding
from restore_blank_dictionary import restore_blank_dictionary
p=Path(r'Z:\HTOC\Data_Analytics\Data\Threat Assessment Scores\ThreatAssessI_W\Dashboard\Dashobard.pbix');raw=p.read_bytes();work=Path(tempfile.mkdtemp(prefix='htoc_themed_column_help_'));candidate=work/'ThemedColumnHelp.pbix';shutil.copyfile(p,candidate)
with zipfile.ZipFile(p) as z:infos={i.filename:copy.copy(i) for i in z.infolist()};parts={n:z.read(n) for n in infos}
def ok(s):
 r=json.loads(s)
 if not r.get('success'):raise RuntimeError(str(r)[:900])
 return r
alias='iw_themed_column_help';ok(api.pbix_open(str(candidate),alias))
try:
 ok(api.pbix_datamodel_add_measure(alias,'Snapshot','Column Help Icon','UNICHAR(9432)',description='Information icon for the individual column definition hover cards.',data_type='String'))
 ok(api.pbix_datamodel_modify_metadata(alias,"UPDATE Measure SET IsHidden=1 WHERE Name='Column Help Icon'"))
 info=api._ensure_open(alias);dm=(Path(info['work_dir'])/'DataModel').read_bytes()
finally:ok(api.pbix_close(alias,force=True))
parts['DataModel']=restore_blank_dictionary(dm,Path(os.environ['LOCALAPPDATA'])/'HTOC/IWDashboard/native_tests/partner_autofit_final.pbix')
d=json.loads(parts['Report/Layout'].decode('utf-16-le'));before=copy.deepcopy(d);lit=lambda v:{'expr':{'Literal':{'Value':v}}};txt=lambda v:lit("'"+v.replace("'","''")+"'");solid=lambda v:{'solid':{'color':txt(v)}};icons=[]
for v in d['sections'][0]['visualContainers']:
 c=json.loads(v['config']);name=c['name']
 if name.startswith('column_help_'):
  oldsv=c['singleVisual'];vc=copy.deepcopy(oldsv['vcObjects']);vc.pop('visualLink',None);key=name[len('column_help_'):];page='HelpIWAttribute_'+key;assert any(s['name']==page for s in d['sections'])
  vc['visualTooltip']=[{'properties':{'show':lit('true'),'type':txt('Canvas'),'section':txt(page)}}];vc['visualHeader']=[{'properties':{'show':lit('false')}}];vc['padding']=[{'properties':{k:lit('0D') for k in ['top','bottom','left','right']}}]
  sv={'visualType':'card','projections':{'Values':[{'queryRef':'Snapshot.Column Help Icon'}]},'prototypeQuery':{'Version':2,'From':[{'Name':'s','Entity':'Snapshot','Type':0}],'Select':[{'Measure':{'Expression':{'SourceRef':{'Source':'s'}},'Property':'Column Help Icon'},'Name':'Snapshot.Column Help Icon'}]},'objects':{'labels':[{'properties':{'fontSize':lit('9D'),'color':solid('#D9D9D9'),'fontFamily':txt('Segoe UI Symbol')}}],'categoryLabels':[{'properties':{'show':lit('false')}}],'wordWrap':[{'properties':{'show':lit('false')}}]},'vcObjects':vc}
  v['width']=14;v['height']=14
  for layout in c['layouts']:layout['position'].update({'width':14,'height':14})
  c['singleVisual']=sv;q,t=compile_visual_binding(sv,lambda e,p,is_measure:'String');v['config']=json.dumps(c,ensure_ascii=False);v['query']=json.dumps(q,ensure_ascii=False);v['dataTransforms']=json.dumps(t,ensure_ascii=False);icons.append({'visual':name,'page':page,'label':vc['general'][0]['properties']['altText']['expr']['Literal']['Value'].strip("'")})
assert len(icons)==7
for va,vb in zip(before['sections'][0]['visualContainers'],d['sections'][0]['visualContainers']):
 if not json.loads(va['config'])['name'].startswith('column_help_'):assert va==vb
assert before['sections'][1:]==d['sections'][1:]
parts['Report/Layout']=json.dumps(d,ensure_ascii=False).encode('utf-16-le');parts.pop('SecurityBindings',None);infos.pop('SecurityBindings',None);infos['DataModel'].compress_type=zipfile.ZIP_STORED
with zipfile.ZipFile(candidate,'w') as z:
 for n,b in parts.items():z.writestr(infos[n],b)
with zipfile.ZipFile(candidate) as z:assert z.testzip() is None
oldm=ModelReader(str(p));newm=ModelReader(str(candidate))
for table in ['Unreported I&W','Snapshot','Reported I&W (5 days)','Indicator Partners']:assert oldm.get_table(table)==newm.get_table(table),table
state={'candidate':str(candidate),'work':str(work),'original_sha256':hashlib.sha256(raw).hexdigest(),'icons':icons};(work/'state.json').write_text(json.dumps(state,indent=2));print(json.dumps({'candidate':str(candidate),'work':str(work),'original_sha256':state['original_sha256']}))
