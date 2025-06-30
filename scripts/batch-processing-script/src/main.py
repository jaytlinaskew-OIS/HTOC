import os
import pandas as pd
from data_loader import group_and_merge_by_opdiv, load_files, generate_date_list, preprocess_data
from feature_engineering import build_features
from model import get_model_outputs
from ensemble import add_rule_and_ensemble, add_confidence_and_format, build_production_output
from forecast_log import update_horizontal_forecast_log

def main():
    today = pd.Timestamp.today().date()

    prediction_path = r'Z:\HTOC\Data_Analytics\Data\OpDiv_Predictions'
    log_path = r'Z:\HTOC\Data_Analytics\Data\OpDiv_Predictions\Logs'

    opdiv_production_outputs = {}
    opdiv_forecast_logs = {}

    # Load data
    datelist = generate_date_list()
    src = load_files(datelist)
    src = preprocess_data(src)  # <--- Add this line

    # Group and merge by OpDiv, creating all user/date/indicator combinations
    opdiv_merged = group_and_merge_by_opdiv(src)

    # Process each OpDiv
    for opdiv_name, opdiv_df in opdiv_merged.items():
        opdiv_df = opdiv_df.copy()
        features_df = build_features(opdiv_df)
        output = get_model_outputs(features_df, opdiv_df)
        output = add_rule_and_ensemble(output)
        output = add_confidence_and_format(output)
        production_output = build_production_output(output)

        # Save production output
        opdiv_production_outputs[opdiv_name] = production_output

        # Update the log
        opdiv_log_dir = os.path.join(log_path, opdiv_name)
        os.makedirs(opdiv_log_dir, exist_ok=True)
        log_csv_path = os.path.join(opdiv_log_dir, f"{opdiv_name}_forecast_log.csv")
        forecast_log = update_horizontal_forecast_log(production_output, opdiv_df, log_csv_path)
        opdiv_forecast_logs[opdiv_name] = forecast_log

        # Save updated forecast log
        forecast_log.to_csv(log_csv_path, index=False)

        # Save today's prediction CSV
        opdiv_output_dir = os.path.join(prediction_path, opdiv_name)
        os.makedirs(opdiv_output_dir, exist_ok=True)
        output_csv_path = os.path.join(opdiv_output_dir, f"{opdiv_name}_output_{today.strftime('%Y%m%d')}.csv")
        production_output.to_csv(output_csv_path, index=False)

if __name__ == "__main__":
    main()