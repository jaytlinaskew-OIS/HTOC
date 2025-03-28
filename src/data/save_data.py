import pandas as pd
import os


def save_data(data: pd.DataFrame, file_path: str):
    data.to_csv(file_path, index=False)
    
def save_json(data: pd.DataFrame, file_path: str):
    data.to_json(file_path, orient='records', lines=True)

def save_processed_data(data: pd.DataFrame, filename: str, file_format: str = "csv"):
    """
    Save a DataFrame to the `data/processed` folder.

    Args:
        data (pd.DataFrame): The DataFrame to save.
        filename (str): The name of the file (without extension).
        file_format (str): The format to save the file in ("csv" or "json"). Default is "csv".

    Returns:
        str: The full path of the saved file.
    """
    # Define the processed data directory
    processed_dir = "data/processed"

    # Ensure the directory exists
    os.makedirs(processed_dir, exist_ok=True)

    # Construct the full file path
    file_path = os.path.join(processed_dir, f"{filename}.{file_format}")

    # Save the file in the specified format
    if file_format == "csv":
        data.to_csv(file_path, index=False)
    elif file_format == "json":
        data.to_json(file_path, orient="records", lines=True)
    else:
        raise ValueError("Unsupported file format. Use 'csv' or 'json'.")

    print(f"Data saved to {file_path}")
    return file_path