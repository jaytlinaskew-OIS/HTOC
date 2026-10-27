from pathlib import Path
import copy,hashlib,json,tempfile,zipfile
root=Path(r'\\cscso1fsappv01\home\jaskew\HTOC\dashboards\ThreatAssessment');p=Path(r'Z:\HTOC\Data_Analytics\Data\Threat Assessment Scores\ThreatAssessI_W\Dashboard\Dashobard.pbix');work=Path(tempfile.mkdtemp(prefix='htoc_details_height_'));candidate=work/'Larger Indicator Details.pbix'
with zipfile.ZipFile(p) as z:infos={i.filename:copy.copy(i) for i in z.infolist()};parts={n:z.read(n) for n in infos}
d=json.loads(parts['Report/Layout'].decode('utf-16-le'));before=copy.deepcopy(d);page=d['sections'][0];changes={};amount=64
for v in page['visualContainers']:
 c=json.loads(v['config']);name=c['name'];old={k:v[k] for k in ['x','y','width','height']}
 if name in ['indicator_details_frame','indicator_details_frame_drawer_expanded','indicator_hover_column','indicator_hover_column_drawer_expanded']:v['height']+=amount
 elif name in ['prism_panel','prism_panel_drawer_expanded','prism','prism_drawer_expanded','assessment_panel','assessment_panel_narrow','assessment_notes','assessment_notes_narrow']:v['y']+=amount;v['height']-=amount
 else:continue
 c['layouts']=[{'id':0,'position':{k:v[k] for k in ['x','y','width','height','z','tabOrder']}}];v['config']=json.dumps(c,ensure_ascii=False);changes[name]={'before':old,'after':{k:v[k] for k in ['x','y','width','height']}}
assert len(changes)==12
by={json.loads(v['config'])['name']:v for v in page['visualContainers']}
assert by['indicator_details_frame']['y']+by['indicator_details_frame']['height']+16==by['assessment_panel']['y']
for name in ['assessment_panel','assessment_panel_narrow','prism_panel','prism_panel_drawer_expanded']:assert by[name]['y']+by[name]['height']==632
assert d['sections'][1:]==before['sections'][1:];assert d['config']==before['config'];assert page['config']==before['sections'][0]['config']
parts['Report/Layout']=json.dumps(d,ensure_ascii=False).encode('utf-16-le');parts.pop('SecurityBindings',None)
with zipfile.ZipFile(candidate,'w') as z:
 for name,data in parts.items():z.writestr(infos[name],data)
with zipfile.ZipFile(p) as a,zipfile.ZipFile(candidate) as b:
 assert b.testzip() is None
 for n in a.namelist():
  if n not in ['Report/Layout','SecurityBindings']:assert a.read(n)==b.read(n),n
state={'original':str(p),'candidate':str(candidate),'work':str(work),'original_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'changes':changes};(root/'details_height_state.json').write_text(json.dumps(state,indent=2));print(json.dumps({'candidate':str(candidate),'work':str(work),'details_height':by['indicator_details_frame']['height'],'lower_panels_height':by['assessment_panel']['height']}))
