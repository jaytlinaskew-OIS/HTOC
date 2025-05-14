import sys
import os
import urllib3
import requests
import ipaddress
import pandas as pd
from datetime import datetime
import concurrent.futures
import logging
import pandas as pd
from datetime import datetime, timedelta
import pytz
from scripts.config_loader import load_config
sys.path.append("Z:/HTOC/Data_Analytics/threatconnect")

from ThreatConnect import ThreatConnect # type: ignore
from RequestObject import RequestObject # type: ignore

# Load API config
project_root = r"C:\Users\jaskew\Documents\project_repository\scripts\I&W_Document_Generator"
if project_root not in sys.path:
    sys.path.append(project_root)

config_path = os.path.join(project_root, "utils", "config.json")

try:
    api_secret_key, api_access_id, api_base_url, api_default_org = load_config(config_path)
    logging.info(f"Loaded config from: {config_path}")
except Exception as e:
    logging.error(f"Failed to load configuration: {e}")
    raise

# Disable SSL verification warnings (use cautiously)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Initialize ThreatConnect session
try:
    tc = ThreatConnect(api_access_id, api_secret_key, api_default_org, api_base_url)
    logging.info("ThreatConnect initialized.")
except Exception as e:
    logging.error(f"Failed to initialize ThreatConnect: {e}")
    raise

def initialize_api_client(api_access_id, api_secret_key, api_base_url, api_default_org):
    """
    Fetch indicators from ThreatConnect for the specified organization.
    """
    try:
        # Initialize ThreatConnect session
        tc = ThreatConnect(api_access_id, api_secret_key, api_default_org, api_base_url)
        logging.info("ThreatConnect initialized.")
    except Exception as e:
        logging.error(f"Failed to initialize ThreatConnect: {e}")
        sys.exit(1)

    # Define the owner (organization scope)
    owner = 'HTOC Org'

    try:
        # Create a request object
        ro = create_request_object(owner)
        logging.info("RequestObject successfully created.")
        return ro
    except Exception as e:
        logging.error(f"Failed to create RequestObject: {e}")
        sys.exit(1)


def create_request_object(owner):
    """
    Create and configure a RequestObject for ThreatConnect API requests.
    """
    try:
        ro = RequestObject()
        ro.set_http_method('GET')
        ro.set_owner(owner)
        ro.set_owner_allowed(True)
        return ro
    except Exception as e:
        logging.error(f"Failed to initialize RequestObject: {e}")
        raise

def fetch_indicators(ro):
    # Define time period
    # Calculate the start date (2 days ago) at 00:00:00 UTC
    start_date = (datetime.now(pytz.UTC) - timedelta(days=2)).date()

    # Format as 'YYYY-MM-DDT00:00:00Z'
    start = f"{start_date}T00:00:00Z"

    # List of owners to pull from
    import urllib.parse

    list_of_owners = ['HTOC Org']
    final_results = []
    type_names = [
        "Address", "EmailAddress", "File", "Host", "URL", "ASN", "CIDR", "Email Subject", "Hashtag", "Mutex", "Registry Key", "Stripped URL", "User Agent"]
    type_name_condition = ", ".join([f'"{t}"' for t in type_names])

    for owner in list_of_owners:
        print(f"\nQuerying owner: {owner}")
        try:
            tql_raw = (
                f'ownerName EQ "{owner}" AND '
                f'typeName IN ({type_name_condition})'
                f'lastObserved >= "{start}"'
            )
            tql_encoded = urllib.parse.quote(tql_raw)

            ro.set_http_method('GET')
            ro.set_request_uri(
                f'/v3/indicators?tql={tql_encoded}&fields=tags,observations&resultStart=0&resultLimit=10000'
            )

            # Send the request
            response = tc.api_request(ro)

            # Parse response
            if response.headers.get('content-type') == 'application/json':
                results = response.json()
                final_results.append(results)
            else:
                print(f"Unexpected response format: {response.headers.get('content-type')}")

        except Exception as e:
            print(f"Failed to query indicators for {owner}: {e}")

    # Normalize and clean results
    if final_results:
     # Extract and normalize data only if 'data' key exists and contains 'summary'
        normalized_data = []
        for result in final_results:
            if 'data' in result:
                for item in result['data']:
                    if 'summary' in item:
                        normalized_data.append(item)

        if normalized_data:
            observed_src = pd.json_normalize(normalized_data)
            observed_src['indicator'] = observed_src['summary'].str.split(' ', expand=True)[0].str.strip()
            observed_src = observed_src.drop_duplicates(subset='indicator', keep='first')  # Remove duplicates based on 'indicator'
            observed_src = observed_src[observed_src['lastObserved'] >= start]
            print(f"\nRetrieved {len(observed_src)} unique observed indicators.")
        else:
            print("\nNo valid indicators with 'summary' key retrieved.")
    else:
        print("\nNo indicators retrieved.")

    return observed_src


# VirusTotal and OTX API Integration
VT_API_KEY = "a8b3e24dbd2e6c0cb002784aeb8fee6217a6a425cb11ddf9a3d3361281fbbb08"
OTX_API_KEY = "ea83cf4792fc5db7acc741e82286c0b717fc99be98ec5b14de7e63cd3f74bcfe"

VT_HEADERS = {"x-apikey": VT_API_KEY}
OTX_HEADERS = {"X-OTX-API-KEY": OTX_API_KEY}

VT_URL_IP = "https://www.virustotal.com/api/v3/ip_addresses/{}"
VT_URL_DOMAIN = "https://www.virustotal.com/api/v3/domains/{}"
OTX_URL_IP = "https://otx.alienvault.io/api/v1/indicators/IPv4/{}/general"
OTX_URL_DOMAIN = "https://otx.alienvault.io/api/v1/indicators/domain/{}/general"
OTX_URL_HOSTNAME = "https://otx.alienvault.io/api/v1/indicators/hostname/{}"

def is_ip(value):
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False

def determine_query_type(query):
    if is_ip(query):
        return "ip"
    elif "." in query:
        return "hostname"
    else:
        return "domain"

def fetch_virustotal_data(query):
    query_type = determine_query_type(query)
    url = VT_URL_IP.format(query) if query_type == "ip" else VT_URL_DOMAIN.format(query)

    try:
        response = requests.get(url, headers=VT_HEADERS, verify=False)
        response.raise_for_status()
        data = response.json().get("data", {}).get("attributes", {})
        return {
            "search_term": query,
            "asn": data.get('asn'),
            "as_owner": data.get('as_owner'),
            "country": data.get('country'),
            "network": data.get('network'),
            "last_analysis_stats": data.get('last_analysis_stats'),
            "reputation": data.get('reputation'),
            "total_votes": data.get('total_votes'),
            "open_ports": [s.get("port") for s in data.get("services", []) if "port" in s],
            "link": f"https://www.virustotal.com/gui/ip-address/{query}" if query_type == "ip" else f"https://www.virustotal.com/gui/domain/{query}"
        }
    except Exception as e:
        logging.error(f"VirusTotal Error for {query}: {e}")
        return None

def fetch_otx_data(query):
    query_type = determine_query_type(query)
    url = OTX_URL_IP.format(query) if query_type == "ip" else (
        OTX_URL_HOSTNAME.format(query) if query_type == "hostname" else OTX_URL_DOMAIN.format(query)
    )

    try:
        response = requests.get(url, headers=OTX_HEADERS, verify=False)
        response.raise_for_status()
        data = response.json()
        return {
            "search_term": query,
            "base_indicator": data.get('base_indicator', {}),
            "reputation": data.get('reputation'),
            "geo": data.get('geo', {}),
            "whois": data.get('whois', {}),
            "open_ports": data.get('open_ports', []),
            "link": f"https://otx.alienvault.com/indicator/{query_type}/{query}"
        }
    except Exception as e:
        logging.error(f"OTX Error for {query}: {e}")
        return None

def unnest_base_indicator(df):
    if 'base_indicator' not in df.columns:
        return df
    base_df = pd.json_normalize(df['base_indicator'])
    base_df.columns = [f"base_{col}" for col in base_df.columns]
    df = df.drop(columns=['base_indicator']).reset_index(drop=True)
    df = pd.concat([df, base_df], axis=1)
    return df

def process_indicator(indicator, observed_by, partner_count):
    """Fetch data for a single indicator."""
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    with concurrent.futures.ThreadPoolExecutor() as executor:
        vt_future = executor.submit(fetch_virustotal_data, indicator)
        otx_future = executor.submit(fetch_otx_data, indicator)

        vt_data = vt_future.result()
        otx_data = otx_future.result()

    if vt_data:
        vt_data.update({
            "timestamp": timestamp,
            "observed_by": observed_by,
            "partner_count": partner_count
        })

    if otx_data:
        otx_data.update({
            "timestamp": timestamp,
            "observed_by": observed_by,
            "partner_count": partner_count
        })

    return vt_data, otx_data

def process_indicators(recent_tags):
    """Main function to process indicators."""
    if 'summary' not in recent_tags.columns:
        logging.warning("The 'summary' column is missing.")
        return pd.DataFrame(), pd.DataFrame()

    search_terms = recent_tags['summary'].dropna().unique().tolist()
    logging.info(f"Processing {len(search_terms)} unique search terms.")

    vt_results = []
    otx_results = []

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for indicator in search_terms:
            partners = recent_tags.loc[recent_tags['summary'] == indicator, 'partners'].values
            partner_count = recent_tags.loc[recent_tags['summary'] == indicator, 'partner_count'].values
            observed_by = partners[0] if len(partners) > 0 else "N/A"
            partner_count = partner_count[0] if len(partner_count) > 0 else "N/A"

            futures.append(executor.submit(process_indicator, indicator, observed_by, partner_count))

        for future in concurrent.futures.as_completed(futures):
            vt_data, otx_data = future.result()
            if vt_data:
                vt_results.append(vt_data)
            if otx_data:
                otx_results.append(otx_data)

    vt_df = pd.DataFrame(vt_results)
    otx_df = pd.DataFrame(otx_results)

    otx_df = unnest_base_indicator(otx_df)

    return vt_df, otx_df