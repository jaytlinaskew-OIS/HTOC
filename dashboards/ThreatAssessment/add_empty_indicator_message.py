from pathlib import Path
import json,sys,copy,zipfile,shutil,tempfile,hashlib
root=Path(r'\\cscso1fsappv01\home\jaskew\HTOC\dashboards\ThreatAssessment');app=Path(r'C:\Users\jaskew\AppData\Local\Packages\OpenAI.Codex_2p2nqsd0c76g0\LocalCache\Local\HTOC\IWDashboard');sys.path.insert(0,str(app));import managed_refresh as m
config=m.read_json(app/'managed-config.json');p=Path(config['template']);work=Path(tempfile.mkdtemp(prefix='htoc_empty_message_'));candidate=work/'Empty State Message.pbix';shutil.copy2(p,candidate)
with zipfile.ZipFile(p) as z:infos={i.filename:copy.copy(i) for i in z.infolist()};parts={n:z.read(n) for n in infos}
original=m.ModelReader(str(p));record=original._query_metadata("SELECT Expression FROM Measure WHERE Name='Indicator Filter Context'")[0];prefix,body=record['Expression'].rsplit('\nRETURN ',1);expression=prefix+'\nRETURN IF(TotalCount = 0, "No I&W Indicators to report today", '+body+')'
alias='iw_empty_state';m.ok(m.api.pbix_open(str(candidate),alias))
try:
 m.ok(m.api.pbix_datamodel_modify_measure(alias,'Indicator Filter Context',new_expression=expression));parts['DataModel']=(Path(m.api._ensure_open(alias)['work_dir'])/'DataModel').read_bytes()
finally:m.ok(m.api.pbix_close(alias,force=True))
m.model_health(parts['DataModel']);parts.pop('SecurityBindings',None);infos['DataModel'].compress_type=zipfile.ZIP_STORED
with zipfile.ZipFile(candidate,'w') as z:
 for n,b in parts.items():z.writestr(infos[n],b)
new=m.ModelReader(str(candidate));tables={}
for name in m.TABLES:
 old_table=original.get_table(name);t=new.get_table(name);assert old_table==t,name;tables[name]=[dict(zip(t['columns'],r)) for r in t['rows']]
with zipfile.ZipFile(p) as a,zipfile.ZipFile(candidate) as b:
 assert b.testzip() is None
 for n in a.namelist():
  if n not in ['DataModel','SecurityBindings']:assert a.read(n)==b.read(n),n
state={'original':str(p),'candidate':str(candidate),'work':str(work),'original_sha256':m.sha(p)};m.write_json(root/'empty_message_state.json',state)
print('Testing the normal populated state in native Power BI.',flush=True)
filled=m.native_validate(candidate,tables);assert filled['counts']['context'].startswith('Showing ');assert 'No I&W' not in filled['counts']['context'];print('Populated state passed; testing the latest empty report.',flush=True)
manifest,needed=m.source_manifest(Path(config['source_dir']),candidate,m.dt.date.today());schema=m.table_schema(new);latest=m.load_tables(needed,m.dt.date.today(),schema);assert len(latest['Unreported I&W'])==0,'Latest report is no longer empty'
empty=work/'Latest Empty Report.pbix';m.build_candidate(candidate,empty,schema,latest);zero=m.native_validate(empty,latest);assert zero['counts']['context']=='No I&W Indicators to report today'
state['validation']={'populated':filled,'empty':zero,'data_rows_preserved':True,'layout_unchanged':True};m.write_json(root/'empty_message_state.json',state);print(json.dumps({'status':'passed','normal_context':filled['counts']['context'],'empty_context':zero['counts']['context'],'work':str(work)}),flush=True)
