from pathlib import Path
import zipfile,json,copy,textwrap,datetime,shutil,hashlib,os,sys,site
p=Path(r'Z:\HTOC\Data_Analytics\Data\Threat Assessment Scores\ThreatAssessI_W\Dashboard\Dashobard.pbix');before=p.read_bytes()
with zipfile.ZipFile(p) as z:parts={i.filename:z.read(i.filename) for i in z.infolist()}
l=json.loads(parts['Report/Layout'].decode('utf-16-le'));main=l['sections'][0];canvas=(main['width'],main['height'])
old=next(v for v in main['visualContainers'] if json.loads(v['config'])['name']=='queue');base=json.loads(old['config']);source_query=copy.deepcopy(base['singleVisual']['prototypeQuery'])
combined=next(s for s in l['sections'] if s['name']=='HelpIWDetailDefinitions');body=next(v for v in combined['visualContainers'] if json.loads(v['config'])['name'].endswith('_body'));paragraphs=json.loads(body['config'])['singleVisual']['objects']['general'][0]['properties']['paragraphs'];definitions={}
for para in paragraphs:
 text=''.join(r.get('value','') for r in para['textRuns']);name,meaning=text.split(':',1);definitions[name]=meaning.strip()
l['sections']=[s for s in l['sections'] if s['name']!='HelpIWDetailDefinitions']
lib=Path(os.environ['LOCALAPPDATA'])/'HTOC/IWDashboard/lib';sys.path.insert(0,str(lib));site.addsitedir(str(lib))
from pbix_mcp.report_binding import compile_visual_binding
def lit(v):return {'expr':{'Literal':{'Value':'true' if v is True else 'false' if v is False else str(v)+'D' if isinstance(v,(int,float)) else "'"+v.replace("'","''")+"'"}}}
def textbox(name,text,x,y,w,h,size,bold=False):
 s={'visualType':'textbox','objects':{'general':[{'properties':{'paragraphs':[{'textRuns':[{'value':text,'textStyle':{'fontFamily':'Segoe UI','fontSize':str(size)+'pt','color':'#18324D' if bold else '#42556A','fontWeight':'bold' if bold else 'normal'}}]}]}}]},'vcObjects':{'title':[{'properties':{'show':lit(False)}}],'visualTooltip':[{'properties':{'show':lit(False)}}]}}
 return {'x':x,'y':y,'width':w,'height':h,'config':json.dumps({'name':name,'singleVisual':s},ensure_ascii=False)}
fields=[('severity','Severity',64),('prism','PRISM Score',80),('type','Indicator Type',98),('virustotal','VirusTotal Malicious Score',160),('lastobserved','Last Observed',110),('opdiv','OpDiv',200)]
new=[];x=old['x'];queries=[]
for short,field,width in fields:
 page_id='HelpIWAttribute_'+short;meaning=definitions[field];body_h=max(56,len(textwrap.wrap(meaning,50))*22+12)
 h=body_h+64;tooltip={'name':page_id,'displayName':field+' Definition','ordinal':len(l['sections']),'filters':'[]','config':json.dumps({'visibility':1,'type':1}),'displayOption':3,'width':460,'height':h,'visualContainers':[textbox(page_id+'_heading',field,12,8,436,36,14,True),textbox(page_id+'_body',meaning,12,48,436,body_h,12)]}
 l['sections'].append(tooltip)
 v=copy.deepcopy(old);c=copy.deepcopy(base);c['name']='detail_'+short;s=c['singleVisual'];ref='Unreported I&W.'+field
 s['projections']['Values']=[{'queryRef':ref}]
 s['objects']['columnWidth']=[{'selector':{'metadata':ref},'properties':{'value':lit(max(40,width-12))}}]
 s['vcObjects']['visualTooltip']=[{'properties':{'show':lit(True),'type':lit('Canvas'),'section':lit(page_id)}}]
 def resolve(e,prop,m):return None if m else 'Double' if prop in ['PRISM Score','VirusTotal Malicious Score'] else 'DateTime' if prop=='Last Observed' else 'String'
 resolve.summarize_by=lambda e,p:2;resolve.data_category=lambda e,p:None
 q,dt=compile_visual_binding(s,resolve);v['query']=json.dumps(q);v['dataTransforms']=json.dumps(dt);v.update(x=x,y=old['y'],width=width,height=old['height']);v['config']=json.dumps(c,ensure_ascii=False)
 assert s['prototypeQuery']==source_query;queries.append(q);new.append(v);x+=width
assert x==old['x']+old['width'];assert all(q==queries[0] for q in queries)
visible=[]
for v in main['visualContainers']:
 if json.loads(v['config'])['name']=='queue':visible.extend(new)
 else:visible.append(v)
main['visualContainers']=visible;names={json.loads(v['config'])['name'] for v in visible};cfg=json.loads(main.get('config','{}'));cfg['relationships']=[r for r in cfg.get('relationships',[]) if r['source'] in names and r['target'] in names]
for v in new:
 name=json.loads(v['config'])['name'];cfg['relationships'] += [{'source':name,'target':n,'type':3} for n in names if n!=name]+[{'source':n,'target':name,'type':3} for n in names if n!=name]
main['config']=json.dumps(cfg)
for page in l['sections']:
 for i,v in enumerate(page['visualContainers']):
  v['z']=i*1000;v['tabOrder']=(i+1)*1000;c=json.loads(v['config']);c['layouts']=[{'id':0,'position':{k:v[k] for k in ['x','y','z','width','height','tabOrder']}}];v['config']=json.dumps(c,ensure_ascii=False)
  assert v['x']+v['width']<=page['width'] and v['y']+v['height']<=page['height']
assert (main['width'],main['height'])==canvas==(1120,680)
assert sum(json.loads(s.get('config','{}')).get('visibility',0)!=1 for s in l['sections'])==1
for v in new:
 c=json.loads(v['config']);assert len(c['singleVisual']['projections']['Values'])==1
for v in main['visualContainers']:
 c=json.loads(v['config'])
 if c['name'] in ['indicator_hover_column','reported_last5days']:assert 'ReportSectionIW' in c['singleVisual']['vcObjects']['visualTooltip'][0]['properties']['section']['expr']['Literal']['Value']
parts['Report/Layout']=json.dumps(l,ensure_ascii=False).encode('utf-16-le');parts.pop('SecurityBindings',None)
backup=p.with_name('Dashobard.before-attribute-hovers-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'.pbix');assert not backup.exists();shutil.copy2(p,backup)
staging=p.with_name('Dashobard.attribute-hovers.tmp');assert not staging.exists()
with zipfile.ZipFile(staging,'w',zipfile.ZIP_DEFLATED) as z:
 for n,b in parts.items():z.writestr(n,b)
with zipfile.ZipFile(staging) as z:assert z.testzip() is None;assert z.read('DataModel')==parts['DataModel']
assert hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256(before).digest();os.replace(staging,p)
print('Saved six attribute-specific definition cards. Detail area occupies the exact same rectangle; common source query and sort preserved. Canvas, data, and Indicator assessment-and-Tags hovers unchanged.')
