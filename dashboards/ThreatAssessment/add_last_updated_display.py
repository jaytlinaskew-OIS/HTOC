from pathlib import Path
import zipfile,json,copy,os,sys,site,hashlib,sqlite3
lib=Path(os.environ['LOCALAPPDATA'])/'HTOC/IWDashboard/lib';sys.path.insert(0,str(lib));site.addsitedir(str(lib))
from pbix_mcp.formats.datamodel_roundtrip import decompress_datamodel
from pbix_mcp.formats.abf_rebuild import list_abf_files,read_metadata_sqlite
p=Path(r'Z:\HTOC\Data_Analytics\Data\Threat Assessment Scores\ThreatAssessI_W\Dashboard\Dashobard.pbix');raw=p.read_bytes()
with zipfile.ZipFile(p) as z:infos={i.filename:copy.copy(i) for i in z.infolist()};parts={n:z.read(n) for n in infos}
abf=decompress_datamodel(parts['DataModel']);names={f['FileName'].lower() for f in list_abf_files(abf)};db=sqlite3.connect(':memory:');db.deserialize(read_metadata_sqlite(abf));missing=[r[0] for r in db.execute('select FileName from StorageFile') if r[0] and r[0].lower() not in names];db.close();assert not missing,missing
lit=lambda v:{'expr':{'Literal':{'Value':v}}}
d=json.loads(parts['Report/Layout'].decode('utf-16-le'));before=copy.deepcopy(d);page=d['sections'][0];by={json.loads(v['config'])['name']:v for v in page['visualContainers']};assert 'last_updated_timestamp' not in by
# Keep all existing visuals, including the Date card, exactly in place.
card=copy.deepcopy(by['overview_asof']);c=json.loads(card['config']);c['name']='last_updated_timestamp'
for k,val in dict(x=972,y=102,width=132,height=16,z=2100,tabOrder=2100).items():card[k]=val
for layout in c['layouts']:layout['position']={k:card[k] for k in ['x','y','width','height','z','tabOrder']}
sv=c['singleVisual'];sv['projections']['Values']=[{'queryRef':'Snapshot.Last Refresh'}];sel=sv['prototypeQuery']['Select'][0];sel['Measure']['Property']='Last Refresh';sel['Name']='Snapshot.Last Refresh';sv['objects']['labels'][0]['properties'].update({'fontSize':lit('8D'),'fontFamily':lit("'Segoe UI'")})
vc=sv['vcObjects']
for key in ['title','background','border']:vc[key][0]['properties']['show']=lit('false')
vc['padding']=[{'properties':{k:lit('0D') for k in ['top','bottom','left','right']}}];vc['visualTooltip'][0]['properties']['section']=lit("'HelpIWLastUpdated'")
card['config']=json.dumps(c,ensure_ascii=False)
q=json.loads(card['query']);q['Commands'][0]['SemanticQueryDataShapeCommand']['Query']=copy.deepcopy(sv['prototypeQuery']);card['query']=json.dumps(q,ensure_ascii=False)
t=json.loads(card['dataTransforms']);t['objects']=copy.deepcopy(sv['objects']);meta=t['queryMetadata']['Select'][0];meta.update({'Restatement':'Last Refresh','Name':'Snapshot.Last Refresh','Format':'dd MMM yyyy HH:mm'});s=t['selects'][0];s.update({'displayName':'Last Refresh','queryName':'Snapshot.Last Refresh','format':'dd MMM yyyy HH:mm'});s['expr']['Measure']['Property']='Last Refresh';card['dataTransforms']=json.dumps(t,ensure_ascii=False)
label={'x':904,'y':102,'width':68,'height':16,'z':2099,'tabOrder':2099};lc={'name':'last_updated_label','layouts':[{'id':0,'position':copy.deepcopy(label)}],'singleVisual':{'visualType':'textbox','objects':{'general':[{'properties':{'paragraphs':[{'textRuns':[{'value':'Last updated:','textStyle':{'fontFamily':'Segoe UI','fontSize':'8pt','color':'#D9D9D9'}}]}]}}]},'vcObjects':{'title':[{'properties':{'show':lit('false')}}],'background':[{'properties':{'show':lit('false')}}],'border':[{'properties':{'show':lit('false')}}],'padding':[{'properties':{k:lit('0D') for k in ['top','bottom','left','right']}}],'visualTooltip':[{'properties':{'show':lit('false')}}]}}};label['config']=json.dumps(lc,ensure_ascii=False)
page['visualContainers'].extend([label,card])
help_page=copy.deepcopy(next(s for s in d['sections'] if s['name']=='HelpIWDataDate'));help_page.update({'name':'HelpIWLastUpdated','displayName':'Last Updated','id':max(s.get('id',0) for s in d['sections'])+1})
for v in help_page['visualContainers']:
 hc=json.loads(v['config']);is_heading=hc['name'].endswith('_heading');hc['name']='HelpIWLastUpdated_'+('heading' if is_heading else 'body');ps=hc['singleVisual']['objects']['general'][0]['properties']['paragraphs'];ps[0]['textRuns'][0]['value']='Last Updated' if is_heading else 'The last time data was loaded into this dashboard. This can differ from the source report date. Editing the layout does not change this time.'
 for para in ps:
  for run in para['textRuns'][1:]:run['value']=''
 v['config']=json.dumps(hc,ensure_ascii=False)
d['sections'].append(help_page)
assert page['visualContainers'][:-2]==before['sections'][0]['visualContainers'];assert d['sections'][1:-1]==before['sections'][1:]
parts['Report/Layout']=json.dumps(d,ensure_ascii=False).encode('utf-16-le');parts.pop('SecurityBindings',None);infos.pop('SecurityBindings',None);infos['DataModel'].compress_type=zipfile.ZIP_STORED
work=Path(os.environ['LOCALAPPDATA'])/'HTOC/IWDashboard/native_tests';candidate=work/'last_updated_display_test.pbix'
with zipfile.ZipFile(candidate,'w') as z:
 for n,b in parts.items():z.writestr(infos[n],b)
with zipfile.ZipFile(candidate) as z:
 assert z.testzip() is None
 for n,b in parts.items():assert z.read(n)==b,n
with zipfile.ZipFile(p) as z:
 for n,b in parts.items():
  if n!='Report/Layout':assert z.read(n)==b,n
(work/'last_updated_display_state.json').write_text(json.dumps({'candidate':str(candidate),'original_sha256':hashlib.sha256(raw).hexdigest()},indent=2));print('Added compact Last updated label and refresh timestamp beneath Date; existing data and visuals unchanged.')
