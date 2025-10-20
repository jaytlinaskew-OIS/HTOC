import os
import warnings
# Suppress pandas and lifelines warnings
warnings.filterwarnings("ignore", category=FutureWarning)
try:
    from lifelines.fitters import ApproximationWarning
    warnings.filterwarnings("ignore", category=ApproximationWarning)
except ImportError:
    pass

import pandas as pd
from data_loader import group_and_merge_by_opdiv, load_files, generate_date_list, preprocess_data
from feature_engineering import build_features
from model import get_model_outputs
from ensemble import add_rule_and_ensemble, add_confidence_and_format, build_production_output
from forecast_log import update_long_forecast_log_with_formatting

def main():
    today = pd.Timestamp.today().date()

    prediction_path = r'C:\Users\jaskew\Documents\Test Outputs'
    log_path = r'C:\Users\jaskew\Documents\Test Logs'

    opdiv_production_outputs = {}
    opdiv_forecast_logs = {}

    print(f"[START] Forecast pipeline initiated for {today}")

    # Load data
    print("[INFO] Generating date list and loading files...")
    datelist = generate_date_list()
    src = load_files(datelist)

    if src.empty:
        print("[WARN] No data loaded; exiting.")
        return

    print("[INFO] Preprocessing source data...")
    src = preprocess_data(src)

    print("[INFO] Grouping and merging data by OpDiv...")
    opdiv_merged = group_and_merge_by_opdiv(src)

    # Process each OpDiv
    for opdiv_name, opdiv_df in opdiv_merged.items():
        print(f"\n[PROCESSING] {opdiv_name}...")
        opdiv_df = opdiv_df.copy()

        # Debug: display first 5 records
        print(f"[DEBUG] {opdiv_name} - first 5 records:\n{opdiv_df.head(5)}")

        print(f"[{opdiv_name}] Building features...")
        features_df = build_features(opdiv_df)

        print(f"[{opdiv_name}] Running model inference...")
        output = get_model_outputs(features_df, opdiv_df)

        print(f"[{opdiv_name}] Applying ensemble logic and formatting...")
        output = add_rule_and_ensemble(output)
        output = add_confidence_and_format(output)
        production_output = build_production_output(output)

        print(f"[DEBUG] Production output - first 5 records:\n{production_output.head(5)}")

        opdiv_production_outputs[opdiv_name] = production_output

        print(f"[{opdiv_name}] Updating forecast log...")
        opdiv_log_dir = os.path.join(log_path, opdiv_name)
        os.makedirs(opdiv_log_dir, exist_ok=True)
        log_xlsx_path = os.path.join(opdiv_log_dir, f"{opdiv_name}_forecast_log.xlsx")
        forecast_log = update_long_forecast_log_with_formatting(production_output, opdiv_df, log_xlsx_path)
        opdiv_forecast_logs[opdiv_name] = forecast_log

        print(f"[{opdiv_name}] Saving updated forecast log to: {log_xlsx_path}")

        print(f"[{opdiv_name}] Saving today's production output...")
        opdiv_output_dir = os.path.join(prediction_path, opdiv_name)
        os.makedirs(opdiv_output_dir, exist_ok=True)
        output_csv_path = os.path.join(opdiv_output_dir, f"{opdiv_name}_output_{today.strftime('%Y%m%d')}.csv")
        production_output.to_csv(output_csv_path, index=False)

        print(f"[{opdiv_name}] Completed.")

    print("\n [COMPLETE] All OpDivs processed.")
    print("You may close this window now.")

if __name__ == "__main__":
    main()
