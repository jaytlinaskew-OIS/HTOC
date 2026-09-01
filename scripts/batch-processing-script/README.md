# Batch processing scripts

Scheduled jobs that still run outside `htoc_ml`. Live Task Scheduler launchers:

| Folder | Job |
|---|---|
| `NextObserved/` | Older ensemble forecast into `OpDiv_Predictions` (8:15 AM partner path; separate from NOI V4) |
| `Next_Obs_Daily/` | Consolidates those OpDiv prediction CSVs |
| `Tipper/` | Daily partner indicator tips (`run_tipper.bat`) |

I&W batch reporting was archived to `archive/production_20260831/I&W_Reporting_Batch/`
(see `notebooks/I&W Reporting/README.md`). NOI V4 and PRISM live under `notebooks/`
until those `.bat` files are pointed at `htoc_ml`.
