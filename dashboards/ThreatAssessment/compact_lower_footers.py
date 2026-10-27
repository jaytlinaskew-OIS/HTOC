from pathlib import Path
import json,zipfile,copy
root=Path(r'\\cscso1fsappv01\home\jaskew\HTOC\dashboards\ThreatAssessment');state_path=root/'details_height_state.json';state=json.loads(state_path.read_text());p=Path(state['candidate'])
with zipfile.ZipFile(p) as z:infos={i.filename:copy.copy(i) for i in z.infolist()};parts={n:z.read(n) for n in infos}
d=json.loads(parts['Report/Layout'].decode('utf-16-le'));changes={}
lit=lambda v:{'expr':{'Literal':{'Value':v}}}
for v in d['sections'][0]['visualContainers']:
 c=json.loads(v['config']);name=c['name']
 if name.startswith('prism_meaning'):
  v.update(y=594,height=26)
 elif name.startswith('assessment_note_hint'):
  v.update(y=604,height=16)
 elif name in ['prism','prism_drawer_expanded']:
  v['height']=210
 elif name in ['assessment_notes','assessment_notes_narrow']:
  v['height']=220
 else:continue
 if name.startswith('prism_meaning') or name.startswith('assessment_note_hint'):
  for paragraph in c['singleVisual']['objects']['general'][0]['properties']['paragraphs']:
   for run in paragraph['textRuns']:run.setdefault('textStyle',{})['fontSize']='7pt'
  c['singleVisual']['vcObjects']['padding']=[{'properties':{k:lit('0D') for k in ['top','bottom','left','right']}}]
 c['layouts']=[{'id':0,'position':{k:v[k] for k in ['x','y','width','height','z','tabOrder']}}];v['config']=json.dumps(c,ensure_ascii=False);changes[name]={k:v[k] for k in ['x','y','width','height']}
parts['Report/Layout']=json.dumps(d,ensure_ascii=False).encode('utf-16-le');out=Path(state['work'])/'Larger Details Compact Footers.pbix'
with zipfile.ZipFile(out,'w') as z:
 for n,b in parts.items():z.writestr(infos[n],b)
with zipfile.ZipFile(out) as z:assert z.testzip() is None
state['candidate']=str(out);state['footer_changes']=changes;state_path.write_text(json.dumps(state,indent=2));print(json.dumps({'candidate':str(out),'footer_font':'7pt','notes_footer_height':16,'prism_footer_height':26}))
