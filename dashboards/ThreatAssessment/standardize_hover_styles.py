from pathlib import Path
import zipfile,json,copy,textwrap,datetime,shutil,hashlib,os
p=Path(r'Z:\HTOC\Data_Analytics\Data\Threat Assessment Scores\ThreatAssessI_W\Dashboard\Dashobard.pbix');before=p.read_bytes()
with zipfile.ZipFile(p) as z:
 infos={i.filename:copy.copy(i) for i in z.infolist()}
 parts={i.filename:z.read(i.filename) for i in z.infolist()}
infos['DataModel'].compress_type=zipfile.ZIP_STORED
l=json.loads(parts['Report/Layout'].decode('utf-16-le'));protected_main=copy.deepcopy(l['sections'][0]);protected_report={k:copy.deepcopy(v) for k,v in l.items() if k!='sections'}
def content(page):
 return [{'name':(c:=json.loads(v['config']))['name'],'fields':c['singleVisual'].get('projections'),'prototype':c['singleVisual'].get('prototypeQuery'),'query':v.get('query'),'dataTransforms':v.get('dataTransforms'),'text':[[r.get('value','') for r in para.get('textRuns',[])] for e in c['singleVisual'].get('objects',{}).get('general',[]) for para in e.get('properties',{}).get('paragraphs',[])]} for v in page['visualContainers']]
old_content={pg['name']:content(pg) for pg in l['sections'][1:]}
BG='#AFC9DA';FG='#1A1A1A';BORDER='#7FA4BB'
def lit(v):return {'expr':{'Literal':{'Value':'true' if v is True else 'false' if v is False else str(v)+'D' if isinstance(v,(int,float)) else "'"+str(v).replace("'","''")+"'"}}}
def color(v):return {'solid':{'color':lit(v)}}
def props(o,k,**values):
 es=o.setdefault(k,[{'properties':{}}])
 if not es:es.append({'properties':{}})
 es[0].setdefault('properties',{}).update(values)
changed=[]
for pg in l['sections'][1:]:
 cfg=json.loads(pg.get('config','{}'))
 if cfg.get('type')!=1:continue
 po=cfg.setdefault('objects',{});props(po,'background',color=color(BG),transparency=lit(0));props(po,'outspace',color=color(BG),transparency=lit(0));pg['config']=json.dumps(cfg)
 definition=pg['name'].startswith('HelpIW')
 if definition:pg['width']=520
 for i,v in enumerate(pg['visualContainers']):
  c=json.loads(v['config']);s=c['singleVisual'];o=s.setdefault('objects',{});vc=s.setdefault('vcObjects',{});name=c['name']
  if s['visualType']=='textbox':
   heading=name.endswith('_heading')
   for e in o.get('general',[]):
    for para in e.get('properties',{}).get('paragraphs',[]):
     for r in para.get('textRuns',[]):r.setdefault('textStyle',{}).update(fontFamily='Segoe UI',fontSize='15pt' if heading else '12pt',fontWeight='bold' if heading else 'normal',color=FG)
   if definition:
    v['x']=12;v['width']=496
    if heading:v['y']=8;v['height']=36
    else:
     texts=[''.join(r.get('value','') for r in para.get('textRuns',[])) for e in o['general'] for para in e['properties']['paragraphs']]
     v['y']=48;v['height']=max(56,sum(max(1,len(textwrap.wrap(t,58)))*22+8 for t in texts)+8);pg['height']=v['height']+64
   props(vc,'background',show=lit(False),color=color(BG),transparency=lit(0));props(vc,'border',show=lit(False))
  elif s['visualType']=='tableEx':
   # Long notes keep their existing compact geometry and wrapping.
   props(vc,'background',show=lit(True),color=color(BG),transparency=lit(0));props(vc,'border',show=lit(False),color=color(BORDER))
   props(vc,'title',fontFamily=lit('Segoe UI Semibold'),fontSize=lit(15),fontColor=color(FG),bold=lit(True))
   props(o,'columnHeaders',fontFamily=lit('Segoe UI Semibold'),fontSize=lit(11),fontColor=color(FG),backColor=color(BG))
   props(o,'values',fontFamily=lit('Segoe UI'),fontSize=lit(11),fontColor=color(FG),fontColorPrimary=color(FG),fontColorSecondary=color(FG),backColor=color(BG),backColorPrimary=color(BG),backColorSecondary=color(BG),wordWrap=lit(True))
   props(o,'grid',textSize=lit(11),gridHorizontalColor=color(BORDER),gridVerticalColor=color(BORDER),outlineColor=color(BORDER))
  v['config']=json.dumps(c,ensure_ascii=False)
  c['layouts']=[{'id':0,'position':{k:v[k] for k in ['x','y','z','width','height','tabOrder']}}];v['config']=json.dumps(c,ensure_ascii=False)
  assert v['x']+v['width']<=pg['width'] and v['y']+v['height']<=pg['height']
 changed.append(pg['name'])
assert l['sections'][0]==protected_main,'Main page was changed'
assert {k:v for k,v in l.items() if k!='sections'}==protected_report,'Report-level settings were changed'
assert {pg['name']:content(pg) for pg in l['sections'][1:]}==old_content,'Tooltip content or field bindings changed'
parts['Report/Layout']=json.dumps(l,ensure_ascii=False).encode('utf-16-le')
parts.pop('SecurityBindings',None)
# Preserve the saved model and user-authored settings; discard the stale layout security binding.
backup=p.with_name('Dashobard.before-hover-consistency-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'.pbix');assert not backup.exists();shutil.copy2(p,backup)
staging=p.with_name('Dashobard.hover-consistency.tmp');assert not staging.exists()
with zipfile.ZipFile(staging,'w',zipfile.ZIP_DEFLATED) as z:
 for n,b in parts.items():z.writestr(infos[n],b)
with zipfile.ZipFile(staging) as z:
 assert z.testzip() is None
 for n,b in parts.items():
  if n!='Report/Layout':assert z.read(n)==b
 assert json.loads(z.read('Report/Layout').decode('utf-16-le'))['sections'][0]==protected_main
assert hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256(before).digest(),'Dashboard was edited while changes were being prepared'
os.replace(staging,p)
print('Standardized',len(changed),'hover pages. Latest visible page preserved exactly; all other archive members, metric definitions, field bindings, and hover assignments unchanged.')
