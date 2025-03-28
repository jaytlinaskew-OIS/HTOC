import pandas as pd

def load_data(file_path: str) -> pd.DataFrame:
    data = pd.read_csv(file_path)
    return data
