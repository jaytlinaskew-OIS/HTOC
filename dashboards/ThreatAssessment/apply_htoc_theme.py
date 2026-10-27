from pathlib import Path
import zipfile,json,copy,datetime,shutil,hashlib,os,sys,site
sys.stdout.reconfigure(encoding='utf-8')
root=Path(r'\\cscso1fsappv01\home\jaskew\HTOC\dashboards\ThreatAssessment')
p=Path(r'Z:\HTOC\Data_Analytics\Data\Threat Assessment Scores\ThreatAssessI_W\Dashboard\Dashobard.pbix')
reference=Path(r'Z:\HTOC\Data_Analytics\Business_Intelligence\Dashboards-Code\HTOC Big Board\Dashboard\1. In Development\HTOC_BigBoard_Dashboard_Metrics_OCIO Format_Master_New.pbix')
assert p.resolve()!=reference.resolve()
refhash=hashlib.sha256(reference.read_bytes()).hexdigest();before=p.read_bytes()
with zipfile.ZipFile(reference) as z:theme=json.loads(z.read('Report/StaticResources/RegisteredResources/HTOC6860670713044413.json').decode('utf-8-sig'))
with zipfile.ZipFile(p) as z:parts={i.filename:z.read(i.filename) for i in z.infolist()}
l=json.loads(parts['Report/Layout'].decode('utf-16-le'))
# These invariants protect the existing layout, fields, source data, and hover routing.
def invariants(layout):
 return [{'name':pg['name'],'size':[pg['width'],pg['height']],'config':{k:v for k,v in json.loads(pg.get('config','{}')).items() if k!='objects'},'visuals':[{'name':(c:=json.loads(v['config']))['name'],'position':{k:v[k] for k in ['x','y','z','width','height','tabOrder']},'layouts':c.get('layouts'),'fields':c['singleVisual'].get('projections'),'prototype':c['singleVisual'].get('prototypeQuery'),'query':v.get('query'),'transforms':v.get('dataTransforms'),'tooltip':c['singleVisual'].get('vcObjects',{}).get('visualTooltip'),'text':[[r.get('value','') for r in para.get('textRuns',[])] for e in c['singleVisual'].get('objects',{}).get('general',[]) for para in e.get('properties',{}).get('paragraphs',[])]} for v in pg['visualContainers']]} for pg in layout['sections']]
protected=invariants(l)
BG='#0D0D0D';PANEL='#0D1724';ALT='#152B40';BORDER='#2A3A4A';FG='#D9D9D9';SECONDARY='#AFC9DA';BLUE='#0075DB';CYAN='#75D2FF';TIP='#AFC9DA';TIPTEXT='#1A1A1A'
def lit(v):
 s='true' if v is True else 'false' if v is False else str(v)+'D' if isinstance(v,(int,float)) else "'"+str(v).replace("'","''")+"'"
 return {'expr':{'Literal':{'Value':s}}}
def color(s):return {'solid':{'color':lit(s)}}
def setprops(objects,card,**properties):
 entries=objects.setdefault(card,[{'properties':{}}])
 if not entries:entries.append({'properties':{}})
 entry=next((e for e in entries if not e.get('selector')),None)
 if entry is None:entry={'properties':{}};entries.insert(0,entry)
 entry.setdefault('properties',{}).update(properties)
# Register a compatible legacy theme resource, adapted from the read-only reference theme.
theme=copy.deepcopy(theme);theme.update(name='HTOC I&W Dark',foreground=FG,background=PANEL,backgroundLight=ALT,backgroundNeutral=BORDER,tableAccent=BLUE)
theme['textClasses']={'callout':{'fontFace':'Segoe UI Semibold','color':CYAN},'title':{'fontFace':'Segoe UI Semibold','color':FG},'header':{'fontFace':'Segoe UI Semibold','color':FG},'label':{'fontFace':'Segoe UI','color':FG}}
styles=theme.setdefault('visualStyles',{}).setdefault('*',{}).setdefault('*',{})
styles['title']=[{'fontFamily':'Segoe UI Semibold','fontColor':FG}]
styles['background']=[{'color':PANEL,'transparency':0}]
styles['border']=[{'color':BORDER}]
theme_file='HTOC_IW_Dark.json';parts['Report/StaticResources/RegisteredResources/'+theme_file]=(json.dumps(theme,indent=2,ensure_ascii=False)+'\n').encode('utf-8')
packages=l.setdefault('resourcePackages',[]);registered=next((p2['resourcePackage'] for p2 in packages if p2.get('resourcePackage',{}).get('name')=='RegisteredResources'),None)
if registered is None:
 registered={'name':'RegisteredResources','type':1,'items':[],'disabled':False};packages.append({'resourcePackage':registered})
registered['items']=[i for i in registered['items'] if i.get('name')!=theme_file]+[{'type':201,'path':theme_file,'name':theme_file}]
report_cfg=json.loads(l.get('config','{}'));report_cfg.setdefault('themeCollection',{})['customTheme']={'name':theme_file,'version':'5.61','type':1}
setprops(report_cfg.setdefault('objects',{}),'outspacePane',backgroundColor=color(PANEL),foregroundColor=color(FG));l['config']=json.dumps(report_cfg)
for pi,page in enumerate(l['sections']):
 tooltip=pi>0;page_bg=TIP if tooltip else BG;text=TIPTEXT if tooltip else FG;panel=TIP if tooltip else PANEL;line='#7FA4BB' if tooltip else BORDER
 pc=json.loads(page.get('config','{}'));po=pc.setdefault('objects',{});setprops(po,'background',color=color(page_bg),transparency=lit(0));setprops(po,'outspace',color=color(page_bg),transparency=lit(0));page['config']=json.dumps(pc)
 for v in page['visualContainers']:
  c=json.loads(v['config']);s=c['singleVisual'];typ=s['visualType'];name=c['name'];o=s.setdefault('objects',{});vc=s.setdefault('vcObjects',{})
  # Add only style properties to existing titles, preserving their visibility and wording.
  for e in vc.get('title',[]):e.setdefault('properties',{}).update(fontColor=color(text),fontFamily=lit('Segoe UI Semibold'))
  if 'background' in vc:
   for e in vc['background']:e.setdefault('properties',{}).update(color=color(panel),transparency=lit(0))
  if 'border' in vc:
   for e in vc['border']:e.setdefault('properties',{}).update(color=color(line))
  # Tooltip routing is intentionally left byte-for-byte equivalent.
  if typ=='textbox':
   for e in o.get('general',[]):
    for para in e.get('properties',{}).get('paragraphs',[]):
     for run in para.get('textRuns',[]):
      st=run.setdefault('textStyle',{});st['fontFamily']='Segoe UI';st['color']=TIPTEXT if tooltip else FG if name=='dashboard_title' else SECONDARY
      if name.endswith('_heading') or name=='dashboard_title':st['fontWeight']='bold'
  elif typ=='card':
   setprops(o,'labels',color=color(text if tooltip or name=='overview_asof' else CYAN),fontFamily=lit('Segoe UI Semibold'))
   if 'categoryLabels' in o:setprops(o,'categoryLabels',color=color(text),fontFamily=lit('Segoe UI'))
  elif typ=='tableEx':
   setprops(o,'columnHeaders',fontColor=color(text),backColor=color(panel),fontFamily=lit('Segoe UI Semibold'))
   setprops(o,'values',fontColor=color(text),backColor=color(panel),fontColorPrimary=color(text),fontColorSecondary=color(text),backColorPrimary=color(panel),backColorSecondary=color(TIP if tooltip else ALT),fontFamily=lit('Segoe UI'))
   setprops(o,'grid',gridHorizontalColor=color(line),gridVerticalColor=color(line),outlineColor=color(line))
   if 'total' in o:setprops(o,'total',fontColor=color(text),backColor=color(panel),fontFamily=lit('Segoe UI Semibold'))
  elif typ=='clusteredBarChart':
   for axis in ['categoryAxis','valueAxis']:setprops(o,axis,labelColor=color(FG),fontFamily=lit('Segoe UI'),gridlineShow=lit(False))
   setprops(o,'dataPoint',fill=color(BLUE if name=='severity' else CYAN))
   setprops(o,'labels',show=lit(True),color=color(FG),fontFamily=lit('Segoe UI Semibold'),fontSize=lit(11))
   if 'legend' in o:setprops(o,'legend',labelColor=color(FG),fontFamily=lit('Segoe UI'))
  v['config']=json.dumps(c,ensure_ascii=False)
assert invariants(l)==protected,'Theme application changed a protected layout, field, text, or hover setting'
parts['Report/Layout']=json.dumps(l,ensure_ascii=False).encode('utf-16-le');parts.pop('SecurityBindings',None)
work=root/'POWERBI/Dashobard.HTOC-theme.pbix'
with zipfile.ZipFile(work,'w',zipfile.ZIP_DEFLATED) as z:
 for n,b in parts.items():z.writestr(n,b)
with zipfile.ZipFile(work) as z:
 assert z.testzip() is None;assert z.read('DataModel')==parts['DataModel'];assert theme_file in z.read('Report/Layout').decode('utf-16-le')
# Check native resource registration and all report/model diagnostics.
lib=Path(os.environ['LOCALAPPDATA'])/'HTOC/IWDashboard/lib';sys.path.insert(0,str(lib));site.addsitedir(str(lib))
from pbix_mcp import server as api
r=json.loads(api.pbix_open(str(work),'theme_check'));assert r['success'];health=json.loads(api.pbix_doctor('theme_check'));assert health['success'] and '\u274c' not in health['message'];api.pbix_close('theme_check',force=True)
assert hashlib.sha256(reference.read_bytes()).hexdigest()==refhash,'Reference file changed externally during work'
assert hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256(before).digest(),'Dashboard changed externally during work'
backup=p.with_name('Dashobard.before-HTOC-theme-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'.pbix');assert not backup.exists();shutil.copy2(p,backup)
staged=p.with_name('Dashobard.theme-staging.tmp');assert not staged.exists();shutil.copy2(work,staged);os.replace(staged,p)
assert hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256(work.read_bytes()).digest();assert hashlib.sha256(reference.read_bytes()).hexdigest()==refhash
(root/'POWERBI/HTOC_theme_validation.json').write_text(json.dumps({'target':str(p),'reference':str(reference),'referenceSHA256':refhash,'referenceUnchanged':True,'layoutFieldsTextAndHoverRoutingUnchanged':True,'dataModelUnchanged':True,'nativeDiagnostics':'passed','mainBackground':BG,'panels':PANEL,'text':FG,'accentColors':[BLUE,CYAN],'tooltipBackground':TIP,'font':'Segoe UI / Segoe UI Semibold'},indent=2),encoding='utf-8')
print('Applied HTOC dark theme to',p)
print('Layout, data model, definitions, and hover routing preserved. Native diagnostics passed. Reference SHA256 unchanged:',refhash)
