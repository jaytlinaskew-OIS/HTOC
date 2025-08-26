import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

import os
import pandas as pd

def load_files(filenames):
    dataframes = []
    for path in filenames:
        if os.path.exists(path):
            try:
                df = pd.read_csv(path)
                dataframes.append(df)
            except Exception as e:
                print(f"Error reading {path!r}: {e}")
        else:
            print(f"File {path!r} does not exist. Skipping.")

    if not dataframes:
        print("No input files found—returning empty DataFrame.")
        return pd.DataFrame()

    return pd.concat(dataframes, ignore_index=True)


def load_data(file_path_template, start_date, end_date):
    date_format = "%Y%m%d"
    dates_to_pull = pd.date_range(start_date, end_date, freq='D')
    datelist = [file_path_template.format(date=dt.strftime(date_format)) for dt in dates_to_pull]
    return load_files(datelist)

def generate_date_list(n_days=100):
    today = datetime.today()
    start_date = today - timedelta(days=n_days)
    date_format = "%Y%m%d"
    file_path_template = r"\\10.1.4.22\data\HTOC\Data_Analytics\Data\OpDiv_Observations\htoc_opdiv_obs_d{date}.csv"
    dates_to_pull = pd.date_range(start_date, today, freq='D')
    datelist = [file_path_template.format(date=dt.strftime(date_format)) for dt in dates_to_pull]
    return datelist

def preprocess_data(df):
    if 'indicator' in df.columns:
        df['indicator'] = df['indicator'].astype(str).str.split(' ', expand=True)[0].str.strip()
    if 'OpDiv' in df.columns:
        df['OpDiv'] = df['OpDiv'].astype(str).str.strip()
    df.drop(columns=['curr_date', 'indicator_key'], inplace=True, errors='ignore')
    df.rename(columns={'obs_date': 'date'}, inplace=True)
    df['date'] = pd.to_datetime(df['date'])
    return df.reset_index(drop=True)

def group_and_merge_by_opdiv(src):
    opdiv_groups = {opdiv: group for opdiv, group in src.groupby('OpDiv')}
    opdiv_merged = {}

    for opdiv, group_df in opdiv_groups.items():
        group_df['date'] = pd.to_datetime(group_df['date'])
        all_users = group_df['API_UserName'].unique()
        all_indicators = group_df['indicator'].unique()
        all_dates = pd.date_range(start=group_df['date'].min(), end=pd.Timestamp.now().normalize(), freq='D')
        all_combinations = pd.MultiIndex.from_product(
            [all_users, all_dates, all_indicators],
            names=['API_UserName', 'date', 'indicator']
        ).to_frame(index=False)
        all_combinations['OpDiv'] = opdiv  # Add OpDiv column

        merged = all_combinations.merge(group_df, how='left', on=['API_UserName', 'date', 'indicator', 'OpDiv'])
        merged['observations'] = merged['observations'].fillna(0).astype(int)
        merged['date'] = pd.to_datetime(merged['date'])
        merged['dayofweek'] = merged['date'].dt.dayofweek
        merged['is_weekend'] = merged['dayofweek'].isin([5, 6])
        merged['day'] = merged['date'].dt.day
        merged['month'] = merged['date'].dt.month
        merged['seen'] = (merged['observations'] > 0).astype(int)
        # Add total number of seen for each indicator
        seen_totals = merged.groupby('indicator')['seen'].sum().rename('total_seen')
        merged = merged.merge(seen_totals, on='indicator', how='left')
        # Filter out indicators seen only 1 time
        merged = merged[merged['total_seen'] > 1].reset_index(drop=True)
        opdiv_merged[opdiv] = merged
        

    return opdiv_merged