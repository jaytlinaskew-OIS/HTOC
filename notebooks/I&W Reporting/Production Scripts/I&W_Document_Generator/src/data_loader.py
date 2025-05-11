# src/data_loader.py

import os
import pandas as pd
from datetime import datetime, timedelta
from src.config import RAW_DATA_DIR, get_logger

logger = get_logger(__name__)

def generate_file_paths(base_path, days=3):
    """ Generate file paths for the last `days` days. """
    date_format = "%Y%m%d"
    today = datetime.utcnow()
    dates = [(today - timedelta(days=i)).strftime(date_format) for i in range(days)]
    
    file_paths = [base_path.format(date=dt) for dt in dates]
    return [path for path in file_paths if os.path.exists(path)]

def load_observed_data(base_path, days=3):
    """ Load data from the last `days` days. """
    file_paths = generate_file_paths(base_path, days)
    
    data_frames = []
    for file_path in file_paths:
        try:
            df = pd.read_csv(file_path)
            data_frames.append(df)
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
    
    if data_frames:
        return pd.concat(data_frames, ignore_index=True)
    else:
        logger.warning("No data files found.")
        return pd.DataFrame()
