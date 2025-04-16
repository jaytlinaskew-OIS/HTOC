import os
import pandas as pd
from datetime import datetime

start_date = "20250101"  
end_date = "20250414" 
# Define the folder path and date range
folder_path = r"C:\Users\jaskew\Documents\project_repository\data\raw\ObservationDataFiles"

output_file = r"C:\Users\jaskew\Documents\project_repository\data\processed\ProcessedObservedData.csv"  

def get_files_by_date_range(folder_path, start_date, end_date):
    """
    Get a list of files in the folder that fall within the specified date range.
    
    Args:
        folder_path (str): Path to the folder containing the files.
        start_date (str): Start date in the format 'YYYYMMDD'.
        end_date (str): End date in the format 'YYYYMMDD'.
    
    Returns:
        list: List of file paths that match the date range.
    """
    files_in_range = []
    for file_name in os.listdir(folder_path):
        # Extract the date from the file name
        try:
            date_str = file_name.split('_')[-1].split('.')[0][1:]  # Extract date part
            file_date = datetime.strptime(date_str, '%Y%m%d')
            if datetime.strptime(start_date, '%Y%m%d') <= file_date <= datetime.strptime(end_date, '%Y%m%d'):
                files_in_range.append(os.path.join(folder_path, file_name))
        except (ValueError, IndexError):
            continue  # Skip files that don't match the expected format
    return files_in_range
def data_preprocessing(data):
    """
    Preprocess the data by cleaning and standardizing it.
    
    Args:
        data (pd.DataFrame): The input data to preprocess.
    
    Returns:
        pd.DataFrame: The preprocessed data.
    """
    # Cleaning up the data
    data['curr_date'] = pd.to_datetime(data['curr_date'])
    data['obs_date'] = pd.to_datetime(data['obs_date'])

    # Dropping the 'indicator_key' column
    data = data.drop(columns=['indicator_key'], inplace=True)
    
    return data

def merge_csv_files(file_list, output_file):
    """
    Merge multiple CSV files into one.
    
    Args:
        file_list (list): List of file paths to merge.
        output_file (str): Path to save the merged CSV file.
    """
    merged_data = pd.DataFrame()

    for file in file_list:
        data = pd.read_csv(file)
        merged_data = pd.concat([merged_data, data], ignore_index=True)
        data_preprocessing(merged_data)
    merged_data.to_csv(output_file, index=False)

if __name__ == "__main__":
    # Get files in the date range
    files_to_merge = get_files_by_date_range(folder_path, start_date, end_date)

    #prevent duplicate records in ProcessedObservedData from merging
    if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
        existing_data = pd.read_csv(output_file)
        existing_dates = set(existing_data['obs_date'].astype(str))
        files_to_merge = [file for file in files_to_merge if file.split('_')[-1].split('.')[0][1:] not in existing_dates]
        print(f"Filtered out {len(files_to_merge)} files already in {output_file}")
    elif os.path.exists(output_file):
        print(f"{output_file} exists but is empty. Proceeding without filtering existing dates.")

    # Merge the files
    if files_to_merge:
        merge_csv_files(files_to_merge, output_file)
        print(f"Merged {len(files_to_merge)} files into {output_file}")
    else:
        print("No files found in the specified date range.")