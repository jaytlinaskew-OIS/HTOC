# Auto-generated from ThreatScoreIW.ipynb

# %% [code cell 0]
import sys
import os
import urllib3
import logging
from configparser import ConfigParser

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("ThreatScoreIW")

def _mask(s: object, keep_last: int = 4) -> str:
    v = "" if s is None else str(s)
    if len(v) <= keep_last:
        return "*" * len(v)
    return ("*" * (len(v) - keep_last)) + v[-keep_last:]

try:
    from IPython.display import display  # type: ignore
except Exception:  # pragma: no cover
    def display(*args, **kwargs):
        print(*args)

# Add your local ThreatConnect SDK to path
sys.path.append(r"Z:\HTOC\Data_Analytics\threatconnect")
from ThreatConnect import ThreatConnect
from RequestObject import RequestObject
from Owners import Owners

# Add your project repo to path
project_root = r"C:\Users\jaskew\Documents\project_repository\scripts\Data Movement\ThrearConnect-api-pull"
if project_root not in sys.path:
    sys.path.append(project_root)

from utils.config_loader import load_config

# Load API config
config_path = os.path.join(project_root, "utils", "config.json")
try:
    api_secret_key, api_access_id, api_base_url, api_default_org = load_config(config_path)
    logger.info("Loaded config from: %s", config_path)
    logger.info("Base URL: %s", api_base_url)
    logger.info("Access ID: %s", _mask(api_access_id))
    logger.info("Default Org: %s", api_default_org)
except Exception as e:
    logger.exception("Failed to load configuration from %s", config_path)
    sys.exit(1)

# Disable SSL verification warnings (use cautiously)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
verify_ssl = False
logger.info("SSL verification disabled: %s", not verify_ssl)

# Initialize ThreatConnect session
try:
    tc = ThreatConnect(api_access_id, api_secret_key, api_default_org, api_base_url)
    logger.info("ThreatConnect initialized.")
except Exception as e:
    logger.exception("Failed to initialize ThreatConnect.")
    sys.exit(1)

# Define the owner (organization scope)
owner = 'HTOC Org'

# Create a request object to fetch indicators (or other data)
try:
    ro = RequestObject()
    ro.set_http_method('GET')
    ro.set_owner(owner)
    ro.set_owner_allowed(True)
    # ro.set_resource_pagination(True)  # Uncomment if needed
    logger.info("RequestObject successfully created (owner=%s).", owner)
except Exception as e:
    logger.exception("Failed to initialize RequestObject.")
    sys.exit(1)

# %% [code cell 1]
import pandas as pd
import ast
from datetime import datetime, timedelta
import pytz
import urllib.parse

# Configuration for ThreatConnect indicator query (rolling window for lastObserved in TQL)
INSIGHT_LOOKBACK_HOURS = 48
INDICATOR_TYPE_NAMES = [
    "Address", "EmailAddress", "File", "Host", "URL", "ASN", "CIDR",
    "Email Subject", "Hashtag", "Mutex", "Registry Key", "User Agent",
]
OWNER_NAMES = [
    'HTOC Org',
    'CISA Federal Feed',
    'CMS_CTI',
    'Crowdstrike Falcon Intelligence',
    'DHS CISCP',
    'Intel471',
    'Mandiant Advantage Threat Intelligence',
    'VA_TIP Data',
]
RESULT_PAGE_SIZE = 500  # keep this smaller; same fields, just paged

# Setup: rolling 48-hour window for lastObserved (aligned with downstream insight window)
start_dt = datetime.now(pytz.UTC) - timedelta(hours=INSIGHT_LOOKBACK_HOURS)
start = start_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

type_names = INDICATOR_TYPE_NAMES
type_name_condition = ", ".join([f'"{t}"' for t in type_names])

list_of_owners = OWNER_NAMES

# Build owner IN (...) clause
owner_condition = ", ".join([f'"{o}"' for o in list_of_owners])

tql_raw = (
    f'ownerName IN ({owner_condition}) AND '
    f'typeName IN ({type_name_condition}) AND '
    f'lastObserved >= "{start}"'
)

tql_encoded = urllib.parse.quote(tql_raw)

final_results = []
logger.info("Querying indicators (lookback_hours=%s) starting %s", INSIGHT_LOOKBACK_HOURS, start)
logger.debug("TQL (raw): %s", tql_raw)

# Query indicators (paginate so you don't 502 with heavy fields)
# Create a NEW RequestObject WITHOUT owner restriction to query across all owners
ro_multi = RequestObject()
ro_multi.set_http_method('GET')

result_start = 0
result_limit = RESULT_PAGE_SIZE

while True:
    try:
        # NOTE: same fields list you requested (tags,observations,associatedGroups,falsePositives,threatAssess)
        # Only change here is removing the trailing comma after threatAssess which can break parsing.
        ro_multi.set_request_uri(
            f'/v3/indicators?tql={tql_encoded}'
            f'&fields=tags,observations,associatedGroups,falsePositives,threatAssess'
            f'&resultStart={result_start}&resultLimit={result_limit}'
        )

        response = tc.api_request(ro_multi)

        ct = response.headers.get('content-type', '')
        if not ct.startswith('application/json'):
            raise RuntimeError(f"Non-JSON response ({ct}): {response.content[:200]}")

        results = response.json()
        data_items = results.get('data', []) or []

        # stop when no more results
        if not data_items:
            logger.info("Indicator query complete (pages=%s).", max(1, result_start // result_limit) if result_start else 0)
            break

        final_results.append(results)
        logger.info("Fetched %s indicators (resultStart=%s).", len(data_items), result_start)
        result_start += result_limit

    except Exception as e:
        logger.exception("Failed to query indicators (resultStart=%s).", result_start)
        break

# Normalize results
normalized_data = []
for result in final_results:
    data_items = result.get('data', [])
    if not data_items:
        logger.warning("API page returned no data items.")
    for item in data_items:
        if isinstance(item, dict) and 'summary' in item:
            normalized_data.append(item)

if normalized_data:
    logger.info("Normalizing %s indicator records.", len(normalized_data))
    observed_src = pd.json_normalize(normalized_data)
    observed_src['indicator'] = observed_src['summary'].astype(str).str.split().str[0].str.strip()
    observed_src['lastObserved'] = pd.to_datetime(observed_src['lastObserved'], utc=True, errors='coerce')
    observed_src = observed_src[observed_src['lastObserved'] >= pd.to_datetime(start, utc=True)]
    
    # Create a 'sources' column by aggregating ownerName values per indicator
    sources_per_indicator = (
        observed_src.groupby('indicator')['ownerName']
        .apply(lambda x: ', '.join(sorted(set(x))))
        .reset_index()
        .rename(columns={'ownerName': 'sources'})
    )

    # Merge sources back into observed_src
    observed_src = observed_src.merge(sources_per_indicator, on='indicator', how='left')
    # Filter to keep only records where ownerName is 'HTOC Org'
    observed_src = observed_src[observed_src['ownerName'] == 'HTOC Org'].copy()
    # Exclude indicators below threatAssessRating 3 or threatAssessConfidence 50 (from threatAssess field)
    _ta = pd.Series(float('nan'), index=observed_src.index)
    _tc = pd.Series(float('nan'), index=observed_src.index)
    for c in ('threatAssessRating', 'threatAssess.threatAssessRating', 'threatAssess.rating', 'rating'):
        if c in observed_src.columns:
            _ta = pd.to_numeric(observed_src[c], errors='coerce')
            break
    for c in ('threatAssessConfidence', 'threatAssess.threatAssessConfidence', 'threatAssess.confidence', 'confidence'):
        if c in observed_src.columns:
            _tc = pd.to_numeric(observed_src[c], errors='coerce')
            break
    _pre_ta = len(observed_src)
    observed_src = observed_src[(_ta >= 3) & (_tc >= 50)].copy()
    logger.info(
        "Threat assess filter (rating>=3, confidence>=50): %s -> %s rows.",
        _pre_ta,
        len(observed_src),
    )
    logger.info("observed_src ready (rows=%s, cols=%s).", len(observed_src), len(observed_src.columns))
else:
    logger.warning("No valid indicator data found.")
    observed_src = pd.DataFrame()

# %% [code cell 2]
import pandas as pd

# Load the Excel file
file_path = r"Z:\HTOC\Data_Analytics\Data\Threat Assessment Scores\Threat_Assessment_Scores.xlsx"
logger.info("Reading Excel scores: %s", file_path)
df = pd.read_excel(file_path)
logger.info("Loaded df (rows=%s, cols=%s).", len(df), len(df.columns))

# Keep only indicators that are also in observed_src
_indicator_col = next((c for c in ["indicator", "Indicator", "INDICATOR"] if c in df.columns), None)
if _indicator_col is None:
    raise KeyError(f"Could not find indicator column in df. Columns: {list(df.columns)}")

_observed_indicators = set(observed_src["indicator"].dropna().astype(str))
_pre = len(df)
df = df[df[_indicator_col].astype(str).isin(_observed_indicators)].copy()
logger.info("Filtered df by observed_src indicators: %s -> %s rows.", _pre, len(df))

# Update df's Last Observed from observed_src.lastObserved
_last_observed_col = next(
    (
        c
        for c in [
            "Last Observed",
            "lastObserved",
            "LastObserved",
            "last_observed",
            "LAST OBSERVED",
        ]
        if c in df.columns
    ),
    None,
)
if _last_observed_col is None:
    raise KeyError(f"Could not find 'Last Observed' column in df. Columns: {list(df.columns)}")

_assoc_groups_src_col = "associatedGroups.data"
_assoc_groups_target_col = "Associated Groups"
if _assoc_groups_src_col not in observed_src.columns:
    raise KeyError(
        f"Could not find '{_assoc_groups_src_col}' column in observed_src. Columns: {list(observed_src.columns)}"
    )

def _extract_group_ids(value):
    if value is None:
        return pd.NA

    parsed = value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return pd.NA
        try:
            parsed = ast.literal_eval(text)
        except (ValueError, SyntaxError):
            return text
    elif isinstance(value, float) and pd.isna(value):
        return pd.NA

    if isinstance(parsed, dict):
        gid = parsed.get("id")
        return f"Group Id: {gid}" if gid is not None else pd.NA

    if isinstance(parsed, list):
        ids = []
        for item in parsed:
            if isinstance(item, dict) and item.get("id") is not None:
                ids.append(f"Group Id: {item.get('id')}")
        return ", ".join(ids) if ids else pd.NA

    return pd.NA

_observed_latest = (
    observed_src.dropna(subset=["indicator"])
    .assign(
        indicator=lambda d: d["indicator"].astype(str),
        lastObserved=lambda d: pd.to_datetime(d["lastObserved"], utc=True, errors="coerce"),
    )
    .sort_values("lastObserved")
    .drop_duplicates(subset=["indicator"], keep="last")
)
_last_obs_by_indicator = _observed_latest.set_index("indicator")["lastObserved"]
_assoc_groups_by_indicator = _observed_latest.set_index("indicator")[_assoc_groups_src_col].map(_extract_group_ids)

# Ensure df's last observed column is datetime-like, then overwrite for matches
_df_ind = df[_indicator_col].astype(str)
df[_last_observed_col] = pd.to_datetime(df[_last_observed_col], utc=True, errors="coerce")
df[_last_observed_col] = _df_ind.map(_last_obs_by_indicator).combine_first(df[_last_observed_col])

# Add associatedGroups.data ids from observed_src by indicator, stored as 'Associated Groups'
if _assoc_groups_target_col in df.columns:
    df[_assoc_groups_target_col] = _df_ind.map(_assoc_groups_by_indicator).combine_first(df[_assoc_groups_target_col])
else:
    df[_assoc_groups_target_col] = _df_ind.map(_assoc_groups_by_indicator)
logger.info("Updated '%s' from observed_src.lastObserved (unique indicators=%s).", _last_observed_col, df[_indicator_col].nunique(dropna=True))

df

# %% [code cell 3]
import pandas as pd

# Ensure Last Observed is datetime
df['Last Observed'] = pd.to_datetime(df['Last Observed'])

# Get last 48 hours relative to latest observation
max_obs = df['Last Observed'].max()
cutoff = max_obs - pd.Timedelta(hours=48)
last_48h_from_max = df[df['Last Observed'] >= cutoff]
logger.info("Last 48h window from max obs (%s): %s rows.", max_obs, len(last_48h_from_max))

last_48h_from_max

# %% [code cell 4]
# Filter last 48h results to indicators seen at more than one partner
last_48h_multiple_partners = last_48h_from_max[last_48h_from_max['Partners'].str.contains(',', na=False)]
logger.info("Multi-partner indicators in window: %s rows.", len(last_48h_multiple_partners))

last_48h_multiple_partners

# %% [code cell 5]
# Filter multi-partner, last-48h indicators to VT score >= 10 based on Explanation text
vt_scores = last_48h_multiple_partners['Explanation'].str.extract(r'VT score:\s*(\d+)', expand=False)
vt_scores = pd.to_numeric(vt_scores, errors='coerce')

last_48h_multi_partners_vt10 = last_48h_multiple_partners[vt_scores >= 10]
logger.info("Multi-partner with VT>=10: %s rows.", len(last_48h_multi_partners_vt10))

last_48h_multi_partners_vt10

# %% [code cell 6]
# Keep only high or critical indicators from the VT>=10, multi-partner, last-48h set
high_critical_last_48h = last_48h_multi_partners_vt10[last_48h_multi_partners_vt10['Severity'].isin(['high', 'critical'])]
logger.info("High/Critical in set: %s rows.", len(high_critical_last_48h))

high_critical_last_48h

# %% [code cell 7]
high_critical_last_48h[high_critical_last_48h['Indicator'] == '45.148.10.141']

# %% [code cell 8]
# Extract VT scores for high/critical last-48h indicators
vt_scores_hc = high_critical_last_48h['Explanation'].str.extract(r'VT score:\s*(\d+)', expand=False)

# VT-based selection only: keep high/critical last-48h indicators with VT score > 15
vt = pd.to_numeric(vt_scores_hc, errors='coerce')
mask_vt = vt >= 15

final_indicators = high_critical_last_48h[mask_vt]
logger.info("Final indicators (VT>=15): %s rows.", len(final_indicators))
final_indicators

# %% [code cell 9]
import sys
import os
import urllib3
from configparser import ConfigParser

# Add your local ThreatConnect SDK to path
sys.path.append(r"Z:\HTOC\Data_Analytics\threatconnect")
from ThreatConnect import ThreatConnect
from RequestObject import RequestObject
from Owners import Owners

# Add your project repo to path
project_root = r"C:\Users\jaskew\Documents\project_repository\scripts\Data Movement\ThrearConnect-api-pull"
if project_root not in sys.path:
    sys.path.append(project_root)

from utils.config_loader import load_config

# Load API config
config_path = os.path.join(project_root, "utils", "config.json")
try:
    api_secret_key, api_access_id, api_base_url, api_default_org = load_config(config_path)
    logger.info("Loaded config from: %s", config_path)
    logger.info("Base URL: %s", api_base_url)
    logger.info("Access ID: %s", _mask(api_access_id))
    logger.info("Default Org: %s", api_default_org)
except Exception as e:
    logger.exception("Failed to load configuration from %s", config_path)
    sys.exit(1)

# Disable SSL verification warnings (use cautiously)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
verify_ssl = False

# Initialize ThreatConnect session
try:
    tc = ThreatConnect(api_access_id, api_secret_key, api_default_org, api_base_url)
    logger.info("ThreatConnect initialized.")
except Exception as e:
    logger.exception("Failed to initialize ThreatConnect.")
    sys.exit(1)

# Define the owner (organization scope)
owner = 'HTOC Org'

# Create a request object to fetch indicators (or other data)
try:
    ro = RequestObject()
    ro.set_http_method('GET')
    ro.set_owner(owner)
    ro.set_owner_allowed(True)
    # ro.set_resource_pagination(True)  # Uncomment if needed
    logger.info("RequestObject successfully created (owner=%s).", owner)
except Exception as e:
    logger.exception("Failed to initialize RequestObject.")
    sys.exit(1)

# %% [code cell 10]
import pandas as pd
from datetime import datetime, timedelta
import pytz
import urllib.parse

# Configuration for ThreatConnect indicator query
QUERY_LOOKBACK_DAYS = 30  # days of lastObserved activity to include
INDICATOR_TYPE_NAMES = [
    "Address", "EmailAddress", "File", "Host", "URL", "ASN", "CIDR",
    "Email Subject", "Hashtag", "Mutex", "Registry Key", "User Agent",
]
OWNER_NAMES = [
    'HTOC Org',
    'CISA Federal Feed',
    'CMS_CTI',
    'Crowdstrike Falcon Intelligence',
    'DHS CISCP',
    'Intel471',
    'Mandiant Advantage Threat Intelligence',
    'VA_TIP Data',
]
RESULT_PAGE_SIZE = 500  # keep this smaller; same fields, just paged
INDICATOR_CHUNK_SIZE = 100  # limit size of summary IN (...) clauses

# Setup
cutoff = pd.Timestamp.utcnow()
start_date = (datetime.now(pytz.UTC) - timedelta(days=QUERY_LOOKBACK_DAYS)).date()
start = f"{start_date}T00:00:00Z"

type_names = INDICATOR_TYPE_NAMES
type_name_condition = ", ".join([f'"{t}"' for t in type_names])

list_of_owners = OWNER_NAMES

# Build owner IN (...) clause
owner_condition = ", ".join([f'"{o}"' for o in list_of_owners])

# Build indicator list from final_indicators (must already exist)
if 'final_indicators' not in globals():
    raise RuntimeError("final_indicators is not defined. Run the scoring cell first.")

if 'Indicator' not in final_indicators.columns:
    raise RuntimeError("final_indicators must have an 'Indicator' column.")

indicator_values = (
    final_indicators['Indicator']
    .astype(str)
    .str.strip()
    .unique()
    .tolist()
)

if not indicator_values:
    raise RuntimeError("final_indicators has no Indicator values to query.")

# Chunk indicators so the TQL summary IN (...) clause and URL don't get too large
indicator_chunks = [
    indicator_values[i:i + INDICATOR_CHUNK_SIZE]
    for i in range(0, len(indicator_values), INDICATOR_CHUNK_SIZE)
]

final_results = []

# Query indicators (paginate so you don't 502 with heavy fields)
# Create a NEW RequestObject WITHOUT owner restriction to query across all owners
ro_multi = RequestObject()
ro_multi.set_http_method('GET')

for chunk in indicator_chunks:
    # Build summary IN ("x","y",...) clause for this chunk
    summary_condition = ", ".join([f'"{v}"' for v in chunk])

    tql_raw = (
        f'ownerName IN ({owner_condition}) AND '
        f'typeName IN ({type_name_condition}) AND '
        f'lastObserved >= "{start}" AND '
        f'summary IN ({summary_condition})'
    )

    tql_encoded = urllib.parse.quote(tql_raw)

    result_start = 0
    result_limit = RESULT_PAGE_SIZE

    while True:
        try:
            # NOTE: same fields list you requested (tags,observations,associatedGroups,falsePositives,threatAssess)
            ro_multi.set_request_uri(
                f'/v3/indicators?tql={tql_encoded}'
                f'&fields=tags,observations,associatedGroups,falsePositives,threatAssess'
                f'&resultStart={result_start}&resultLimit={result_limit}'
            )

            response = tc.api_request(ro_multi)

            ct = response.headers.get('content-type', '')
            if not ct.startswith('application/json'):
                raise RuntimeError(f"Non-JSON response ({ct}): {response.content[:200]}")

            results = response.json()
            data_items = results.get('data', []) or []

            # stop when no more results
            if not data_items:
                break

            final_results.append(results)
            logger.info("Fetched %s indicators (chunk=%s, resultStart=%s).", len(data_items), len(chunk), result_start)
            result_start += result_limit

        except Exception as e:
            logger.exception("Failed to query indicators (chunk=%s, resultStart=%s).", len(chunk), result_start)
            break

# Normalize results
normalized_data = []
for result in final_results:
    data_items = result.get('data', [])
    if not data_items:
        display("No data returned in API response:", result)
    for item in data_items:
        if isinstance(item, dict) and 'summary' in item:
            normalized_data.append(item)

if normalized_data:
    observed_src = pd.json_normalize(normalized_data)
    observed_src['indicator'] = observed_src['summary'].astype(str).str.split().str[0].str.strip()
    observed_src['lastObserved'] = pd.to_datetime(observed_src['lastObserved'], utc=True, errors='coerce')
    observed_src = observed_src[observed_src['lastObserved'] >= pd.to_datetime(start, utc=True)]

    # Create a 'sources' column by aggregating ownerName values per indicator
    sources_per_indicator = (
        observed_src.groupby('indicator')['ownerName']
        .apply(lambda x: ', '.join(sorted(set(x))))
        .reset_index()
        .rename(columns={'ownerName': 'sources'})
    )

    # Merge sources back into observed_src
    observed_src = observed_src.merge(sources_per_indicator, on='indicator', how='left')
    # Filter to keep only records where ownerName is 'HTOC Org'
    observed_src = observed_src[observed_src['ownerName'] == 'HTOC Org'].copy()
else:
    logger.warning("No valid indicator data found.")
    observed_src = pd.DataFrame()

logger.info("observed_src (final query) rows=%s cols=%s", len(observed_src), len(observed_src.columns))

# %% [code cell 11]
import pandas as pd

# Helper to see if an indicator has an I&W tag
def has_iw(tags_value):
    """
    tags_value is typically a list of dicts from ThreatConnect, e.g.:
    [{'name': 'I&W'}, {'name': 'something else'}, ...]
    """
    if tags_value is None or (isinstance(tags_value, float) and pd.isna(tags_value)):
        return False

    if not isinstance(tags_value, (list, tuple)):
        return False

    for t in tags_value:
        try:
            if isinstance(t, dict):
                name = str(t.get('name', '')).strip()
            else:
                name = str(t).strip()

            if name.lower() in {"i&w", "i & w", "iw"}:
                return True
        except Exception:
            continue
    return False

# 1) Add has_iw flag to observed_src if tags.data exists
if 'tags.data' in observed_src.columns:
    observed_src['has_iw'] = observed_src['tags.data'].apply(has_iw)
else:
    observed_src['has_iw'] = False

# 2) Collapse to one flag per indicator
iw_per_indicator = (
    observed_src.groupby('indicator', dropna=False)['has_iw']
    .max()  # any True -> True
    .reset_index()
    .rename(columns={'indicator': 'Indicator', 'has_iw': 'Reported I&W?_raw'})
)

# 3) Drop ANY existing Reported I&W? variants (_x, _y, etc.)
cols_to_drop = [c for c in final_indicators.columns if c.startswith('Reported I&W?')]
final_indicators = final_indicators.drop(columns=cols_to_drop, errors='ignore')

# 4) Merge once, with a temporary raw boolean column
final_indicators = final_indicators.merge(
    iw_per_indicator,
    on='Indicator',
    how='left'
)

# 5) Convert to Yes/No, defaulting missing to 'No'
final_indicators['Reported I&W?'] = (
    final_indicators['Reported I&W?_raw']
    .fillna(False)
    .map({True: 'Yes', False: 'No'})
)

# 6) Drop the temporary raw column
final_indicators = final_indicators.drop(columns=['Reported I&W?_raw'])

final_indicators

# %% [code cell 12]
import pandas as pd

# Load external tags data
tags_path = r"Z:\HTOC\Data_Analytics\Data\Observed_Tags\htoc_observed_indicator_tags.csv"
tags_df = pd.read_csv(tags_path)

# Find indicator column (case-insensitive)
tags_indicator_col = None
for col in tags_df.columns:
    if str(col).lower() == 'indicator':
        tags_indicator_col = col
        break
if tags_indicator_col is None:
    raise ValueError("Could not find an 'Indicator' column in the tags CSV.")

# Find tags column — check both 'tag' (singular) and 'tags' (plural)
tags_value_col = None
for col in tags_df.columns:
    if str(col).lower() in ('tags', 'tag'):
        tags_value_col = col
        break
if tags_value_col is None:
    raise ValueError(
        f"Could not find a 'Tag' or 'Tags' column in the tags CSV. "
        f"Available columns: {list(tags_df.columns)}"
    )

# Build indicator -> tags lookup and map onto final_indicators
indicator_to_tags = tags_df.set_index(tags_indicator_col)[tags_value_col].to_dict()
final_tags = final_indicators['Indicator'].map(indicator_to_tags)

# Insert 'Tags' as the second-to-last column
final_cols = list(final_indicators.columns)
if 'Tags' in final_cols:
    final_cols.remove('Tags')
new_cols = final_cols[:-1] + ['Tags'] + final_cols[-1:]

final_indicators['Tags'] = final_tags
final_indicators = final_indicators[new_cols]

# %% [code cell 13]
from datetime import datetime

# Build dated output path
today_str = datetime.today().strftime('%Y%m%d')  # e.g. 20260316
output_path = rf"Z:\HTOC\Data_Analytics\Data\Threat Assessment Scores\ThreatAssessI_W\ThreatAssessI_W_{today_str}.xlsx"

# Excel can't write timezone-aware datetimes; strip tz info before export
_dt_tz_cols = final_indicators.select_dtypes(include=["datetimetz"]).columns
for _c in _dt_tz_cols:
    final_indicators[_c] = final_indicators[_c].dt.tz_convert(None)

# Write to Excel with explicit column widths/wrapping for readability
logger.info("Writing Excel output: %s", output_path)
try:
    iw_col = "Reported I&W?"
    if iw_col not in final_indicators.columns:
        raise KeyError(f"Missing required column '{iw_col}' for sheet split.")

    final_iw_no = final_indicators[final_indicators[iw_col] == "No"].copy()
    final_iw_yes = final_indicators[final_indicators[iw_col] == "Yes"].copy()

    with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:
        final_iw_no.to_excel(writer, index=False, sheet_name="I&W_No")
        final_iw_yes.to_excel(writer, index=False, sheet_name="I&W_Yes")

        workbook = writer.book
        wrap_fmt = workbook.add_format({"text_wrap": True, "valign": "top"})

        for sheet_name, sheet_df in [("I&W_No", final_iw_no), ("I&W_Yes", final_iw_yes)]:
            worksheet = writer.sheets[sheet_name]
            worksheet.set_column(0, len(final_indicators.columns) - 1, 18)

            if "Explanation" in final_indicators.columns:
                _exp_idx = final_indicators.columns.get_loc("Explanation")
                worksheet.set_column(_exp_idx, _exp_idx, 100, wrap_fmt)

            if "Associated Groups" in final_indicators.columns:
                _ag_idx = final_indicators.columns.get_loc("Associated Groups")
                worksheet.set_column(_ag_idx, _ag_idx, 45, wrap_fmt)

        logger.info(
            "Excel write succeeded (total=%s, I&W No=%s, I&W Yes=%s).",
            len(final_indicators),
            len(final_iw_no),
            len(final_iw_yes),
        )
except Exception:
    logger.exception("Excel write failed: %s", output_path)
    raise

output_path

