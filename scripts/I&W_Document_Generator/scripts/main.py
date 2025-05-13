import sys
import os
import pandas as pd
from datetime import datetime
from scripts.config_loader import load_config
from scripts.api_integration import fetch_indicators, process_indicators, initialize_api_client
from scripts.data_processing import process_data, get_file_paths
from scripts.report_generator import generate_report

# Base file path with placeholder for date
base_path = r"Z:/HTOC/Data_Analytics/Data/OpDiv_Observations/htoc_opdiv_obs_d{date}.csv"
#base_path = r"C:\Users\jaskew\Documents\project_repository\data\raw\ObservationDataFiles\htoc_opdiv_obs_d{date}.csv"

def main():
    # Load API configuration
    project_root = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(project_root, "..", "utils", "config.json")
    
    try:
        api_secret_key, api_access_id, api_base_url, api_default_org = load_config(config_path)
        print(f"Loaded config from: {config_path}")
    except Exception as e:
        print(f"[ERROR] Failed to load configuration: {e}")
        sys.exit(1)

    #initialize API client
    try:
        ro = initialize_api_client(api_secret_key, api_access_id, api_base_url, api_default_org)
        print("API client initialized successfully.")
    except Exception as e:
        print(f"[ERROR] Failed to initialize API client: {e}")
        sys.exit(1)
        
    # Fetch indicators from the API
    try:
        indicators = fetch_indicators(ro)
        print(f"Fetched {len(indicators)} indicators.")
    except Exception as e:
        print(f"[ERROR] Failed to fetch indicators: {e}")
        sys.exit(1)

    observed_data = get_file_paths(base_path, days=3)

    # Process the fetched data
    try:
        processed_data = process_data(indicators, observed_data)
        processed_data
    except Exception as e:
        print(f"[ERROR] Failed to process data: {e}")
        sys.exit(1)

    # Generate report
    try:
        current_date = datetime.now().strftime("%Y-%m-%d")
        report_path = os.path.join(project_root, "..", "reports", f"IW_Report_{current_date}.docx")
        # Ensure processed_data is in the correct format
        if isinstance(processed_data, pd.DataFrame) and 'summary' in processed_data.columns:
            vt_df, otx_df = process_indicators(processed_data)
            print(f"Processed VirusTotal data: {len(vt_df)} records.")
            print(f"Processed OTX data: {len(otx_df)} records.")
        else:
            print("[ERROR] processed_data is not in the expected format.")
            sys.exit(1)

        generate_report(vt_df, otx_df)
        print(f"Report generated at: {report_path}")
    except Exception as e:
        print(f"[ERROR] Failed to generate report: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()