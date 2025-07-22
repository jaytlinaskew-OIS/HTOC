import os
import sys
from datetime import datetime, timedelta
import pandas as pd
import pytz
import urllib.parse
import numpy as np
import re
# Use the UNC path—this works even when the Z: drive isn’t mapped
SDK_PATH = r"\\10.1.4.22\data\HTOC\Data_Analytics\threatconnect"
sys.path.insert(0, SDK_PATH)

from ThreatConnect import ThreatConnect
from RequestObject import RequestObject
from utils.config_loader import get_threatconnect_config

# Constants
PROJECT_ROOT = r"C:\Users\jaskew\Documents\project_repository\scripts\Data Movement\ThrearConnect-api-pull"
CONFIG_PATH = r"C:\Users\jaskew\Documents\project_repository\scripts\batch-processing-script\Tipper\utils\config.json"
TIPPERS_PATH = r'\\10.1.4.22\data\HTOC\HTOC Reports\Tippers'
BASE_PATH = r"\\10.1.4.22\data\HTOC\Data_Analytics\Data\OpDiv_Observations\htoc_opdiv_obs_d{date}.csv"

DATE_FORMAT = "%Y%m%d"

# Functions
def initialize_threatconnect():
    """Initialize ThreatConnect session and request object."""
    try:
        tc_config = get_threatconnect_config(CONFIG_PATH)
        global tc
        tc = ThreatConnect(
            tc_config['access_id'],
            tc_config['secret_key'],
            tc_config['default_org'],
            tc_config['base_url']
        )
        print("[DEBUG] ThreatConnect initialized successfully.")
        print(f"[DEBUG] ThreatConnect object: {repr(tc)}")
        # Create a global request object for reuse
        global ro
        ro = RequestObject()
        ro.set_http_method('GET')
        ro.set_owner('HTOC Org')
        ro.set_owner_allowed(True)
        print("[DEBUG] RequestObject successfully created.")
        return tc
    except Exception as e:
        print(f"[ERROR] Failed to initialize ThreatConnect or RequestObject: {e}")
        sys.exit(1)

def get_file_paths(base_path, days=3):
    """Generate file paths for the last `days` days."""
    today = datetime.utcnow()
    dates_to_pull = [(today - timedelta(days=i)).strftime(DATE_FORMAT) for i in range(days)]
    file_paths = [base_path.format(date=dt) for dt in dates_to_pull]
    return [file_path for file_path in file_paths if os.path.exists(file_path)]

def load_observed_data(file_paths):
    """Load and concatenate observed data from multiple files."""
    data_frames = []
    for file_path in file_paths:
        try:
            df = pd.read_csv(file_path)
            data_frames.append(df)
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
    return pd.concat(data_frames, ignore_index=True) if data_frames else pd.DataFrame()

def process_recent_tags(observed_src, observed_data_df):
    """Process recent tags and prepare partner buckets."""
    all_filtered = []
    cutoff = pd.Timestamp.utcnow()

    for _, row in observed_src.iterrows():
        tags_data = row.get('tags.data')
        if isinstance(tags_data, list):
            tags_df = pd.json_normalize(tags_data)
            api_tags = tags_df[tags_df['name'].str.contains('API', case=False, na=False)].copy()
            if not api_tags.empty:
                all_tags_list = tags_df['name'].astype(str).tolist()
                for col in ['summary', 'observations', 'description', 'type', 'dateAdded', 'lastModified', 'lastObserved', 'webLink', 'rating', 'confidence', 'id']:
                    api_tags.loc[:, col] = row.get(col)
                api_tags.loc[:, 'all_tags'] = [all_tags_list] * len(api_tags)
                all_filtered.append(api_tags)

    if not all_filtered:
        print("[DEBUG] No filtered tags found. Returning empty DataFrame.")
        return pd.DataFrame()

    filtered_tags = pd.concat(all_filtered, ignore_index=True)
    print(f"[DEBUG] Filtered tags DataFrame shape: {filtered_tags.shape}")

    filtered_tags['lastObserved'] = pd.to_datetime(filtered_tags['lastObserved'], errors='coerce')
    filtered_tags['dateAdded'] = pd.to_datetime(filtered_tags['dateAdded'], errors='coerce')
    filtered_tags['OpDiv'] = filtered_tags['name'].str.replace(' Splunk API', '', regex=False)

    obs_subset = observed_data_df[['indicator', 'OpDiv', 'obs_date']].drop_duplicates()
    print(f"[DEBUG] Observed data subset shape: {obs_subset.shape}")

    recent_tags = pd.merge(filtered_tags, obs_subset, left_on=['summary', 'OpDiv'], right_on=['indicator', 'OpDiv'], how='inner')
    print(f"[DEBUG] Recent tags after merge shape: {recent_tags.shape}")

    cutoff_naive = cutoff.tz_convert(None)
    recent_tags = recent_tags[
        (recent_tags['lastObserved'] >= cutoff - timedelta(hours=24)) &
        (pd.to_datetime(recent_tags['obs_date'], errors='coerce') >= cutoff_naive - timedelta(days=1))
    ].copy()
    print(f"[DEBUG] Recent tags after filtering shape: {recent_tags.shape}")

    recent_tags['partner'] = recent_tags['name'].str.replace(' Splunk API', '', regex=False)
    partner_groups = (
        recent_tags.groupby('summary')['partner']
        .agg(['nunique', lambda x: ', '.join(sorted(set(x)))])
        .reset_index()
        .rename(columns={'nunique': 'partner_count', '<lambda_0>': 'Partners'})
    )
    print(f"[DEBUG] Partner groups shape: {partner_groups.shape}")

    recent_tags = recent_tags.merge(partner_groups, on='summary', how='left')
    recent_tags.drop_duplicates(subset='summary', inplace=True)
    print(f"[DEBUG] Final recent tags shape: {recent_tags.shape}")

    # Enrich only final filtered indicators
    indicator_values = recent_tags['summary'].dropna().unique().tolist()
    enriched_results = []

    print(f"Enriching {len(indicator_values)} indicators with DomainTools and VirusTotalV3...")

    for value in indicator_values:
        try:
            # Use the indicator *value*, not the ID
            encoded_value = urllib.parse.quote(value)
            enrich_url = f'/v3/indicators/{encoded_value}/enrich?type=Shodan&type=VirusTotalV3'
            ro.set_http_method('POST')
            ro.set_request_uri(enrich_url)
            ro.set_body({})
            enrich_response = tc.api_request(ro)

            if enrich_response.status_code == 200:
                enrich_data = enrich_response.json()
                enrich_data['summary'] = value  # Save the value as key
                enriched_results.append(enrich_data)
            elif enrich_response.status_code == 400:
                # Suppress specific error messages for unsupported indicator types
                error_message = enrich_response.content.decode('utf-8')
                if "cannot be enriched with Shodan because the indicator type isn't supported" in error_message:
                    continue
                else:
                    print(f"[DEBUG] Unexpected 400 error: {error_message}")
        except Exception as e:
            # Suppress detailed error messages
            continue

    if enriched_results:
        df_enriched = pd.json_normalize(enriched_results)
        recent_tags = recent_tags.merge(df_enriched, on='summary', how='left')

        # Unnest 'data.enrichment.data' (list of dicts) into separate columns
        if 'data.enrichment.data' in recent_tags.columns:
            enrichment_df = pd.json_normalize(
                recent_tags['data.enrichment.data'].dropna().explode()
            )
            enrichment_df.index = recent_tags['data.enrichment.data'].dropna().explode().index
            enrichment_cols = [col for col in enrichment_df.columns if col not in recent_tags.columns]
            # Join enrichment columns back to recent_tags
            recent_tags = recent_tags.join(enrichment_df[enrichment_cols], how='left')

        # Keep only records with vtMaliciousCount > 10
        recent_tags = recent_tags[recent_tags['vtMaliciousCount'] > 10]

        print(f"Successfully enriched and merged {len(df_enriched)} indicators.")
    else:
        print("No enrichment data retrieved.")

    # Unnest the 'data.enrichment.data' column into separate columns for each enrichment type
    def extract_enrichment(row):
        """Extracts enrichment fields from the list of dicts in 'data.enrichment.data'."""
        enrichments = row.get('data.enrichment.data')
        result = {}
        if isinstance(enrichments, list):
            for enrich in enrichments:
                enrich_type = enrich.get('type')
                if enrich_type == 'Shodan':
                    # Flatten Shodan fields
                    for key in ['hostNames', 'domains', 'tags', 'country', 'city', 'isp', 'asn', 'org', 'openPorts']:
                        result[f'shodan_{key}'] = enrich.get(key, np.nan)
                elif enrich_type == 'VirusTotal':
                    result['vtMaliciousCount'] = enrich.get('vtMaliciousCount', np.nan)
        return pd.Series(result)

    # Apply extraction to recent_tags
    enrichment_expanded = recent_tags.apply(extract_enrichment, axis=1)
    recent_tags = pd.concat([recent_tags, enrichment_expanded], axis=1)

    recent_tags = recent_tags.rename(columns={
        'indicator': 'Indicator',
        'vtMaliciousCount': 'Malicious Score/Count',
        'obs_date': 'Observation Date',
        'shodan_asn': 'ASN',
        'rating': 'ThreatAssessRating',
        'confidence': 'ThreatAssessConfidence',
        'shodan_city': 'City',
        'shodan_country': 'Country',
        'data.legacyLink': 'ThreatConnect Link',
        'partners': 'Partners'
    })

    # Now select only the columns you want, after renaming
    recent_tags = recent_tags[
        [
            'Indicator',
            'Malicious Score/Count',
            'Observation Date',
            'ASN',
            'ThreatAssessRating',
            'ThreatAssessConfidence',
            'City',
            'Country',
            'ThreatConnect Link',
            'Partners'
        ]
    ]

    # Remove duplicate columns by keeping only the first occurrence
    recent_tags = recent_tags.loc[:, ~recent_tags.columns.duplicated()]
    recent_tags = recent_tags.fillna('unknown')
    recent_tags = recent_tags.drop_duplicates()

    return recent_tags

def save_to_excel(partner_buckets):
    """Save partner buckets to an Excel file."""
    os.makedirs(TIPPERS_PATH, exist_ok=True)
    today_str = datetime.utcnow().strftime("%Y%m%d")
    excel_path = os.path.join(TIPPERS_PATH, f"tippers_by_partner_{today_str}.xlsx")

    with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
        for partner, df in partner_buckets.items():
            safe_partner = re.sub(r'[^a-zA-Z0-9_-]', '_', partner)[:31]

            for col in df.select_dtypes(include=['datetimetz']).columns:
                df[col] = df[col].dt.tz_localize(None)

            df.to_excel(writer, sheet_name=safe_partner, index=False)

            worksheet = writer.sheets[safe_partner]
            worksheet.autofilter(0, 0, len(df), len(df.columns) - 1)
            worksheet.freeze_panes(1, 0)

            for i, col in enumerate(df.columns):
                if not df.empty:
                    col_lens = df[col].fillna("").astype(str).apply(len)
                    max_len = max(col_lens.max(), len(str(col)))
                else:
                    max_len = len(str(col))
                worksheet.set_column(i, i, min(max_len + 2, 50))

    print(f"Excel file with partner tabs saved to: {excel_path}")

def query_observed_src(tc):
    """Query observed source data from ThreatConnect."""
    cutoff = pd.Timestamp.utcnow()
    start_date = (datetime.now(pytz.UTC) - timedelta(days=3)).date()
    start = f"{start_date}T00:00:00Z"
    type_names = ["Address", "EmailAddress", "File", "Host", "URL", "ASN", "CIDR",
                  "Email Subject", "Hashtag", "Mutex", "Registry Key", "Stripped URL", "User Agent"]
    type_name_condition = ", ".join([f'"{t}"' for t in type_names])
    list_of_owners = ['HTOC Org']
    final_results = []

    for owner in list_of_owners:
        print(f"Querying owner: {owner}")
        try:
            tql_raw = (
                f'ownerName EQ "{owner}" AND '
                f'typeName IN ({type_name_condition}) AND '
                f'lastObserved >= "{start}"'
            )
            tql_encoded = urllib.parse.quote(tql_raw)
            ro = RequestObject()
            ro.set_http_method('GET')
            ro.set_request_uri(f'/v3/indicators?tql={tql_encoded}&fields=tags,observations&resultStart=0&resultLimit=10000')
            response = tc.api_request(ro)

            if response.headers.get('content-type') == 'application/json':
                results = response.json()
                final_results.append(results)
        except Exception as e:
            print(f"Failed to query indicators for {owner}: {e}")

    normalized_data = []
    for result in final_results:
        for item in result.get('data', []):
            if 'summary' in item:
                normalized_data.append(item)

    observed_src = pd.json_normalize(normalized_data)
    observed_src['indicator'] = observed_src['summary'].str.split().str[0].str.strip()
    observed_src.drop_duplicates(subset='indicator', inplace=True)
    observed_src['lastObserved'] = pd.to_datetime(observed_src['lastObserved'], utc=True)
    observed_src = observed_src[observed_src['lastObserved'] >= pd.to_datetime(start)]

    return observed_src

def main():
    """Main function to execute the workflow."""
    tc = initialize_threatconnect()

    file_paths = get_file_paths(BASE_PATH, days=3)
    observed_data_df = load_observed_data(file_paths)

    observed_src = query_observed_src(tc)

    if observed_src.empty:
        print("[DEBUG] observed_src is empty. Exiting.")
        return

    recent_tags = process_recent_tags(observed_src, observed_data_df)

    print(f"[DEBUG] recent_tags DataFrame:")
    print(recent_tags.head())

    if recent_tags.empty:
        print("[DEBUG] recent_tags is empty after processing. Exiting.")
        return

    all_partners = set(
        p.strip()
        for partners in recent_tags['Partners'].dropna().unique()
        for p in partners.split(',')
    )
    partner_buckets = {
        partner: recent_tags[recent_tags['Partners'].str.contains(fr'\b{re.escape(partner)}\b', na=False, regex=True)]
        for partner in all_partners
    }

    print(f"[DEBUG] all_partners set: {all_partners}")

    if not all_partners:
        print("[DEBUG] all_partners is empty. No partners found.")
        return

    print(f"[DEBUG] partner_buckets dictionary:")
    for partner, df in partner_buckets.items():
        print(f"Partner: {partner}, Records: {len(df)}")

    if not partner_buckets:
        print("[DEBUG] partner_buckets is empty. No data to save.")
        return

    save_to_excel(partner_buckets)

if __name__ == "__main__":
    main()
