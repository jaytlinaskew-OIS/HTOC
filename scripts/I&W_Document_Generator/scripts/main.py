import sys
import os
import pandas as pd
from datetime import datetime
from scripts.api_integration import fetch_indicators, process_indicators, initialize_api_client
from scripts.data_processing import process_data, get_file_paths, get_tc_config
from scripts.report_generator import generate_report

# Base file path with placeholder for date
base_path = r"Z:/HTOC/Data_Analytics/Data/OpDiv_Observations/htoc_opdiv_obs_d{date}.csv"
#base_path = r"C:\Users\jaskew\Documents\project_repository\data\raw\ObservationDataFiles\htoc_opdiv_obs_d{date}.csv"

# Load API config
project_root = r"C:\Users\jaskew\Documents\project_repository\scripts\I&W_Document_Generator"
if project_root not in sys.path:
    sys.path.append(project_root)

config_path = os.path.join(project_root, "utils", "config.json")

def main():

    tc_config = get_tc_config()
    # Initialize API client (configuration handled internally)
    tc = initialize_api_client(tc_config)
        
    # Fetch indicators
    try:
        indicators = fetch_indicators(tc)
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

        generate_report(vt_df, otx_df, processed_data)
        print(f"Report generated at: {report_path}")
    except Exception as e:
        print(f"[ERROR] Failed to generate report: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()