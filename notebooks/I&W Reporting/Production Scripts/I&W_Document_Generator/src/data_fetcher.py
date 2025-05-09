# src/data_fetcher.py

import requests
from src.config import VT_API_KEY, OTX_API_KEY, get_logger

logger = get_logger(__name__)

def fetch_virustotal_data(ip):
    """ Fetch data from VirusTotal API. """
    url = f"https://www.virustotal.com/api/v3/ip_addresses/{ip}"
    headers = {"x-apikey": VT_API_KEY}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error fetching VirusTotal data for {ip}: {e}")
        return None

def fetch_otx_data(ip):
    """ Fetch data from OTX API. """
    url = f"https://otx.alienvault.io/api/v1/indicators/IPv4/{ip}/general"
    headers = {"X-OTX-API-KEY": OTX_API_KEY}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error fetching OTX data for {ip}: {e}")
        return None

# src/data_fetcher.py

import urllib.parse
import pandas as pd
from datetime import datetime, timedelta
import pytz
from collections import defaultdict
from src.setup import initialize_threatconnect, create_request_object
from src.config import get_logger

logger = get_logger(__name__)

def build_tql_query(owner, start):
    """ Construct TQL query for ThreatConnect. """
    type_names = [
        "Address", "EmailAddress", "File", "Host", "URL", "ASN", "CIDR", 
        "Email Subject", "Hashtag", "Mutex", "Registry Key", "Stripped URL", "User Agent"
    ]
    type_name_condition = ", ".join([f'"{t}"' for t in type_names])

    tql_raw = (
        f'ownerName EQ "{owner}" AND '
        f'typeName IN ({type_name_condition}) AND '
        f'lastObserved >= "{start}"'
    )

    return urllib.parse.quote(tql_raw)


def fetch_indicators(tc, owner):
    """
    Fetch indicators from ThreatConnect based on the given owner.
    """
    # Calculate the start date (2 days ago) at 00:00:00 UTC
    start_date = (datetime.now(pytz.UTC) - timedelta(days=2)).date()
    start = f"{start_date}T00:00:00Z"

    # Construct query
    tql_query = build_tql_query(owner, start)
    ro = create_request_object(owner)
    ro.set_http_method('GET')
    ro.set_request_uri(
        f'/v3/indicators?tql={tql_query}&fields=tags,observations&resultStart=0&resultLimit=10000'
    )

    final_results = []

    try:
        logger.info(f"Querying indicators for owner: {owner}")
        response = tc.api_request(ro)

        # Check response content type
        if response.headers.get('content-type') == 'application/json':
            results = response.json()
            final_results.append(results)
        else:
            logger.warning(f"Unexpected response format: {response.headers.get('content-type')}")
    except Exception as e:
        logger.error(f"Failed to query indicators for {owner}: {e}")

    return final_results


def normalize_data(raw_data):
    """ Normalize and clean the fetched data. """
    if not raw_data:
        logger.warning("No data to normalize.")
        return pd.DataFrame()

    normalized_data = []

    for result in raw_data:
        if 'data' in result:
            for item in result['data']:
                if 'summary' in item:
                    normalized_data.append(item)

    if normalized_data:
        # Flatten JSON data
        df = pd.json_normalize(normalized_data)

        # Extract indicator as the first word of 'summary'
        df['indicator'] = df['summary'].str.split(' ', expand=True)[0].str.strip()

        # Drop duplicates based on 'indicator'
        df = df.drop_duplicates(subset='indicator', keep='first')

        # Ensure 'lastObserved' is datetime and apply the filter
        df['lastObserved'] = pd.to_datetime(df['lastObserved'], errors='coerce')
        return df

    logger.info("No valid data retrieved after normalization.")
    return pd.DataFrame()
