"""
Auto-generated standalone script from notebook.
Generated for SOP appendix use.
"""

# Fallback display for non-Jupyter execution
try:
    from IPython.display import display
except Exception:
    def display(obj):
        try:
            if hasattr(obj, "head"):
                print(obj.head())
            else:
                print(obj)
        except Exception:
            print(obj)


# ==== Cell 1 ====
import os
import pandas as pd
from datetime import datetime
import re

data_path_specific = r'Z:\HTOC\Data_Analytics\Data\OpDiv_Predictions'

def load_all_csvs_from_folders(root_path):
    """
    Recursively loads only today's CSV files from all subfolders under root_path into a single DataFrame.
    Excludes folders with titles 'automation scripts', 'Logs', or 'LogsBackup'.
    Adds columns 'Partner' (from folder name) and 'FileDate' (from filename, if present in YYYYMMDD format).
    Each CSV is expected to have the same structure.
    """
    exclude_folders = {'automation scripts', 'Logs', 'LogsBackup','Full Daily Reports'}
    all_dfs = []
    today_str = datetime.today().strftime("%Y%m%d")
    date_pattern = re.compile(rf'({today_str})\.csv$', re.IGNORECASE)
    for dirpath, dirnames, filenames in os.walk(root_path):
        if any(ex in os.path.normpath(dirpath).split(os.sep) for ex in exclude_folders):
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

daily_search = load_all_csvs_from_folders(data_path_specific)
    
display(daily_search)


# ==== Cell 2 ====
save_path = r'Z:\HTOC\Data_Analytics\Data\OpDiv_Predictions\Full Daily Reports'

today_str = datetime.today().strftime("%Y%m%d")

output_path = os.path.join(save_path, f"full_daily_report_{today_str}.csv")
if os.path.exists(output_path):
    print(f"File already exists: {output_path}")
else:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    daily_search.to_csv(output_path, index=False)
    print(f"Saved to {output_path}")
