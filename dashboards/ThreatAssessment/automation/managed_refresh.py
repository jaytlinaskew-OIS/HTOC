"""Automatic refresh of an owned Desktop display copy; the original is read-only."""
from __future__ import annotations
import argparse,copy,datetime as dt,hashlib,json,logging,math,msvcrt,os,re,shutil,sqlite3,subprocess,sys,tempfile,time,zipfile
from logging.handlers import RotatingFileHandler
from pathlib import Path
APP=Path(__file__).resolve().parent if Path(__file__).with_name('managed-config.json').exists() else Path(os.environ['LOCALAPPDATA'])/'HTOC/IWDashboard'
sys.path.insert(0,str(APP/'lib'))
import site
site.addsitedir(str(APP/'lib'))
import openpyxl
from pbix_mcp import server as api
from pbix_mcp.formats.model_reader import ModelReader
from pbix_mcp.formats.datamodel_roundtrip import decompress_datamodel
from pbix_mcp.formats.abf_rebuild import list_abf_files,read_metadata_sqlite
VERSION=1
TABLES=('Unreported I&W','Snapshot','Reported I&W (5 days)','Indicator Partners')
TYPES={2:'String',6:'Int64',8:'Double',9:'DateTime',10:'Decimal',11:'Boolean'}
REPORT_NAME=re.compile(r'ThreatAssessI_W_(\d{8})\.xlsx',re.IGNORECASE)
NO={'','no','n','false','0','unreported','not reported'}
LOG=logging.getLogger('managed_refresh')

def read_json(path):
 return json.loads(path.read_text(encoding='utf-8-sig')) if path.exists() else {}

def write_json(path,value):
 path.parent.mkdir(parents=True,exist_ok=True);staging=path.with_name(path.name+'.tmp')
 staging.write_text(json.dumps(value,indent=2,default=str),encoding='utf-8');os.replace(staging,path)

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def signature(path):
 st=path.stat();return {'name':path.name,'size':st.st_size,'modified_ns':st.st_mtime_ns,'sha256':sha(path)}

def reports(folder,today):
 found=[]
 for p in folder.glob('*.xlsx'):
  match=REPORT_NAME.fullmatch(p.name)
  if not match:continue
  try:day=dt.datetime.strptime(match[1],'%Y%m%d').date()
  except ValueError:continue
  if day<=today:found.append((day,p))
 if not found:raise ValueError('No correctly named report dated today or earlier was found')
 return sorted(found,key=lambda x:(x[0],x[1].name),reverse=True)

def sheet_rows(book,name,required,optional=False):
 sheets=[s for s in book if s.title.strip().casefold()==name.casefold()]
 if not sheets and optional:return []
 if len(sheets)!=1:raise ValueError(f'Expected one {name} sheet')
 iterator=iter(sheets[0].values);headers=[str(v).strip() if v is not None else '' for v in next(iterator,())]
 nonblank=[v for v in headers if v]
 if len(nonblank)!=len(set(nonblank)):raise ValueError(f'{name}: duplicate column headings')
 if not required.issubset(headers):raise ValueError(f'{name}: missing columns {sorted(required-set(headers))}')
 rows=[]
 for values in iterator:
  record=dict(zip(headers,values));indicator=str(record.get('Indicator') or '').strip()
  if indicator:record['Indicator']=indicator;rows.append(record)
 return rows

def source_manifest(folder,template,today):
 choices=reports(folder,today);start=today-dt.timedelta(days=4)
 needed=[(day,p) for i,(day,p) in enumerate(choices) if i==0 or day>=start]
 manifest={'version':VERSION,'window_date':today.isoformat(),'template_sha256':sha(template),'latest':choices[0][1].name,'sources':[signature(p) for _,p in needed]}
 return manifest,needed

def convert(value,kind,name):
 if value is None or value=='':return None
 if kind=='String':return str(value)
 if kind in {'Double','Decimal','Int64'}:
  number=float(value)
  if not math.isfinite(number):raise ValueError(f'{name}: score must be finite')
  if name=='PRISM Score' and not 0<=number<=1000:raise ValueError('PRISM Score must be between 0 and 1000')
  if kind=='Int64' and number!=int(number):raise ValueError(f'{name}: expected a whole number')
  return int(number) if kind=='Int64' else number
 if kind=='DateTime':
  if isinstance(value,dt.datetime):return value
  if isinstance(value,dt.date):return dt.datetime.combine(value,dt.time())
  return dt.datetime.fromisoformat(str(value))
 if kind=='Boolean':
  if isinstance(value,bool):return value
  if str(value).strip().lower() in {'true','1'}:return True
  if str(value).strip().lower() in {'false','0'}:return False
  raise ValueError(f'{name}: invalid Boolean')
 raise ValueError(f'Unsupported field type {kind}')

def table_schema(model):
 schema={}
 for r in model._query_metadata('SELECT t.Name AS T,c.ExplicitName AS C,c.ExplicitDataType AS D FROM [Column] c JOIN [Table] t ON c.TableID=t.ID WHERE t.ModelID=1 AND t.SystemFlags=0 AND c.Type=1 ORDER BY t.ID,c.ID'):
  schema.setdefault(r['T'],[]).append({'name':r['C'],'data_type':TYPES[r['D']]})
 if set(schema)!=set(TABLES):raise ValueError(f'Unexpected dashboard tables: {sorted(schema)}')
 return schema

def load_tables(needed,today,schema):
 day,latest=needed[0];now=dt.datetime.now();book=openpyxl.load_workbook(latest,read_only=True,data_only=True)
 try:raw=sheet_rows(book,'I&W_No',{'Indicator','Severity','PRISM Score','Partners'})
 finally:book.close()
 current=[];seen=set()
 for record in raw:
  if str(record.get('Reported I&W?') or '').strip().lower() not in NO:continue
  indicator=record['Indicator']
  if indicator in seen:raise ValueError(f'Duplicate Indicator in I&W_No: {indicator}; partner relationship requires unique Indicators')
  seen.add(indicator);severity=str(record.get('Severity') or 'Unknown').strip().title()
  derived={'Severity':severity,'Severity Rank':{'Critical':1,'High':2,'Medium':3,'Low':4,'Informational':5}.get(severity,6),'Reported I&W?':'No','Snapshot Date':dt.datetime.combine(day,dt.time()),'Source File':latest.name}
  row={c['name']:convert(derived.get(c['name'],record.get(c['name'])),c['data_type'],c['name']) for c in schema['Unreported I&W']}
  if row['PRISM Score'] is None:raise ValueError(f'{indicator}: missing PRISM Score')
  current.append(row)
 current.sort(key=lambda r:(-r['PRISM Score'],r['Indicator']))
 snapshot=[{'Snapshot Date':dt.datetime.combine(day,dt.time()),'Source File':latest.name,'File Modified':dt.datetime.fromtimestamp(latest.stat().st_mtime),'Refreshed At':now,'Unreported Rows':len(current)}]
 reported={}
 # Each source is read once; dict/set membership deduplicates in O(rows).
 for report_day,path in needed:
  if report_day<today-dt.timedelta(days=4):continue
  book=openpyxl.load_workbook(path,read_only=True,data_only=True)
  try:
   for row in sheet_rows(book,'I&W_Yes',{'Indicator'},optional=True):
    reported.setdefault(row['Indicator'],{c['name']:convert(row.get(c['name']),c['data_type'],c['name']) for c in schema['Reported I&W (5 days)']})
  finally:book.close()
 links=sorted({(r['Indicator'],partner.strip()) for r in current for partner in str(r.get('Partners') or '').split(',') if partner.strip()})
 return {'Unreported I&W':current,'Snapshot':snapshot,'Reported I&W (5 days)':[reported[k] for k in sorted(reported)],'Indicator Partners':[{'Indicator':i,'Partner':p} for i,p in links]}

def ok(value):
 result=json.loads(value)
 if not result.get('success'):raise RuntimeError(str(result)[:1500])
 return result

def model_health(datamodel):
 abf=decompress_datamodel(datamodel);names={f['FileName'].lower() for f in list_abf_files(abf)};db=sqlite3.connect(':memory:')
 try:
  db.deserialize(read_metadata_sqlite(abf));missing=[r[0] for r in db.execute('SELECT FileName FROM StorageFile') if r[0] and r[0].lower() not in names]
  if missing:raise ValueError(f'Missing embedded model files: {missing}')
  duplicates=db.execute('SELECT Name FROM Annotation GROUP BY ObjectID,ObjectType,Name COLLATE NOCASE HAVING COUNT(*)>1').fetchall()
  if duplicates:raise ValueError(f'Duplicate model annotations: {duplicates}')
 finally:db.close()

def build_candidate(template,candidate,schema,tables):
 with zipfile.ZipFile(template) as z:
  infos={i.filename:copy.copy(i) for i in z.infolist()};parts={n:z.read(n) for n in infos}
 original=ModelReader(str(template));shutil.copy2(template,candidate);alias='iw_managed_'+str(os.getpid());ok(api.pbix_open(str(candidate),alias))
 try:
  info=api._ensure_open(alias);lost=[]
  api._rebuild_preserving_calc(alias,info,table_updates={name:{'columns':schema[name],'rows':tables[name]} for name in TABLES},lost_report=lost)
  if lost:raise RuntimeError(f'Model metadata could not be preserved: {lost}')
  ok(api.pbix_datamodel_modify_metadata(alias,'DELETE FROM Annotation WHERE ID NOT IN (SELECT MIN(ID) FROM Annotation GROUP BY ObjectID,ObjectType,Name COLLATE NOCASE)'))
  ok(api.pbix_datamodel_modify_metadata(alias,"UPDATE Model SET DefaultPowerBIDataSourceVersion=2,SourceQueryCulture='en-US' WHERE ID=1"))
  # Rebuilt inline M matches cached rows; Desktop Refresh cannot restore old test rows.
  datamodel=(Path(info['work_dir'])/'DataModel').read_bytes()
 finally:ok(api.pbix_close(alias,force=True))
 model_health(datamodel);parts['DataModel']=datamodel;parts.pop('SecurityBindings',None);infos['DataModel'].compress_type=zipfile.ZIP_STORED
 with zipfile.ZipFile(candidate,'w') as z:
  for name,content in parts.items():z.writestr(infos[name],content)
 with zipfile.ZipFile(candidate) as z:
  if z.testzip() is not None:raise ValueError('Invalid PBIX archive')
  for name,content in parts.items():assert z.read(name)==content,name
 updated=ModelReader(str(candidate));assert updated.dax_measures==original.dax_measures,'DAX measures changed'
 for name in TABLES:
  table=updated.get_table(name);actual=[dict(zip(table['columns'],r)) for r in table['rows']]
  assert actual==tables[name],f'{name}: rebuilt rows differ'
 assert len(original._query_metadata('SELECT * FROM Relationship'))==len(updated._query_metadata('SELECT * FROM Relationship')),'Relationship count changed'

def powershell(script,*arguments,timeout=180):
 run=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(script),*map(str,arguments)],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout,creationflags=subprocess.CREATE_NO_WINDOW)
 if run.returncode:raise RuntimeError(f'{script.name}: {run.stderr.strip() or run.stdout.strip()}')
 lines=[s for s in run.stdout.splitlines() if s.strip()];return json.loads(lines[-1]) if lines else {}

def native_validate(candidate,tables):
 expectation={'current':len(tables['Unreported I&W']),'reported':len(tables['Reported I&W (5 days)']),'links':len(tables['Indicator Partners']),'highest':max((r['PRISM Score'] for r in tables['Unreported I&W']),default=0)}
 expected=candidate.with_suffix('.expected.json');write_json(expected,expectation)
 return powershell(Path(__file__).with_name('validate_desktop.ps1'),'-Candidate',str(candidate),'-Expected',str(expected),timeout=150)

def display(action,config):
 return powershell(Path(__file__).with_name('display_window.ps1'),'-Action',action,'-DisplayFile',config['display_file'],'-ProcessState',config['process_state'])

def run(config,check_only=False,force=False,no_display=False):
 if Path(config.get('pause_file',APP/'managed-paused.flag')).exists():return {'status':'paused'}
 template,target=Path(config['template']),Path(config['display_file'])
 if template.resolve()==target.resolve():raise ValueError('Managed display must be separate from editable original')
 today=dt.date.today();manifest,needed=source_manifest(Path(config['source_dir']),template,today);previous=read_json(Path(config['state_file']))
 unchanged=previous.get('manifest')==manifest and target.exists() and previous.get('display_sha256')==sha(target)
 if check_only:
  tables=load_tables(needed,today,table_schema(ModelReader(str(template))))
  return {'status':'unchanged' if unchanged else 'new-data','latest':manifest['latest'],'counts':{t:len(tables[t]) for t in TABLES},'display_file':str(target)}
 if unchanged and not force:return {'status':'unchanged','latest':manifest['latest'],'display':display('Ensure',config) if not no_display else {}}
 time.sleep(config.get('settle_seconds',3))
 if source_manifest(Path(config['source_dir']),template,today)[0]!=manifest:raise RuntimeError('A source or original dashboard is still changing; retry next check')
 schema=table_schema(ModelReader(str(template)));tables=load_tables(needed,today,schema);target.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='update-',dir=target.parent) as temp:
  candidate=Path(temp)/'Validated I&W Dashboard.pbix';LOG.info('Building %s; counts %s',manifest['latest'],{t:len(tables[t]) for t in TABLES})
  build_candidate(template,candidate,schema,tables);native=native_validate(candidate,tables)
  if source_manifest(Path(config['source_dir']),template,today)[0]!=manifest:raise RuntimeError('Source/template changed during build; retained last good display')
  if Path(config.get('pause_file',APP/'managed-paused.flag')).exists():return {'status':'paused'}
  old_hash=sha(target) if target.exists() else None
  if target.exists():
   backups=target.parent/'Deprecated';backups.mkdir(exist_ok=True);shutil.copy2(target,backups/('HTOC I&W Dashboard-'+dt.datetime.now().strftime('%Y%m%d-%H%M%S-%f')+'.pbix'))
  if not no_display:display('Stop',config)
  if target.exists() and sha(target)!=old_hash:raise RuntimeError('Managed copy edited during update; retained for review')
  staging=target.with_suffix('.staging')
  try:shutil.copy2(candidate,staging);os.replace(staging,target)
  except Exception:
   if not no_display:display('Ensure',config)
   raise
  finally:staging.unlink(missing_ok=True)
  state={'manifest':manifest,'updated_at':dt.datetime.now().astimezone().isoformat(),'display_sha256':sha(target),'counts':{t:len(tables[t]) for t in TABLES},'native_validation':native};write_json(Path(config['state_file']),state)
 window=display('Ensure',config) if not no_display and not Path(config.get('pause_file',APP/'managed-paused.flag')).exists() else {}
 return {'status':'updated','latest':manifest['latest'],'counts':state['counts'],'display':window}

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--config',type=Path,default=APP/'managed-config.json');parser.add_argument('--check-only',action='store_true');parser.add_argument('--force',action='store_true');parser.add_argument('--no-display',action='store_true');args=parser.parse_args();APP.mkdir(parents=True,exist_ok=True)
 handler=RotatingFileHandler(APP/'managed-refresh.log',maxBytes=1024*1024,backupCount=3,encoding='utf-8');logging.basicConfig(level=logging.INFO,handlers=[handler],format='%(asctime)s %(levelname)s %(message)s',force=True)
 with (APP/'managed-refresh.lock').open('a+b') as lock:
  lock.seek(0)
  if lock.read(1)==b'':lock.write(b'0');lock.flush()
  lock.seek(0)
  try:msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
  except OSError:print(json.dumps({'status':'already-running'}));return 0
  try:
   outcome=run(read_json(args.config),check_only=args.check_only,force=args.force,no_display=args.no_display)
   if outcome['status']!='unchanged':LOG.info(json.dumps(outcome))
   write_json(APP/'managed-status.json',{'checked_at':dt.datetime.now().astimezone().isoformat(),**outcome});print(json.dumps(outcome));return 0
  except Exception as exc:
   LOG.exception('Update failed; retained last working display');outcome={'status':'error','message':str(exc),'checked_at':dt.datetime.now().astimezone().isoformat()};write_json(APP/'managed-status.json',outcome);print(json.dumps(outcome));return 1
  finally:lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)
if __name__=='__main__':sys.exit(main())
