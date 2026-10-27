from pathlib import Path
import zipfile,json,copy,hashlib,os,sys,site,sqlite3
lib=Path(os.environ['LOCALAPPDATA'])/'HTOC/IWDashboard/lib';sys.path.insert(0,str(lib));site.addsitedir(str(lib))
from pbix_mcp.formats.datamodel_roundtrip import decompress_datamodel
from pbix_mcp.formats.abf_rebuild import list_abf_files,read_metadata_sqlite
p=Path(r'Z:\HTOC\Data_Analytics\Data\Threat Assessment Scores\ThreatAssessI_W\Dashboard\Dashobard.pbix');raw=p.read_bytes()
with zipfile.ZipFile(p) as z:
 infos={i.filename:copy.copy(i) for i in z.infolist()};parts={n:z.read(n) for n in infos}
d=json.loads(parts['Report/Layout'].decode('utf-16-le'));before=copy.deepcopy(d);page=d['sections'][0];vs=page['visualContainers'];by={json.loads(v['config'])['name']:v for v in vs}
removed={'detail_severity','detail_prism','detail_type','detail_threatactor','detail_lastobserved','detail_opdiv'}
v=by['indicator_hover_column'];c=json.loads(v['config']);sv=c['singleVisual'];selects=sv['prototypeQuery']['Select'];assert len(selects)==7
sv['projections']['Values']=[{'queryRef':s['Name']} for s in selects]
sv['prototypeQuery']['OrderBy']=[{'Direction':2,'Expression':copy.deepcopy(selects[2]['Column']) and {'Column':copy.deepcopy(selects[2]['Column'])}},{'Direction':1,'Expression':{'Column':copy.deepcopy(selects[0]['Column'])}}]
widths=[114,70,86,106,154,108,166]
sv['objects']['columnWidth']=[{'properties':{'value':{'expr':{'Literal':{'Value':str(w)+'D'}}}},'selector':{'metadata':s['Name']}} for s,w in zip(selects,widths)]
sv['objects']['columnHeaders'][0]['properties']['wordWrap']={'expr':{'Literal':{'Value':'true'}}}
sv['objects']['total']=[{'properties':{'totals':{'expr':{'Literal':{'Value':'false'}}}}}]
v['width']=836
for layout in c['layouts']:layout['position'].update({k:v[k] for k in ['x','y','width','height','z','tabOrder']})
v['config']=json.dumps(c,ensure_ascii=False)
q=json.loads(v['query']);cmd=q['Commands'][0]['SemanticQueryDataShapeCommand'];cmd['Query']=copy.deepcopy(sv['prototypeQuery']);cmd['Binding']['Primary']['Groupings']=[{'Projections':list(range(7))}];v['query']=json.dumps(q,ensure_ascii=False)
t=json.loads(v['dataTransforms']);t['objects']=copy.deepcopy(sv['objects']);t['projectionOrdering']={'Values':list(range(7))}
metadata={}
for name in ['indicator_hover_column']+list(removed):
 td=json.loads(by[name]['dataTransforms'])
 for s in td.get('queryMetadata',{}).get('Select',[]):
  if s:metadata[s['Name']]=s
for s in t['selects']:s['roles']={'Values':True}
t['queryMetadata']['Select']=[metadata.get(s['queryName'],{'Restatement':s['displayName'],'Name':s['queryName'],'Type':2048 if s['type']['underlyingType']==1 else s['type']['underlyingType']}) for s in t['selects']]
t['visualElements']=[{'DataRoles':[{'Name':'Values','Projection':i,'isActive':False} for i in range(7)]}]
v['dataTransforms']=json.dumps(t,ensure_ascii=False)
page['visualContainers']=[x for x in vs if json.loads(x['config'])['name'] not in removed]
pc=json.loads(page['config']);pc['relationships']=[r for r in pc.get('relationships',[]) if r.get('source') not in removed and r.get('target') not in removed];page['config']=json.dumps(pc,ensure_ascii=False)
assert d['sections'][1:]==before['sections'][1:]
oldby={json.loads(x['config'])['name']:x for x in before['sections'][0]['visualContainers']}
for x in page['visualContainers']:
 n=json.loads(x['config'])['name']
 if n!='indicator_hover_column':assert x==oldby[n],n
parts['Report/Layout']=json.dumps(d,ensure_ascii=False).encode('utf-16-le')
parts.pop('SecurityBindings',None);infos.pop('SecurityBindings',None);infos['DataModel'].compress_type=zipfile.ZIP_STORED
abf=decompress_datamodel(parts['DataModel']);names={f['FileName'].lower() for f in list_abf_files(abf)};db=sqlite3.connect(':memory:');db.deserialize(read_metadata_sqlite(abf));missing=[r[0] for r in db.execute('select FileName from StorageFile') if r[0] and r[0].lower() not in names];db.close();assert not missing,missing
work=Path(os.environ['LOCALAPPDATA'])/'HTOC/IWDashboard/native_tests';candidate=work/'aligned_details_test.pbix'
with zipfile.ZipFile(candidate,'w') as z:
 for n,b in parts.items():z.writestr(infos[n],b)
with zipfile.ZipFile(candidate) as z:
 assert z.testzip() is None
 for n,b in parts.items():assert z.read(n)==b,n
with zipfile.ZipFile(p) as z:
 for n,b in parts.items():
  if n!='Report/Layout':assert z.read(n)==b,n
state={'original_sha256':hashlib.sha256(raw).hexdigest(),'candidate':str(candidate),'layout_sha256':hashlib.sha256(parts['Report/Layout']).hexdigest()};(work/'aligned_details_state.json').write_text(json.dumps(state,indent=2))
print('Candidate created: single native details table, seven columns, shared sorting and scrolling. Model and all other visuals/pages preserved.')

