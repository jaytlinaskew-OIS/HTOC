import numpy as np
import pandas as pd

def extract_time_series_features(group):
    series = group['seen'].values
    indices = np.where(series == 1)[0]
    if len(indices) == 0:
        return pd.Series({
            'last_seen': len(series),
            'freq_1': 0,
            'freq_7': 0,
            'freq_14': 0,
            'freq_30': 0,
            'freq_45': 0,
            'avg_gap': len(series),
            'burstiness': 0,
            'label_7': 0,
            'label_14': 0,
            'label_30': 0,
            'label_45': 0
        })
    last_seen = len(series) - 1 - indices[-1]
    freq_1 = np.sum(series[-1:])
    freq_7 = np.sum(series[-7:])
    freq_14 = np.sum(series[-14:])
    freq_30 = np.sum(series[-30:])
    freq_45 = np.sum(series[-45:])
    gaps = np.diff(indices)
    avg_gap = np.mean(gaps) if len(gaps) > 0 else len(series)
    burstiness = (np.std(gaps) - avg_gap) / (np.std(gaps) + avg_gap) if len(gaps) > 1 else 0

    label_7 = 1 if np.any(series[-7:]) else 0
    label_14 = 1 if np.any(series[-14:]) else 0
    label_30 = 1 if np.any(series[-30:]) else 0
    label_45 = 1 if np.any(series[-45]) else 0
    return pd.Series({
        'last_seen': last_seen,
        'freq_1': freq_1,
        'freq_7': freq_7,
        'freq_14': freq_14,
        'freq_30': freq_30,
        'freq_45': freq_45,
        'avg_gap': avg_gap,
        'burstiness': burstiness,
        'label_7': label_7,
        'label_14': label_14,
        'label_30': label_30,
        'label_45': label_45
    })

def build_features(df):
    features_df = df.groupby('indicator').apply(extract_time_series_features).reset_index()
    return features_df