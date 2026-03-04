import pandas as pd

def validate_data(data: pd.DataFrame, required_columns: list) -> bool:
    return all(column in data.columns for column in required_columns)