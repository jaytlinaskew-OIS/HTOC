"""Stack the reported/partner rails and show assessment notes in the main area."""
from pathlib import Path
import copy,hashlib,json,os,site,sys,tempfile,zipfile,shutil
ROOT=Path(r'\\cscso1fsappv01\home\jaskew\HTOC\dashboards\ThreatAssessment')
APP=Path(r'C:\Users\jaskew\AppData\Local\Packages\OpenAI.Codex_2p2nqsd0c76g0\LocalCache\Local\HTOC\IWDashboard')
sys.path.insert(0,str(APP/'lib'));site.addsitedir(str(APP/'lib'))
from pbix_mcp.report_binding import compile_visual_binding
from pbix_mcp import server as api
from pbix_mcp.formats.model_reader import ModelReader
p=Path(r'Z:\HTOC\Data_Analytics\Data\Threat Assessment Scores\ThreatAssessI_W\Dashboard\Dashobard.pbix')
work=Path(tempfile.mkdtemp(prefix='htoc_stacked_rails_'));candidate=work/'Stacked Rails.pbix'
with zipfile.ZipFile(p) as z:infos={i.filename:copy.copy(i) for i in z.infolist()};parts={n:z.read(n) for n in infos}
d=json.loads(parts['Report/Layout'].decode('utf-16-le'));before=copy.deepcopy(d);page=d['sections'][0]
by={json.loads(v['config'])['name']:v for v in page['visualContainers']}
lit=lambda v:{'expr':{'Literal':{'Value':v}}}
txt=lambda v:lit("'"+v.replace("'","''")+"'")
solid=lambda v:{'solid':{'color':txt(v)}}
def config(v):return json.loads(v['config'])
def put(v,c):v['config']=json.dumps(c,ensure_ascii=False)
def position(v,x,y,w,h,z=None):
 v.update(x=x,y=y,width=w,height=h)
 if z is not None:v.update(z=z,tabOrder=z)
 c=config(v);c['layouts']=[{'id':0,'position':{k:v[k] for k in ['x','y','width','height','z','tabOrder']}}];put(v,c)
def hidden(v,value):
 c=config(v)
 if value:v['isHidden']=True;c['singleVisual']['display']={'mode':'hidden'}
 else:v.pop('isHidden',None);c['singleVisual'].pop('display',None)
 put(v,c)
def rename(v,name):c=config(v);c['name']=name;put(v,c)
def copy_visual(source,name,x,y,w,h,z):
 v=copy.deepcopy(source);rename(v,name);position(v,x,y,w,h,z);hidden(v,False);page['visualContainers'].append(v);return v
# Retain user-authored header, details, and hover definitions; retire only our old drawer machinery.
removed={'reported_drawer_open','reported_drawer_close','reported_drawer_open_chevron','reported_drawer_gutter','severity_panel_drawer_expanded','severity_drawer_expanded','severity_meaning_drawer_expanded','severity_meaning'}
page['visualContainers']=[v for v in page['visualContainers'] if config(v)['name'] not in removed]
by={config(v)['name']:v for v in page['visualContainers']}
# Equal-height rails: 248 + 16 gap + 248 fills the existing 512-pixel body.
rail_template=copy.deepcopy(json.loads(parts['Report/Layout'].decode('utf-16-le'))['sections'][0]['visualContainers'][0])
old_by={config(v)['name']:v for v in before['sections'][0]['visualContainers']}
rail_template=old_by['reported_drawer_open'];arrow_template=old_by['reported_drawer_open_chevron']
# Reported list uses the upper half of the drawer column.
position(by['reported_panel'],60,120,220,248,5000)
position(by['reported_last5days'],68,176,204,132,6000)
position(by['reported_drawer_heading'],68,124,204,44,7000)
position(by['reported_footnote'],72,316,196,40,8000)
# One permanent partner chart preserves the selected filter even when covered.
position(by['severity_panel'],60,384,220,248,5000)
position(by['severity'],60,384,220,184,6000);hidden(by['severity'],False)
partner_note=copy_visual(by['reported_footnote'],'partner_filter_note',72,578,196,42,8000)
c=config(partner_note);c['singleVisual']['objects']['general'][0]['properties']['paragraphs']=[{'textRuns':[{'value':t,'textStyle':{'fontFamily':'Segoe UI','fontSize':'8pt','color':'#D9D9D9'}}],'horizontalTextAlignment':'center'} for t in ['Select a partner to filter Indicators.','Select it again to clear.']];put(partner_note,c)
partner_mask=copy_visual(by['severity_panel'],'partner_closed_mask',60,384,220,248,20000)
c=config(partner_mask);vc=c['singleVisual']['vcObjects'];vc['background'][0]['properties'].update({'show':lit('true'),'color':solid('#0D0D0D'),'transparency':lit('0D')});vc['border'][0]['properties']['show']=lit('false');put(partner_mask,c)
# Detail-table arrangements depend only on whether the upper reported drawer is open.
detail_wide=['indicator_details_frame','indicator_hover_column','indicator_filter_context']+['column_help_'+k for k in ['indicator','severity','prism','type','threatactor','lastobserved','opdiv']]
detail_narrow=[n+'_drawer_expanded' for n in detail_wide]
position(by['indicator_details_frame_drawer_expanded'],296,120,808,172)
position(by['indicator_hover_column_drawer_expanded'],304,148,792,136)
c=config(by['indicator_hover_column_drawer_expanded']);widths=c['singleVisual']['objects']['columnWidth'];old_widths=[float(w['properties']['value']['expr']['Literal']['Value'][:-1]) for w in widths];ratio=792/836
for entry,w in zip(widths,old_widths):entry['properties']['value']=lit(str(round(w*ratio,3))+'D')
put(by['indicator_hover_column_drawer_expanded'],c)
old_start=260;new_start=304
for key,w in zip(['indicator','severity','prism','type','threatactor','lastobserved','opdiv'],old_widths):
 v=by['column_help_'+key+'_drawer_expanded'];x=v['x']+(new_start+w*ratio/2)-(old_start+w/2);position(v,x,v['y'],v['width'],v['height']);old_start+=w;new_start+=w*ratio
# Restore a consistent notes-left / score-right arrangement in both widths.
for suffix,left,width,right in [('',60,514,590),('_drawer_expanded',296,396,708)]:
 for name,y,h,z in [('prism_panel',308,324,30000),('prism',308,248,31000),('prism_meaning',568,52,32000)]:
  v=by[name+suffix];position(v,right+(12 if name=='prism_meaning' else 0),y,width-(24 if name=='prism_meaning' else 0),h,z)

def notes_table(name,left,width):
 v=copy_visual(by['indicator_hover_column'],name,left+8,312,width-16,266,31000)
 c=config(v);sv=c['singleVisual'];fields=[('Assessment Indicator','Indicator'),('Assessment Notes Text','Assessment Notes')]
 sv['prototypeQuery']={'Version':2,'From':[{'Name':'u','Entity':'Unreported I&W','Type':0}],'Select':[{'Measure':{'Expression':{'SourceRef':{'Source':'u'}},'Property':n},'Name':'Unreported I&W.'+n} for n,label in fields]}
 sv['projections']={'Values':[{'queryRef':'Unreported I&W.'+n} for n,label in fields]}
 sv['columnProperties']={'Unreported I&W.'+n:{'displayName':label} for n,label in fields}
 sv['objects']={'grid':[{'properties':{'textSize':lit('9D'),'rowPadding':lit('3D'),'gridHorizontalColor':solid('#2A3A4A'),'gridVerticalColor':solid('#2A3A4A')}}],'columnWidth':[{'selector':{'metadata':'Unreported I&W.'+n},'properties':{'value':lit(str(w)+'D')}} for n,w in [('Assessment Indicator',110),('Assessment Notes Text',width-150)]],'columnHeaders':[{'properties':{'fontSize':lit('9D'),'fontFamily':txt('Segoe UI Semibold'),'fontColor':solid('#D9D9D9'),'backColor':solid('#171722'),'wordWrap':lit('false')}}],'values':[{'properties':{'fontSize':lit('9D'),'fontFamily':txt('Segoe UI'),'fontColor':solid('#D9D9D9'),'backColor':solid('#171722'),'fontColorPrimary':solid('#D9D9D9'),'fontColorSecondary':solid('#D9D9D9'),'backColorPrimary':solid('#171722'),'backColorSecondary':solid('#171722'),'wordWrap':lit('true')}}],'total':[{'properties':{'totals':lit('false')}}],'columnFormatting':[{'selector':{'metadata':'Unreported I&W.'+n},'properties':{'alignment':txt('Left'),'styleHeader':lit('true')}} for n,label in fields]}
 vc=sv['vcObjects'];vc['title']=[{'properties':{'show':lit('true'),'text':txt('Indicator Assessment Notes'),'fontSize':lit('13D'),'fontFamily':txt('Segoe UI Semibold'),'fontColor':solid('#D9D9D9'),'bold':lit('true')}}];vc['visualTooltip']=[{'properties':{'show':lit('false')}}]
 put(v,c);q,t=compile_visual_binding(sv,lambda entity,prop,is_measure:'String')
 for i,(n,label) in enumerate(fields):t['queryMetadata']['Select'][i]['Restatement']=label;t['selects'][i]['displayName']=label
 v['query']=json.dumps(q,ensure_ascii=False);v['dataTransforms']=json.dumps(t,ensure_ascii=False);return v
notes_groups={}
for suffix,left,width in [('',60,514),('_narrow',296,396)]:
 panel=copy_visual(by['prism_panel'],'assessment_panel'+suffix,left,308,width,324,30000)
 table=notes_table('assessment_notes'+suffix,left,width)
 foot=copy_visual(by['reported_footnote'],'assessment_note_hint'+suffix,left+12,586,width-24,34,32000)
 c=config(foot);c['singleVisual']['objects']['general'][0]['properties']['paragraphs']=[{'textRuns':[{'value':'Defaults to the highest-scoring Indicator. Select a row above to change.','textStyle':{'fontFamily':'Segoe UI','fontSize':'8pt','color':'#D9D9D9'}}],'horizontalTextAlignment':'center'}];put(foot,c)
 notes_groups[suffix]=[config(v)['name'] for v in [panel,table,foot]]
# Main notes/score panels cover the hidden partner chart; no selections are reset.
wide_body=notes_groups['']+['prism_panel','prism','prism_meaning']
narrow_body=notes_groups['_narrow']+['prism_panel_drawer_expanded','prism_drawer_expanded','prism_meaning_drawer_expanded']
reported=['reported_panel','reported_last5days','reported_drawer_heading','reported_footnote']
partner=['severity_panel','partner_filter_note']
controls={}
for reported_open in [False,True]:
 for partner_open in [False,True]:
  key=f'R{int(reported_open)}P{int(partner_open)}';controls[key]=[]
  for kind,label,y,is_open,destination in [('reported','Reported I&W Last 5 Days',120,reported_open,f'R{int(not reported_open)}P{int(partner_open)}'),('partners','Partners',384,partner_open,f'R{int(reported_open)}P{int(not partner_open)}')]:
   action=('Collapse ' if is_open else 'Expand ')+('reported I&W' if kind=='reported' else 'Partners')
   for small,template in [(False,rail_template),(True,arrow_template)]:
    name=f'side_{key}_{kind}_'+('chevron' if small else 'rail');v=copy_visual(template,name,18 if small else 16,y+8 if small else y,28 if small else 32,28 if small else 248,405000 if small else 404000)
    c=config(v);sv=c['singleVisual'];sv['vcObjects']['general'][0]['properties']['altText']=txt(action)
    sv['vcObjects']['visualLink'][0]['properties'].update({'bookmark':txt('BookmarkSidebars_'+destination),'tooltip':txt(action+'. In Power BI Desktop, Ctrl+click.')})
    for entry in sv['objects']['text']:entry['properties'].update({'text':txt(('‹' if is_open else '›') if small else label),'show':lit('true'),'fontSize':lit('16D' if small else ('9D' if kind=='reported' else '10D'))})
    put(v,c);controls[key].append(name)
# Four display-only bookmarks retain partner/data selections while changing presentation.
all_names=detail_wide+detail_narrow+wide_body+narrow_body+reported+partner+['partner_closed_mask']+[n for names in controls.values() for n in names]
rc=json.loads(d['config']);rc['bookmarks']=[b for b in rc.get('bookmarks',[]) if b['name'] not in ['BookmarkReportedDrawerOpen','BookmarkReportedDrawerClosed']]
visible_by_state={}
for reported_open in [False,True]:
 for partner_open in [False,True]:
  key=f'R{int(reported_open)}P{int(partner_open)}'
  visible=set((detail_narrow if reported_open else detail_wide)+(narrow_body if reported_open or partner_open else wide_body)+controls[key])
  if reported_open:visible.update(reported)
  if partner_open:visible.update(partner)
  else:visible.add('partner_closed_mask')
  visible_by_state[key]=visible
  states={name:{'singleVisual':{} if name in visible else {'display':{'mode':'hidden'}}} for name in all_names}
  rc['bookmarks'].append({'displayName':('Reported '+('open' if reported_open else 'closed')+' · Partners '+('open' if partner_open else 'closed')),'name':'BookmarkSidebars_'+key,'explorationState':{'version':'1.2','activeSection':page['name'],'sections':{page['name']:{'visualContainers':states}}},'options':{'applyOnlyToTargetVisuals':True,'targetVisualNames':all_names,'suppressData':True,'suppressDisplay':False,'suppressActiveSection':True}})
d['config']=json.dumps(rc,ensure_ascii=False)
for v in page['visualContainers']:
 name=config(v)['name']
 if name in all_names:hidden(v,name not in visible_by_state['R0P0'])
# Filter notes from the partner chart and from the currently selected details row.
existing={config(v)['name'] for v in page['visualContainers']};pc=json.loads(page['config']);relations=[r for r in pc.get('relationships',[]) if r.get('source') in existing and r.get('target') in existing]
for target in ['assessment_notes','assessment_notes_narrow']:
 for source in ['severity','indicator_hover_column','indicator_hover_column_drawer_expanded']:
  relations=[r for r in relations if not (r['source']==source and r['target']==target)];relations.append({'source':source,'target':target,'type':1})
 for source in ['reported_last5days','prism','prism_drawer_expanded']:
  relations.append({'source':source,'target':target,'type':3})
for source in ['assessment_notes','assessment_notes_narrow']:
 for target in ['severity','prism','prism_drawer_expanded','indicator_hover_column','indicator_hover_column_drawer_expanded','indicator_filter_context','indicator_filter_context_drawer_expanded']:
  relations.append({'source':source,'target':target,'type':3})
pc['relationships']=relations;page['config']=json.dumps(pc,ensure_ascii=False)
assert d['sections'][1:]==before['sections'][1:]
assert 120+248+16==384 and 384+248==632
# String measures produce exactly one assessment row. A details-row selection
# or partner filter narrows the input first; otherwise TOPN picks the top score.
shutil.copy2(p,candidate);alias='iw_stacked_notes';opened=json.loads(api.pbix_open(str(candidate),alias));assert opened.get('success'),opened
try:
 expression="VAR _Top = TOPN(1, 'Unreported I&W', 'Unreported I&W'[PRISM Score], DESC, 'Unreported I&W'[Indicator], ASC) RETURN MAXX(_Top, 'Unreported I&W'[{field}])"
 for name,field in [('Assessment Indicator','Indicator'),('Assessment Notes Text','Explanation')]:
  result=json.loads(api.pbix_datamodel_add_measure(alias,'Unreported I&W',name,expression.format(field=field),data_type='String',description='Top-scoring Indicator in the current partner/row selection; Indicator breaks score ties.'));assert result.get('success'),result
 result=json.loads(api.pbix_datamodel_modify_metadata(alias,"UPDATE Measure SET IsHidden=1 WHERE Name IN ('Assessment Indicator','Assessment Notes Text')"));assert result.get('success'),result
 parts['DataModel']=(Path(api._ensure_open(alias)['work_dir'])/'DataModel').read_bytes()
finally:api.pbix_close(alias,force=True)
infos['DataModel'].compress_type=zipfile.ZIP_STORED

parts['Report/Layout']=json.dumps(d,ensure_ascii=False).encode('utf-16-le');parts.pop('SecurityBindings',None)
with zipfile.ZipFile(candidate,'w') as z:
 for name,data in parts.items():z.writestr(infos[name],data)
with zipfile.ZipFile(p) as a,zipfile.ZipFile(candidate) as b:
 assert b.testzip() is None
 for name in a.namelist():
  if name not in ['Report/Layout','DataModel','SecurityBindings']:assert a.read(name)==b.read(name),name
old_model=ModelReader(str(p));new_model=ModelReader(str(candidate))
for table in ['Unreported I&W','Snapshot','Reported I&W (5 days)','Indicator Partners']:assert old_model.get_table(table)==new_model.get_table(table),table
state={'original':str(p),'candidate':str(candidate),'work':str(work),'original_sha256':hashlib.sha256(p.read_bytes()).hexdigest()};(ROOT/'stacked_rails_state.json').write_text(json.dumps(state,indent=2));print(json.dumps(state))
