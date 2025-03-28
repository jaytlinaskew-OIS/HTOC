import pandas as pd
import requests

def load_data(file_path: str) -> pd.DataFrame:
    data = pd.read_csv(file_path)
    return data

def load_json(file_path: str) -> pd.DataFrame:
    return pd.read_json(file_path)

def download_data(url: str, save_path: str):
    response = requests.get(url)
    with open(save_path, 'wb') as file:
        file.write(response.content)