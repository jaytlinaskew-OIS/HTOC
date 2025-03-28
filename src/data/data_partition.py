import pandas as pd
import os
from sklearn.model_selection import train_test_split

def split_data(data: pd.DataFrame, test_size: float = 0.2):
    train, test = train_test_split(data, test_size=test_size)
    return train, test

def get_metadata(data: pd.DataFrame) -> dict:
    return {
        "num_rows": data.shape[0],
        "num_columns": data.shape[1],
        "columns": list(data.columns)
    }

def check_file_exists(file_path: str) -> bool:
    return os.path.exists(file_path)