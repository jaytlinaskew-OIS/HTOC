from pathlib import Path
import sys,os,site,json,zipfile,sqlite3,shutil,datetime,hashlib,re,copy
sys.stdout.reconfigure(encoding='utf-8');lib=Path(os.environ['LOCALAPPDATA'])/'HTOC/IWDashboard/lib';sys.path.insert(0,str(lib));site.addsitedir(str(lib))
from pbix_mcp import server as api
from pbix_mcp.report_binding import compile_visual_binding
from pbix_mcp.formats.datamodel_roundtrip import decompress_datamodel
from pbix_mcp.formats.abf_rebuild import read_metadata_sqlite
from pbix_mcp.formats.model_reader import ModelReader
import openpyxl
root=Path(r'\\cscso1fsappv01\home\jaskew\HTOC\dashboards\ThreatAssessment');target=Path(r'Z:\HTOC\Data_Analytics\Data\Threat Assessment Scores\ThreatAssessI_W\Dashobard.pbix');before=hashlib.sha256(target.read_bytes()).digest()
with zipfile.ZipFile(target) as z:
 original_layout=json.loads(z.read('Report/Layout').decode('utf-16-le'));c=sqlite3.connect(':memory:');c.deserialize(read_metadata_sqlite(decompress_datamodel(z.read('DataModel'))));queries=dict(c.execute('SELECT t.Name,p.QueryDefinition FROM Partition p JOIN [Table] t ON p.TableID=t.ID WHERE t.ModelID=1').fetchall());c.close()
R='Reported I&W (5 days)';T='Unreported I&W';end=datetime.date(2026,10,21);start=end-datetime.timedelta(days=4);records={}
for f in sorted(target.parent.glob('ThreatAssessI_W_*.xlsx'),reverse=True):
 m=re.fullmatch(r'ThreatAssessI_W_(\d{8})\.xlsx',f.name)
 if not m:continue
 try:day=datetime.datetime.strptime(m[1],'%Y%m%d').date()
 except ValueError:continue
 if not start<=day<=end:continue
 w=openpyxl.load_workbook(f,read_only=True,data_only=True)
 for s in w:
  if s.title.strip().lower()!='i&w_yes':continue
  it=iter(s.values);headers=list(next(it,[]))
  for vals in it:
   r=dict(zip(headers,vals));ind=str(r.get('Indicator') or '').strip()
   if ind and ind not in records:records[ind]={'Indicator':ind,'Explanation':str(r.get('Explanation') or 'No source assessment notes were provided.'),'Tags':str(r.get('Tags') or '')}
 w.close()
rows=[records[k] for k in sorted(records)]
rquery=queries[R].replace('[Indicator = text, Explanation = text]','[Indicator = text, Explanation = text, Tags = text]').replace('{"Indicator","Explanation"}','{"Indicator","Explanation","Tags"}')
assert '"Tags"' in rquery
work=root/'POWERBI/Dashobard.hover-tags.pbix';shutil.copy2(target,work)
def check(text):
 r=json.loads(text);assert r.get('success'),r;return r
check(api.pbix_open(str(work),'hover_tags'))
api._rebuild_preserving_calc('hover_tags',api._ensure_open('hover_tags'),table_updates={R:{'columns':[{'name':n,'data_type':'String'} for n in ['Indicator','Explanation','Tags']],'rows':rows}})
for table,q in {**queries,R:rquery}.items():check(api.pbix_set_partition_m('hover_tags',table,q))
check(api.pbix_datamodel_modify_metadata('hover_tags','DELETE FROM Annotation WHERE ID NOT IN (SELECT MIN(ID) FROM Annotation GROUP BY ObjectID,ObjectType,Name COLLATE NOCASE)'))
check(api.pbix_datamodel_modify_metadata('hover_tags',"UPDATE Model SET DefaultPowerBIDataSourceVersion=2,SourceQueryCulture='en-US' WHERE ID=1"))
check(api.pbix_save('hover_tags',overwrite=True,backup=False));check(api.pbix_close('hover_tags',force=True))
with zipfile.ZipFile(work) as z:parts={i.filename:z.read(i.filename) for i in z.infolist()}
# Use the original layout verbatim for the visible page; only tooltip pages change.
layout=copy.deepcopy(original_layout)
def lit(v):return {'expr':{'Literal':{'Value':'true' if v is True else 'false' if v is False else str(v)+'D' if isinstance(v,(int,float)) else "'"+v+"'"}}}
for page in layout['sections'][1:]:
 table=T if page['name']=='ReportSectionIWCurrentNotes' else R
 notes=page['visualContainers'][0];notes.update(x=8,y=8,width=624,height=240)
 tags=copy.deepcopy(notes);tags.update(x=8,y=260,width=624,height=212)
 cfg=json.loads(tags['config']);cfg['name']='tags_'+('current' if table==T else 'reported');s=cfg['singleVisual'];ref=table+'.Tags'
 s['projections']={'Values':[{'queryRef':ref}]};s['prototypeQuery']={'Version':2,'From':[{'Name':'t','Entity':table,'Type':0}],'Select':[{'Column':{'Expression':{'SourceRef':{'Source':'t'}},'Property':'Tags'},'Name':ref}]}
 s.setdefault('vcObjects',{})['title'][0]['properties']['text']=lit('Tags')
 s['vcObjects']['visualTooltip']=[{'properties':{'show':lit(False)}}]
 s.setdefault('objects',{})['columnWidth']=[{'selector':{'metadata':ref},'properties':{'value':lit(584)}}]
 s['objects']['values']=[{'properties':{'wordWrap':lit(True)}}]
 def resolve(e,p,m):return None if m else 'String'
 resolve.summarize_by=lambda e,p:2;resolve.data_category=lambda e,p:None
 q,dt=compile_visual_binding(s,resolve);tags['query']=json.dumps(q);tags['dataTransforms']=json.dumps(dt);tags['config']=json.dumps(cfg,ensure_ascii=False)
 page['height']=480;page['visualContainers']=[notes,tags]
 for i,v in enumerate(page['visualContainers']):
  c=json.loads(v['config']);v['z']=i*1000;v['tabOrder']=(i+1)*1000;c['layouts']=[{'id':0,'position':{k:v[k] for k in ['x','y','z','width','height','tabOrder']}}];v['config']=json.dumps(c,ensure_ascii=False)
  assert v['x']+v['width']<=640 and v['y']+v['height']<=480
assert layout['sections'][0]==original_layout['sections'][0]
parts['Report/Layout']=json.dumps(layout,ensure_ascii=False).encode('utf-16-le');parts.pop('SecurityBindings',None)
with zipfile.ZipFile(work,'w',zipfile.ZIP_DEFLATED) as z:
 for n,b in parts.items():z.writestr(n,b)
with zipfile.ZipFile(work) as z:assert z.testzip() is None
reader=ModelReader(str(work));reported=reader.get_table(R);assert set(reported['columns'])=={'Indicator','Explanation','Tags'};assert len(reported['rows'])==6
for row in reported['rows']:
 d=dict(zip(reported['columns'],row));assert d['Tags']==records[d['Indicator']]['Tags']
check(api.pbix_open(str(work),'tags_check'));health=check(api.pbix_doctor('tags_check'));assert '\u274c' not in health['message'];check(api.pbix_close('tags_check',force=True))
assert hashlib.sha256(target.read_bytes()).digest()==before
backup=target.with_name('Dashobard.before-hover-tags-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'.pbix');assert not backup.exists();shutil.copy2(target,backup)
staging=target.with_name('Dashobard.hover-tags-staging.tmp');assert not staging.exists();shutil.copy2(work,staging);os.replace(staging,target)
(root/'automation/ReportedLast5Days.pq').write_text(rquery,encoding='utf-8')
print('Saved Tags sections below assessment notes in both Indicator tooltip pages. Visible page identical; canvas and Indicator-only tooltip assignments unchanged. Reported tags match each latest source row.')
