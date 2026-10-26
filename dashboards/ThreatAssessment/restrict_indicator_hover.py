from pathlib import Path
import json,zipfile,copy,datetime,hashlib,shutil,os,sys,site
p=Path(r'Z:\HTOC\Data_Analytics\Data\Threat Assessment Scores\ThreatAssessI_W\Dashobard.pbix');original=p.read_bytes()
with zipfile.ZipFile(p) as z:parts={i.filename:z.read(i.filename) for i in z.infolist()}
l=json.loads(parts['Report/Layout'].decode('utf-16-le'));page=l['sections'][0];assert (page['width'],page['height'])==(1120,680)
lib=Path(os.environ['LOCALAPPDATA'])/'HTOC/IWDashboard/lib';sys.path.insert(0,str(lib));site.addsitedir(str(lib))
from pbix_mcp.report_binding import compile_visual_binding
def lit(v):return {'expr':{'Literal':{'Value':'true' if v is True else 'false' if v is False else str(v)+'D' if isinstance(v,(int,float)) else "'"+v+"'"}}}
def compile(s):
 def resolve(e,p,m):return None if m else 'Double' if p in ['PRISM Score','VirusTotal Malicious Score'] else 'DateTime' if p=='Last Observed' else 'String'
 resolve.summarize_by=lambda e,p:2;resolve.data_category=lambda e,p:None
 q,dt=compile_visual_binding(s,resolve);return json.dumps(q),json.dumps(dt)
old=next(v for v in page['visualContainers'] if json.loads(v['config'])['name']=='queue');oldc=json.loads(old['config']);oldsv=oldc['singleVisual'];indicator_ref='Unreported I&W.Indicator'
# Two visual regions share the exact source query, so row identity and ordering are preserved.
left=copy.deepcopy(old);lc=copy.deepcopy(oldc);lc['name']='indicator_hover_column';ls=lc['singleVisual'];ls['projections']['Values']=[a for a in ls['projections']['Values'] if a['queryRef']==indicator_ref]
right=copy.deepcopy(old);rc=copy.deepcopy(oldc);rc['name']='queue';rs=rc['singleVisual'];rs['projections']['Values']=[a for a in rs['projections']['Values'] if a['queryRef']!=indicator_ref]
left.update(x=260,y=148,width=124,height=136);right.update(x=384,y=148,width=712,height=136)
for v,c,s in [(left,lc,ls),(right,rc,rs)]:
 vc=s.setdefault('vcObjects',{});vc['title']=[{'properties':{'show':lit(False)}}];vc['border']=[{'properties':{'show':lit(False)}}];vc['background']=[{'properties':{'show':lit(False)}}]
 s.setdefault('objects',{})['columnHeaders']=[{'properties':{'wordWrap':lit(False),'fontSize':lit(10)}}]
 s['objects']['values']=[{'properties':{'wordWrap':lit(False)}}]
 s['objects']['grid']=[{'properties':{'textSize':lit(10),'rowPadding':lit(2)}}]
 s['objects']['columnWidth']=[a for a in s['objects'].get('columnWidth',[]) if (a['selector']['metadata']==indicator_ref)==(v is left)]
 if v is left:s['objects']['columnWidth'][0]['properties']['value']=lit(112)
 else:vc['visualTooltip']=[{'properties':{'show':lit(False)}}]
 v['query'],v['dataTransforms']=compile(s);v['config']=json.dumps(c,ensure_ascii=False)
# Retain the original panel and title as a non-data frame; no section is moved.
frame=copy.deepcopy(old);fc=copy.deepcopy(oldc);fc['name']='indicator_details_frame';fc['singleVisual']={'visualType':'textbox','objects':{'general':[{'properties':{'paragraphs':[]}}]},'vcObjects':copy.deepcopy(oldsv['vcObjects'])};fc['singleVisual']['vcObjects']['visualTooltip']=[{'properties':{'show':lit(False)}}];frame['config']=json.dumps(fc,ensure_ascii=False)
for k in ['query','dataTransforms','filters']:frame.pop(k,None)
visuals=[]
for v in page['visualContainers']:
 c=json.loads(v['config']);name=c['name']
 if name=='queue':visuals.extend([frame,left,right]);continue
 if name!='reported_last5days' and c['singleVisual'].get('vcObjects',{}).get('visualTooltip'):
  c['singleVisual']['vcObjects']['visualTooltip']=[{'properties':{'show':lit(False)}}];v['config']=json.dumps(c,ensure_ascii=False)
 visuals.append(v)
for i,v in enumerate(visuals):
 c=json.loads(v['config']);v['z']=i*1000;v['tabOrder']=(i+1)*1000;c['layouts']=[{'id':0,'position':{k:v[k] for k in ['x','y','z','width','height','tabOrder']}}];v['config']=json.dumps(c,ensure_ascii=False)
 assert v['x']+v['width']<=1120 and v['y']+v['height']<=680
 # Only the two Indicator-only tables may show assessment tooltips.
 tips=c['singleVisual'].get('vcObjects',{}).get('visualTooltip',[])
 if any(e.get('properties',{}).get('show')==lit(True) for e in tips):
  assert c['name'] in ['indicator_hover_column','reported_last5days']
  assert all(p['queryRef'].endswith('.Indicator') for p in c['singleVisual']['projections']['Values'])
assert ls['prototypeQuery']==rs['prototypeQuery']
assert json.loads(left['query'])==json.loads(right['query'])
page['visualContainers']=visuals
names={json.loads(v['config'])['name'] for v in visuals};cfg=json.loads(page.get('config','{}'));cfg['relationships']=[r for r in cfg.get('relationships',[]) if r['source'] in names and r['target'] in names];cfg['relationships'] += [{'source':a,'target':b,'type':3} for a in ['indicator_hover_column'] for b in names if a!=b]+[{'source':a,'target':'indicator_hover_column','type':3} for a in names if a!='indicator_hover_column'];page['config']=json.dumps(cfg)
parts['Report/Layout']=json.dumps(l,ensure_ascii=False).encode('utf-16-le');parts.pop('SecurityBindings',None)
backup=p.with_name('Dashobard.before-indicator-hover-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'.pbix');assert not backup.exists();shutil.copy2(p,backup)
staging=p.with_name('Dashobard.indicator-hover.tmp');assert not staging.exists()
with zipfile.ZipFile(staging,'w',zipfile.ZIP_DEFLATED) as z:
 for n,b in parts.items():z.writestr(n,b)
with zipfile.ZipFile(staging) as z:assert z.testzip() is None;assert z.read('DataModel')==parts['DataModel']
assert hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256(original).digest();os.replace(staging,p)
print('Saved: canvas 1120x680 and existing section bounds unchanged. Assessment tooltips assigned only to Indicator-only columns. Chart and other-column assessment tooltips disabled. Data model unchanged.')
