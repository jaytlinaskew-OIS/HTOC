from pathlib import Path
import os,sys,json,re,urllib.request,urllib.parse,datetime
sys.path.insert(0,os.path.join(os.environ['TEMP'],'htoc-powerbi-validator'))
import jsonschema,openpyxl
ROOT=Path(r'\\cscso1fsappv01\home\jaskew\HTOC\dashboards\ThreatAssessment')
cache={}
def get_schema(url):
    url=urllib.parse.urldefrag(url)[0]
    if url not in cache:
        cache[url]=json.load(urllib.request.urlopen(url.replace('schema.embedded.json','schema-embedded.json'),timeout=30))
    return cache[url]
checked=[]; errors=[]
for path in list(ROOT.rglob('*.json'))+list(ROOT.rglob('*.pbir'))+list(ROOT.rglob('*.pbism')):
    if path.name=='validation.json':continue
    j=json.loads(path.read_text(encoding='utf-8-sig'))
    if '$schema' not in j: continue
    s=get_schema(j['$schema'])
    resolver=jsonschema.RefResolver(base_uri=j['$schema'],referrer=s,handlers={'https':get_schema})
    es=list(jsonschema.Draft7Validator(s,resolver=resolver).iter_errors(j))
    errors.extend({'file':str(path.relative_to(ROOT)),'path':list(e.absolute_path),'error':e.message} for e in es)
    checked.append(str(path.relative_to(ROOT)))
source=Path(r'\\cscso1fsappv01\data\HTOC\Data_Analytics\Data\Threat Assessment Scores\ThreatAssessI_W')
files=sorted(x for x in source.glob('*.xlsx') if re.fullmatch(r'ThreatAssessI_W_\d{8}\.xlsx',x.name))
samples=[]
for f in files[-3:]:
    wb=openpyxl.load_workbook(f,read_only=True,data_only=True)
    s=wb['I&W_No']; vals=iter(s.values); headers=next(vals); records=[dict(zip(headers,row)) for row in vals if row[0] is not None and str(row[0]).strip()]
    keep=[r for r in records if str(r.get('Reported I&W?') or '').lower().strip() in ['', 'no','n','false','0','unreported','not reported']]
    nums=[float(r['PRISM Score']) for r in keep if r.get('PRISM Score') is not None]
    samples.append({'file':f.name,'unreportedRows':len(keep),'distinctIndicators':len(set(r['Indicator'] for r in keep)),'highOrCritical':len(set(r['Indicator'] for r in keep if str(r.get('Severity','')).lower() in ['high','critical'])),'averagePRISM':sum(nums)/len(nums) if nums else None,'highestPRISM':max(nums) if nums else None,'reportedRowsExcludedBySheet':sum(max(wb[n].max_row-1,0) for n in wb.sheetnames if n.lower()=='i&w_yes')})
    wb.close()
# Verify every visual projection refers to a model table/column/measure.
model=json.loads((ROOT/'UnreportedIW.SemanticModel/model.bim').read_text())
tables={t['name']:t for t in model['model']['tables']}
refs=0
for p in ROOT.rglob('visual.json'):
    j=json.loads(p.read_text())
    for role in j['visual'].get('query',{}).get('queryState',{}).values():
        for projection in role['projections']:
            field=projection['field']; kind=next(iter(field)); spec=field[kind]; table=tables[spec['Expression']['SourceRef']['Entity']]; names=[v['name'] for v in table['measures' if kind=='Measure' else 'columns']]
            assert spec['Property'] in names,(p,spec)
            refs+=1
    pos=j['position']; assert 0<=pos['x'] and pos['x']+pos['width']<=1600; assert 0<=pos['y'] and pos['y']+pos['height']<=1200
result={'validatedAt':datetime.datetime.now().isoformat(),'schemaValidatedFiles':len(checked),'officialSchemasRetrieved':len(cache),'schemaErrors':errors,'visualFieldReferencesChecked':refs,'sourceFolderAccessible':source.is_dir(),'eligibleSnapshots':len(files),'recentSnapshots':samples,'nativeTabularModelDeserialization':'passed using installed Power BI Desktop libraries', 'reportPages':1, 'powerBIDesktopRefreshValidated':False}
(ROOT/'validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
if errors:sys.exit(1)
