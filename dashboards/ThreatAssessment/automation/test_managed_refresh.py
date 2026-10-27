"""Regression tests using copies of real reports; source files are never edited."""
import datetime as dt
from pathlib import Path
import shutil,tempfile,unittest
import managed_refresh as m
ROOT=Path(r'\\cscso1fsappv01\data\HTOC\Data_Analytics\Data\Threat Assessment Scores\ThreatAssessI_W')
TEMPLATE=ROOT/'Dashboard/Dashobard.pbix'
class RefreshTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.schema=m.table_schema(m.ModelReader(str(TEMPLATE)))
 def test_latest_empty_clears_prior_records(self):
  tables=m.load_tables([(dt.date(2026,10,26),ROOT/'ThreatAssessI_W_20261026.xlsx')],dt.date(2026,10,26),self.schema)
  self.assertEqual(tables['Unreported I&W'],[]);self.assertEqual(tables['Indicator Partners'],[])
 def test_new_report_drop_replaces_earlier_snapshot(self):
  with tempfile.TemporaryDirectory() as t:
   folder=Path(t);shutil.copy2(ROOT/'ThreatAssessI_W_20261021.xlsx',folder/'ThreatAssessI_W_20261024.xlsx')
   self.assertEqual(m.reports(folder,dt.date(2026,10,26))[0][0],dt.date(2026,10,24))
   shutil.copy2(ROOT/'ThreatAssessI_W_20261026.xlsx',folder/'ThreatAssessI_W_20261026.xlsx')
   needed=m.reports(folder,dt.date(2026,10,26));tables=m.load_tables(needed,dt.date(2026,10,26),self.schema)
   self.assertEqual(tables['Unreported I&W'],[])
 def test_multirecord_partner_links_are_exact(self):
  tables=m.load_tables([(dt.date(2026,9,25),ROOT/'ThreatAssessI_W_20260925.xlsx')],dt.date(2026,9,25),self.schema)
  self.assertEqual(len(tables['Unreported I&W']),7)
  expected={(r['Indicator'],p.strip()) for r in tables['Unreported I&W'] for p in r['Partners'].split(',')}
  actual={(r['Indicator'],r['Partner']) for r in tables['Indicator Partners']};self.assertEqual(actual,expected)
  self.assertEqual(len(tables['Indicator Partners']),len(actual))
 def test_single_record_keeps_partners(self):
  tables=m.load_tables([(dt.date(2026,10,21),ROOT/'ThreatAssessI_W_20261021.xlsx')],dt.date(2026,10,21),self.schema)
  self.assertEqual(len(tables['Unreported I&W']),1);self.assertEqual({r['Partner'] for r in tables['Indicator Partners']},{'HHS','HRSA','IHS','OS'})
 def test_reported_dedupe_and_window(self):
  path=ROOT/'ThreatAssessI_W_20261023.xlsx'
  tables=m.load_tables([(dt.date(2026,10,26),ROOT/'ThreatAssessI_W_20261026.xlsx'),(dt.date(2026,10,23),path),(dt.date(2026,10,22),path),(dt.date(2026,9,25),ROOT/'ThreatAssessI_W_20260925.xlsx')],dt.date(2026,10,26),self.schema)
  self.assertEqual(len(tables['Reported I&W (5 days)']),3)
 def test_future_and_backup_files_ignored(self):
  with tempfile.TemporaryDirectory() as t:
   folder=Path(t)
   for name in ['ThreatAssessI_W_20261026.xlsx','ThreatAssessI_W_20261027.xlsx','ThreatAssessI_W_20261026_ORIG.xlsx','ThreatAssessI_W_20260230.xlsx']:(folder/name).touch()
   self.assertEqual([p.name for _,p in m.reports(folder,dt.date(2026,10,26))],['ThreatAssessI_W_20261026.xlsx'])
 def test_invalid_scores_are_rejected(self):
  for score in [-1,1001,float('nan'),float('inf')]:
   with self.assertRaises(ValueError):m.convert(score,'Double','PRISM Score')
 def test_rollover_changes_manifest_without_new_file(self):
  before,_=m.source_manifest(ROOT,TEMPLATE,dt.date(2026,10,26));after,_=m.source_manifest(ROOT,TEMPLATE,dt.date(2026,10,27));self.assertNotEqual(before,after)
if __name__=='__main__':unittest.main()
