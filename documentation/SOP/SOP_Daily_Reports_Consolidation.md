# Standard Operating Procedure
## Daily Partner Prediction Report Consolidation — daily_reports

| Field | Detail |
|---|---|
| **SOP Title** | Daily Partner Prediction Report Consolidation |
| **Notebook** | GitHub: [`notebooks/observationEventForecasting/daily_reports.ipynb`](https://github.com/jaytlinaskew-OIS/HTOC/blob/main/notebooks/observationEventForecasting/daily_reports.ipynb) |
| **Batch Script** | GitHub: [`scripts/batch-processing-script/Next_Obs_Daily/src/main.py`](https://github.com/jaytlinaskew-OIS/HTOC/blob/main/scripts/batch-processing-script/Next_Obs_Daily/src/main.py) |
| **Owner** | HTOC Data Analytics |
| **Last Reviewed** | April 2026 |
| **Input** | Partner prediction CSVs `Z:\HTOC\Data_Analytics\Data\OpDiv_Predictions\{PartnerName}\{YYYYMMDD}.csv` |
| **Output** | Consolidated CSV `Z:\HTOC\Data_Analytics\Data\OpDiv_Predictions\Full Daily Reports\full_daily_report_{YYYYMMDD}.csv` |
| **Current Schedule** | Executed daily at **8:15 AM** via Windows Task Scheduler on **F.R.E.D** |
| **Associated Batch Files** | None documented; automated path executes `scripts/batch-processing-script/Next_Obs_Daily/src/main.py` directly |

---

## 1. Purpose

This SOP describes the daily consolidation of per-partner NOI (Next Observed Indicator) prediction CSVs into a single full daily report. Each day, partner-specific prediction files are written to subfolders under the `OpDiv_Predictions` directory. This process discovers those files, merges them into one consolidated dataset, and writes a dated output CSV to the `Full Daily Reports` folder.

This process has two execution paths:

| Path | Use When |
|---|---|
| **Automated batch script** (`main.py`) | Normal daily operations — runs automatically on a schedule |
| **Interactive notebook** (`daily_reports.ipynb`) | Manual runs, troubleshooting, or backfilling historical dates |

---

## 2. Scope

This procedure applies to HTOC analysts and data engineers who run, monitor, or troubleshoot the daily prediction report consolidation. It covers both the automated script path and the interactive notebook path.

---

## 3. Prerequisites

### 3.1 Environment

| Requirement | Notes |
|---|---|
| Python 3.x | Must be available in the environment where `main.py` executes |
| pandas | CSV loading and concatenation |
| numpy | Indirect dependency |
| Access to `Z:\HTOC\Data_Analytics\` | All input and output paths are on this share |

Example dependency install command:
```powershell
pip install pandas
```

### 3.2 Input Data

Partner prediction CSVs must be present under the `OpDiv_Predictions` directory tree **before** this process runs. These files are produced by the NOI forecasting pipeline (`NextObservedIndicatorV3.0.ipynb` / its scheduled batch equivalent). See `SOP_NextObservedIndicator_Forecasting.md` for details on that upstream process.

Expected input file naming convention:
```
Z:\HTOC\Data_Analytics\Data\OpDiv_Predictions\{PartnerName}\{YYYYMMDD}.csv
```

---

## 4. Key Configuration

Both the notebook and `main.py` share the same path constants:

| Constant | Value |
|---|---|
| `DATA_PATH` | `Z:\HTOC\Data_Analytics\Data\OpDiv_Predictions` |
| `SAVE_PATH` | `Z:\HTOC\Data_Analytics\Data\OpDiv_Predictions\Full Daily Reports` |
| `EXCLUDE_FOLDERS` | `automation scripts`, `Logs`, `LogsBackup`, `Full Daily Reports` |

The `EXCLUDE_FOLDERS` set prevents the loader from reading its own output or log directories during the folder walk.

---

## 5. How the Process Works

### 5.1 File Discovery

The loader uses `os.walk` to recursively traverse all subfolders under `DATA_PATH`. For each directory, it:

1. Skips any path containing a folder name in `EXCLUDE_FOLDERS`.
2. Treats the **immediate folder name** as the `Partner` value.
3. Matches files whose names end with `{YYYYMMDD}.csv` — in the automated path, only **today's** date is matched.

### 5.2 Consolidation

For each matched file:
- The CSV is read into a DataFrame.
- Two columns are added: `Partner` (from the folder name) and `FileDate` (from the filename date string).
- All per-partner DataFrames are concatenated into a single `daily_search` DataFrame.

If no files are found, the process prints `"No CSV files found for today."` and exits without writing an output file.

### 5.3 Output

The consolidated DataFrame is written to:
```
Z:\HTOC\Data_Analytics\Data\OpDiv_Predictions\Full Daily Reports\full_daily_report_{YYYYMMDD}.csv
```

The output file is **never overwritten** — if it already exists for today's date, the process prints `"File already exists: …"` and skips the write. This prevents duplicate runs from corrupting the report.

---

## 6. Automated Execution (main.py)

### 6.1 Schedule

`main.py` runs automatically every day at **8:15 AM** via **Windows Task Scheduler** on **F.R.E.D**. It executes the **today-only** consolidation flow: load today's partner CSVs → merge → save single consolidated report.

Manual execution (Section 7) is only necessary when troubleshooting a failed scheduled run, backfilling historical dates, or testing changes to the notebook before deployment.

### 6.2 Script Logic

```
main()
  ├── Compute today_str (YYYYMMDD)
  ├── load_all_csvs_from_folders(DATA_PATH, today_only=True)
  │     ├── Walk DATA_PATH, skip EXCLUDE_FOLDERS
  │     ├── Match files: {today_str}.csv only
  │     ├── Add Partner and FileDate columns
  │     └── Return concatenated DataFrame (or empty if none found)
  └── If DataFrame is non-empty:
        └── save_daily_report(df, SAVE_PATH, today_str)
              ├── Build output path: full_daily_report_{today_str}.csv
              ├── If file exists → print and skip
              └── Else → makedirs + to_csv + print path
```

### 6.3 Verifying a Successful Automated Run

Confirm the run succeeded by checking that:
1. The file `full_daily_report_{YYYYMMDD}.csv` exists in `Full Daily Reports` for today's date.
2. The file is non-empty and contains the expected `Partner` and `FileDate` columns.

---

## 7. Manual / Interactive Execution (Notebook)

Use `daily_reports.ipynb` when you need to run the consolidation manually, troubleshoot a failed automated run, or backfill reports for historical dates.

### 7.1 Open the Notebook

1. Open **Cursor** (or VS Code / JupyterLab).
2. Navigate to `H:\HTOC\notebooks\observationEventForecasting\`.
3. Open `daily_reports.ipynb`.

### 7.2 Verify Prerequisites

- [ ] `Z:\HTOC\Data_Analytics\` is accessible and mapped.
- [ ] Partner prediction CSVs for the target date exist under `Z:\HTOC\Data_Analytics\Data\OpDiv_Predictions\`.

### 7.3 Standard Run — Today's Report

Run **Cell 0** and **Cell 1** in order:

- **Cell 0** loads today's partner CSVs and displays the consolidated `daily_search` DataFrame.
- **Cell 1** saves `full_daily_report_{today_str}.csv` to the `Full Daily Reports` folder (skips if already exists).

**Verify:** After Cell 0, `daily_search` should be non-empty and display rows from multiple partners. After Cell 1, confirm the output path is printed.

### 7.4 Backfill Run — All Historical Dates

> **Note:** Cells 2 and 3 contain valid Python code but are currently stored as **markdown cells** in the notebook. To use them, convert each to a code cell first (`Cell` → `Cell Type` → `Code` in JupyterLab, or click the cell type selector in VS Code).

- **Cell 2** redefines `load_all_csvs_from_folders` to match **all** dated CSVs (not just today's) and reloads `daily_search` with the full history.
- **Cell 3** loops over each unique `FileDate` in `daily_search` and writes a separate `full_daily_report_{FileDate}.csv` for each date.

Use this path when catching up after missed days or rebuilding the `Full Daily Reports` archive.

---

## 8. Output File

| Detail | Value |
|---|---|
| Location | `Z:\HTOC\Data_Analytics\Data\OpDiv_Predictions\Full Daily Reports\` |
| Filename | `full_daily_report_{YYYYMMDD}.csv` |
| Overwrite behavior | Never overwritten — skipped if already exists |
| Key added columns | `Partner` (source folder name), `FileDate` (from filename) |

The output file contains all prediction columns from the upstream NOI forecasting output, with `Partner` and `FileDate` appended for traceability.

---

## 9. Troubleshooting

| Symptom | Likely Cause | Resolution |
|---|---|---|
| `"No CSV files found for today."` | Partner prediction CSVs not yet written for today | Verify the NOI forecasting pipeline ran successfully; check `Z:\HTOC\Data_Analytics\Data\OpDiv_Predictions\` for today's files |
| `"File already exists: …"` | Automated run already completed successfully | No action needed; this is the expected idempotency guard |
| `"No data to save."` | `daily_search` is empty after loading | Same as above — check upstream prediction files |
| Output file is missing partners | One or more partner subfolders had no matching file | Check the partner's subfolder for a `{YYYYMMDD}.csv` file; the loader skips unreadable files but prints a skip message |
| `Skipping {path}: …` printed | A CSV file could not be read (encoding, permissions, corruption) | Inspect the file at the printed path; re-run after fixing or removing the corrupt file |
| Backfill cells (2 & 3) don't execute | Cells are stored as markdown type | Convert cells 2 and 3 to code cells before running |
| `Z:\` path not found | Network drive not mapped | Map the `Z:\` drive to `\\cscso1fsappv01\...` and re-run |

---

## 10. Relationship to Other Processes

This process sits **downstream** of the NOI forecasting pipeline and **upstream** of any reporting or distribution that consumes the consolidated daily file.

| Step | Process | Output |
|---|---|---|
| 1 | NOI forecasting pipeline (`NextObservedIndicatorV3.0.ipynb` or batch equivalent) runs first | Partner-level daily files: `Z:\HTOC\Data_Analytics\Data\OpDiv_Predictions\{PartnerName}\{YYYYMMDD}.csv` |
| 2 | Daily reports consolidation process (`main.py` or `daily_reports.ipynb`) runs second | Consolidated daily file: `Z:\HTOC\Data_Analytics\Data\OpDiv_Predictions\Full Daily Reports\full_daily_report_{YYYYMMDD}.csv` |
| 3 | Downstream reporting/distribution jobs consume the consolidated file | Partner distribution products and operational reports |

If the daily report is missing or incomplete, check the NOI forecasting step first before rerunning this process.

---

## 11. Appendix - Standalone Python Script

The complete standalone script extracted from the notebook is attached at:

`H:\HTOC\documentation\SOP\Appendix Scripts\daily_reports_standalone.py`

Run with:

```powershell
&"C:\Program Files\Python313\python.exe" "H:\HTOC\documentation\SOP\Appendix Scripts\daily_reports_standalone.py"
```

---

## 12. Related Documents

- `SOP_NextObservedIndicator_Forecasting.md` — upstream process that generates the per-partner input CSVs
- `Z:\HTOC\Data_Analytics\Data\OpDiv_Predictions\` (input data location)
- `Z:\HTOC\Data_Analytics\Data\OpDiv_Predictions\Full Daily Reports\` (output location)
- `scripts/batch-processing-script/Next_Obs_Daily/src/main.py` — production batch script
