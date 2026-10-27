from pathlib import Path
import copy,zipfile,sqlite3
from pbix_mcp.formats.datamodel_roundtrip import decompress_datamodel,compress_datamodel
from pbix_mcp.formats.abf_rebuild import list_abf_files,read_metadata_sqlite,read_abf_file,_ABFStructure,_rebuild_abf

def restore_blank_dictionary(dm, donor_path):
 abf=decompress_datamodel(dm);files=list_abf_files(abf);names={f['FileName'].lower() for f in files};db=sqlite3.connect(':memory:');db.deserialize(read_metadata_sqlite(abf));missing=[r[0] for r in db.execute('SELECT FileName FROM StorageFile') if r[0] and r[0].lower() not in names];db.close()
 if not missing:return dm
 assert all(n.endswith('.dictionary') and '.incidents/events ' in n for n in missing),missing
 donor_path=Path(donor_path)
 if not donor_path.exists():
  archived=sorted((donor_path.parent/'Deprecated').glob('*/'+donor_path.name))
  if not archived:raise FileNotFoundError('Dictionary recovery source not found: '+str(donor_path))
  donor_path=archived[-1]
 with zipfile.ZipFile(donor_path) as z:donor_abf=decompress_datamodel(z.read('DataModel'))
 donor_files={f['FileName'].lower():f for f in list_abf_files(donor_abf)};struct=_ABFStructure(abf);replacements={}
 for i,name in enumerate(missing):
  source=donor_files[name.lower()];content=read_abf_file(donor_abf,source);assert len(content)==65,'Only the known empty dictionary may be restored'
  template_entry=next(f for f in files if f['FileName'].endswith('.dictionary'))
  group=next(g for g in struct.backup_log_root.findall('FileGroups/FileGroup') if any(b.findtext('StoragePath')==template_entry['StoragePath'] for b in g.findall('FileList/BackupFile')))
  log=next((b for b in group.findall('FileList/BackupFile') if b.findtext('Path','').endswith('\\'+name)),None)
  if log is None:
   template_log=next(b for b in group.findall('FileList/BackupFile') if b.findtext('StoragePath')==template_entry['StoragePath']);log=copy.deepcopy(template_log);log.find('Path').text=template_log.findtext('Path').rsplit('\\',1)[0]+'\\'+name;log.find('StoragePath').text='CodexRestoredDictionary_'+str(i);group.find('FileList').append(log)
  sp=log.findtext('StoragePath');log.find('Size').text=str(len(content));entry=copy.deepcopy(struct.data_entries[0]);entry.path=sp;entry.size=len(content);entry.m_cbOffsetHeader=0;entry.delete=False;struct.data_entries.append(entry);replacements[sp]=content
 repaired=_rebuild_abf(struct,replacements);newfiles={f['FileName']:f for f in list_abf_files(repaired)}
 for f in files:assert read_abf_file(abf,f)==read_abf_file(repaired,newfiles[f['FileName']]),f['FileName']
 assert read_metadata_sqlite(abf)==read_metadata_sqlite(repaired)
 assert all(n in newfiles for n in missing)
 return compress_datamodel(repaired)
