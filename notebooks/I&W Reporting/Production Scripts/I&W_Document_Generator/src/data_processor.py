# src/data_processor.py

import pandas as pd
from datetime import datetime, timedelta
from src.config import get_logger

logger = get_logger(__name__)

def filter_recent_data(df, days=2):
    """
    Filter data to include only the most recent observations within the given timeframe.
    """
    if df.empty:
        logger.warning("Dataframe is empty, skipping filtering.")
        return df

    # Calculate the cutoff timestamp
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    # Apply the filter
    recent_data = df[df['lastObserved'] >= cutoff_date]
    logger.info(f"Filtered data to {len(recent_data)} records from the last {days} days.")
    return recent_data


def clean_data(df):
    """
    Apply additional cleaning and processing steps to the data.
    """
    if df.empty:
        return df

    # Example cleaning: Remove rows where 'summary' is missing
    df = df.dropna(subset=['summary'])

    # Extract partner names and remove ' Splunk API' suffix
    df['partner'] = df['summary'].str.replace(' Splunk API', '', regex=False)

    return df
