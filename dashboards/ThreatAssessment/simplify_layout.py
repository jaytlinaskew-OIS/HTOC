from pathlib import Path
import json,zipfile,datetime,shutil,os,hashlib,sys,site
p=Path(r'Z:\HTOC\Data_Analytics\Data\Threat Assessment Scores\ThreatAssessI_W\Dashobard.pbix')
before=p.read_bytes()
with zipfile.ZipFile(p) as z:parts={i.filename:z.read(i.filename) for i in z.infolist()}
l=json.loads(parts['Report/Layout'].decode('utf-16-le'));page=l['sections'][0];page['height']=900
removed={'modified','metric_guide','kpi_2','kpi_2_meaning'}
visuals=[v for v in page['visualContainers'] if json.loads(v['config'])['name'] not in removed]
byname={json.loads(v['config'])['name']:v for v in visuals}
for name,x,w in [('kpi_0',24,504),('kpi_1',544,504),('kpi_3',1064,512)]:
 byname[name].update(x=x,width=w);byname[name+'_meaning'].update(x=x,width=w)
byname['explanation'].update(x=1072,y=570,width=504,height=230)
byname['refreshed'].update(x=24,y=816,width=1552,height=64)
# Keep the assessment notes focused on the item and its explanation in the narrower panel.
v=byname['explanation'];cfg=json.loads(v['config']);sv=cfg['singleVisual'];keep={'Indicator','Explanation'}
selects=[s for s in sv['prototypeQuery']['Select'] if (s.get('Column') or {}).get('Property') in keep]
sv['prototypeQuery']['Select']=selects;refs={s['Name'] for s in selects};sv['projections']['Values']=[f for f in sv['projections']['Values'] if f['queryRef'] in refs]
sv.setdefault('objects',{}).setdefault('values',[{'properties':{}}])[0]['properties']['wordWrap']={'expr':{'Literal':{'Value':'true'}}}
lib=Path(os.environ['LOCALAPPDATA'])/'HTOC/IWDashboard/lib';sys.path.insert(0,str(lib));site.addsitedir(str(lib))
from pbix_mcp.report_binding import compile_visual_binding
def resolve(e,p,m):return None if m else 'String'
resolve.summarize_by=lambda e,p:2;resolve.data_category=lambda e,p:None
q,dt=compile_visual_binding(sv,resolve);v['query']=json.dumps(q);v['dataTransforms']=json.dumps(dt);v['config']=json.dumps(cfg)
# Synchronize Power BI's two saved copies of each visual's position.
for i,v in enumerate(visuals):
 v['z']=i*1000;v['tabOrder']=(i+1)*1000
 c=json.loads(v['config']);c['layouts']=[{'id':0,'position':{k:v[k] for k in ['x','y','z','width','height','tabOrder']}}];v['config']=json.dumps(c,ensure_ascii=False)
page['visualContainers']=visuals
cfg=json.loads(page.get('config','{}'));names=set(byname);cfg['relationships']=[r for r in cfg.get('relationships',[]) if r['source'] in names and r['target'] in names];page['config']=json.dumps(cfg)
assert len(l['sections'])==1
for i,v in enumerate(visuals):
 assert v['x']>=0 and v['y']>=0 and v['x']+v['width']<=1600 and v['y']+v['height']<=900
 for b in visuals[:i]:
  assert not (min(v['x']+v['width'],b['x']+b['width'])>max(v['x'],b['x']) and min(v['y']+v['height'],b['y']+b['height'])>max(v['y'],b['y']))
parts['Report/Layout']=json.dumps(l,ensure_ascii=False).encode('utf-16-le');parts.pop('SecurityBindings',None)
backup=p.with_name('Dashobard.before-simplify-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'.pbix');assert not backup.exists();shutil.copy2(p,backup)
staging=p.with_name('Dashobard.simplified.tmp');assert not staging.exists()
with zipfile.ZipFile(staging,'w',zipfile.ZIP_DEFLATED) as z:
 for n,b in parts.items():z.writestr(n,b)
with zipfile.ZipFile(staging) as z:assert z.testzip() is None;assert z.read('DataModel')==parts['DataModel']
assert hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256(before).digest();os.replace(staging,p)
print('Updated:',p)
print('Removed source-file timestamp, reading guide, and average risk card. Assessment notes moved right. One page, three metric cards, no overlaps. Data model unchanged.')
