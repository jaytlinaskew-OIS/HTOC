Datapipeline runners (double-click or Task Scheduler -> *_hidden.vbs)
=====================================================================
run_threat_score_iw.bat   ThreatScoreIW I&W workbook
run_triage.bat            PRISM indicator triage
run_search_tags.bat       Search indicators by tags
run_iw_listing.bat        I&W listing from PDFs

Share probe helpers (ensure_htoc_data_share.bat) live next to these.
Logs go under bats\logs\<job>\.

Regenerate:
  cd htoc_ml
  py -3.13 -m htoc.datapipelines make-launcher --name threat-score-iw
