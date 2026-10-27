from pathlib import Path
import zipfile,json,copy,datetime,shutil,hashlib,os,math,textwrap
p=Path(r'Z:\HTOC\Data_Analytics\Data\Threat Assessment Scores\ThreatAssessI_W\Dashboard\Dashobard.pbix');before=p.read_bytes()
with zipfile.ZipFile(p) as z:parts={i.filename:z.read(i.filename) for i in z.infolist()}
l=json.loads(parts['Report/Layout'].decode('utf-16-le'));main=l['sections'][0]
geometry={json.loads(v['config'])['name']:{k:v[k] for k in ['x','y','width','height']} for v in main['visualContainers']};size=(main['width'],main['height'])
def lit(v):return {'expr':{'Literal':{'Value':'true' if v is True else 'false' if v is False else str(v)+'D' if isinstance(v,(int,float)) else "'"+v.replace("'","''")+"'"}}}
def text_visual(name,text,x,y,w,h,size=12,bold=False):
 s={'visualType':'textbox','objects':{'general':[{'properties':{'paragraphs':[{'textRuns':[{'value':line,'textStyle':{'fontFamily':'Segoe UI','fontSize':str(size)+'pt','color':'#18324D' if bold else '#42556A','fontWeight':'bold' if bold else 'normal'}}]} for line in text]}}]},'vcObjects':{'title':[{'properties':{'show':lit(False)}}],'border':[{'properties':{'show':lit(False)}}],'visualTooltip':[{'properties':{'show':lit(False)}}]}}
 return {'x':x,'y':y,'width':w,'height':h,'config':json.dumps({'name':name,'singleVisual':s},ensure_ascii=False)}
def help_page(name,title,paragraphs):
 body_height=sum(max(1,len(textwrap.wrap(t,58)))*22+8 for t in paragraphs)+8
 h=body_height+64;body=text_visual(name+'_body',paragraphs,12,48,496,body_height)
 header=text_visual(name+'_heading',[title],12,8,496,34,15,True)
 page={'name':name,'displayName':title,'ordinal':len(l['sections']),'filters':'[]','config':json.dumps({'visibility':1,'type':1,'objects':{'background':[{'properties':{'color':{'solid':{'color':lit('#FFFFFF')}},'transparency':lit(0)}}]}}),'displayOption':3,'width':520,'height':h,'visualContainers':[header,body]}
 for i,v in enumerate(page['visualContainers']):
  v['z']=i*1000;v['tabOrder']=(i+1)*1000;c=json.loads(v['config']);c['layouts']=[{'id':0,'position':{k:v[k] for k in ['x','y','z','width','height','tabOrder']}}];v['config']=json.dumps(c,ensure_ascii=False)
 l['sections'].append(page)
 return name
help_definitions={
'kpi_0':('HelpIWIndicatorCount','I&W Indicators',['Number of different Indicators in the current daily assessment that have not been reported.','An Indicator repeated in multiple rows is counted once. Previously reported Indicators appear in the separate five-day list.']),
'kpi_3':('HelpIWHighestPrism','Highest PRISM Score',['The largest PRISM score among the current Indicators.','PRISM is the assessment’s overall concern score, from 0 to 1,000. A higher score means greater assessed concern.']),
'overview_asof':('HelpIWDataDate','Data Date',['The date of the daily assessment currently loaded in the dashboard.','This date changes when a newer assessment is loaded with Refresh.']),
'severity':('HelpIWPriorityGraph','Indicators by Priority',['Each bar shows how many different Indicators have the same priority in the current assessment.','The labels are the source file’s priority categories. The number and bar length show the Indicator count.']),
'prism':('HelpIWPrismGraph','PRISM Score by Indicator',['Each bar represents one Indicator and its PRISM score.','The score runs from 0 to 1,000. A longer bar means greater assessed concern.','If an Indicator has more than one source row, the graph shows its highest score.']),
'queue':('HelpIWDetailDefinitions','Indicator Details — Definitions',['Severity: the priority assigned in the source assessment, such as Critical, High, Medium or Low.','PRISM Score: the overall assessment score, from 0 to 1,000. Higher means greater concern.','Indicator Type: the kind of Indicator, such as an IP address, domain, URL or file hash.','Last Observed: when the source assessment says the Indicator was most recently seen.','OpDiv: the operating division or divisions listed for the Indicator.'])}
# Re-running the update replaces only our definition pages.
ids={x[0] for x in help_definitions.values()};l['sections']=[s for s in l['sections'] if s['name'] not in ids]
for v in main['visualContainers']:
 c=json.loads(v['config']);name=c['name'];s=c['singleVisual']
 if name in help_definitions:
  page_name,title,paragraphs=help_definitions[name];help_page(page_name,title,paragraphs)
  s.setdefault('vcObjects',{})['visualTooltip']=[{'properties':{'show':lit(True),'type':lit('Canvas'),'section':lit(page_name)}}]
 if name in ['severity_meaning','prism_meaning']:
  text=('Each bar counts different Indicators in a source priority category. Longer bars mean more Indicators.' if name=='severity_meaning' else 'Each bar shows one Indicator’s highest PRISM score (0–1,000). Longer bars mean greater concern.')
  s['objects']['general'][0]['properties']['paragraphs']=[{'textRuns':[{'value':text,'textStyle':{'fontFamily':'Segoe UI','fontSize':'11pt','color':'#53677C'}}]}]
 v['config']=json.dumps(c,ensure_ascii=False)
assert (main['width'],main['height'])==size
assert {json.loads(v['config'])['name']:{k:v[k] for k in ['x','y','width','height']} for v in main['visualContainers']}==geometry
# Preserve the separate Indicator-only assessment and Tags tooltips.
for v in main['visualContainers']:
 c=json.loads(v['config'])
 if c['name'] in ['indicator_hover_column','reported_last5days']:
  section=c['singleVisual']['vcObjects']['visualTooltip'][0]['properties']['section']['expr']['Literal']['Value'];assert section in ["'ReportSectionIWCurrentNotes'","'ReportSectionIWReportedNotes'"]
assert sum(json.loads(p.get('config','{}')).get('visibility',0)!=1 for p in l['sections'])==1
for p2 in l['sections']:
 for v in p2['visualContainers']:assert v['x']+v['width']<=p2['width'] and v['y']+v['height']<=p2['height']
parts['Report/Layout']=json.dumps(l,ensure_ascii=False).encode('utf-16-le');parts.pop('SecurityBindings',None)
backup=p.with_name('Dashobard.before-metric-help-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'.pbix');assert not backup.exists();shutil.copy2(p,backup)
staging=p.with_name('Dashobard.metric-help.tmp');assert not staging.exists()
with zipfile.ZipFile(staging,'w',zipfile.ZIP_DEFLATED) as z:
 for n,b in parts.items():z.writestr(n,b)
with zipfile.ZipFile(staging) as z:assert z.testzip() is None;assert z.read('DataModel')==parts['DataModel']
assert hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256(before).digest();os.replace(staging,p)
print('Added visible graph explanations and six definition tooltips. Canvas, visual positions, model, and Indicator assessment tooltips preserved. VirusTotal definition omitted pending user confirmation.')
