# main.py

import sys
from src.setup import initialize_threatconnect
from src.data_fetcher import fetch_indicators, normalize_data
from src.data_processor import filter_recent_data, clean_data
from src.config import get_logger

logger = get_logger(__name__)

def main(owner):
    # Initialize ThreatConnect
    tc = initialize_threatconnect()

    # Fetch data
    raw_data = fetch_indicators(tc, owner)
    logger.info(f"Fetched data for {owner}")

    # Normalize data
    normalized_data = normalize_data(raw_data)

    # Filter recent data
    recent_data = filter_recent_data(normalized_data)

    # Clean data
    cleaned_data = clean_data(recent_data)

    # Display data summary
    logger.info(f"Data processing complete. Processed {len(cleaned_data)} records.")
    print(cleaned_data.head())

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <OWNER>")
        sys.exit(1)

    owner_arg = sys.argv[1]
    main(owner_arg)
