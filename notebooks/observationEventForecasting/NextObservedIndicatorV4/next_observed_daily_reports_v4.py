r"""
Next Observed Daily Reports — V4 test consolidator.

Reads per-OpDiv forecast CSVs from NextObserveV4Test and writes a single
full_daily_report_YYYYMMDD.csv under NextObserveV4Test\Full Daily Reports.

Does NOT touch production OpDiv_Predictions / existing Daily Reports task.

Expected inputs (from NextObservedIndicatorV4):
  {SAVE_ROOT}\{OpDiv}\{OpDiv}_output_YYYYMMDD.csv
"""

from __future__ import annotations

import os
import re
import sys
from datetime import datetime

import pandas as pd

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SAVE_ROOT = os.environ.get(
    "NOI_V4_SAVE_DIR",
    r"\\10.1.4.22\data\HTOC\JA\NextObserveV4Test",
)
DATA_PATH = SAVE_ROOT
SAVE_PATH = os.path.join(SAVE_ROOT, "Full Daily Reports")
EXCLUDE_FOLDERS = {"automation scripts", "Logs", "LogsBackup", "Full Daily Reports"}

# V4 forecast files look like: CMS_output_20260810.csv
# Also accept legacy-style YYYYMMDD.csv if present.
V4_NAME = re.compile(r"^.+_output_(\d{8})\.csv$", re.IGNORECASE)
LEGACY_NAME = re.compile(r"^(\d{8})\.csv$", re.IGNORECASE)


def load_all_csvs_from_folders(root_path: str, today_only: bool = True) -> pd.DataFrame:
    all_dfs: list[pd.DataFrame] = []
    today_str = datetime.today().strftime("%Y%m%d")

    if not os.path.isdir(root_path):
        print(f"FATAL: data root does not exist: {root_path}")
        sys.exit(2)

    for dirpath, dirnames, filenames in os.walk(root_path):
        parts = set(os.path.normpath(dirpath).split(os.sep))
        if parts & EXCLUDE_FOLDERS:
            continue
        partner = os.path.basename(dirpath)
        for fname in filenames:
            m = V4_NAME.match(fname) or LEGACY_NAME.match(fname)
            if not m:
                continue
            file_date = m.group(1)
            if today_only and file_date != today_str:
                continue
            fpath = os.path.join(dirpath, fname)
            try:
                df = pd.read_csv(fpath)
                df["Partner"] = partner
                df["FileDate"] = file_date
                all_dfs.append(df)
                print(f"loaded {fpath} ({len(df)} rows)")
            except Exception as e:
                print(f"Skipping {fpath}: {e}")

    if all_dfs:
        return pd.concat(all_dfs, ignore_index=True)
    print("No CSV files found for today.")
    return pd.DataFrame()


def save_daily_report(df: pd.DataFrame, save_path: str, today_str: str) -> str:
    os.makedirs(save_path, exist_ok=True)
    output_path = os.path.join(save_path, f"full_daily_report_{today_str}.csv")
    df.to_csv(output_path, index=False)
    print(f"Saved to {output_path} ({len(df)} rows)")
    return output_path


def main() -> int:
    today_str = datetime.today().strftime("%Y%m%d")
    print(f"DATA_PATH={DATA_PATH}")
    print(f"SAVE_PATH={SAVE_PATH}")
    print(f"today={today_str}")

    daily_search = load_all_csvs_from_folders(DATA_PATH, today_only=True)
    if daily_search.empty:
        print("No data to save.")
        # Not a hard failure during early V4 testing if forecast hasn't produced yet,
        # but scheduled chain should usually have files after 7:30 run.
        print("PIPELINE_OK_NOWORK")
        return 0

    out = save_daily_report(daily_search, SAVE_PATH, today_str)
    if not os.path.exists(out):
        print(f"FATAL: expected report missing: {out}")
        return 3
    print("PIPELINE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
