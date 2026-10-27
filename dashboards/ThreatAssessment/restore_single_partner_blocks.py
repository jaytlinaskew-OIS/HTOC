from pathlib import Path
import os,sys,site,json,zipfile,copy,shutil,hashlib
lib=Path(os.environ['LOCALAPPDATA'])/'HTOC/IWDashboard/lib';sys.path.insert(0,str(lib));site.addsitedir(str(lib))
from pbix_mcp import server as api
from pbix_mcp.formats.model_reader import ModelReader
from restore_blank_dictionary import restore_blank_dictionary
p=Path(r'Z:\HTOC\Data_Analytics\Data\Threat Assessment Scores\ThreatAssessI_W\Dashboard\Dashobard.pbix');raw=p.read_bytes();work=Path(os.environ['LOCALAPPDATA'])/'HTOC/IWDashboard/native_tests';candidate=work/'visible_single_partner_blocks_test.pbix';shutil.copyfile(p,candidate)
with zipfile.ZipFile(p) as z:infos={i.filename:copy.copy(i) for i in z.infolist()};parts={n:z.read(n) for n in infos}
def ok(s):
 r=json.loads(s)
 if not r.get('success'):raise RuntimeError(str(r)[:1000])
 return r
guidance='''VAR IndicatorCount = CALCULATE(DISTINCTCOUNT('Unreported I&W'[Indicator]), REMOVEFILTERS())
RETURN SWITCH(TRUE(), IndicatorCount = 0, "No Indicators are available.", IndicatorCount = 1, "These partners are linked to this Indicator. Selecting a block keeps the same details and PRISM score displayed.", "Select a partner block to filter Indicator Details and PRISM scores. Blocks resize automatically as partners are added.")'''
alias='iw_restore_single_blocks';ok(api.pbix_open(str(candidate),alias))
try:
 ok(api.pbix_datamodel_modify_measure(alias,'Partner Block Area',new_expression='1'))
 ok(api.pbix_datamodel_modify_measure(alias,'Partner Panel Guidance',new_expression=guidance))
 ok(api.pbix_datamodel_modify_metadata(alias,"UPDATE Measure SET Description='Explains partner blocks for single and multiple Indicators.' WHERE Name='Partner Panel Guidance'"))
 info=api._ensure_open(alias);dm=(Path(info['work_dir'])/'DataModel').read_bytes()
finally:ok(api.pbix_close(alias,force=True))
parts['DataModel']=restore_blank_dictionary(dm,work/'partner_autofit_final.pbix');d=json.loads(parts['Report/Layout'].decode('utf-16-le'));before=copy.deepcopy(d)
for page in d['sections']:
 if page['name']=='HelpIWPriorityGraph':
  for v in page['visualContainers']:
   c=json.loads(v['config'])
   if c['name'].endswith('_body'):
    c['singleVisual']['objects']['general'][0]['properties']['paragraphs'][0]['textRuns'][0]['value']='Each block represents a partner linked to the Indicators. Blocks share the available space and resize as partners are added. Selecting a partner filters Indicator Details and PRISM scores. With one Indicator, all its partner blocks remain visible and refer to that same record.';v['config']=json.dumps(c,ensure_ascii=False)
assert before['sections'][0]==d['sections'][0]
parts['Report/Layout']=json.dumps(d,ensure_ascii=False).encode('utf-16-le');parts.pop('SecurityBindings',None);infos.pop('SecurityBindings',None);infos['DataModel'].compress_type=zipfile.ZIP_STORED
with zipfile.ZipFile(candidate,'w') as z:
 for n,b in parts.items():z.writestr(infos[n],b)
a=ModelReader(str(p));b=ModelReader(str(candidate))
for name in ['Unreported I&W','Snapshot','Reported I&W (5 days)','Indicator Partners']:assert a.get_table(name)==b.get_table(name),name
(work/'visible_single_partner_state.json').write_text(json.dumps({'candidate':str(candidate),'original_sha256':hashlib.sha256(raw).hexdigest()},indent=2))
# Build a separate one-Indicator fixture with exactly that Indicator's partner associations.
fixture=work/'visible_single_partner_blocks_fixture.pbix';shutil.copyfile(candidate,fixture);t=b.get_table('Unreported I&W');single=dict(zip(t['columns'],t['rows'][0]));bt=b.get_table('Indicator Partners');rows=[dict(zip(bt['columns'],r)) for r in bt['rows'] if r[bt['columns'].index('Indicator')]==single['Indicator']]
tm={2:'String',6:'Int64',8:'Double',9:'DateTime',10:'Decimal',11:'Boolean'};schema={}
for r in b._query_metadata('SELECT t.Name AS T,c.ExplicitName AS C,c.ExplicitDataType AS D FROM [Column] c JOIN [Table] t ON c.TableID=t.ID WHERE t.ModelID=1 AND t.SystemFlags=0 AND c.Type=1 ORDER BY t.ID,c.ID'):schema.setdefault(r['T'],[]).append({'name':r['C'],'data_type':tm[r['D']]})
queries=b._query_metadata('SELECT t.Name AS T,p.QueryDefinition AS Q FROM Partition p JOIN [Table] t ON p.TableID=t.ID WHERE t.ModelID=1 AND t.SystemFlags=0');alias='iw_visible_one_fixture';ok(api.pbix_open(str(fixture),alias))
try:
 info=api._ensure_open(alias);api._rebuild_preserving_calc(alias,info,table_updates={'Unreported I&W':{'columns':schema['Unreported I&W'],'rows':[single]},'Indicator Partners':{'columns':schema['Indicator Partners'],'rows':rows}})
 ok(api.pbix_datamodel_modify_metadata(alias,'DELETE FROM Annotation WHERE ID NOT IN (SELECT MIN(ID) FROM Annotation GROUP BY ObjectID,ObjectType,Name COLLATE NOCASE)'));ok(api.pbix_datamodel_modify_metadata(alias,"UPDATE Model SET DefaultPowerBIDataSourceVersion=2,SourceQueryCulture='en-US' WHERE ID=1"))
 for q in queries:
  if q['Q']:ok(api.pbix_set_partition_m(alias,q['T'],q['Q']))
 fixture_dm=(Path(info['work_dir'])/'DataModel').read_bytes()
finally:ok(api.pbix_close(alias,force=True))
fixture_parts=copy.copy(parts);fixture_parts['DataModel']=fixture_dm
with zipfile.ZipFile(fixture,'w') as z:
 for n,data in fixture_parts.items():z.writestr(infos[n],data)
print('Restored partner blocks for single and multiple Indicators. Production records unchanged; created one-record fixture with four partner blocks.')
