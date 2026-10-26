from pathlib import Path
import zipfile,json,datetime,hashlib,shutil,os
ROOT=Path(r'\\cscso1fsappv01\home\jaskew\HTOC\dashboards\ThreatAssessment')
target=Path(r'Z:\HTOC\Data_Analytics\Data\Threat Assessment Scores\ThreatAssessI_W\Dashobard.pbix')
original=target.read_bytes()
with zipfile.ZipFile(target) as z: parts={i.filename:z.read(i.filename) for i in z.infolist()}
layout=json.loads(parts['Report/Layout'].decode('utf-16-le'));page=layout['sections'][0]
page['displayName']='I&W Dashboard';page['width']=1600;page['height']=1000
old={json.loads(v['config'])['name']:v for v in page['visualContainers']}
def lit(v):
 if isinstance(v,bool):s='true' if v else 'false'
 elif isinstance(v,(int,float)):s=str(v)+'D'
 else:s="'"+str(v).replace("'","''")+"'"
 return {'expr':{'Literal':{'Value':s}}}
def set_title(v,title):
 c=json.loads(v['config']);c['singleVisual'].setdefault('vcObjects',{}).setdefault('title',[{'properties':{}}])[0]['properties']['text']=lit(title);v['config']=json.dumps(c,ensure_ascii=False)
def move(v,x,y,w,h):v.update(x=x,y=y,width=w,height=h);return v
out=[]
def text(name,x,y,w,h,paragraphs,size=12,bg=None):
 runs=[{'textRuns':[{'value':t,'textStyle':{'fontFamily':'Segoe UI','fontSize':str(size)+'pt','color':'#53677C'}}]} for t in paragraphs]
 sv={'visualType':'textbox','objects':{'general':[{'properties':{'paragraphs':runs}}]},'vcObjects':{'title':[{'properties':{'show':lit(False)}}],'background':[{'properties':{'show':lit(bool(bg)),'color':{'solid':{'color':lit(bg or '#F2F5F9')}},'transparency':lit(0)}}]}}
 v={'x':x,'y':y,'z':len(out)*1000,'tabOrder':len(out)*1000+1000,'width':w,'height':h,'config':json.dumps({'name':name,'singleVisual':sv},ensure_ascii=False)};out.append(v);return v
heading=text('dashboard_title',24,12,1140,52,['I&W Dashboard'],28)
c=json.loads(heading['config']);c['singleVisual']['objects']['general'][0]['properties']['paragraphs'][0]['textRuns'][0]['textStyle'].update(fontWeight='bold',color='#18324D');heading['config']=json.dumps(c)
text('dashboard_subtitle',24,70,1140,35,['Latest daily threat information. Scores help decide what to review first.'],13)
asof=move(old['overview_asof'],1200,12,376,90);set_title(asof,'Data date');out.append(asof)
metrics=[('kpi_0','I&W items','Number of different items in the latest daily file.'),('kpi_1','High-priority items','Items marked High or Critical in the source file. Review these first.'),('kpi_2','Average risk score','Average PRISM score across the listed records. Scores run from 0 to 1,000; higher means greater concern.'),('kpi_3','Highest risk score','Largest PRISM score in the file. It highlights the item with the greatest assessed concern.')]
for i,(name,title,meaning) in enumerate(metrics):
 v=move(old[name],24+i*392,116,376,96);set_title(v,title);out.append(v);text(name+'_meaning',24+i*392,218,376,60,[meaning],11)
charts=[('severity','Items by priority','Priority is the source file’s urgency rating: Critical, High, Medium or Low.'),('verdict','Threat intelligence assessment','GTI means Google Threat Intelligence. “Suspicious” means the item needs closer review.'),('prism','Risk score by item','Each bar shows an item’s PRISM score. Longer bars mean greater assessed concern.')]
for i,(name,title,meaning) in enumerate(charts):
 x=[24,544,1064][i];w=[504,504,512][i];v=move(old[name],x,292,w,210);set_title(v,title);out.append(v);text(name+'_meaning',x,508,w,48,[meaning],11)
queue=move(old['queue'],24,570,1032,230);set_title(queue,'I&W details');out.append(queue)
text('metric_guide',1072,570,504,230,[
 'READING THE DETAILS',
 'Indicator / Host IP: the internet address or other item being reviewed.',
 'Severity: how urgently the source recommends reviewing it.',
 'PRISM score: the overall 0–1,000 risk score.',
 'GTI score / verdict: Google’s threat score and assessment.',
 'VirusTotal: the source’s malicious-detection result.',
 'Last observed: when the item was most recently seen.',
 'Partners / OpDiv: organizations linked to the observation.'
],11,'#FFFFFF')
# Remove less relevant technical columns from the visible queue; keep their raw data in the model.
c=json.loads(queue['config']);sv=c['singleVisual'];keep=['Indicator','Severity','PRISM Score','GTI Verdict','VirusTotal Malicious Score','Last Observed','OpDiv']
from_alias={f['Name']:f['Entity'] for f in sv['prototypeQuery']['From']}
selects=sv['prototypeQuery']['Select'];selected=[]
for s in selects:
 spec=s.get('Column') or s.get('Measure') or {};prop=spec.get('Property')
 if prop in keep:selected.append(s)
sv['prototypeQuery']['Select']=selected;refs={s['Name'] for s in selected};sv['projections']['Values']=[p for p in sv['projections']['Values'] if p['queryRef'] in refs]
# Recompile the reduced field list with the same types used by the model.
import sys,site
runtime=Path(os.environ['TEMP'])/'htoc-pbix-tools';sys.path.insert(0,str(runtime));site.addsitedir(str(runtime))
from pbix_mcp.report_binding import compile_visual_binding
types={'Indicator':'String','Severity':'String','PRISM Score':'Double','GTI Verdict':'String','VirusTotal Malicious Score':'Double','Last Observed':'DateTime','OpDiv':'String'}
def resolver(entity,prop,is_measure):return None if is_measure else types.get(prop,'String')
resolver.summarize_by=lambda e,p:2
resolver.data_category=lambda e,p:None
q,dt=compile_visual_binding(sv,resolver);queue['query']=json.dumps(q);queue['dataTransforms']=json.dumps(dt);queue['config']=json.dumps(c)
explain=move(old['explanation'],24,816,1552,100);set_title(explain,'Source assessment notes');out.append(explain)
for name,x,w,title in [('modified',24,760,'Source file saved'),('refreshed',800,776,'Data last updated')]:
 v=move(old[name],x,932,w,52);set_title(v,title);out.append(v)
# Display-only screen: charts do not filter the other visuals when clicked.
for i,v in enumerate(out):
 v['z']=i*1000;v['tabOrder']=(i+1)*1000
 c=json.loads(v['config']);c['layouts']=[{'id':0,'position':{k:v[k] for k in ['x','y','z','width','height','tabOrder']}}];v['config']=json.dumps(c,ensure_ascii=False)
page['visualContainers']=out;cfg=json.loads(page.get('config','{}'));data_names=[json.loads(v['config'])['name'] for v in out if 'query' in v]
cfg['relationships']=[{'source':a,'target':b,'type':3} for a in data_names for b in data_names if a!=b];page['config']=json.dumps(cfg)
assert len(layout['sections'])==1
assert not any(json.loads(v['config'])['singleVisual']['visualType']=='slicer' for v in out)
assert not any('unreported' in run.get('value','').lower() for v in out for para in json.loads(v['config'])['singleVisual'].get('objects',{}).get('general',[{'properties':{}}])[0]['properties'].get('paragraphs',[]) for run in para.get('textRuns',[]))
for v in out:assert v['x']+v['width']<=1600 and v['y']+v['height']<=1000
parts['Report/Layout']=json.dumps(layout,ensure_ascii=False).encode('utf-16-le');parts.pop('SecurityBindings',None)
candidate=ROOT/'POWERBI/Dashobard.display-layout.pbix'
with zipfile.ZipFile(candidate,'w',zipfile.ZIP_DEFLATED) as z:
 for n,b in parts.items():z.writestr(n,b)
with zipfile.ZipFile(candidate) as z:assert z.testzip() is None
backup=target.with_name('Dashobard.before-layout-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'.pbix');assert not backup.exists();shutil.copy2(target,backup)
assert hashlib.sha256(target.read_bytes()).digest()==hashlib.sha256(original).digest()
staging=target.with_name('Dashobard.display-staging.tmp');assert not staging.exists();shutil.copy2(candidate,staging);os.replace(staging,target)
print('Updated layout:',target,'visuals',len(out),'one page, no slicers')
