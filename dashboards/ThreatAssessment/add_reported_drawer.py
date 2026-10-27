from pathlib import Path
import json,zipfile,copy,tempfile,hashlib
ROOT=Path(r'\\cscso1fsappv01\home\jaskew\HTOC\dashboards\ThreatAssessment');p=Path(r'Z:\HTOC\Data_Analytics\Data\Threat Assessment Scores\ThreatAssessI_W\Dashboard\Dashobard.pbix');work=Path(tempfile.mkdtemp(prefix='htoc_reported_drawer_'));candidate=work/'Reported Drawer.pbix'
with zipfile.ZipFile(p) as z:infos={i.filename:copy.copy(i) for i in z.infolist()};parts={n:z.read(n) for n in infos}
d=json.loads(parts['Report/Layout'].decode('utf-16-le'));before=copy.deepcopy(d);page=d['sections'][0];by={json.loads(v['config'])['name']:v for v in page['visualContainers']}
lit=lambda s:{'expr':{'Literal':{'Value':s}}};txt=lambda s:lit("'"+s.replace("'","''")+"'");solid=lambda s:{'solid':{'color':txt(s)}}
def put(v,c):v['config']=json.dumps(c,ensure_ascii=False)
def position(v,x,y,w,h,z=None):
 v.update(x=x,y=y,width=w,height=h)
 if z is not None:v.update(z=z,tabOrder=z)
 c=json.loads(v['config']);c['layouts']=[{'id':0,'position':{k:v[k] for k in ['x','y','width','height','z','tabOrder']}}];put(v,c)
def hidden(v,value=True):
 c=json.loads(v['config'])
 if value:v['isHidden']=True;c['singleVisual']['display']={'mode':'hidden'}
 else:v.pop('isHidden',None);c['singleVisual'].pop('display',None)
 put(v,c)
# Reclaim the left panel's space while preserving the existing header and report height.
positions={'indicator_details_frame':(60,120,1044,172),'indicator_hover_column':(68,148,1028,136),'severity_panel':(60,308,514,324),'severity':(60,308,514,248),'severity_meaning':(72,568,490,52),'prism_panel':(590,308,514,324),'prism':(590,308,514,248),'prism_meaning':(602,568,490,52)}
for name,pos in positions.items():position(by[name],*pos)
c=json.loads(by['indicator_hover_column']['config']);widths=c['singleVisual']['objects']['columnWidth'];old_widths=[float(w['properties']['value']['expr']['Literal']['Value'][:-1]) for w in widths];ratio=1028/836
for entry,w in zip(widths,old_widths):entry['properties']['value']=lit(str(round(w*ratio,3))+'D')
put(by['indicator_hover_column'],c)
start_old=260;start_new=68
for key,w in zip(['indicator','severity','prism','type','threatactor','lastobserved','opdiv'],old_widths):
 v=by['column_help_'+key];new_x=v['x']+(start_new+w*ratio/2)-(start_old+w/2)+(24 if key=='prism' else 0);position(v,new_x,v['y'],v['width'],v['height']);start_old+=w;start_new+=w*ratio
# Overlay drawer; opening it does not change data or other visual selections.
position(by['reported_panel'],16,120,280,512,50000)
position(by['reported_last5days'],24,160,264,400,51000)
c=json.loads(by['reported_last5days']['config']);c['singleVisual']['vcObjects']['title'][0]['properties']['show']=lit('false');c['singleVisual']['objects']['columnWidth'][0]['properties']['value']=lit('240D');put(by['reported_last5days'],c)
position(by['reported_footnote'],28,572,256,48,52000)
heading=copy.deepcopy(by['reported_footnote']);position(heading,24,124,236,28,53000);c=json.loads(heading['config']);c['name']='reported_drawer_heading';c['singleVisual']['objects']['general'][0]['properties']['paragraphs']=[{'textRuns':[{'value':'Reported I&W — Last 5 Days','textStyle':{'fontFamily':'Segoe UI Semibold','fontSize':'12pt','color':'#D9D9D9'}}]}];put(heading,c);page['visualContainers'].append(heading)
open_bm='BookmarkReportedDrawerOpen';close_bm='BookmarkReportedDrawerClosed'
def button(name,label,x,y,w,h,bm,tooltip,z):
 pos={'x':x,'y':y,'width':w,'height':h,'z':z,'tabOrder':z};objects={}
 specs={'text':{'show':lit('true'),'text':txt(label),'fontSize':lit('16D'),'fontFamily':txt('Segoe UI Semibold'),'fontColor':solid('#D9D9D9'),'horizontalAlignment':txt('center'),'verticalAlignment':txt('middle'),'leftMargin':lit('0D'),'rightMargin':lit('0D'),'topMargin':lit('0D'),'bottomMargin':lit('0D')},'fill':{'show':lit('true'),'fillColor':solid('#171722'),'transparency':lit('0D')},'outline':{'show':lit('true'),'lineColor':solid('#2A3A4A'),'weight':lit('1D')},'icon':{'show':lit('false')}}
 for key,props in specs.items():objects[key]=[{'properties':copy.deepcopy(props)}]+[{'selector':{'id':state},'properties':copy.deepcopy(props)} for state in ['default','hover','selected','disabled']]
 objects['shape']=[{'properties':{'tileShape':txt('rectangleRounded'),'rectangleRoundedCurve':lit('8D')}}]
 vc={'title':[{'properties':{'show':lit('false')}}],'background':[{'properties':{'show':lit('false')}}],'border':[{'properties':{'show':lit('false')}}],'padding':[{'properties':{k:lit('0D') for k in ['top','bottom','left','right']}}],'visualHeader':[{'properties':{'show':lit('false')}}],'general':[{'properties':{'keepLayerOrder':lit('true'),'altText':txt(tooltip)}}],'visualLink':[{'properties':{'show':lit('true'),'type':txt('Bookmark'),'bookmark':txt(bm),'tooltip':txt(tooltip+'. In Power BI Desktop, Ctrl+click.'),'showDefaultTooltip':lit('true')}}]}
 v={**pos,'config':json.dumps({'name':name,'layouts':[{'id':0,'position':pos.copy()}],'singleVisual':{'visualType':'actionButton','objects':objects,'vcObjects':vc}},ensure_ascii=False)};page['visualContainers'].append(v);return v
open_button=button('reported_drawer_open','›',16,120,32,512,open_bm,'Show reported I&W from the last five days',54000)
close_button=button('reported_drawer_close','‹',260,124,28,28,close_bm,'Collapse the reported I&W panel',55000)
drawer=['reported_panel','reported_last5days','reported_footnote','reported_drawer_heading','reported_drawer_close'];all_targets=drawer+['reported_drawer_open'];by={json.loads(v['config'])['name']:v for v in page['visualContainers']}
for name in drawer:hidden(by[name])
config=json.loads(d['config'])
for name,label,show in [(open_bm,'Show reported I&W — Last 5 Days',True),(close_bm,'Collapse reported I&W — Last 5 Days',False)]:
 states={}
 for target in all_targets:
  is_hidden=(target=='reported_drawer_open') if show else (target in drawer)
  states[target]={'singleVisual':{'display':{'mode':'hidden'}} if is_hidden else {}}
 config.setdefault('bookmarks',[]).append({'displayName':label,'name':name,'explorationState':{'version':'1.2','activeSection':page['name'],'sections':{page['name']:{'visualContainers':states}}},'options':{'applyOnlyToTargetVisuals':True,'targetVisualNames':all_targets,'suppressData':True,'suppressDisplay':False,'suppressActiveSection':True}})
d['config']=json.dumps(config,ensure_ascii=False)
# Two display layouts provide native reflow without overlapping the side panel.
base_by={json.loads(v['config'])['name']:v for v in before['sections'][0]['visualContainers']}
main_names=list(positions)+['column_help_'+k for k in ['indicator','severity','prism','type','threatactor','lastobserved','opdiv']]+['indicator_filter_context']
aliases={name:name+'_drawer_expanded' for name in main_names}
for name in main_names:
 clone=copy.deepcopy(base_by[name]);cc=json.loads(clone['config']);cc['name']=aliases[name];put(clone,cc);position(clone,clone['x'],clone['y'],clone['width'],clone['height'],clone['z']+100000);hidden(clone);page['visualContainers'].append(clone)
position(by['reported_panel'],16,120,220,512,50000)
position(by['reported_last5days'],24,172,204,388,51000)
cc=json.loads(by['reported_last5days']['config']);cc['singleVisual']['objects']['columnWidth'][0]['properties']['value']=lit('180D');put(by['reported_last5days'],cc)
position(by['reported_footnote'],28,572,196,48,52000)
position(by['reported_drawer_heading'],24,124,176,42,53000)
cc=json.loads(by['reported_drawer_heading']['config']);cc['singleVisual']['objects']['general'][0]['properties']['paragraphs']=[{'textRuns':[{'value':t,'textStyle':{'fontFamily':'Segoe UI Semibold','fontSize':'11pt','color':'#D9D9D9'}}]} for t in ['Reported I&W','Last 5 Days']];put(by['reported_drawer_heading'],cc)
position(by['reported_drawer_close'],204,124,28,28,55000)
pc=json.loads(page['config']);relations=pc.get('relationships',[]);expanded=[]
for r in relations:
 for source in [r['source']]+([aliases[r['source']]] if r['source'] in aliases else []):
  for target in [r['target']]+([aliases[r['target']]] if r['target'] in aliases else []):expanded.append({**r,'source':source,'target':target})
expanded.extend([{'source':'severity','target':aliases['severity'],'type':3},{'source':aliases['severity'],'target':'severity','type':3}]);pc['relationships']=expanded;page['config']=json.dumps(pc,ensure_ascii=False)
rc=json.loads(d['config']);targets=all_targets+main_names+list(aliases.values())
for bookmark in rc['bookmarks']:
 if bookmark['name'] not in [open_bm,close_bm]:continue
 opened=bookmark['name']==open_bm;states={}
 for target in targets:
  if target in main_names:is_hidden=opened
  elif target in aliases.values():is_hidden=not opened
  else:is_hidden=(target=='reported_drawer_open') if opened else target in drawer
  states[target]={'singleVisual':{'display':{'mode':'hidden'}} if is_hidden else {}}
 bookmark['options']['targetVisualNames']=targets;bookmark['explorationState']['sections'][page['name']]['visualContainers']=states
 d['config']=json.dumps(rc,ensure_ascii=False)
# Both arrangements have a real gutter between the side control/list and main content.
assert 16+32<60 and 16+220<252

# Keep partner-chart selection alive across the layout switch. The inactive
# partner chart stays behind an opaque active panel instead of being hidden.
by={json.loads(v['config'])['name']:v for v in page['visualContainers']}
position(by['severity_panel_drawer_expanded'],686,308,418,324,105000)
position(by['severity_drawer_expanded'],686,308,418,248,106000)
position(by['severity_meaning_drawer_expanded'],698,568,394,52,107000)
for name,z in [('prism_panel',220000),('prism',221000),('prism_meaning',222000)]:
 v=by[name];position(v,v['x'],v['y'],v['width'],v['height'],z)
for name,x,y,w,h,z in [('prism_panel_drawer_expanded',252,308,418,324,230000),('prism_drawer_expanded',252,308,418,248,231000),('prism_meaning_drawer_expanded',264,568,394,52,232000)]:position(by[name],x,y,w,h,z)
for name in drawer:
 v=by[name];position(v,v['x'],v['y'],v['width'],v['height'],v['z']+200000)
mask=copy.deepcopy(by['reported_panel']);position(mask,236,308,16,324,240000);cc=json.loads(mask['config']);cc['name']='reported_drawer_gutter';vc=cc['singleVisual']['vcObjects'];vc['background'][0]['properties'].update({'show':lit('true'),'color':solid('#0D0D0D'),'transparency':lit('0D')});vc.setdefault('border',[{'properties':{}}])[0]['properties']['show']=lit('false');put(mask,cc);hidden(mask);page['visualContainers'].append(mask)
# Native text rotation leaves the bar's rounded outline upright.
rail=by['reported_drawer_open'];cc=json.loads(rail['config'])
for entry in cc['singleVisual']['objects']['text']:entry['properties'].update({'text':txt('Reported I&W\nLast 5 Days'),'fontSize':lit('10D')})
cc['singleVisual']['objects']['rotation']=[{'properties':{'shapeAngle':lit('0D'),'textAngle':lit('270D')}}];put(rail,cc)
chevron=button('reported_drawer_open_chevron','›',18,128,28,28,open_bm,'Show reported I&W from the last five days',56000)
rc=json.loads(d['config'])
for bookmark in rc['bookmarks']:
 if bookmark['name'] not in [open_bm,close_bm]:continue
 opened=bookmark['name']==open_bm;states=bookmark['explorationState']['sections'][page['name']]['visualContainers']
 for source in ['severity','severity_drawer_expanded']:states[source]={'singleVisual':{}};hidden(by[source],False)
 states['reported_drawer_gutter']={'singleVisual':{}} if opened else {'singleVisual':{'display':{'mode':'hidden'}}}
 states['reported_drawer_open_chevron']={'singleVisual':{'display':{'mode':'hidden'}}} if opened else {'singleVisual':{}}
 bookmark['options']['targetVisualNames']+=['reported_drawer_gutter','reported_drawer_open_chevron']
d['config']=json.dumps(rc,ensure_ascii=False)

# Match section-box corners via the native container border. Chevrons have
# no individual fill or outline; only the full rail retains its rounded border.
by={json.loads(v['config'])['name']:v for v in page['visualContainers']}
rail=by['reported_drawer_open'];cc=json.loads(rail['config']);panelvc=json.loads(by['reported_panel']['config'])['singleVisual']['vcObjects']
for k in ['background','border']:cc['singleVisual']['vcObjects'][k]=copy.deepcopy(panelvc[k])
for entry in cc['singleVisual']['objects']['text']:entry['properties']['show']=lit('false')
for k in ['fill','outline']:
 for entry in cc['singleVisual']['objects'][k]:entry['properties']['show']=lit('false')
put(rail,cc)
for name in ['reported_drawer_close','reported_drawer_open_chevron']:
 v=by[name];cc=json.loads(v['config'])
 for k in ['fill','outline']:
  for entry in cc['singleVisual']['objects'][k]:entry['properties']['show']=lit('false')
 put(v,cc)
label_names=[]
for name,label,x in [('reported_drawer_label_1','Reported I&W',17),('reported_drawer_label_2','Last 5 Days',32)]:
 v=button(name,label,x,164,15,440,open_bm,'Show reported I&W from the last five days',54500+len(label_names));cc=json.loads(v['config'])
 for entry in cc['singleVisual']['objects']['text']:entry['properties']['fontSize']=lit('9D')
 for k in ['fill','outline']:
  for entry in cc['singleVisual']['objects'][k]:entry['properties']['show']=lit('false')
 cc['singleVisual']['objects']['rotation']=[{'properties':{'shapeAngle':lit('0D'),'textAngle':lit('270D')}}];put(v,cc);label_names.append(name)
rc=json.loads(d['config'])
for bookmark in rc['bookmarks']:
 if bookmark['name'] not in [open_bm,close_bm]:continue
 opened=bookmark['name']==open_bm;states=bookmark['explorationState']['sections'][page['name']]['visualContainers']
 for name in label_names:states[name]={'singleVisual':{'display':{'mode':'hidden'}}} if opened else {'singleVisual':{}}
 bookmark['options']['targetVisualNames']+=label_names
d['config']=json.dumps(rc,ensure_ascii=False)

# Transparent fills keep the entire control clickable without drawing a box.
for v in page['visualContainers']:
 cc=json.loads(v['config'])
 if cc['name'] in ['reported_drawer_open','reported_drawer_close','reported_drawer_open_chevron','reported_drawer_label_1','reported_drawer_label_2']:
  for entry in cc['singleVisual']['objects']['fill']:entry['properties'].update({'show':lit('true'),'transparency':lit('100D')})
  put(v,cc)

# The collapsed label is one continuous sideways line.
page['visualContainers']=[v for v in page['visualContainers'] if json.loads(v['config'])['name'] not in ['reported_drawer_label_1','reported_drawer_label_2']]
for v in page['visualContainers']:
 cc=json.loads(v['config'])
 if cc['name']=='reported_drawer_open':
  for entry in cc['singleVisual']['objects']['text']:entry['properties'].update({'show':lit('true'),'text':txt('Reported I&W Last 5 Days'),'fontSize':lit('10D')})
  put(v,cc)
rc=json.loads(d['config'])
for bookmark in rc['bookmarks']:
 if bookmark['name'] not in [open_bm,close_bm]:continue
 bookmark['options']['targetVisualNames']=[n for n in bookmark['options']['targetVisualNames'] if n not in ['reported_drawer_label_1','reported_drawer_label_2']]
 states=bookmark['explorationState']['sections'][page['name']]['visualContainers']
 for n in ['reported_drawer_label_1','reported_drawer_label_2']:states.pop(n,None)
d['config']=json.dumps(rc,ensure_ascii=False)

# An opaque fill matching the section background keeps borderless controls
# reliably clickable in Desktop, without introducing a visible inner box.
for v in page['visualContainers']:
 cc=json.loads(v['config'])
 if cc['name'] in ['reported_drawer_open','reported_drawer_close','reported_drawer_open_chevron']:
  for entry in cc['singleVisual']['objects']['fill']:entry['properties'].update({'show':lit('true'),'transparency':lit('0D'),'fillColor':solid('#171722')})
  if cc['name']=='reported_drawer_open':
   props={'tileShape':txt('rectangleRoundedByPixel'),'rectangleRoundedCurve':lit('8D')}
   cc['singleVisual']['objects']['shape']=[{'properties':copy.deepcopy(props)}]+[{'selector':{'id':st},'properties':copy.deepcopy(props)} for st in ['default','hover','selected','disabled']]
  put(v,cc)

# Keep the remaining KPI beside the date after removing the highest-score card.
page['visualContainers']=[v for v in page['visualContainers'] if json.loads(v['config'])['name']!='kpi_3']
for v in page['visualContainers']:
 if json.loads(v['config'])['name']=='kpi_0':position(v,713.1914893617021,11.063829787234042,176.17021276595744,88.51063829787233)
pc=json.loads(page['config']);pc['relationships']=[r for r in pc.get('relationships',[]) if 'kpi_3' not in [r.get('source'),r.get('target')]];page['config']=json.dumps(pc,ensure_ascii=False)

assert d['sections'][1:]==before['sections'][1:]
parts['Report/Layout']=json.dumps(d,ensure_ascii=False).encode('utf-16-le');parts.pop('SecurityBindings',None)
with zipfile.ZipFile(candidate,'w') as z:
 for n,b in parts.items():z.writestr(infos[n],b)
with zipfile.ZipFile(p) as a,zipfile.ZipFile(candidate) as b:
 assert b.testzip() is None
 for n in a.namelist():
  if n not in ['Report/Layout','SecurityBindings']:assert a.read(n)==b.read(n),n
state={'original':str(p),'candidate':str(candidate),'original_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'work':str(work)};(ROOT/'reported_drawer_state.json').write_text(json.dumps(state,indent=2));print(json.dumps(state))
