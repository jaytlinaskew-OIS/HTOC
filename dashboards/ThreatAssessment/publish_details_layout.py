"""Apply the approved sizing/footer changes while preserving all other original content."""
from pathlib import Path
import copy,datetime as dt,hashlib,json,os,shutil,uuid,zipfile
ROOT=Path(r'\\cscso1fsappv01\home\jaskew\HTOC\dashboards\ThreatAssessment')
state_path=ROOT/'details_height_state.json';state=json.loads(state_path.read_text());p=Path(state['original']);original=p.read_bytes();digest=hashlib.sha256(original).hexdigest()
with zipfile.ZipFile(p) as z:infos={i.filename:copy.copy(i) for i in z.infolist()};parts={n:z.read(n) for n in infos}
d=json.loads(parts['Report/Layout'].decode('utf-16-le'));before=copy.deepcopy(d);changed=[]
updates={**{n:{'height':236} for n in ['indicator_details_frame','indicator_details_frame_drawer_expanded']},**{n:{'height':200} for n in ['indicator_hover_column','indicator_hover_column_drawer_expanded']},**{n:{'y':372,'height':260} for n in ['prism_panel','prism_panel_drawer_expanded','assessment_panel','assessment_panel_narrow']},**{n:{'y':372,'height':210} for n in ['prism','prism_drawer_expanded']},**{n:{'y':376,'height':220} for n in ['assessment_notes','assessment_notes_narrow']},**{n:{'y':594,'height':26} for n in ['prism_meaning','prism_meaning_drawer_expanded']},**{n:{'y':604,'height':16} for n in ['assessment_note_hint','assessment_note_hint_narrow']}}
lit=lambda v:{'expr':{'Literal':{'Value':v}}}
for v in d['sections'][0]['visualContainers']:
 c=json.loads(v['config']);name=c['name']
 if name not in updates:continue
 v.update(updates[name])
 if name in ['prism_meaning','prism_meaning_drawer_expanded','assessment_note_hint','assessment_note_hint_narrow']:
  for paragraph in c['singleVisual']['objects']['general'][0]['properties']['paragraphs']:
   for run in paragraph['textRuns']:run.setdefault('textStyle',{})['fontSize']='7pt'
  c['singleVisual']['vcObjects']['padding']=[{'properties':{k:lit('0D') for k in ['top','bottom','left','right']}}]
 c['layouts']=[{'id':0,'position':{k:v[k] for k in ['x','y','width','height','z','tabOrder']}}];v['config']=json.dumps(c,ensure_ascii=False);changed.append(name)
assert set(changed)==set(updates),'Expected dashboard sections changed; review before updating'
assert d['config']==before['config'] and d['sections'][1:]==before['sections'][1:] and d['sections'][0]['config']==before['sections'][0]['config']
parts['Report/Layout']=json.dumps(d,ensure_ascii=False).encode('utf-16-le');parts.pop('SecurityBindings',None)
stamp=dt.datetime.now().strftime('%Y%m%d-%H%M%S');backup=p.parent/'Deprecated'/('before-details-and-footers-'+stamp);backup.mkdir(parents=True);shutil.copy2(p,backup/p.name)
staging=p.with_name('Dashobard.layout-'+uuid.uuid4().hex+'.tmp')
try:
 with zipfile.ZipFile(staging,'w') as z:
  for n,b in parts.items():z.writestr(infos[n],b)
 with zipfile.ZipFile(staging) as z:
  assert z.testzip() is None
  for n,b in parts.items():assert z.read(n)==b,n
 assert hashlib.sha256(p.read_bytes()).hexdigest()==digest,'Original edited during save; stop'
 os.replace(staging,p)
finally:staging.unlink(missing_ok=True)
state.update({'status':'published','backup':str(backup),'published_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'validation':{'data_model_unchanged':True,'drawer_bookmarks_and_filters_unchanged':True,'details_height':236,'footer_font':'7pt','notes_footer_height':16,'prism_footer_height':26,'only_approved_geometry_and_footer_style_applied':True}});state_path.write_text(json.dumps(state,indent=2))
readme=ROOT/'automation/README.txt';text=readme.read_text(encoding='utf-8-sig');note='\nDETAILS AND FOOTER PROPORTIONS\nIndicator Details is 236 pixels high; its table is 200 pixels high. Both lower panels are 260 pixels high. Footer text is 7 pt with zero padding: assessment hint height 16 pixels; PRISM legend height 26 pixels. Reclaimed footer space is available to the assessment text and score plot. Explanation wording remains sourced from the I&W report without dashboard restructuring.\n'
if 'DETAILS AND FOOTER PROPORTIONS' not in text:readme.write_text(text+note,encoding='utf-8')
shutil.copy2(readme,p.parent/'Live Display Instructions.txt');print(json.dumps({'updated':str(p),'tests_archive':state.get('tests_archive'),'archived_files':state.get('archived_tests')}))
