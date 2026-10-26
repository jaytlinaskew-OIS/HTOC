from pathlib import Path
import zipfile,json,datetime,shutil,hashlib,os
p=Path(r'Z:\HTOC\Data_Analytics\Data\Threat Assessment Scores\ThreatAssessI_W\Dashobard.pbix');before=p.read_bytes()
with zipfile.ZipFile(p) as z:parts={i.filename:z.read(i.filename) for i in z.infolist()}
l=json.loads(parts['Report/Layout'].decode('utf-16-le'));page=l['sections'][0];page['width']=1120;page['height']=620
# Compact two-column composition: data and notes on the left, reported list on the right.
pos={
'dashboard_title':(16,8,872,50),'dashboard_subtitle':(16,62,872,26),'overview_asof':(904,8,200,76),
'reported_last5days':(16,100,220,200),
'kpi_0':(252,100,160,78),'kpi_0_meaning':(252,184,160,66),
'kpi_3':(428,100,176,78),'kpi_3_meaning':(428,184,176,66),
'explanation':(620,100,484,200),
'severity':(16,316,352,132),'severity_meaning':(16,454,352,52),
'verdict':(384,316,352,132),'verdict_meaning':(384,454,352,52),
'prism':(752,316,352,132),'prism_meaning':(752,454,352,52),
'queue':(16,522,1088,82)}
def num(v):return {'expr':{'Literal':{'Value':str(v)+'D'}}}
for i,v in enumerate(page['visualContainers']):
 c=json.loads(v['config']);name=c['name'];x,y,w,h=pos[name];v.update(x=x,y=y,width=w,height=h,z=i*1000,tabOrder=(i+1)*1000);c['layouts']=[{'id':0,'position':{k:v[k] for k in ['x','y','z','width','height','tabOrder']}}]
 s=c['singleVisual'];o=s.setdefault('objects',{})
 if name in ['kpi_0','kpi_3']:o.setdefault('labels',[{'properties':{}}])[0]['properties']['fontSize']=num(28)
 if name=='explanation':
  o['columnWidth']=[{'selector':{'metadata':p['queryRef']},'properties':{'value':num(100 if p['queryRef'].endswith('.Indicator') else 348)}} for p in s['projections']['Values']]
  o.setdefault('grid',[{'properties':{}}])[0]['properties']['textSize']=num(10)
 if name=='reported_last5days':
  o['columnWidth']=[{'selector':{'metadata':p['queryRef']},'properties':{'value':num(180)}} for p in s['projections']['Values']]
 if name=='queue':
  widths={'Indicator':128,'Severity':64,'PRISM Score':88,'GTI Verdict':180,'VirusTotal Malicious Score':180,'Last Observed':112,'OpDiv':280}
  o['columnWidth']=[{'selector':{'metadata':p['queryRef']},'properties':{'value':num(widths[p['queryRef'].rsplit('.',1)[-1]])}} for p in s['projections']['Values']]
  o.setdefault('grid',[{'properties':{}}])[0]['properties']['textSize']=num(10)
 if name=='kpi_0_meaning':o['general'][0]['properties']['paragraphs'][0]['textRuns'][0]['value']='Different items in the current daily file.'
 if name=='kpi_3_meaning':o['general'][0]['properties']['paragraphs'][0]['textRuns'][0]['value']='Highest PRISM score. Higher means greater concern.'
 if name=='severity_meaning':o['general'][0]['properties']['paragraphs'][0]['textRuns'][0]['value']='Source priority: Critical, High, Medium or Low.'
 if name=='verdict_meaning':o['general'][0]['properties']['paragraphs'][0]['textRuns'][0]['value']='GTI is Google Threat Intelligence. Suspicious means review is needed.'
 if name=='prism_meaning':o['general'][0]['properties']['paragraphs'][0]['textRuns'][0]['value']='PRISM scores run from 0 to 1,000. Higher means greater concern.'
 v['config']=json.dumps(c,ensure_ascii=False)
for i,v in enumerate(page['visualContainers']):
 assert v['x']+v['width']<=1120 and v['y']+v['height']<=620
 for b in page['visualContainers'][:i]:assert not(min(v['x']+v['width'],b['x']+b['width'])>max(v['x'],b['x']) and min(v['y']+v['height'],b['y']+b['height'])>max(v['y'],b['y']))
parts['Report/Layout']=json.dumps(l,ensure_ascii=False).encode('utf-16-le');parts.pop('SecurityBindings',None)
backup=p.with_name('Dashobard.before-compact-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'.pbix');assert not backup.exists();shutil.copy2(p,backup)
staging=p.with_name('Dashobard.compact.tmp');assert not staging.exists()
with zipfile.ZipFile(staging,'w',zipfile.ZIP_DEFLATED) as z:
 for n,b in parts.items():z.writestr(n,b)
with zipfile.ZipFile(staging) as z:assert z.testzip() is None;assert z.read('DataModel')==parts['DataModel']
assert hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256(before).digest();os.replace(staging,p)
print('Compact layout saved; all visual bounds and overlaps checked. Model unchanged.')
