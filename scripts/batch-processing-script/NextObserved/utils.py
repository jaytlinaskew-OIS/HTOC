def load_csv(filepath):
    import pandas as pd
    return pd.read_csv(filepath)

def save_csv(df, filepath):
    df.to_csv(filepath, index=False)

def format_date(date):
    return date.strftime("%Y-%m-%d")

def calculate_days_since(last_seen_date):
    from datetime import datetime
    return (datetime.today() - last_seen_date).days

def check_file_exists(filepath):
    import os
    return os.path.exists(filepath)

def create_directory(directory):
    import os
    if not os.path.exists(directory):
        os.makedirs(directory)