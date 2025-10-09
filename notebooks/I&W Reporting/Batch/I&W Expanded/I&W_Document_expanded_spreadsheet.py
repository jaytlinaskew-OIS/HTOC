#!/usr/bin/env python3
"""
I&W Document Expanded Spreadsheet Generator
Converts the Jupyter notebook functionality into a standalone Python script.
"""

import sys
import os
import urllib3
import pandas as pd
from datetime import datetime, timedelta, UTC
import pytz
import urllib.parse
import warnings

# Suppress warnings
warnings.simplefilter(action='ignore', category=pd.errors.SettingWithCopyWarning)

def setup_paths_and_imports():
    """Setup system paths and import required modules."""
    print("Setting up paths and imports...")
    
    # Add your local ThreatConnect SDK to path
    sys.path.append("Z:/HTOC/Data_Analytics/threatconnect")
    from ThreatConnect import ThreatConnect
    from RequestObject import RequestObject

    # Add your project repo to path
    project_root = r"C:\Users\jaskew\Documents\project_repository\scripts\Data Movement\ThrearConnect-api-pull"
    if project_root not in sys.path:
        sys.path.append(project_root)

    from utils.config_loader import load_config
    
    return ThreatConnect, RequestObject, load_config, project_root

def initialize_threatconnect(project_root, load_config):
    """Initialize ThreatConnect API connection."""
    print("Initializing ThreatConnect connection...")
    
    # Load API config
    config_path = os.path.join(project_root, "utils", "config.json")
    try:
        api_secret_key, api_access_id, api_base_url, api_default_org = load_config(config_path)
        print(f"Loaded config from: {config_path}")
        print(f"Base URL: {api_base_url}")
        print(f"Access ID: {api_access_id}")
        print(f"Default Org: {api_default_org}")
    except Exception as e:
        print(f"[ERROR] Failed to load configuration: {e}")
        sys.exit(1)

    # Disable SSL verification warnings
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # Initialize ThreatConnect session
    try:
        tc = ThreatConnect(api_access_id, api_secret_key, api_default_org, api_base_url)
        print("ThreatConnect initialized.")
    except Exception as e:
        print(f"[ERROR] Failed to initialize ThreatConnect: {e}")
        sys.exit(1)

    # Define the owner (organization scope)
    owner = 'HTOC Org'

    # Create a request object to fetch indicators
    try:
        ro = RequestObject()
        ro.set_http_method('GET')
        ro.set_owner(owner)
        ro.set_owner_allowed(True)
        print("RequestObject successfully created.")
    except Exception as e:
        print(f"[ERROR] Failed to initialize RequestObject: {e}")
        sys.exit(1)
    
    return tc, ro

def fetch_indicators(tc, ro):
    """Fetch indicators from ThreatConnect API."""
    print("Fetching indicators from ThreatConnect...")
    
    # Calculate the start date (2 days ago) at 00:00:00 UTC
    start_date = (datetime.now(pytz.UTC) - timedelta(days=2)).date()
    start = f"{start_date}T00:00:00Z"

    list_of_owners = ['HTOC Org']
    final_results = []
    type_names = [
        "Address", "EmailAddress", "File", "Host", "URL", "ASN", "CIDR", 
        "Email Subject", "Hashtag", "Mutex", "Registry Key", "Stripped URL", "User Agent"
    ]
    type_name_condition = ", ".join([f'"{t}"' for t in type_names])

    for owner in list_of_owners:
        print(f"Querying owner: {owner}")
        try:
            tql_raw = (
                f'ownerName EQ "{owner}" AND '
                f'typeName IN ({type_name_condition})'
                f'lastObserved >= "{start}"'
            )
            tql_encoded = urllib.parse.quote(tql_raw)

            ro.set_http_method('GET')
            ro.set_request_uri(
                f'/v3/indicators?tql={tql_encoded}&fields=tags,observations,associatedGroups&resultStart=0&resultLimit=10000'
            )

            response = tc.api_request(ro)

            if response.headers.get('content-type') == 'application/json':
                results = response.json()
                final_results.append(results)
            else:
                print(f"Unexpected response format: {response.headers.get('content-type')}")

        except Exception as e:
            print(f"Failed to query indicators for {owner}: {e}")

    # Normalize and clean results
    if final_results:
        normalized_data = []
        for result in final_results:
            if 'data' in result:
                for item in result['data']:
                    if 'summary' in item:
                        normalized_data.append(item)

        if normalized_data:
            observed_src = pd.json_normalize(normalized_data)
            observed_src['indicator'] = observed_src['summary'].str.split(' ', expand=True)[0].str.strip()
            observed_src = observed_src.drop_duplicates(subset='indicator', keep='first')
            observed_src = observed_src[observed_src['lastObserved'] >= start]
            print(f"Retrieved {len(observed_src)} unique observed indicators.")
        else:
            print("No valid indicators with 'summary' key retrieved.")
            observed_src = pd.DataFrame()
    else:
        print("No indicators retrieved.")
        observed_src = pd.DataFrame()
    
    return observed_src, start

def load_observed_data():
    """Load observed data from CSV files."""
    print("Loading observed data from CSV files...")
    
    base_path = r"Z:/HTOC/Data_Analytics/Data/OpDiv_Observations/htoc_opdiv_obs_d{date}.csv"
    date_format = "%Y%m%d"

    def get_file_paths(base_path, days=3):
        """Generate file paths for the last `days` days."""
        today = datetime.utcnow()
        dates_to_pull = [(today - timedelta(days=i)).strftime(date_format) for i in range(days)]
        
        file_paths = [base_path.format(date=dt) for dt in dates_to_pull]
        existing_files = [file_path for file_path in file_paths if os.path.exists(file_path)]
        
        if not existing_files:
            print("No files found for the specified date range.")
        else:
            print(f"Files to be loaded: {existing_files}")
        
        return existing_files

    def load_observed_data_files(file_paths):
        """Load and concatenate observed data from multiple files."""
        data_frames = []

        for file_path in file_paths:
            try:
                df = pd.read_csv(file_path)
                data_frames.append(df)
            except Exception as e:
                print(f"Error reading file {file_path}: {e}")
        
        if data_frames:
            observed_data_df = pd.concat(data_frames, ignore_index=True)
            print(f"Loaded data from {len(data_frames)} files.")
        else:
            observed_data_df = pd.DataFrame()

        return observed_data_df

    file_paths = get_file_paths(base_path, days=3)
    observed_data_df = load_observed_data_files(file_paths)
    
    return observed_data_df

def process_tag_row(row, observed_src):
    """Process a single row from observed_src to extract and filter tags."""
    tags_data = row.get('tags.data')
    if not isinstance(tags_data, list):
        return None

    tags_df = pd.json_normalize(tags_data)
    tags_df['name'] = (
        tags_df['name']
        .astype(str)
        .str.replace('VA CSOC CTS Splunk', 'VA Splunk API', regex=False)
    )

    # Skip if all associated groups are Adversary
    if 'associatedGroups.data' in observed_src.columns:
        ag_data = row.get('associatedGroups.data')
        if isinstance(ag_data, list) and len(ag_data) > 0:
            groups_df = pd.json_normalize(ag_data)
            if 'type' in groups_df.columns and set(groups_df['type']) == {'Adversary'}:
                return None

    all_tags_list = tags_df['name'].tolist()
    api_tags = tags_df[tags_df['name'].str.contains('API', case=False, na=False)].copy()
    if api_tags.empty:
        return None

    meta_cols = [
        'summary', 'observations', 'description', 'type',
        'dateAdded', 'lastModified', 'lastObserved', 'webLink',
        'rating', 'confidence', 'id', 'associatedGroups.data'
    ]
    for col in meta_cols:
        api_tags[col] = [row.get(col)] * len(api_tags)

    if len(api_tags) > 0:
        api_tags['all_tags'] = [all_tags_list] * len(api_tags)

    return api_tags

def map_observed_dates(filtered_tags, observed_data_df):
    """Map observed dates from observed_data_df to filtered_tags."""
    if filtered_tags.empty:
        return filtered_tags
    
    filtered_tags['cleaned_name'] = filtered_tags['name'].str.replace(r'\s+Splunk API$', '', regex=True)
    filtered_tags['observed_date'] = pd.NaT
    
    observed_data_df['obs_date'] = pd.to_datetime(observed_data_df['obs_date'], errors='coerce')

    for idx, r in filtered_tags.iterrows():
        summary = r.get('summary')
        cleaned_name = r.get('cleaned_name')
        if pd.isna(summary) or pd.isna(cleaned_name):
            continue
        match = observed_data_df[
            (observed_data_df['indicator'] == summary) &
            (observed_data_df['OpDiv'] == cleaned_name)
        ]
        if not match.empty:
            filtered_tags.at[idx, 'observed_date'] = match['obs_date'].iloc[0]

    filtered_tags['observed_date'] = pd.to_datetime(filtered_tags['observed_date'], errors='coerce')
    filtered_tags.drop(columns=['cleaned_name'], inplace=True, errors='ignore')
    
    return filtered_tags

def apply_filters_and_grouping(filtered_tags, cutoff_naive):
    """Apply time filters, partner grouping, and other filtering criteria."""
    if filtered_tags.empty:
        return pd.DataFrame()
    
    recent_tags = filtered_tags[filtered_tags['observed_date'] >= cutoff_naive - timedelta(days=2)].copy()

    if recent_tags.empty:
        return recent_tags
    
    recent_tags['partner'] = recent_tags['name'].str.replace(' Splunk API', '', regex=False)

    partner_groups = (
        recent_tags.groupby('summary')['partner']
        .agg(['nunique', lambda s: ', '.join(sorted(set(s.dropna())))]).reset_index()
        .rename(columns={'nunique': 'partner_count', '<lambda_0>': 'partners'})
    )

    recent_tags = recent_tags.merge(partner_groups, on='summary', how='left')
    recent_tags = recent_tags[recent_tags['partner_count'] >= 2]
    recent_tags = recent_tags.drop_duplicates(subset='summary', keep='first')

    cols_to_drop = [
        'techniqueId', 'tactics.data', 'tactics.count',
        'platforms.data', 'platforms.count', 'partner', 'name'
    ]
    recent_tags = recent_tags.drop(columns=[c for c in cols_to_drop if c in recent_tags.columns], errors='ignore')

    if 'all_tags' in recent_tags.columns:
        recent_tags = recent_tags[~recent_tags['all_tags'].apply(lambda x: isinstance(x, list) and 'I&W' in x)]
        recent_tags = recent_tags[~recent_tags['all_tags'].apply(lambda x: isinstance(x, list) and 'htoc_wl' in x)]

    return recent_tags

def extract_group_ids(recent_tags):
    """Extract group IDs from associatedGroups.data."""
    if 'associatedGroups.data' in recent_tags.columns:
        recent_tags['group_id'] = recent_tags['associatedGroups.data'].apply(
            lambda x: x[0]['id'] if isinstance(x, list) and len(x) > 0 and 'id' in x[0] else None
        )
        if 'group_id' in recent_tags.columns:
            recent_tags['group_id'] = recent_tags['group_id'].apply(
                lambda x: str(int(float(x))) if pd.notna(x) and str(x) != 'None' else x
            ).astype(str)
    return recent_tags

def process_tags(observed_src, observed_data_df):
    """Main tag processing pipeline."""
    print("Starting tag processing pipeline...")
    
    cutoff = pd.Timestamp.utcnow()
    cutoff_naive = cutoff.tz_convert(None)

    # Required columns validation
    required_columns = ['indicator', 'OpDiv', 'obs_date']
    missing_columns = [c for c in required_columns if c not in observed_data_df.columns]
    if missing_columns:
        raise ValueError(f"Missing columns in observed data: {missing_columns}")

    # Process tags from observed_src
    print("Processing tags from observed_src...")
    all_filtered = []

    for _, row in observed_src.iterrows():
        processed_tags = process_tag_row(row, observed_src)
        if processed_tags is not None:
            all_filtered.append(processed_tags)

    # Create filtered_tags DataFrame
    print("Creating filtered_tags DataFrame...")
    filtered_tags = pd.concat(all_filtered, ignore_index=True) if all_filtered else pd.DataFrame()

    if not filtered_tags.empty:
        filtered_tags['lastObserved'] = pd.to_datetime(filtered_tags['lastObserved'], errors='coerce', utc=True)
        filtered_tags['dateAdded'] = pd.to_datetime(filtered_tags['dateAdded'], errors='coerce', utc=True)
        print(f"Created filtered_tags with {len(filtered_tags)} rows")
    else:
        print("No filtered tags found")

    # Map observed dates
    print("Mapping observed dates...")
    filtered_tags = map_observed_dates(filtered_tags, observed_data_df)

    # Apply filters and grouping
    print("Applying filters and partner grouping...")
    recent_tags = apply_filters_and_grouping(filtered_tags, cutoff_naive)

    # Extract group IDs
    print("Extracting group IDs...")
    recent_tags = extract_group_ids(recent_tags)

    print(f"Processing complete! Final dataset shape: {recent_tags.shape}")
    if not recent_tags.empty:
        print(f"Partners represented: {recent_tags['partners'].nunique()} unique partner combinations")

    return recent_tags

def fetch_attributes(tc, ro, recent_tags):
    """Fetch attributes for indicators."""
    print("Fetching attributes for indicators...")
    
    indicators = recent_tags['summary'].unique()
    attributes_data = []
    indicators_with_no_attributes = []

    for indicator in indicators:
        try:
            ro.set_http_method('GET')
            ro.set_request_uri(f'/v3/indicators/{indicator}?fields=attributes&resultStart=0&resultLimit=1000')
            response = tc.api_request(ro)

            if response.headers.get('content-type') == 'application/json':
                data = response.json().get('data', {})
                attributes = data.get('attributes', {}).get('data', [])

                if not attributes:
                    indicators_with_no_attributes.append(indicator)
                else:
                    for attr in attributes:
                        attr.update({
                            'id': data.get('id'),
                            'summary': data.get('summary'),
                            'type': data.get('type'),
                            'ownerName': data.get('ownerName')
                        })
                        attributes_data.append(attr)
        except Exception as e:
            if hasattr(e, 'response') and getattr(e.response, 'status_code', None) == 400:
                continue
            if "Status Code: 400" in str(e):
                continue
            pass

    attributes_observed_src = pd.json_normalize(attributes_data)

    if not attributes_observed_src.empty and attributes_observed_src['createdBy.lastName'].notnull().any():
        attributes_observed_src = attributes_observed_src[attributes_observed_src['createdBy.lastName'] != 'SOAR']

    attributes_observed_src = attributes_observed_src.drop_duplicates(subset='id').reset_index(drop=True)

    # Filter recent_tags for indicators that had attributes
    filtered_with_attrs = recent_tags[recent_tags['summary'].isin(attributes_observed_src['summary'])]
    no_attrs_df = recent_tags[recent_tags['summary'].isin(indicators_with_no_attributes)]

    # Combine both and remove duplicates
    filtered_recent_tags = pd.concat([filtered_with_attrs, no_attrs_df], ignore_index=True)
    filtered_recent_tags = filtered_recent_tags.drop_duplicates(subset='summary').reset_index(drop=True)
    
    return filtered_recent_tags

def filter_reported_indicators(filtered_recent_tags):
    """Filter out already-reported indicators."""
    print("Filtering out already-reported indicators...")
    
    reported_indicators_path = r"Z:\HTOC\HTOC Reports\I&W Reports\5. I&W Staging\Reported Indicators\indicators.csv"

    try:
        reported_indicators_df = pd.read_csv(reported_indicators_path, on_bad_lines='skip')
        print(f"Loaded reported indicators - shape: {reported_indicators_df.shape}")
        
        if not reported_indicators_df.empty:
            reported_indicators_df = reported_indicators_df.drop_duplicates().reset_index(drop=True)
            
            if 'Indicator' in reported_indicators_df.columns:
                reported_set = set(reported_indicators_df['Indicator'].astype(str))
                col_name = 'Indicator'
            elif 'indicator' in reported_indicators_df.columns:
                reported_set = set(reported_indicators_df['indicator'].astype(str))
                col_name = 'indicator'
            elif 'summary' in reported_indicators_df.columns:
                reported_set = set(reported_indicators_df['summary'].astype(str))
                col_name = 'summary'
            elif len(reported_indicators_df.columns) == 1:
                col_name = reported_indicators_df.columns[0]
                reported_set = set(reported_indicators_df[col_name].astype(str))
            else:
                print("No suitable indicator column found")
                reported_set = set()
            
            print(f"Found {len(reported_set)} indicators in '{col_name}' column")
            
            if not filtered_recent_tags.empty and reported_set:
                before_count = len(filtered_recent_tags)
                filtered_recent_tags = filtered_recent_tags[
                    ~filtered_recent_tags['summary'].astype(str).isin(reported_set)
                ].reset_index(drop=True)
                after_count = len(filtered_recent_tags)
                print(f"Removed {before_count - after_count} already-reported indicators")
                print(f"Final filtered dataset: {after_count} indicators")
        else:
            print("No reported indicators loaded")
            
    except Exception as e:
        print(f"Error loading reported indicators: {e}")
    
    return filtered_recent_tags

def save_to_excel(filtered_recent_tags):
    """Save the final dataset to Excel."""
    print("Saving dataset to Excel...")
    
    output_path = 'Z:\\HTOC\\HTOC Reports\\I&W Reports\\5. I&W Staging\\Spreadsheet\\Expanded'
    
    # Ensure output directory exists
    os.makedirs(output_path, exist_ok=True)
    
    # Generate filename with today's date
    today_str = datetime.now(UTC).strftime("%Y%m%d")
    excel_filename = f"expanded_indicators_{today_str}.xlsx"
    excel_path = os.path.join(output_path, excel_filename)

    # Convert timezone-aware datetime columns to naive
    for col in filtered_recent_tags.select_dtypes(include=['datetimetz']).columns:
        filtered_recent_tags[col] = filtered_recent_tags[col].dt.tz_localize(None)

    # Drop the 'description' column if it exists
    if 'description' in filtered_recent_tags.columns:
        filtered_recent_tags = filtered_recent_tags.drop(columns=['description'])

    filtered_recent_tags.to_excel(excel_path, index=False)
    print(f"Saved to {excel_path}")
    
    return excel_path

def main():
    """Main execution function."""
    print("=== I&W Document Expanded Spreadsheet Generator ===")
    print(f"Started at: {datetime.now()}")
    
    try:
        # Setup and initialization
        ThreatConnect, RequestObject, load_config, project_root = setup_paths_and_imports()
        tc, ro = initialize_threatconnect(project_root, load_config)
        
        # Fetch data
        observed_src, start = fetch_indicators(tc, ro)
        observed_data_df = load_observed_data()
        
        if observed_src.empty:
            print("No indicators retrieved from ThreatConnect. Exiting.")
            return
        
        if observed_data_df.empty:
            print("No observed data loaded. Exiting.")
            return
        
        # Process data
        recent_tags = process_tags(observed_src, observed_data_df)
        
        if recent_tags.empty:
            print("No tags found after processing. Exiting.")
            return
        
        # Fetch attributes and filter
        filtered_recent_tags = fetch_attributes(tc, ro, recent_tags)
        filtered_recent_tags = filter_reported_indicators(filtered_recent_tags)
        
        if filtered_recent_tags.empty:
            print("No indicators remaining after filtering. Exiting.")
            return
        
        # Save results
        excel_path = save_to_excel(filtered_recent_tags)
        
        print("=== Processing Complete ===")
        print(f"Final dataset contains {len(filtered_recent_tags)} indicators")
        print(f"Output saved to: {excel_path}")
        print(f"Completed at: {datetime.now()}")
        
    except Exception as e:
        print(f"[ERROR] Script failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()