from pathlib import Path
import os,sys,site,json,zipfile,copy,hashlib,datetime,sqlite3,shutil
lib=Path(os.environ['LOCALAPPDATA'])/'HTOC/IWDashboard/lib';sys.path.insert(0,str(lib));site.addsitedir(str(lib))
import openpyxl
from pbix_mcp import server as api
from pbix_mcp.formats.model_reader import ModelReader
from pbix_mcp.formats.datamodel_roundtrip import decompress_datamodel
from pbix_mcp.formats.abf_rebuild import read_metadata_sqlite,list_abf_files
p=Path(r'Z:\HTOC\Data_Analytics\Data\Threat Assessment Scores\ThreatAssessI_W\Dashboard\Dashobard.pbix')
source=p.parent.parent/'ThreatAssessI_W_20260925.xlsx'
work=Path(os.environ['LOCALAPPDATA'])/'HTOC/IWDashboard/native_tests';work.mkdir(parents=True,exist_ok=True)
candidate=work/'multiple_indicators_test.pbix'
raw=p.read_bytes();source_raw=source.read_bytes()
with zipfile.ZipFile(p) as z:
 infos={i.filename:copy.copy(i) for i in z.infolist()};parts={n:z.read(n) for n in infos}
m=ModelReader(str(p));cur=m.get_table('Unreported I&W');rows=[dict(zip(cur['columns'],r)) for r in cur['rows']]
snap=m.get_table('Snapshot');meta=[dict(zip(snap['columns'],r)) for r in snap['rows']]
reported=m.get_table('Reported I&W (5 days)')
schema={}
type_map={2:'String',6:'Int64',8:'Double',9:'DateTime',10:'Decimal',11:'Boolean'}
for r in m._query_metadata('SELECT t.Name AS T,c.ExplicitName AS C,c.ExplicitDataType AS D FROM [Column] c JOIN [Table] t ON c.TableID=t.ID WHERE t.ModelID=1 AND t.SystemFlags=0 AND c.Type=1 ORDER BY t.ID,c.ID'):
 schema.setdefault(r['T'],[]).append({'name':r['C'],'data_type':type_map[r['D']]})
queries=m._query_metadata('SELECT t.Name AS T,p.QueryDefinition AS Q FROM Partition p JOIN [Table] t ON p.TableID=t.ID WHERE t.ModelID=1 AND t.SystemFlags=0')
w=openpyxl.load_workbook(source,read_only=True,data_only=True);it=iter(w['I&W_No'].values);headers=list(next(it));incoming=[dict(zip(headers,r)) for r in it if r and r[0]];w.close()
assert set(headers).issubset(cur['columns'])
known={r['Indicator'] for r in rows};added=[];day=datetime.datetime(2026,9,25)
for r in incoming:
 if str(r.get('Reported I&W?') or '').strip().lower() not in ['','no','n','false','0','unreported','not reported']:continue
 if r['Indicator'] in known:continue
 out={}
 for col in schema['Unreported I&W']:
  n=col['name'];v=r.get(n)
  if n=='Severity':v=str(v).strip().title() if v else 'Unknown'
  elif n=='Severity Rank':v={'critical':1,'high':2,'medium':3,'low':4,'informational':5}.get(str(r.get('Severity','')).lower(),6)
  elif n=='Snapshot Date':v=day
  elif n=='Source File':v=source.name
  elif n=='Reported I&W?':v='No'
  elif v is not None and col['data_type']=='String':v=str(v)
  elif v is not None and col['data_type']=='Double':v=float(v)
  elif v is not None and col['data_type']=='Int64':v=int(v)
  elif v is not None and col['data_type']=='DateTime' and not isinstance(v,datetime.datetime):v=datetime.datetime.fromisoformat(str(v))
  out[n]=v
 rows.append(out);added.append(out);known.add(out['Indicator'])
assert len(added)==7 and len(rows)==8
if not any(r['Source File']==source.name for r in meta):meta.append({'Snapshot Date':day,'Source File':source.name,'File Modified':datetime.datetime.fromtimestamp(source.stat().st_mtime),'Refreshed At':datetime.datetime.now(),'Unreported Rows':len(added)})
shutil.copyfile(p,candidate)
def ok(s):
 r=json.loads(s)
 if not r.get('success'):raise RuntimeError(str(r)[:1500])
 return r
alias='iw_multi_test';ok(api.pbix_open(str(candidate),alias))
try:
 info=api._ensure_open(alias)
 print('Rebuilding test model with eight Indicators',flush=True)
 api._rebuild_preserving_calc(alias,info,table_updates={'Unreported I&W':{'columns':schema['Unreported I&W'],'rows':rows},'Snapshot':{'columns':schema['Snapshot'],'rows':meta}})
 ok(api.pbix_datamodel_modify_metadata(alias,'DELETE FROM Annotation WHERE ID NOT IN (SELECT MIN(ID) FROM Annotation GROUP BY ObjectID,ObjectType,Name COLLATE NOCASE)'))
 ok(api.pbix_datamodel_modify_metadata(alias,"UPDATE Model SET DefaultPowerBIDataSourceVersion=2,SourceQueryCulture='en-US' WHERE ID=1"))
 for q in queries:
  if q['T']=='Reported I&W (5 days)' and q['Q']:ok(api.pbix_set_partition_m(alias,q['T'],q['Q']))
 dm=(Path(info['work_dir'])/'DataModel').read_bytes()
finally:ok(api.pbix_close(alias,force=True))
parts['DataModel']=dm;parts.pop('SecurityBindings',None);infos.pop('SecurityBindings',None);infos['DataModel'].compress_type=zipfile.ZIP_STORED
with zipfile.ZipFile(candidate,'w') as z:
 for n,b in parts.items():z.writestr(infos[n],b)
with zipfile.ZipFile(candidate) as z:
 assert z.testzip() is None
 assert z.read('Report/Layout')==parts['Report/Layout']
 for n,b in parts.items():assert z.read(n)==b,n
abf=decompress_datamodel(dm);files=list_abf_files(abf);names={f['FileName'].lower() for f in files}
c=sqlite3.connect(':memory:');c.deserialize(read_metadata_sqlite(abf));missing=[r[0] for r in c.execute('select FileName from StorageFile') if r[0] and r[0].lower() not in names];assert not missing,missing;c.close()
new=ModelReader(str(candidate));got=new.get_table('Unreported I&W');assert len(got['rows'])==8
assert new.get_table('Reported I&W (5 days)')==reported
for name in ['Unreported I&W','Snapshot']:
 exp=rows if name=='Unreported I&W' else meta;got=new.get_table(name)
 assert [dict(zip(got['columns'],r)) for r in got['rows']]==exp,name
assert new.dax_measures==m.dax_measures
assert source.read_bytes()==source_raw
state={'original_sha256':hashlib.sha256(raw).hexdigest(),'candidate':str(candidate),'source':str(source),'added':len(added),'total':len(rows),'highest_prism':max(r['PRISM Score'] for r in rows),'layout_sha256':hashlib.sha256(parts['Report/Layout']).hexdigest()}
(work/'multiple_indicators_state.json').write_text(json.dumps(state,indent=2))
print(json.dumps(state,indent=2),flush=True)
