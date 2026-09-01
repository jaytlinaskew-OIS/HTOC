# I&W Reporting Batch (archived 2026-09-01)

Snapshot of the four-script I&W staging pipeline and the spreadsheet test launcher.

| Folder | Launcher | Script |
|---|---|---|
| `I&W Spreadsheet/` | `run_iw_spreadsheet.bat`, `run_iw_spreadsheet_Test.bat` | `I&W_Spreadsheet.py` |
| `I&W Generator/` | `run_iw_generator.bat` | `I&W_Generator.py` |
| `I&W Expanded/` | `run_iw_expanded_spreadsheet.bat`, `run_iw_expanded_generator.bat` | `I&W_Document_expanded_*.py` |

Operator SOP: `documentation/SOP/SOP_IW_Batch_Reporting_Pipeline.md`.

Production Task Scheduler launchers on the staging host (`Z:\HTOC\...`) are unchanged.
