import os
import pandas as pd
from datetime import datetime, timedelta
from config_loader import get_threatconnect_config, get_virustotal_config, get_AlienVaultOtx_config

date_format = "%Y%m%d"

# Path to configuration file
project_root = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(project_root, "..", "utils", "config.json")

def get_tc_config():
    """Load and return ThreatConnect configuration."""
    try:
        return get_threatconnect_config(config_path)
    except Exception as e:
        raise RuntimeError(f"Error loading VirusTotal config: {e}")

def get_vt_config():
    """Load and return VirusTotal configuration."""
    try:
        return get_virustotal_config(config_path)
    except Exception as e:
        raise RuntimeError(f"Error loading VirusTotal config: {e}")

def get_otx_config():
    """Load and return OTX configuration."""
    try:
        return get_AlienVaultOtx_config(config_path)
    except Exception as e:
        raise RuntimeError(f"Error loading OTX config: {e}")

def get_file_paths(base_path, days=3):
    """ Generate file paths for the last `days` days using list comprehension. """
    today = datetime.utcnow()
    dates_to_pull = [(today - timedelta(days=i)).strftime(date_format) for i in range(days)]
    
    # Construct file paths
    file_paths = [base_path.format(date=dt) for dt in dates_to_pull]
    
    # Filter for existing files
    existing_files = [file_path for file_path in file_paths if os.path.exists(file_path)]
    
    if not existing_files:
        print("No files found for the specified date range.")
    else:
        print(f"Files to be loaded: {existing_files}")
    
    observed_data = load_observed_data(existing_files)

    return observed_data

def load_observed_data(file_paths):
    """ Load and concatenate observed data from multiple files. """
    data_frames = []

    for file_path in file_paths:
        try:
            df = pd.read_csv(file_path)
            data_frames.append(df)
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
    
    # Concatenate data
    if data_frames:
        observed_data_df = pd.concat(data_frames, ignore_index=True)
        print(f"Loaded data from {len(data_frames)} files.")
    else:
        observed_data_df = pd.DataFrame()

    return observed_data_df

def initialize_dataframe():
    """Initialize an empty DataFrame for storing filtered tags."""
    return pd.DataFrame()

def normalize_tags_data(row):
    """Normalize tags data and extract relevant information."""
    tags_data = row.get('tags.data')

    if not isinstance(tags_data, list):
        return pd.DataFrame()

    tags = pd.json_normalize(tags_data)
    tags['name'] = tags['name'].astype(str)
    all_tags_list = tags['name'].tolist()

    # Filter for "API" tags
    api_tags = tags[tags['name'].str.contains('API', case=False, na=False)].copy()

    if not api_tags.empty:
        # Add metadata columns and all_tags list
        metadata_columns = ['summary', 'observations', 'description', 'type', 'dateAdded', 'lastModified', 'lastObserved', 'webLink']
        for col in metadata_columns:
            api_tags[col] = row.get(col)

        api_tags['all_tags'] = [all_tags_list] * len(api_tags)

    return api_tags

def extract_api_tags(observed_src):
    """Extract and process API tags from observed data."""
    filtered_tags = initialize_dataframe()

    for _, row in observed_src.iterrows():
        api_tags = normalize_tags_data(row)
        if not api_tags.empty:
            filtered_tags = pd.concat([filtered_tags, api_tags], ignore_index=True)

    return filtered_tags

def clean_name_column(tags_df):
    """Remove 'Splunk API' suffix from the 'name' column."""
    tags_df['cleaned_name'] = tags_df['name'].str.replace(r'\s+Splunk API$', '', regex=True)
    return tags_df

def map_observed_dates(tags_df, observed_data_df):
    """Map observed dates based on indicator and OpDiv matching."""
    tags_df['observed_date'] = None

    for index, row in tags_df.iterrows():
        summary = row['summary']
        cleaned_name = row['cleaned_name']

        # Search for matching rows in observed data
        match = observed_data_df[(observed_data_df['indicator'] == summary) & (observed_data_df['OpDiv'] == cleaned_name)]

        # Assign the first matching obs_date
        if not match.empty:
            tags_df.at[index, 'observed_date'] = match['obs_date'].iloc[0]

    tags_df['observed_date'] = pd.to_datetime(tags_df['observed_date'], errors='coerce')
    return tags_df

def filter_recent_tags(tags_df, hours=24):
    """Filter tags observed within the last specified hours."""
    cutoff = pd.Timestamp.utcnow() - timedelta(hours=hours)
    return tags_df[tags_df['lastObserved'] >= cutoff].copy()

def filter_by_observed_date(tags_df, days=2):
    """Filter tags based on observed date within the last specified days."""
    cutoff_naive = pd.Timestamp.utcnow().tz_convert(None) - timedelta(days=days)
    return tags_df[tags_df['observed_date'] >= cutoff_naive].copy()

def aggregate_partners(tags_df):
    """Aggregate partners per summary."""
    tags_df['partner'] = tags_df['name'].str.replace(' Splunk API', '', regex=False)

    partner_groups = (
        tags_df.groupby('summary')['partner']
        .agg(['nunique', lambda x: ', '.join(sorted(set(x)))]).reset_index()
        .rename(columns={'nunique': 'partner_count', '<lambda_0>': 'partners'})
    )

    tags_df = tags_df.merge(partner_groups, on='summary', how='left')
    return tags_df

def apply_filters(tags_df, date_added_cutoff):
    """Apply final filters based on partner count, observations, and dateAdded."""
    tags_df = tags_df[tags_df['partner_count'] >= 2]
    tags_df = tags_df[tags_df['observations'] < 15000]
    tags_df = tags_df[tags_df['dateAdded'] >= date_added_cutoff]
    return tags_df

def drop_unnecessary_columns(tags_df):
    """Drop unnecessary columns from the DataFrame."""
    columns_to_drop = [
        'techniqueId', 'tactics.data', 'tactics.count',
        'platforms.data', 'platforms.count', 'partner', 'description', 'name'
    ]
    return tags_df.drop(columns=[col for col in columns_to_drop if col in tags_df.columns], errors='ignore')

def remove_iw_tags(tags_df):
    """Remove rows where 'all_tags' contains 'I&W'."""
    return tags_df[~tags_df['all_tags'].apply(lambda x: 'I&W' in x)]

def remove_htoc_wl_tags(tags_df):
    """Remove rows where 'all_tags' contains 'I&W'."""
    return tags_df[~tags_df['all_tags'].apply(lambda x: 'htoc_wl' in x)]

def process_data(observed_src, observed_data_df):
    """
    Main function to orchestrate data processing.
    """
    # Extract API tags
    tags_df = extract_api_tags(observed_src)

    # Ensure 'lastObserved' and 'dateAdded' are datetime
    tags_df['lastObserved'] = pd.to_datetime(tags_df['lastObserved'], errors='coerce')
    tags_df['dateAdded'] = pd.to_datetime(tags_df['dateAdded'], errors='coerce')

    # Ensure necessary columns exist
    required_columns = ['indicator', 'OpDiv', 'obs_date']
    missing_columns = [col for col in required_columns if col not in observed_data_df.columns]
    if missing_columns:
        raise ValueError(f"Missing columns in observed data: {missing_columns}")

    # Clean 'name' column and map observed dates
    tags_df = clean_name_column(tags_df)
    tags_df = map_observed_dates(tags_df, observed_data_df)

    # Filter recent and observed date
    tags_df = filter_recent_tags(tags_df)
    tags_df = filter_by_observed_date(tags_df)

    # Aggregate partners and apply final filters
    tags_df = aggregate_partners(tags_df)
    date_added_cutoff = pd.Timestamp.utcnow() - timedelta(days=30)
    tags_df = apply_filters(tags_df, date_added_cutoff)

    # Drop unnecessary columns and remove I&W tags
    tags_df = drop_unnecessary_columns(tags_df)
    tags_df = remove_iw_tags(tags_df)
    tags_df = remove_htoc_wl_tags(tags_df)

    return tags_df


def process_attributes_data(attributes_data):

    # Convert to DataFrame
    attributes_observed_src = pd.json_normalize(attributes_data)

    # Un-nest 'createdBy' and filter out 'SOAR' entries
    if not attributes_observed_src.empty and attributes_observed_src['createdBy.lastName'].notnull().any():
        attributes_observed_src = attributes_observed_src[attributes_observed_src['createdBy.lastName'] != 'SOAR']

    # Drop duplicates based on 'id'
    return attributes_observed_src.drop_duplicates(subset='id').reset_index(drop=True)


def filter_unwanted_indicators(recent_tags, ro):
    from api_integration import fetch_attributes_data

    # Extract unique indicators
    indicators = recent_tags['summary'].unique()

    # Fetch attributes data
    attributes_data = fetch_attributes_data(indicators, ro)

    # Process attributes data
    attributes_observed_src = process_attributes_data(attributes_data)

    # Filter `recent_tags` based on common 'summary' values
    filtered_recent_tags = recent_tags[recent_tags['summary'].isin(attributes_observed_src['summary'])].reset_index(drop=True)

    return filtered_recent_tags
