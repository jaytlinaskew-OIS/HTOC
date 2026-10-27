from pathlib import Path
import os,sys,site,json,zipfile,copy,hashlib,sqlite3,collections,shutil
lib=Path(os.environ['LOCALAPPDATA'])/'HTOC/IWDashboard/lib';sys.path.insert(0,str(lib));site.addsitedir(str(lib))
from pbix_mcp import server as api
from pbix_mcp.formats.model_reader import ModelReader
from pbix_mcp.formats.datamodel_roundtrip import decompress_datamodel
from pbix_mcp.formats.abf_rebuild import list_abf_files,read_metadata_sqlite
from pbix_mcp.report_binding import compile_visual_binding
p=Path(r'Z:\HTOC\Data_Analytics\Data\Threat Assessment Scores\ThreatAssessI_W\Dashboard\Dashobard.pbix');raw=p.read_bytes();m=ModelReader(str(p))
with zipfile.ZipFile(p) as z:
 infos={i.filename:copy.copy(i) for i in z.infolist()};parts={n:z.read(n) for n in infos}
original_tables={n:m.get_table(n) for n in ['Unreported I&W','Snapshot','Reported I&W (5 days)']}
current=original_tables['Unreported I&W'];bridge=[];expected={}
for row in current['rows']:
 r=dict(zip(current['columns'],row))
 for partner in sorted(set(s.strip() for s in str(r.get('Partners') or '').split(',') if s.strip())):
  bridge.append({'Indicator':r['Indicator'],'Partner':partner});expected.setdefault(partner,[]).append({'Indicator':r['Indicator'],'Score':r['PRISM Score']})
assert len({r['Indicator'] for r in bridge})==len(current['rows'])
queries=m._query_metadata('SELECT t.Name AS T,p.QueryDefinition AS Q FROM Partition p JOIN [Table] t ON p.TableID=t.ID WHERE t.ModelID=1 AND t.SystemFlags=0')
work=Path(os.environ['LOCALAPPDATA'])/'HTOC/IWDashboard/native_tests';candidate=work/'partner_tiles_test.pbix';shutil.copyfile(p,candidate)
def ok(s):
 r=json.loads(s)
 if not r.get('success'):raise RuntimeError(str(r)[:1000])
 return r
alias='iw_partner_tiles';ok(api.pbix_open(str(candidate),alias))
bridge_m='''let
    Source = #"Unreported I&W",
    Keep = Table.SelectColumns(Source, {"Indicator", "Partners"}),
    Split = Table.TransformColumns(Keep, {{"Partners", each if _ = null then {} else List.Select(List.Transform(Text.Split(Text.From(_), ","), each Text.Trim(_)), each _ <> ""), type list}}),
    Expand = Table.ExpandListColumn(Split, "Partners"),
    Rename = Table.RenameColumns(Expand, {{"Partners", "Partner"}}),
    Result = Table.Distinct(Table.TransformColumnTypes(Rename, {{"Indicator", type text}, {"Partner", type text}}))
in
    Result'''
try:
 info=api._ensure_open(alias);lost=[]
 api._rebuild_preserving_calc(alias,info,extra_tables=[{'name':'Indicator Partners','columns':[{'name':'Indicator','data_type':'String'},{'name':'Partner','data_type':'String'}],'rows':bridge}],extra_relationships=[{'from_table':'Indicator Partners','from_column':'Indicator','to_table':'Unreported I&W','to_column':'Indicator','cross_filter_behavior':2,'from_cardinality':2,'to_cardinality':1,'is_active':True}],lost_report=lost)
 assert not lost,lost
 ok(api.pbix_datamodel_modify_metadata(alias,'DELETE FROM Annotation WHERE ID NOT IN (SELECT MIN(ID) FROM Annotation GROUP BY ObjectID,ObjectType,Name COLLATE NOCASE)'))
 ok(api.pbix_datamodel_modify_metadata(alias,"UPDATE Model SET DefaultPowerBIDataSourceVersion=2,SourceQueryCulture='en-US' WHERE ID=1"))
 for q in queries:
  if q['Q']:ok(api.pbix_set_partition_m(alias,q['T'],q['Q']))
 ok(api.pbix_set_partition_m(alias,'Indicator Partners',bridge_m))
 dm=(Path(info['work_dir'])/'DataModel').read_bytes()
finally:ok(api.pbix_close(alias,force=True))
parts['DataModel']=dm
d=json.loads(parts['Report/Layout'].decode('utf-16-le'));before=copy.deepcopy(d);page=d['sections'][0];by={json.loads(v['config'])['name']:v for v in page['visualContainers']}
lit=lambda val:{'expr':{'Literal':{'Value':val}}}
text=lambda val:lit("'"+val.replace("'","''")+"'")
solid=lambda col:{'solid':{'color':text(col)}}
v=by['severity'];c=json.loads(v['config']);oldvc=c['singleVisual']['vcObjects'];oldvc['title'][0]['properties']['text']=text('Partners')
oldvc['padding']=[{'properties':{k:lit('8D') for k in ['top','bottom','left','right']}}]
sv={'visualType':'advancedSlicerVisual','projections':{'Values':[{'queryRef':'Indicator Partners.Partner','active':True}]},'prototypeQuery':{'Version':2,'From':[{'Name':'p','Entity':'Indicator Partners','Type':0}],'Select':[{'Column':{'Expression':{'SourceRef':{'Source':'p'}},'Property':'Partner'},'Name':'Indicator Partners.Partner'}],'OrderBy':[{'Direction':1,'Expression':{'Column':{'Expression':{'SourceRef':{'Source':'p'}},'Property':'Partner'}}}]},'objects':{
 'layout':[{'properties':{'orientation':lit('0D'),'columnCount':lit('3D'),'rowCount':lit('2D'),'maxTiles':lit('6D'),'style':text('Cards'),'customizePadding':lit('true'),'columnPadding':lit('8D'),'rowPadding':lit('8D'),'leftOuterMargin':lit('34D'),'rightOuterMargin':lit('34D'),'topOuterMargin':lit('4D'),'bottomOuterMargin':lit('4D')}}],
 'selection':[{'properties':{'singleSelect':lit('true'),'strictSingleSelect':lit('false'),'selectAllCheckboxEnabled':lit('false')}}],
 'value':[{'selector':{'id':'default'},'properties':{'show':lit('true'),'fontColor':solid('#D9D9D9'),'fontFamily':text('Segoe UI Semibold'),'fontSize':lit('14D'),'horizontalAlignment':text('center'),'verticalAlignment':text('middle'),'textWrap':lit('false')}}],
 'fillCustom':[{'properties':{'show':lit('true'),'fillColor':solid('#303366'),'transparency':lit('0D')}}],
 'outline':[{'selector':{'id':state},'properties':{'show':lit('true'),'lineColor':solid('#D9D9D9' if state=='selected' else '#303366'),'weight':lit('3D' if state=='selected' else '1D'),'transparency':lit('0D')}} for state in ['default','hover','selected']],
 'shapeCustomRectangle':[{'properties':{'tileShape':text('rectangle'),'rectangleRoundedCurve':lit('0D')}}],
 'selectionIcon':[{'properties':{'show':lit('true'),'color':solid('#D9D9D9')}}]
 },'vcObjects':oldvc}
c['singleVisual']=sv;v['config']=json.dumps(c,ensure_ascii=False);q,t=compile_visual_binding(sv,lambda e,p,is_measure:'String');v['query']=json.dumps(q,ensure_ascii=False);v['dataTransforms']=json.dumps(t,ensure_ascii=False)
foot=by['severity_meaning'];fc=json.loads(foot['config']);paragraphs=fc['singleVisual']['objects']['general'][0]['properties']['paragraphs'];paragraphs[0]['textRuns'][0]['value']='Select a partner to filter Indicator Details and PRISM scores. Click the selected partner again to show all Indicators.'
for para in paragraphs:
 for run in para['textRuns'][1:]:run['value']=''
foot['config']=json.dumps(fc,ensure_ascii=False)
# Apply the partner filter only to the two requested visuals.
pc=json.loads(page['config']);targets={'indicator_hover_column','prism'};rels=pc.setdefault('relationships',[]);rels[:]=[r for r in rels if r.get('source')!='severity']
for other in page['visualContainers']:
 name=json.loads(other['config'])['name']
 if name!='severity' and name not in targets:rels.append({'source':'severity','target':name,'type':3})
page['config']=json.dumps(pc,ensure_ascii=False)
help_page=next(s for s in d['sections'] if s['name']=='HelpIWPriorityGraph')
for hv in help_page['visualContainers']:
 hc=json.loads(hv['config']);hsv=hc['singleVisual'];paragraphs=hsv['objects']['general'][0]['properties']['paragraphs'];value='Partners' if hc['name'].endswith('_heading') else 'Each square is a partner listed in the source report. Select a partner to see its Indicators and PRISM scores. An Indicator can belong to more than one partner. Click the selected partner again to clear the filter.'
 paragraphs[0]['textRuns'][0]['value']=value
 for para in paragraphs:
  for run in para['textRuns'][1:]:run['value']=''
 hv['config']=json.dumps(hc,ensure_ascii=False)
for a,b in zip(before['sections'],d['sections']):
 assert (a['width'],a['height'])==(b['width'],b['height'])
 if a['name']=='ReportSection1':
  for va,vb in zip(a['visualContainers'],b['visualContainers']):
   name=json.loads(va['config'])['name']
   if name not in ['severity','severity_meaning']:assert va==vb,name
 elif a['name']!='HelpIWPriorityGraph':assert a==b,a['name']
parts['Report/Layout']=json.dumps(d,ensure_ascii=False).encode('utf-16-le');parts.pop('SecurityBindings',None);infos.pop('SecurityBindings',None);infos['DataModel'].compress_type=zipfile.ZIP_STORED
with zipfile.ZipFile(candidate,'w') as z:
 for n,b in parts.items():z.writestr(infos[n],b)
with zipfile.ZipFile(candidate) as z:
 assert z.testzip() is None
 for n,b in parts.items():assert z.read(n)==b,n
new=ModelReader(str(candidate))
for n,table in original_tables.items():assert new.get_table(n)==table,n
assert new.dax_measures==m.dax_measures
abf=decompress_datamodel(dm);names={f['FileName'].lower() for f in list_abf_files(abf)};db=sqlite3.connect(':memory:');db.deserialize(read_metadata_sqlite(abf));missing=[r[0] for r in db.execute('select FileName from StorageFile') if r[0] and r[0].lower() not in names];db.close();assert not missing,missing
state={'original_sha256':hashlib.sha256(raw).hexdigest(),'candidate':str(candidate),'expected':expected,'bridge_rows':len(bridge)};(work/'partner_tiles_state.json').write_text(json.dumps(state,indent=2))
print('Partner tiles candidate built; partners:',','.join(sorted(expected)),'associations:',len(bridge),flush=True)
print('Expected counts:',{k:len(v) for k,v in expected.items()},flush=True)
