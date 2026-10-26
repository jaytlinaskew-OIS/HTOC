"""Keep the saved I&W Dashboard PBIX synchronized with the newest daily Excel file.
This updates the file on disk. It does not drive an open Power BI window.
"""
from pathlib import Path
import argparse,datetime,hashlib,json,logging,os,re,shutil,sqlite3,sys,tempfile,time,zipfile
APP=Path(os.environ['LOCALAPPDATA'])/'HTOC/IWDashboard'
sys.path.insert(0,str(APP/'lib'))
import site
site.addsitedir(str(APP/'lib'))
import openpyxl
from pbix_mcp import server as api
from pbix_mcp.formats.datamodel_roundtrip import decompress_datamodel
from pbix_mcp.formats.abf_rebuild import read_metadata_sqlite
from pbix_mcp.formats.model_reader import ModelReader
DEFAULT=Path(r'\\cscso1fsappv01\data\HTOC\Data_Analytics\Data\Threat Assessment Scores\ThreatAssessI_W')
TYPE={'string':'String','double':'Double','int64':'Int64','dateTime':'DateTime'}
SCHEMA=json.loads((Path(__file__).parent/'schema.json').read_text(encoding='utf-8'))
def result(s):
 r=json.loads(s)
 if not r.get('success'):raise RuntimeError(r.get('message',str(r)))
 return r

def latest_file(folder):
 choices=[]
 for p in folder.glob('ThreatAssessI_W_*.xlsx'):
  m=re.fullmatch(r'ThreatAssessI_W_(\d{8})\.xlsx',p.name)
  if not m:continue
  try:day=datetime.datetime.strptime(m[1],'%Y%m%d')
  except ValueError:continue
  choices.append((day,p))
 if not choices:raise ValueError('No valid daily Excel source file was found')
 return max(choices,key=lambda x:(x[0],x[1].name))

def signature(p):
 st=p.stat()
 return {'name':p.name,'size':st.st_size,'modified_ns':st.st_mtime_ns,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}

def read_rows(p,day):
 wb=openpyxl.load_workbook(p,read_only=True,data_only=True)
 try:
  sheets=[s for s in wb if s.title.strip().lower()=='i&w_no']
  if len(sheets)!=1:raise ValueError('The newest file must contain exactly one I&W_No sheet')
  it=iter(sheets[0].values);headers=list(next(it,[]))
  if not {'Indicator','Severity','PRISM Score'}.issubset(headers):raise ValueError('Required source headers are missing')
  rows=[]
  for values in it:
   r=dict(zip(headers,values))
   if r.get('Indicator') is None or not str(r['Indicator']).strip():continue
   status=str(r.get('Reported I&W?') or '').strip().lower()
   if status not in ['','no','n','false','0','unreported','not reported']:continue
   out={}
   for c in SCHEMA[0]['columns']:
    n=c['name'];v=r.get(n)
    if n=='Severity':v=str(v).strip().title() if v is not None and str(v).strip() else 'Unknown'
    elif n=='Severity Rank':v={'critical':1,'high':2,'medium':3,'low':4,'informational':5}.get(str(r.get('Severity','')).lower(),6)
    elif n=='Reported I&W?':v='No'
    elif n=='Snapshot Date':v=day
    elif n=='Source File':v=p.name
    elif v is not None and c['dataType']=='double':v=float(v)
    elif v is not None and c['dataType']=='dateTime' and not isinstance(v,datetime.datetime):v=datetime.datetime.fromisoformat(str(v))
    elif v is not None and c['dataType']=='string':v=str(v)
    out[n]=v
   rows.append(out)
  meta=[{'Snapshot Date':day,'Source File':p.name,'File Modified':datetime.datetime.fromtimestamp(p.stat().st_mtime),'Refreshed At':datetime.datetime.now(),'Unreported Rows':len(rows)}]
  return rows,meta
 finally:wb.close()

def sqlmodel(path):
 with zipfile.ZipFile(path) as z:
  c=sqlite3.connect(':memory:');c.deserialize(read_metadata_sqlite(decompress_datamodel(z.read('DataModel'))))
 return c

def update(args):
 day,source=latest_file(args.source_dir);sig=signature(source)
 state=json.loads(args.state.read_text()) if args.state.exists() else {}
 if not args.force and state.get('source')==sig:
  return {'status':'unchanged','file':source.name}
 if args.check_only:return {'status':'new-source','file':source.name}
 # Give a partially copied workbook time to settle, then check again before committing.
 time.sleep(2)
 if signature(source)!=sig:raise RuntimeError('The newest source file is still changing; retry on the next check')
 rows,meta=read_rows(source,day)
 if signature(source)!=sig:raise RuntimeError('Source file changed during reading; retry on the next check')
 old_digest=hashlib.sha256(args.target.read_bytes()).digest()
 c=sqlmodel(args.target)
 original_queries=dict(c.execute('SELECT t.Name,p.QueryDefinition FROM Partition p JOIN [Table] t ON p.TableID=t.ID WHERE t.ModelID=1').fetchall());c.close()
 with tempfile.TemporaryDirectory(prefix='htoc_iw_refresh_') as td:
  work=Path(td);assert work.resolve().is_relative_to(Path(tempfile.gettempdir()).resolve())
  candidate=work/'dashboard.pbix';shutil.copy2(args.target,candidate)
  alias='iw_auto_'+str(os.getpid());opened=False
  try:
   result(api.pbix_open(str(candidate),alias));opened=True
   changes={t['name']:{'columns':[{'name':c['name'],'data_type':TYPE[c['dataType']]} for c in t['columns']],'rows':rs} for t,rs in zip(SCHEMA,[rows,meta])}
   api._rebuild_preserving_calc(alias,api._ensure_open(alias),table_updates=changes)
   result(api.pbix_datamodel_modify_metadata(alias,'DELETE FROM Annotation WHERE ID NOT IN (SELECT MIN(ID) FROM Annotation GROUP BY ObjectID,ObjectType,Name COLLATE NOCASE)'))
   result(api.pbix_datamodel_modify_metadata(alias,"UPDATE Model SET DefaultPowerBIDataSourceVersion=2,SourceQueryCulture='en-US' WHERE ID=1"))
   # Preserve the latest-file M expressions rather than switching to a static source.
   for table,q in original_queries.items():result(api.pbix_set_partition_m(alias,table,q))
   result(api.pbix_save(alias,overwrite=True,backup=False))
   health=result(api.pbix_doctor(alias))
   if '\u274c' in health['message']:raise RuntimeError('PBIX structural diagnostics failed: '+health['message'])
  finally:
   if opened:result(api.pbix_close(alias,force=True))
  with zipfile.ZipFile(candidate) as z:
   if z.testzip():raise ValueError('Corrupt PBIX archive')
   layout=json.loads(z.read('Report/Layout').decode('utf-16-le'))
   if len(layout['sections'])!=1:raise ValueError('Dashboard must have one page')
   if any(json.loads(v['config'])['singleVisual']['visualType']=='slicer' for v in layout['sections'][0]['visualContainers']):raise ValueError('Unexpected dashboard filter')
  c=sqlmodel(candidate)
  assert c.execute('SELECT DefaultPowerBIDataSourceVersion FROM Model').fetchone()[0]==2
  assert not c.execute('SELECT ObjectID,ObjectType,Name FROM Annotation GROUP BY ObjectID,ObjectType,Name COLLATE NOCASE HAVING COUNT(*)>1').fetchall()
  assert dict(c.execute('SELECT t.Name,p.QueryDefinition FROM Partition p JOIN [Table] t ON p.TableID=t.ID WHERE t.ModelID=1').fetchall())==original_queries;c.close()
  stored=ModelReader(str(candidate)).get_table('Unreported I&W')
  assert len(stored['rows'])==len(rows)
  if rows:
   index=stored['columns'].index('Reported I&W?');assert all(r[index]=='No' for r in stored['rows'])
  if signature(source)!=sig:raise RuntimeError('Source file changed before save; retry on the next check')
  if hashlib.sha256(args.target.read_bytes()).digest()!=old_digest:raise RuntimeError('Dashboard was edited during update; retry on the next check')
  backup=args.target.with_name(args.target.stem+'.auto-refresh-backup.pbix');shutil.copy2(args.target,backup)
  staging=args.target.with_name(args.target.name+'.auto-staging.tmp')
  if staging.exists():raise RuntimeError('A staging file already exists; another update may be running')
  try:
   shutil.copy2(candidate,staging);os.replace(staging,args.target)
  finally:
   if staging.exists():staging.unlink()
 args.state.parent.mkdir(parents=True,exist_ok=True)
 status={'source':sig,'updated_at':datetime.datetime.now().astimezone().isoformat(),'unreported_rows':len(rows),'target':str(args.target)}
 tmp=args.state.with_suffix('.tmp');tmp.write_text(json.dumps(status,indent=2),encoding='utf-8');os.replace(tmp,args.state)
 return {'status':'updated','file':source.name,'rows':len(rows),'target':str(args.target)}

def main():
 p=argparse.ArgumentParser();p.add_argument('--source-dir',type=Path,default=DEFAULT);p.add_argument('--target',type=Path,default=DEFAULT/'Dashobard.pbix');p.add_argument('--state',type=Path,default=APP/'state.json');p.add_argument('--force',action='store_true');p.add_argument('--check-only',action='store_true');a=p.parse_args()
 APP.mkdir(parents=True,exist_ok=True)
 from logging.handlers import RotatingFileHandler
 handler=RotatingFileHandler(APP/'refresh.log',maxBytes=1024*1024,backupCount=2,encoding='utf-8');logging.basicConfig(level=logging.INFO,handlers=[handler],format='%(asctime)s %(levelname)s %(message)s')
 try:
  outcome=update(a)
  if outcome['status']=='updated':logging.info(json.dumps(outcome))
  print(json.dumps(outcome));return 0
 except Exception:
  logging.exception('Dashboard data update failed; existing dashboard retained')
  print(json.dumps({'status':'error','message':'Dashboard update failed; see '+str(APP/'refresh.log')}));return 1
if __name__=='__main__':sys.exit(main())
