from pathlib import Path
import os,sys,site,json,zipfile,copy,hashlib,tempfile,sqlite3
lib=Path(os.environ['LOCALAPPDATA'])/'HTOC/IWDashboard/lib';sys.path.insert(0,str(lib));site.addsitedir(str(lib))
from pbix_mcp.formats.datamodel_roundtrip import decompress_datamodel
from pbix_mcp.formats.abf_rebuild import list_abf_files,read_metadata_sqlite
from restore_blank_dictionary import restore_blank_dictionary
p=Path(r'Z:\HTOC\Data_Analytics\Data\Threat Assessment Scores\ThreatAssessI_W\Dashboard\Dashobard.pbix');raw=p.read_bytes();work=Path(tempfile.mkdtemp(prefix='htoc_column_help_'));candidate=work/'ColumnHelp.pbix'
with zipfile.ZipFile(p) as z:infos={i.filename:copy.copy(i) for i in z.infolist()};parts={n:z.read(n) for n in infos}
parts['DataModel']=restore_blank_dictionary(parts['DataModel'],Path(os.environ['LOCALAPPDATA'])/'HTOC/IWDashboard/native_tests/partner_autofit_final.pbix')
d=json.loads(parts['Report/Layout'].decode('utf-16-le'));before=copy.deepcopy(d);page=d['sections'][0];table=next(v for v in page['visualContainers'] if json.loads(v['config'])['name']=='indicator_hover_column');tc=json.loads(table['config']);assert not any(json.loads(v['config'])['name'].startswith('column_help_') for v in page['visualContainers'])
lit=lambda v:{'expr':{'Literal':{'Value':v}}};txt=lambda v:lit("'"+v.replace("'","''")+"'");solid=lambda v:{'solid':{'color':txt(v)}}
# Keep help icons above the shared table when a user selects or sorts it.
tc['singleVisual'].setdefault('vcObjects',{}).setdefault('general',[{'properties':{}}])[0]['properties']['keepLayerOrder']=lit('true');table['config']=json.dumps(tc,ensure_ascii=False)
indicator_page=copy.deepcopy(next(s for s in d['sections'] if s['name']=='HelpIWAttribute_type'));indicator_page.update({'name':'HelpIWAttribute_indicator','displayName':'Indicator Definition','id':max(s.get('id',0) for s in d['sections'])+1})
for v in indicator_page['visualContainers']:
 c=json.loads(v['config']);heading=c['name'].endswith('_heading');c['name']='HelpIWAttribute_indicator_'+('heading' if heading else 'body');ps=c['singleVisual']['objects']['general'][0]['properties']['paragraphs'];ps[0]['textRuns'][0]['value']='Indicator' if heading else 'The IP address, domain, URL, file, or other observable being assessed for potential threats.'
 for para in ps:
  for run in para['textRuns'][1:]:run['value']=''
 v['config']=json.dumps(c,ensure_ascii=False)
d['sections'].append(indicator_page)
lookup={'Indicator':'indicator','Severity':'severity','PRISM Score':'prism','Indicator Type':'type','Threat Actor':'threatactor','Last Observed':'lastobserved','OpDiv':'opdiv'}
widths={o['selector']['metadata']:float(o['properties']['value']['expr']['Literal']['Value'][:-1]) for o in tc['singleVisual']['objects']['columnWidth']};x=table['x'];icons=[]
for i,pr in enumerate(tc['singleVisual']['projections']['Values']):
 ref=pr['queryRef'];name=ref.split('.',1)[1];key=lookup[name];width=widths[ref];help_page=next(s for s in d['sections'] if s['name']=='HelpIWAttribute_'+key);body=[]
 for hv in help_page['visualContainers']:
  hc=json.loads(hv['config'])
  if hc['name'].endswith('_body'):
   for o in hc['singleVisual']['objects']['general']:
    for para in o['properties']['paragraphs']:body.extend(r['value'] for r in para['textRuns'])
 definition=' '.join(body);rect={'x':x+width-14,'y':174,'width':12,'height':12,'z':30000+i,'tabOrder':30000+i}
 vc={'title':[{'properties':{'show':lit('false')}}],'background':[{'properties':{'show':lit('false')}}],'border':[{'properties':{'show':lit('false')}}],'padding':[{'properties':{k:lit('0D') for k in ['top','bottom','left','right']}}],'general':[{'properties':{'keepLayerOrder':lit('true'),'altText':txt(name+' definition')}}],'visualTooltip':[{'properties':{'show':lit('true'),'type':txt('Canvas'),'section':txt(help_page['name'])}}],'visualLink':[{'properties':{'show':lit('false'),'type':txt('Bookmark'),'tooltip':txt(definition),'disabledTooltip':txt(definition),'showDefaultTooltip':lit('false'),'suppressDefaultTooltip':lit('false')}}]}
 obj={'icon':[{'selector':{'id':'default'},'properties':{'show':lit('true'),'shapeType':txt('information'),'iconSize':lit('10D'),'lineColor':solid('#D9D9D9'),'lineWeight':lit('1D'),'horizontalAlignment':txt('center'),'verticalAlignment':txt('middle'),'leftMargin':lit('0D'),'rightMargin':lit('0D'),'topMargin':lit('0D'),'bottomMargin':lit('0D')}}],'text':[{'selector':{'id':'default'},'properties':{'show':lit('false')}}],'fill':[{'selector':{'id':state},'properties':{'show':lit('false')}} for state in ['default','hover','selected','disabled']],'outline':[{'selector':{'id':state},'properties':{'show':lit('false')}} for state in ['default','hover','selected','disabled']]}
 c={'name':'column_help_'+key,'layouts':[{'id':0,'position':copy.deepcopy(rect)}],'singleVisual':{'visualType':'actionButton','objects':obj,'vcObjects':vc}};v=copy.deepcopy(rect);v['config']=json.dumps(c,ensure_ascii=False);page['visualContainers'].append(v);icons.append({'name':name,'definition':definition,'page':help_page['name'],'visual':'column_help_'+key});x+=width
for va,vb in zip(before['sections'][0]['visualContainers'],page['visualContainers']):
 if json.loads(va['config'])['name']!='indicator_hover_column':assert va==vb
 else:
  ca=json.loads(va['config']);cb=json.loads(vb['config']);ca['singleVisual'].setdefault('vcObjects',{}).setdefault('general',[{'properties':{}}])[0]['properties']['keepLayerOrder']=lit('true');assert ca==cb
assert d['sections'][1:-1]==before['sections'][1:]
parts['Report/Layout']=json.dumps(d,ensure_ascii=False).encode('utf-16-le');parts.pop('SecurityBindings',None);infos.pop('SecurityBindings',None);infos['DataModel'].compress_type=zipfile.ZIP_STORED
with zipfile.ZipFile(candidate,'w') as z:
 for n,b in parts.items():z.writestr(infos[n],b)
with zipfile.ZipFile(candidate) as z:assert z.testzip() is None
abf=decompress_datamodel(parts['DataModel']);names={f['FileName'].lower() for f in list_abf_files(abf)};db=sqlite3.connect(':memory:');db.deserialize(read_metadata_sqlite(abf));missing=[r[0] for r in db.execute('select FileName from StorageFile') if r[0] and r[0].lower() not in names];db.close();assert not missing,missing
state={'candidate':str(candidate),'work':str(work),'original_sha256':hashlib.sha256(raw).hexdigest(),'icons':icons};(work/'state.json').write_text(json.dumps(state,indent=2));print(json.dumps({'candidate':str(candidate),'work':str(work),'original_sha256':state['original_sha256']}))
