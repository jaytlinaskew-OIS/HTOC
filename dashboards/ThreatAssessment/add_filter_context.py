from pathlib import Path
import os,sys,site,json,zipfile,copy,hashlib,tempfile,shutil,uuid
lib=Path(os.environ['LOCALAPPDATA'])/'HTOC/IWDashboard/lib';sys.path.insert(0,str(lib));site.addsitedir(str(lib))
from pbix_mcp import server as api
from pbix_mcp.formats.model_reader import ModelReader
from pbix_mcp.report_binding import compile_visual_binding
from restore_blank_dictionary import restore_blank_dictionary
p=Path(r'Z:\HTOC\Data_Analytics\Data\Threat Assessment Scores\ThreatAssessI_W\Dashboard\Dashobard.pbix');raw=p.read_bytes();work=Path(tempfile.mkdtemp(prefix='htoc_filter_context_'));candidate=work/'FilterContext.pbix';shutil.copyfile(p,candidate)
with zipfile.ZipFile(p) as z:infos={i.filename:copy.copy(i) for i in z.infolist()};parts={n:z.read(n) for n in infos}
def ok(s):
 r=json.loads(s)
 if not r.get('success'):raise RuntimeError(str(r)[:1000])
 return r
expression='''VAR VisibleCount = [Unreported Indicators]
VAR TotalCount = CALCULATE([Unreported Indicators], REMOVEFILTERS())
VAR HasPartnerFilter = ISFILTERED('Indicator Partners'[Partner])
VAR PartnerCount = COUNTROWS(VALUES('Indicator Partners'[Partner]))
VAR PartnerText = SWITCH(TRUE(), NOT HasPartnerFilter, "All partners", PartnerCount <= 2, CONCATENATEX(VALUES('Indicator Partners'[Partner]), 'Indicator Partners'[Partner], ", ", 'Indicator Partners'[Partner], ASC), FORMAT(PartnerCount, "0") & " partners selected")
RETURN "Showing " & FORMAT(VisibleCount, "#,0") & " of " & FORMAT(TotalCount, "#,0") & IF(TotalCount = 1, " Indicator", " Indicators") & " " & UNICHAR(183) & " " & PartnerText'''
alias='iw_filter_context';ok(api.pbix_open(str(candidate),alias))
try:
 ok(api.pbix_datamodel_add_measure(alias,'Unreported I&W','Indicator Filter Context',expression,description='Visible and total Indicator counts with the selected partner context.',data_type='String'))
 info=api._ensure_open(alias);dm=(Path(info['work_dir'])/'DataModel').read_bytes()
finally:ok(api.pbix_close(alias,force=True))
parts['DataModel']=restore_blank_dictionary(dm,Path(os.environ['LOCALAPPDATA'])/'HTOC/IWDashboard/native_tests/partner_autofit_final.pbix')
d=json.loads(parts['Report/Layout'].decode('utf-16-le'));before=copy.deepcopy(d);page=d['sections'][0];page_name=page['name'];assert not any(json.loads(v['config'])['name']=='indicator_filter_context' for v in page['visualContainers'])
lit=lambda x:{'expr':{'Literal':{'Value':x}}};txt=lambda x:lit("'"+x.replace("'","''")+"'");solid=lambda x:{'solid':{'color':txt(x)}}
base_vc={'title':[{'properties':{'show':lit('false')}}],'background':[{'properties':{'show':lit('false')}}],'border':[{'properties':{'show':lit('false')}}],'padding':[{'properties':{k:lit('0D') for k in ['top','bottom','left','right']}}],'visualHeader':[{'properties':{'show':lit('false')}}],'general':[{'properties':{'keepLayerOrder':lit('true')}}]}
card={'x':440,'y':124,'width':500,'height':20,'z':32000,'tabOrder':32000};vc=copy.deepcopy(base_vc);vc['visualTooltip']=[{'properties':{'show':lit('true'),'type':txt('Canvas'),'section':txt('HelpIWFilterContext')}}]
sv={'visualType':'card','projections':{'Values':[{'queryRef':'Unreported I&W.Indicator Filter Context'}]},'prototypeQuery':{'Version':2,'From':[{'Name':'u','Entity':'Unreported I&W','Type':0}],'Select':[{'Measure':{'Expression':{'SourceRef':{'Source':'u'}},'Property':'Indicator Filter Context'},'Name':'Unreported I&W.Indicator Filter Context'}]},'objects':{'labels':[{'properties':{'fontSize':lit('10D'),'color':solid('#D9D9D9'),'fontFamily':txt('Segoe UI')}}],'categoryLabels':[{'properties':{'show':lit('false')}}],'wordWrap':[{'properties':{'show':lit('false')}}]},'vcObjects':vc}
c={'name':'indicator_filter_context','layouts':[{'id':0,'position':copy.deepcopy(card)}],'singleVisual':sv};q,t=compile_visual_binding(sv,lambda e,p,is_measure:'String');card.update({'config':json.dumps(c,ensure_ascii=False),'query':json.dumps(q,ensure_ascii=False),'dataTransforms':json.dumps(t,ensure_ascii=False)});page['visualContainers'].append(card)
bookmark_name='BookmarkClearPartnerFilter'+uuid.uuid4().hex[:12]
rc=json.loads(d['config']);rc.setdefault('bookmarks',[]).append({'displayName':'Clear partner filter','name':bookmark_name,'explorationState':{'version':'1.2','activeSection':page_name,'sections':{page_name:{'visualContainers':{'severity':{'singleVisual':{},'highlight':{'selection':[]}}}}}},'options':{'applyOnlyToTargetVisuals':True,'targetVisualNames':['severity'],'suppressActiveSection':True,'suppressDisplay':True,'suppressData':False}});d['config']=json.dumps(rc,ensure_ascii=False)
button={'x':974,'y':124,'width':122,'height':20,'z':32001,'tabOrder':32001};vc=copy.deepcopy(base_vc);vc['general'][0]['properties']['altText']=txt('Clear partner filter');vc['visualTooltip']=[{'properties':{'show':lit('false')}}];vc['visualLink']=[{'properties':{'show':lit('true'),'type':txt('Bookmark'),'bookmark':txt(bookmark_name),'tooltip':txt('Clear the partner selection and show all Indicators. In Power BI Desktop, Ctrl+click.'),'showDefaultTooltip':lit('true'),'suppressDefaultTooltip':lit('false')}}]
obj={'text':[{'selector':{'id':'default'},'properties':{'show':lit('true'),'text':txt('Clear filter'),'fontSize':lit('9D'),'fontFamily':txt('Segoe UI Semibold'),'fontColor':solid('#D9D9D9'),'horizontalAlignment':txt('center'),'verticalAlignment':txt('middle'),'leftMargin':lit('0D'),'rightMargin':lit('0D'),'topMargin':lit('0D'),'bottomMargin':lit('0D')}}],'icon':[{'selector':{'id':'default'},'properties':{'show':lit('false')}}],'fill':[{'selector':{'id':state},'properties':{'show':lit('true'),'fillColor':solid('#303366'),'transparency':lit('0D')}} for state in ['default','hover','selected']],'outline':[{'selector':{'id':state},'properties':{'show':lit('true'),'lineColor':solid('#D9D9D9' if state=='hover' else '#2A3A4A'),'weight':lit('1D')}} for state in ['default','hover','selected']],'shape':[{'properties':{'tileShape':txt('rectangleRounded'),'rectangleRoundedCurve':lit('4D')}}]}
for key in ['text','fill','outline','icon']:
 props=copy.deepcopy(obj[key][0]['properties']);obj[key]=[{'properties':copy.deepcopy(props)}]+[{'selector':{'id':state},'properties':copy.deepcopy(props)} for state in ['default','hover','selected','disabled']]
c={'name':'clear_partner_filter','layouts':[{'id':0,'position':copy.deepcopy(button)}],'singleVisual':{'visualType':'actionButton','objects':obj,'vcObjects':vc}};button['config']=json.dumps(c,ensure_ascii=False);page['visualContainers'].append(button)
pc=json.loads(page['config']);rels=pc.setdefault('relationships',[])
for old_visual in before['sections'][0]['visualContainers']:
 name=json.loads(old_visual['config'])['name'];rels.append({'source':name,'target':'indicator_filter_context','type':1 if name=='severity' else 3})
page['config']=json.dumps(pc,ensure_ascii=False)
help_page=copy.deepcopy(next(s for s in d['sections'] if s['name']=='HelpIWDataDate'));help_page.update({'name':'HelpIWFilterContext','displayName':'Filter Context','id':max(s.get('id',0) for s in d['sections'])+1})
for v in help_page['visualContainers']:
 hc=json.loads(v['config']);heading=hc['name'].endswith('_heading');hc['name']='HelpIWFilterContext_'+('heading' if heading else 'body');ps=hc['singleVisual']['objects']['general'][0]['properties']['paragraphs'];ps[0]['textRuns'][0]['value']='Filter Context' if heading else 'The first count is the Indicators currently displayed. The second is the total loaded. The partner name shows the active selection. Clear filter restores all Indicators without changing table sorting.'
 for para in ps:
  for run in para['textRuns'][1:]:run['value']=''
 v['config']=json.dumps(hc,ensure_ascii=False)
d['sections'].append(help_page)
assert page['visualContainers'][:-2]==before['sections'][0]['visualContainers'];assert d['sections'][1:-1]==before['sections'][1:]
parts['Report/Layout']=json.dumps(d,ensure_ascii=False).encode('utf-16-le');parts.pop('SecurityBindings',None);infos.pop('SecurityBindings',None);infos['DataModel'].compress_type=zipfile.ZIP_STORED
with zipfile.ZipFile(candidate,'w') as z:
 for n,b in parts.items():z.writestr(infos[n],b)
with zipfile.ZipFile(candidate) as z:assert z.testzip() is None
oldm=ModelReader(str(p));newm=ModelReader(str(candidate))
for table in ['Unreported I&W','Snapshot','Reported I&W (5 days)','Indicator Partners']:assert oldm.get_table(table)==newm.get_table(table),table
state={'candidate':str(candidate),'work':str(work),'original_sha256':hashlib.sha256(raw).hexdigest(),'bookmark':bookmark_name};(work/'state.json').write_text(json.dumps(state,indent=2));print(json.dumps(state))
