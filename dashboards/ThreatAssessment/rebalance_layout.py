from pathlib import Path
import zipfile,json,datetime,shutil,hashlib,os
p=Path(r'Z:\HTOC\Data_Analytics\Data\Threat Assessment Scores\ThreatAssessI_W\Dashobard.pbix')
before=p.read_bytes()
with zipfile.ZipFile(p) as z:parts={i.filename:z.read(i.filename) for i in z.infolist()}
l=json.loads(parts['Report/Layout'].decode('utf-16-le'));page=l['sections'][0];page['width']=1600;page['height']=840
visuals=[v for v in page['visualContainers'] if json.loads(v['config'])['name']!='refreshed']
positions={
 'dashboard_title':(24,12,1200,64),'dashboard_subtitle':(24,78,1200,30),'overview_asof':(1280,12,296,90),
 'reported_last5days':(24,120,280,260),
 'kpi_0':(320,120,220,100),'kpi_0_meaning':(320,226,220,74),
 'kpi_3':(556,120,240,100),'kpi_3_meaning':(556,226,240,74),
 'explanation':(820,120,756,260),
 'severity':(24,396,504,180),'severity_meaning':(24,582,504,52),
 'verdict':(544,396,504,180),'verdict_meaning':(544,582,504,52),
 'prism':(1064,396,512,180),'prism_meaning':(1064,582,512,52),
 'queue':(24,650,1552,166)}
def literal(v):return {'expr':{'Literal':{'Value':str(v)+'D' if isinstance(v,(int,float)) else "'"+v.replace("'","''")+"'"}}}
for i,v in enumerate(visuals):
 c=json.loads(v['config']);name=c['name'];x,y,w,h=positions[name];v.update(x=x,y=y,width=w,height=h,z=i*1000,tabOrder=(i+1)*1000)
 c['layouts']=[{'id':0,'position':{k:v[k] for k in ['x','y','z','width','height','tabOrder']}}]
 s=c['singleVisual'];objects=s.setdefault('objects',{})
 if name in ['reported_last5days','explanation']:
  widths={ 'Indicator':120,'Explanation':600 } if name=='explanation' else {'Indicator':236}
  refs=s['projections']['Values'];objects['columnWidth']=[{'properties':{'value':literal(widths[pr['queryRef'].rsplit('.',1)[-1]])},'selector':{'metadata':pr['queryRef']}} for pr in refs]
  objects.setdefault('values',[{'properties':{}}])[0]['properties']['wordWrap']={'expr':{'Literal':{'Value':'true' if name=='explanation' else 'false'}}}
 if name=='kpi_3_meaning':
  objects['general'][0]['properties']['paragraphs']=[{'textRuns':[{'value':'Largest PRISM score in the current file. Higher scores mean greater concern.','textStyle':{'fontFamily':'Segoe UI','fontSize':'11pt','color':'#53677C'}}]}]
 if name=='kpi_0_meaning':
  objects['general'][0]['properties']['paragraphs']=[{'textRuns':[{'value':'Number of different items in the current daily file.','textStyle':{'fontFamily':'Segoe UI','fontSize':'11pt','color':'#53677C'}}]}]
 v['config']=json.dumps(c,ensure_ascii=False)
page['visualContainers']=visuals;names=set(positions);cfg=json.loads(page.get('config','{}'));cfg['relationships']=[r for r in cfg.get('relationships',[]) if r['source'] in names and r['target'] in names];page['config']=json.dumps(cfg)
assert len(l['sections'])==1
for i,v in enumerate(visuals):
 c=json.loads(v['config']);assert c['layouts'][0]['position']['x']==v['x'] and c['layouts'][0]['position']['width']==v['width']
 assert v['x']>=0 and v['y']>=0 and v['x']+v['width']<=1600 and v['y']+v['height']<=840
 for b in visuals[:i]:assert not(min(v['x']+v['width'],b['x']+b['width'])>max(v['x'],b['x']) and min(v['y']+v['height'],b['y']+b['height'])>max(v['y'],b['y']))
parts['Report/Layout']=json.dumps(l,ensure_ascii=False).encode('utf-16-le');parts.pop('SecurityBindings',None)
backup=p.with_name('Dashobard.before-rebalance-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'.pbix');assert not backup.exists();shutil.copy2(p,backup)
staging=p.with_name('Dashobard.rebalanced.tmp');assert not staging.exists()
with zipfile.ZipFile(staging,'w',zipfile.ZIP_DEFLATED) as z:
 for n,b in parts.items():z.writestr(n,b)
with zipfile.ZipFile(staging) as z:assert z.testzip() is None;assert z.read('DataModel')==parts['DataModel']
assert hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256(before).digest();os.replace(staging,p)
print('Updated:',p)
print('Removed Data last updated; 280px reported list; compact metrics; 756px assessment notes with fixed wrapped columns. All',len(visuals),'visuals fit one page with no overlapping rectangles. Data model unchanged.')
