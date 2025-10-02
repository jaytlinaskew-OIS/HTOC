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
        raise RuntimeError(f"Error loading ThreatConnect config: {e}")

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

def extract_group_ids(recent_tags):
    """Extract group IDs from associatedGroups.data."""
    if 'associatedGroups.data' in recent_tags.columns:
        recent_tags['group_id'] = recent_tags['associatedGroups.data'].apply(
            lambda x: x[0]['id'] if isinstance(x, list) and len(x) > 0 and 'id' in x[0] else None
        )
        # Convert group_id to string type and remove trailing decimals if it exists
        if 'group_id' in recent_tags.columns:
            recent_tags['group_id'] = recent_tags['group_id'].apply(
                lambda x: str(int(float(x))) if pd.notna(x) and str(x) != 'None' else x
            ).astype(str)
    return recent_tags

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

import pandas as pd

def initialize_dataframe():
    """Initialize an empty DataFrame for storing filtered tags."""
    return pd.DataFrame()

import pandas as pd

API_COLS = [
    "name", "group_id",
    "summary", "observations", "description", "type",
    "dateAdded", "lastModified", "lastObserved", "webLink",
    "rating", "confidence", "id",
    "all_tags",
]

GROUP_ID_LEN = len("6755399444000513")  # 16


def normalize_tags_data(row: dict) -> pd.DataFrame:
    """
    Normalize tags and extract API-tag rows with indicator metadata.
    Skips rows where *all* associated groups are 'Adversary'.
    Returns an empty DF with a stable schema when nothing qualifies.
    """
    # --- Early exits / input checks ---
    tags_data = row.get("tags.data")
    if not isinstance(tags_data, list) or len(tags_data) == 0:
        return pd.DataFrame(columns=API_COLS)

    # Normalize tags and ensure we have a 'name' column
    tags = pd.json_normalize(tags_data)
    if "name" not in tags.columns:
        return pd.DataFrame(columns=API_COLS)

    # Rename before filtering (per your intent)
    tags["name"] = (
        tags["name"].astype(str)
        .str.replace("VA CSOC CTS Splunk", "VA Splunk API", regex=False)
    )

    # --- Skip if ALL associated groups are Adversary ---
    ag_data = row.get("associatedGroups.data")
    if isinstance(ag_data, list) and len(ag_data) > 0:
        groups_df = pd.json_normalize(ag_data)
        if "type" in groups_df.columns and set(groups_df["type"].astype(str).unique()) == {"Adversary"}:
            return pd.DataFrame(columns=API_COLS)

    # --- Extract first valid group_id (robust) ---
    def pick_group_id(ag):
        if not isinstance(ag, list):
            return None
        for g in ag:
            if isinstance(g, dict):
                # handle {'id': ...} or nested {'group': {'id': ...}}
                gid = g.get("id") or (g.get("group") or {}).get("id")
                if gid is None:
                    continue
                s = str(gid)
                if s.isdigit() and len(s) == GROUP_ID_LEN:
                    return s
        return None

    group_id = pick_group_id(ag_data)

    # --- Capture all tag names (for metadata column) ---
    all_tags_list = tags["name"].tolist()

    # --- Keep only API tags ---
    api_tags = tags[tags["name"].str.contains("API", case=False, na=False)].copy()
    if api_tags.empty:
        return pd.DataFrame(columns=API_COLS)

    # Attach indicator-level metadata (do NOT include 'group_id' here)
    meta_cols = [
        "summary", "observations", "description", "type",
        "dateAdded", "lastModified", "lastObserved", "webLink",
        "rating", "confidence", "id"
    ]
    for col in meta_cols:
        api_tags[col] = row.get(col)

    # Set group_id AFTER metadata so it can't be overwritten
    api_tags["group_id"] = group_id
    api_tags["all_tags"] = [all_tags_list] * len(api_tags)

    # Ensure final schema
    for col in API_COLS:
        if col not in api_tags.columns:
            api_tags[col] = pd.Series([None] * len(api_tags))

    return api_tags[API_COLS]


def extract_api_tags(observed_src):
    """Extract and process API tags from observed data."""
    batches = []
    for _, row in observed_src.iterrows():
        api_tags = normalize_tags_data(row)
        if not api_tags.empty:
            batches.append(api_tags)
    return pd.concat(batches, ignore_index=True) if batches else pd.DataFrame()

def clean_name_column(tags_df):
    """Remove 'Splunk API' suffix from the 'name' column."""
    tags_df['cleaned_name'] = tags_df['name'].str.replace(r'\s+Splunk API$', '', regex=True)
    return tags_df

def map_observed_dates(tags_df, observed_data_df):
    """Map observed dates from observed_data_df to tags_df using vectorized operations."""
    if tags_df.empty or observed_data_df.empty:
        tags_df['observed_date'] = pd.NaT
        return tags_df
    
    # Ensure obs_date is datetime
    observed_data_df = observed_data_df.copy()
    observed_data_df['obs_date'] = pd.to_datetime(observed_data_df['obs_date'], errors='coerce')
    
    # Create a mapping dictionary for fast lookup
    # Use (indicator, OpDiv) as key and obs_date as value
    observed_data_df_clean = observed_data_df.dropna(subset=['indicator', 'OpDiv', 'obs_date'])
    
    # Create lookup dictionary
    lookup_dict = {}
    for _, row in observed_data_df_clean.iterrows():
        key = (row['indicator'], row['OpDiv'])
        if key not in lookup_dict:  # Keep first occurrence
            lookup_dict[key] = row['obs_date']
    
    # Apply mapping using vectorized operations
    tags_df = tags_df.copy()
    tags_df['lookup_key'] = list(zip(tags_df['summary'], tags_df['cleaned_name']))
    tags_df['observed_date'] = tags_df['lookup_key'].map(lookup_dict)
    
    # Clean up temporary column
    tags_df = tags_df.drop(columns=['lookup_key'])
    
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
    tags_df['partner'] = tags_df['name'].str.replace(' Splunk API', '', regex=False)
    partner_groups = (
        tags_df.groupby('summary')['partner']
        .agg(['nunique', lambda s: ', '.join(sorted(set(s.dropna())))])  # dropna()
        .reset_index()
        .rename(columns={'nunique': 'partner_count', '<lambda_0>': 'partners'})
    )
    return tags_df.merge(partner_groups, on='summary', how='left')

def apply_filters(tags_df, date_added_cutoff):
    """Apply final filters based on partner count, observations, and dateAdded."""
    tags_df = tags_df[tags_df['partner_count'] >= 2]
    tags_df = tags_df[tags_df['observations'] < 15000]
    tags_df = tags_df[tags_df['dateAdded'] >= date_added_cutoff]
    tags_df = tags_df.drop_duplicates(subset='summary', keep='first')
    print(f"Filtered tags shape: {tags_df.shape}")
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
    return tags_df[~tags_df['all_tags'].apply(lambda x: isinstance(x, list) and 'I&W' in x)]

def remove_htoc_wl_tags(tags_df):
    """Remove rows where 'all_tags' contains 'htoc_wl'."""
    return tags_df[~tags_df['all_tags'].apply(lambda x: isinstance(x, list) and 'htoc_wl' in x)]

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
    date_added_cutoff = pd.Timestamp.utcnow() - timedelta(days=180)
    tags_df = apply_filters(tags_df, date_added_cutoff)

    # Drop unnecessary columns and remove I&W tags
    tags_df = drop_unnecessary_columns(tags_df)
    tags_df = remove_iw_tags(tags_df)
    tags_df = remove_htoc_wl_tags(tags_df)

    # Extract group IDs from associatedGroups.data
    tags_df = extract_group_ids(tags_df)

    return tags_df


def process_attributes_data(attributes_data):

    # Convert to DataFrame
    attributes_observed_src = pd.json_normalize(attributes_data)
    print("Indicators in attributes_observed_src:", attributes_observed_src['summary'].unique())
    # Un-nest 'createdBy' and filter out 'SOAR' entries
    if not attributes_observed_src.empty and attributes_observed_src['createdBy.lastName'].notnull().any():
        attributes_observed_src = attributes_observed_src[attributes_observed_src['createdBy.lastName'] != 'SOAR']

    # Drop duplicates based on 'id'
    return attributes_observed_src.drop_duplicates(subset='id').reset_index(drop=True)


def filter_unwanted_indicators(recent_tags, ro):
    from api_integration import fetch_attributes_data

    print("recent_tags in recent_tags:", recent_tags['summary'].unique())

    # Extract unique indicators
    indicators = recent_tags['summary'].unique()
    
    # Fetch attributes data
    attributes_data = fetch_attributes_data(indicators, ro)

    # Process attributes data
    attributes_observed_src = process_attributes_data(attributes_data)

    # Filter `recent_tags` based on common 'summary' values
    filtered_recent_tags = recent_tags[recent_tags['summary'].isin(attributes_observed_src['summary'])].reset_index(drop=True)

    return filtered_recent_tags
