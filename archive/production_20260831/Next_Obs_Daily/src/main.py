import os
import pandas as pd
from datetime import datetime
import re

DATA_PATH = r'Z:\HTOC\Data_Analytics\Data\OpDiv_Predictions'
SAVE_PATH = r'Z:\HTOC\Data_Analytics\Data\OpDiv_Predictions\Full Daily Reports'
EXCLUDE_FOLDERS = {'automation scripts', 'Logs', 'LogsBackup', 'Full Daily Reports'}

def load_all_csvs_from_folders(root_path, today_only=True):
    all_dfs = []
    today_str = datetime.today().strftime("%Y%m%d")
    if today_only:
        date_pattern = re.compile(rf'({today_str})\.csv$', re.IGNORECASE)
    else:
        date_pattern = re.compile(r'(\d{8})\.csv$', re.IGNORECASE)

    for dirpath, dirnames, filenames in os.walk(root_path):
        if any(ex in os.path.normpath(dirpath).split(os.sep) for ex in EXCLUDE_FOLDERS):
            continue
        partner = os.path.basename(dirpath)
        for fname in filenames:
            match = date_pattern.search(fname)
            if match:
                file_date = match.group(1)
                fpath = os.path.join(dirpath, fname)
                try:
                    df = pd.read_csv(fpath)
                    df['Partner'] = partner
                    df['FileDate'] = file_date
                    all_dfs.append(df)
                except Exception as e:
                    print(f"Skipping {fpath}: {e}")
    if all_dfs:
        return pd.concat(all_dfs, ignore_index=True)
    else:
        print("No CSV files found for today.")
        return pd.DataFrame()

def save_daily_report(df, save_path, today_str):
    output_path = os.path.join(save_path, f"full_daily_report_{today_str}.csv")
    if os.path.exists(output_path):
        print(f"File already exists: {output_path}")
    else:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"Saved to {output_path}")

def main():
    today_str = datetime.today().strftime("%Y%m%d")
    daily_search = load_all_csvs_from_folders(DATA_PATH, today_only=True)
    if not daily_search.empty:
        save_daily_report(daily_search, SAVE_PATH, today_str)
    else:
        print("No data to save.")

if __name__ == "__main__":
    main()