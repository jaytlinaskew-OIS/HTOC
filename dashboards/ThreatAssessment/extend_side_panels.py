"""Make the stacked side drawers narrow, full-height, and mutually exclusive."""
from pathlib import Path
import copy,hashlib,json,re,tempfile,zipfile
ROOT=Path(r'\\cscso1fsappv01\home\jaskew\HTOC\dashboards\ThreatAssessment')
p=Path(r'Z:\HTOC\Data_Analytics\Data\Threat Assessment Scores\ThreatAssessI_W\Dashboard\Dashobard.pbix')
work=Path(tempfile.mkdtemp(prefix='htoc_fullheight_drawers_'));candidate=work/'Full Height Drawers.pbix'
with zipfile.ZipFile(p) as z:infos={i.filename:copy.copy(i) for i in z.infolist()};parts={n:z.read(n) for n in infos}
d=json.loads(parts['Report/Layout'].decode('utf-16-le'));before=copy.deepcopy(d);page=d['sections'][0]
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
lit=lambda v:{'expr':{'Literal':{'Value':v}}};txt=lambda v:lit("'"+v.replace("'","''")+"'")
page['visualContainers']=[v for v in page['visualContainers'] if not config(v)['name'].startswith('side_R1P1_')]
by={config(v)['name']:v for v in page['visualContainers']}
# Both drawers occupy the same full-height column, with no simultaneous state.
position(by['reported_panel'],60,120,200,512,25000)
position(by['reported_drawer_heading'],68,124,184,44,27000)
position(by['reported_last5days'],68,176,184,388,26000)
c=config(by['reported_last5days']);c['singleVisual']['objects']['columnWidth'][0]['properties']['value']=lit('160D');put(by['reported_last5days'],c)
position(by['reported_footnote'],72,576,176,44,28000)
position(by['severity_panel'],60,120,200,512,5000)
position(by['severity'],60,120,200,444,6000)
position(by['partner_filter_note'],72,576,176,44,8000)
position(by['partner_closed_mask'],60,120,200,512,20000)
# Put the wide details frame above the partner mask when both drawers are shut.
position(by['indicator_details_frame'],60,120,1044,172,50000)
position(by['indicator_hover_column'],68,148,1028,136,51000)
position(by['indicator_filter_context'],440,124,500,20,54000)
keys=['indicator','severity','prism','type','threatactor','lastobserved','opdiv']
for i,key in enumerate(keys):
 v=by['column_help_'+key];position(v,v['x'],v['y'],v['width'],v['height'],53000+i)
# Narrow main content uses the same arrangement for either expanded drawer.
old_table_x=by['indicator_hover_column_drawer_expanded']['x'];old_table_width=by['indicator_hover_column_drawer_expanded']['width']
position(by['indicator_details_frame_drawer_expanded'],276,120,828,172,50000)
position(by['indicator_hover_column_drawer_expanded'],284,148,812,136,51000)
position(by['indicator_filter_context_drawer_expanded'],440,124,500,20,54000)
c=config(by['indicator_hover_column_drawer_expanded']);entries=c['singleVisual']['objects']['columnWidth'];widths=[float(e['properties']['value']['expr']['Literal']['Value'][:-1]) for e in entries];ratio=812/old_table_width
for e,w in zip(entries,widths):e['properties']['value']=lit(str(round(w*ratio,3))+'D')
put(by['indicator_hover_column_drawer_expanded'],c)
old_start,new_start=old_table_x,284
for i,(key,w) in enumerate(zip(keys,widths)):
 v=by['column_help_'+key+'_drawer_expanded'];x=v['x']+(new_start+w*ratio/2)-(old_start+w/2);position(v,x,v['y'],v['width'],v['height'],53000+i);old_start+=w;new_start+=w*ratio
for name,x,y,w,h,z in [('assessment_panel_narrow',276,308,406,324,30000),('assessment_notes_narrow',284,312,390,266,31000),('assessment_note_hint_narrow',288,586,382,34,32000),('prism_panel_drawer_expanded',698,308,406,324,30000),('prism_drawer_expanded',698,308,406,248,31000),('prism_meaning_drawer_expanded',710,568,382,52,32000)]:position(by[name],x,y,w,h,z)
c=config(by['assessment_notes_narrow']);c['singleVisual']['objects']['columnWidth'][1]['properties']['value']=lit('256D');put(by['assessment_notes_narrow'],c)
# Keep the two equal-height rails. Each expansion closes the other drawer.
for name,v in by.items():
 match=re.fullmatch(r'side_(R[01]P[01])_(reported|partners)_(rail|chevron)',name)
 if not match:continue
 state,kind,_=match.groups();is_open=(state[1]=='1') if kind=='reported' else (state[3]=='1');destination='R0P0' if is_open else ('R1P0' if kind=='reported' else 'R0P1')
 c=config(v);c['singleVisual']['vcObjects']['visualLink'][0]['properties']['bookmark']=txt('BookmarkSidebars_'+destination);put(v,c)
wide=['indicator_details_frame','indicator_hover_column','indicator_filter_context']+['column_help_'+k for k in keys]
narrow=[n+'_drawer_expanded' for n in wide]
rc=json.loads(d['config']);rc['bookmarks']=[b for b in rc.get('bookmarks',[]) if b['name']!='BookmarkSidebars_R1P1']
valid=set(by)
for bookmark in rc['bookmarks']:
 if not bookmark['name'].startswith('BookmarkSidebars_'):continue
 state=bookmark['name'].split('_')[-1];opened=state!='R0P0';states=bookmark['explorationState']['sections'][page['name']]['visualContainers'];states={n:s for n,s in states.items() if n in valid}
 for name in wide:states[name]={'singleVisual':{'display':{'mode':'hidden'}}} if opened else {'singleVisual':{}}
 for name in narrow:states[name]={'singleVisual':{}} if opened else {'singleVisual':{'display':{'mode':'hidden'}}}
 bookmark['explorationState']['sections'][page['name']]['visualContainers']=states;bookmark['options']['targetVisualNames']=[n for n in bookmark['options']['targetVisualNames'] if n in valid]
 if state=='R0P0':
  for name,state_value in states.items():hidden(by[name],state_value.get('singleVisual',{}).get('display',{}).get('mode')=='hidden')
d['config']=json.dumps(rc,ensure_ascii=False)
pc=json.loads(page['config']);pc['relationships']=[r for r in pc.get('relationships',[]) if r['source'] in valid and r['target'] in valid];page['config']=json.dumps(pc,ensure_ascii=False)
assert d['sections'][1:]==before['sections'][1:]
assert 60+200+16==276
for bookmark in rc['bookmarks']:
 if bookmark['name'].startswith('BookmarkSidebars_'):
  states=bookmark['explorationState']['sections'][page['name']]['visualContainers'];visible={n for n,s in states.items() if s.get('singleVisual',{}).get('display',{}).get('mode')!='hidden'}
  assert not {'reported_panel','severity_panel'}.issubset(visible)
parts['Report/Layout']=json.dumps(d,ensure_ascii=False).encode('utf-16-le');parts.pop('SecurityBindings',None)
with zipfile.ZipFile(candidate,'w') as z:
 for name,data in parts.items():z.writestr(infos[name],data)
with zipfile.ZipFile(p) as a,zipfile.ZipFile(candidate) as b:
 assert b.testzip() is None
 for name in a.namelist():
  if name not in ['Report/Layout','SecurityBindings']:assert a.read(name)==b.read(name),name
state={'original':str(p),'candidate':str(candidate),'work':str(work),'original_sha256':hashlib.sha256(p.read_bytes()).hexdigest()};(ROOT/'fullheight_drawers_state.json').write_text(json.dumps(state,indent=2));print(json.dumps(state))
