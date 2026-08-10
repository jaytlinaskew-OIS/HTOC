r"""
ThreatScoreIW — scheduled runner.

Source notebook: ThreatScoreIW.ipynb
Hardened for Task Scheduler (UNC share roots, UTF-8 logs, strict exit contract).

Writes daily workbook under:
  \\10.1.4.22\data\HTOC\Data_Analytics\Data\Threat Assessment Scores\ThreatAssessI_W\

Exit contract for the .bat launcher:
  - print PIPELINE_OK and exit 0 on full success
  - non-zero exit on hard failure; never exit 0 without PIPELINE_OK
"""

import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# --- notebook cell 0 ---
import sys
import os
import urllib3
from configparser import ConfigParser

# Add your local ThreatConnect SDK to path
HTOC_SHARE_ROOT = os.environ.get('HTOC_SHARE_ROOT', r'\\10.1.4.22\data\HTOC')
TC_SDK = os.path.join(HTOC_SHARE_ROOT, 'Data_Analytics', 'threatconnect')
if TC_SDK not in sys.path:
    sys.path.insert(0, TC_SDK)
from ThreatConnect import ThreatConnect
from RequestObject import RequestObject
from Owners import Owners

# Add your project repo to path
project_root = r"\\cscso1fsappv01\home\jaskew\HTOC\scripts\Data Movement\ThrearConnect-api-pull"
if project_root not in sys.path:
    sys.path.append(project_root)

from utils.config_loader import load_config

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

# Disable SSL verification warnings (use cautiously)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
verify_ssl = False

# Initialize ThreatConnect session
try:
    tc = ThreatConnect(api_access_id, api_secret_key, api_default_org, api_base_url)
    print("ThreatConnect initialized.")
except Exception as e:
    print(f"[ERROR] Failed to initialize ThreatConnect: {e}")
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
    print("RequestObject successfully created.")
except Exception as e:
    print(f"[ERROR] Failed to initialize RequestObject: {e}")
    sys.exit(1)



# --- notebook cell 1 ---
import pandas as pd
from datetime import datetime, timedelta
import pytz
import urllib.parse

# Configuration for ThreatConnect indicator query
QUERY_LOOKBACK_HOURS = 48  # rolling wall-clock window in UTC (not calendar midnights)
INDICATOR_TYPE_NAMES = [
    "Address", "EmailAddress", "File", "Host", "URL", "ASN", "CIDR",
    "Email Subject", "Hashtag", "Mutex", "Registry Key", "User Agent","Stripped URL"
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

# Single cutoff instant for TQL, observed_src filter, and workbook filter
_now_utc = datetime.now(pytz.UTC)
_last_observed_cutoff_dt = _now_utc - timedelta(hours=QUERY_LOOKBACK_HOURS)
start = _last_observed_cutoff_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
LAST_OBSERVED_CUTOFF_TS = pd.Timestamp(_last_observed_cutoff_dt)

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
            break

        final_results.append(results)
        result_start += result_limit

    except Exception as e:
        print(f"FATAL: Failed to query indicators (start={result_start}): {e}")
        sys.exit(2)

# Normalize results
normalized_data = []
for result in final_results:
    data_items = result.get('data', [])
    if not data_items:
        print("No data returned in API response:", result)
    for item in data_items:
        if isinstance(item, dict) and 'summary' in item:
            normalized_data.append(item)

if normalized_data:
    observed_src = pd.json_normalize(normalized_data)
    observed_src['indicator'] = observed_src['summary'].astype(str).str.split().str[0].str.strip()
    observed_src['lastObserved'] = pd.to_datetime(observed_src['lastObserved'], utc=True, errors='coerce')
    observed_src = observed_src[observed_src["lastObserved"] >= LAST_OBSERVED_CUTOFF_TS]
    
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
    # Keep rows where top-level rating >= 3 OR coalesced threatAssessRating >= 3, and
    # (coalesced TA confidence >= 50 OR top-level confidence >= 50).
    # Coalesce flat vs nested threatAssess columns; keep top-level rating/confidence separate for OR.
    _rating_cols = ("threatAssessRating", "threatAssess.threatAssessRating", "rating")
    _confidence_cols = ("threatAssessConfidence", "threatAssess.threatAssessConfidence")

    def _first_non_null_numeric(df, ordered_cols):
        present = [c for c in ordered_cols if c in df.columns]
        if not present:
            return None
        out = pd.to_numeric(df[present[0]], errors="coerce")
        for c in present[1:]:
            s = pd.to_numeric(df[c], errors="coerce")
            out = out.mask(out.isna(), s)
        return out

    _tar = _first_non_null_numeric(observed_src, _rating_cols)
    _tc = _first_non_null_numeric(observed_src, _confidence_cols)
    if _tar is None or _tc is None:
        raise KeyError(
            f"Could not resolve Threat Assess columns. Tried rating={_rating_cols}, "
            f"confidence={_confidence_cols}. Columns: {list(observed_src.columns)}"
        )
    if "rating" in observed_src.columns:
        _r = pd.to_numeric(observed_src["rating"], errors="coerce")
    else:
        _r = pd.Series(float("nan"), index=observed_src.index, dtype=float)

    if "confidence" in observed_src.columns:
        _c = pd.to_numeric(observed_src["confidence"], errors="coerce")
    else:
        _c = pd.Series(float("nan"), index=observed_src.index, dtype=float)

    _pre_ta = len(observed_src)
    # Use >= 50 so a boundary value of 50.0 is included (strict > 50 dropped those rows).
    _pass_rating_band = (_tar >= 3) | (_r >= 3)
    _pass_confidence_band = (_tc >= 50) | (_c >= 50)
    observed_src = observed_src[_pass_rating_band & _pass_confidence_band].copy()
    print(
        f"Threat assess filter ((rating>=3 OR threatAssessRating>=3), confidence>=50) coalescing {_rating_cols} / {_confidence_cols}: "
        f"{_pre_ta} -> {len(observed_src)} rows."
    )
else:
    print("FATAL: No valid indicator data found.")
    sys.exit(3)

print(observed_src)

# --- notebook cell 2 skipped (ad-hoc indicator lookup) ---

# --- notebook cell 3 ---
import pandas as pd
import ast
from datetime import datetime, timedelta
import pytz

# Load the Excel file
file_path = r"\\10.1.4.22\data\HTOC\Data_Analytics\Data\Threat Assessment Scores\Threat_Assessment_Scores.xlsx"
df = pd.read_excel(file_path)


# Keep only indicators that are also in observed_src
_indicator_col = next((c for c in ["indicator", "Indicator", "INDICATOR"] if c in df.columns), None)
if _indicator_col is None:
    raise KeyError(f"Could not find indicator column in df. Columns: {list(df.columns)}")

_observed_indicators = set(observed_src["indicator"].dropna().astype(str))
df = df[df[_indicator_col].astype(str).isin(_observed_indicators)].copy()

# Last Observed column: values come only from observed_src (ThreatConnect), not the workbook
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
    # Handle scalar nulls safely; avoid pd.isna on list-like values.
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

# Last Observed: only from ThreatConnect (observed_src); do not fall back to Excel dates
_df_ind = df[_indicator_col].astype(str)
df[_last_observed_col] = pd.to_datetime(_df_ind.map(_last_obs_by_indicator), utc=True, errors="coerce")
_qh = QUERY_LOOKBACK_HOURS if "QUERY_LOOKBACK_HOURS" in globals() else 48
_last_obs_cutoff = (
    LAST_OBSERVED_CUTOFF_TS
    if "LAST_OBSERVED_CUTOFF_TS" in globals()
    else pd.Timestamp(datetime.now(pytz.UTC) - timedelta(hours=_qh), tz="UTC")
)
_pre_lo = len(df)
df = df[df[_last_observed_col].notna() & (df[_last_observed_col] >= _last_obs_cutoff)].copy()
print(
    f"Last Observed filter (ThreatConnect only, >= {_last_obs_cutoff}): {_pre_lo} -> {len(df)} rows."
)

_df_ind = df[_indicator_col].astype(str)

# Add associatedGroups.data ids from observed_src by indicator, stored as 'Associated Groups'
if _assoc_groups_target_col in df.columns:
    df[_assoc_groups_target_col] = _df_ind.map(_assoc_groups_by_indicator).combine_first(df[_assoc_groups_target_col])
else:
    df[_assoc_groups_target_col] = _df_ind.map(_assoc_groups_by_indicator)

df

# --- notebook cell 4 ---
import os
import pandas as pd
from datetime import datetime, timedelta

# Base file path with placeholder for date
base_path = r"\\10.1.4.22/data/HTOC/Data_Analytics/Data/OpDiv_Observations/htoc_opdiv_obs_d{date}.csv"
#base_path = r"C:\Users\jaskew\Documents\project_repository\data\raw\ObservationDataFiles\htoc_opdiv_obs_d{date}.csv"
date_format = "%Y%m%d"

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
    
    return existing_files

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

# Example Usage:
# Fetch file paths for the last 3 days
file_paths = get_file_paths(base_path, days=2)

# Load observed data
observed_data_df = load_observed_data(file_paths)


# --- notebook cell 5 ---
observed_data_df[observed_data_df['indicator'] == '174.128.251.99']

# --- notebook cell 6 ---
# Keep only indicators that are present in observed_data_df and seen by 2+ OpDiv partners
_indicator_col_df = next((c for c in ["indicator", "Indicator", "INDICATOR"] if c in df.columns), None)
_indicator_col_obs = next((c for c in ["indicator", "Indicator", "INDICATOR"] if c in observed_data_df.columns), None)
_opdiv_col = next((c for c in ["OpDiv", "opdiv", "OPDIV"] if c in observed_data_df.columns), None)

if _indicator_col_df is None:
    raise KeyError(f"Could not find indicator column in df. Columns: {list(df.columns)}")
if _indicator_col_obs is None:
    raise KeyError(f"Could not find indicator column in observed_data_df. Columns: {list(observed_data_df.columns)}")
if _opdiv_col is None:
    raise KeyError(f"Could not find OpDiv column in observed_data_df. Columns: {list(observed_data_df.columns)}")

obs = observed_data_df.dropna(subset=[_indicator_col_obs, _opdiv_col]).copy()
obs[_indicator_col_obs] = obs[_indicator_col_obs].astype(str).str.strip()
obs[_opdiv_col] = obs[_opdiv_col].astype(str).str.strip()

partners_by_indicator = (
    obs.groupby(_indicator_col_obs)[_opdiv_col]
    .apply(lambda s: sorted(set(x for x in s if x)))
)

eligible_partners = partners_by_indicator[partners_by_indicator.str.len() >= 2]
opdiv_map = eligible_partners.apply(lambda vals: ", ".join(vals))

last_24h_multiple_partners = df[
    df[_indicator_col_df].astype(str).str.strip().isin(eligible_partners.index)
].copy()
last_24h_multiple_partners["OpDiv"] = (
    last_24h_multiple_partners[_indicator_col_df].astype(str).str.strip().map(opdiv_map)
)
last_24h_multiple_partners["Partners"] = last_24h_multiple_partners["OpDiv"]

last_24h_multiple_partners

# --- notebook cell 7 ---
# Filter multi-partner, last-24h indicators to VT score >= 10 based on Explanation text
vt_scores = last_24h_multiple_partners['Explanation'].str.extract(r'VT score:\s*(\d+)', expand=False)
vt_scores = pd.to_numeric(vt_scores, errors='coerce')

last_24h_multi_partners_vt15 = last_24h_multiple_partners[vt_scores >= 2]

last_24h_multi_partners_vt15

# --- notebook cell 8 ---
# Keep only high or critical indicators from the VT>=10, multi-partner, last-24h set
final_indicators = last_24h_multi_partners_vt15[last_24h_multi_partners_vt15['Severity'].isin(['high', 'critical'])]

final_indicators

# --- notebook cell 9 ---
import pandas as pd

# Load external tags data
tags_path = r"\\10.1.4.22\data\HTOC\Data_Analytics\Data\Observed_Tags\htoc_observed_indicator_tags.csv"
tags_df = pd.read_csv(tags_path)

# The indicator column in the tags CSV could be e.g. 'Indicator' or 'indicator'
tags_indicator_col = None
for col in tags_df.columns:
    if str(col).lower() == 'indicator':
        tags_indicator_col = col
        break
if tags_indicator_col is None:
    raise ValueError("Could not find an 'Indicator' column in the tags CSV.")

# The tags field might be called 'Tags', 'tags', or similar
# The tags field might be called 'Tags', 'tags', 'Tag', 'tag', etc.
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
# For fast lookup, set up a mapping of indicator -> tags value.
indicator_to_tags = tags_df.set_index(tags_indicator_col)[tags_value_col].to_dict()

# Prepare 'Tags' values for final_indicators
final_tags = final_indicators['Indicator'].map(indicator_to_tags)

# Insert the 'Tags' column as the second to last column
final_cols = list(final_indicators.columns)
if 'Tags' in final_cols:
    final_cols.remove('Tags')
second_to_last_idx = -1 if len(final_cols) == 0 else -1
new_cols = final_cols[:second_to_last_idx] + ['Tags'] + final_cols[second_to_last_idx:]

final_indicators['Tags'] = final_tags
final_indicators = final_indicators[new_cols]
final_indicators

# --- notebook cell 10 ---
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

# Rename column 'HTOC Threat Score' to 'PRISM Score' if it exists
if "HTOC Threat Score" in final_indicators.columns:
    final_indicators = final_indicators.rename(columns={"HTOC Threat Score": "PRISM Score"})


final_indicators

# --- notebook cell 11 ---
import ipaddress

MIN_HOSTS_PER_SUBNET = 5  # minimum hosts in a /24 before rolling up to CIDR


def _to_ip(value):
    try:
        return ipaddress.ip_address(str(value).strip())
    except ValueError:
        return None


def _subnet24(ip):
    if ip is None:
        return None
    return str(ipaddress.ip_network(f"{ip}/24", strict=False))


def _union_csv(series):
    parts = set()
    for val in series.dropna():
        for part in str(val).split(","):
            part = part.strip()
            if part:
                parts.add(part)
    return ", ".join(sorted(parts)) if parts else None


def _max_severity(series):
    order = {"critical": 2, "high": 1}
    vals = [str(v).strip().lower() for v in series.dropna()]
    if not vals:
        return None
    return max(vals, key=lambda s: order.get(s, 0))


def _has_threat_actor(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return False
    return bool(str(value).strip())


def condense_final_indicators(df, min_hosts=MIN_HOSTS_PER_SUBNET):
    """Roll dense /24 Address clusters into CIDR rows; keep singles and threat-actor IPs."""
    df = df.copy()
    type_col = "Indicator Type" if "Indicator Type" in df.columns else "Type"

    df["_ip"] = df["Indicator"].map(_to_ip)
    df["_subnet24"] = df["_ip"].map(_subnet24)

    ta_col = "Threat Actor" if "Threat Actor" in df.columns else None
    if ta_col:
        df["_has_ta"] = df[ta_col].map(_has_threat_actor)
    else:
        df["_has_ta"] = False

    condensable_mask = (
        df[type_col].eq("Address")
        & df["_ip"].notna()
        & ~df["_has_ta"]
    )

    subnet_counts = df.loc[condensable_mask].groupby("_subnet24").size()
    dense_subnets = set(subnet_counts[subnet_counts >= min_hosts].index)

    dense_mask = condensable_mask & df["_subnet24"].isin(dense_subnets)
    dense_df = df[dense_mask].copy()
    keep_df = df[~dense_mask].copy()

    if dense_df.empty:
        out = df.drop(columns=["_ip", "_subnet24", "_has_ta"], errors="ignore")
        out["_member_ips"] = out["Indicator"].map(lambda x: [str(x)])
        return out

    numeric_max_cols = [
        c for c in [
            "Observation Yearly Count",
            "ThreatConnect Rating",
            "Observation Penalty Multiplier",
            "Botnet Flag",
            "False Positives",
            "Tagging Boost",
            "CAL Score",
            "ThreatConnect Score",
            "PRISM Score",
        ]
        if c in dense_df.columns
    ]

    agg = {c: "max" for c in numeric_max_cols}
    agg.update({
        "Indicator": lambda s: sorted(s.astype(str).tolist()),
        "Last Observed": "max",
        type_col: lambda _: "CIDR",
        "Severity": _max_severity,
        "Partners": _union_csv,
        "OpDiv": _union_csv,
        "Threat Actor": _union_csv,
        "Tagging Boost Reason": _union_csv,
        "Associated Groups": _union_csv,
        "incidents/events": _union_csv,
        "Tags": "first",
        "Explanation": "first",
    })

    if "Reported I&W?" in dense_df.columns:
        agg["Reported I&W?"] = lambda s: "Yes" if (s == "Yes").any() else "No"

    condensed = dense_df.groupby("_subnet24", as_index=False).agg(agg)
    condensed = condensed.rename(columns={"Indicator": "_member_ips"})
    condensed["Indicator"] = condensed["_subnet24"]

    drop_cols = ["_subnet24", "_ip", "_has_ta"]
    condensed = condensed.drop(columns=drop_cols, errors="ignore")
    keep_df = keep_df.drop(columns=drop_cols, errors="ignore")
    keep_df["_member_ips"] = keep_df["Indicator"].map(lambda x: [str(x)])

    out = pd.concat([condensed, keep_df], ignore_index=True, sort=False)

    base_cols = [c for c in df.columns if c not in drop_cols]
    ordered = []
    for col in base_cols:
        ordered.append(col)
        if col == "Indicator" and "_member_ips" in out.columns:
            ordered.append("_member_ips")
    ordered.extend([c for c in out.columns if c not in ordered])
    return out[[c for c in ordered if c in out.columns]]


_before = len(final_indicators)
final_indicators = condense_final_indicators(final_indicators)
print(f"Subnet condensation: {_before} -> {len(final_indicators)} rows (min_hosts={MIN_HOSTS_PER_SUBNET})")

# _member_ips is kept on final_indicators for Excel dropdown export only — not shown here
final_indicators.drop(columns=["_member_ips"], errors="ignore")

# --- notebook cell 12 ---
from datetime import datetime
import re
from xlsxwriter.utility import xl_rowcol_to_cell

# Build dated output path
today_str = datetime.today().strftime('%Y%m%d')  # e.g. 20260316
output_path = rf"\\10.1.4.22\data\HTOC\Data_Analytics\Data\Threat Assessment Scores\ThreatAssessI_W\ThreatAssessI_W_{today_str}.xlsx"
os.makedirs(os.path.dirname(output_path), exist_ok=True)

# Excel can't write timezone-aware datetimes; strip tz info before export
_dt_tz_cols = final_indicators.select_dtypes(include=["datetimetz"]).columns
for _c in _dt_tz_cols:
    final_indicators[_c] = final_indicators[_c].dt.tz_convert(None)

iw_col = "Reported I&W?"
if iw_col not in final_indicators.columns:
    raise KeyError(f"Missing required column '{iw_col}' for sheet split.")


def _subnet_range_name(subnet):
    return "MBR_" + re.sub(r"[^A-Za-z0-9]", "_", str(subnet))[:200]


def _prepare_export_df(df):
    export_df = df.copy()
    member_ip_lists = export_df.pop("_member_ips") if "_member_ips" in export_df.columns else pd.Series([None] * len(export_df), index=export_df.index)

    indicator_idx = export_df.columns.get_loc("Indicator") + 1
    export_df.insert(indicator_idx, "Host IP", "")

    member_map = {}
    for idx, ips in member_ip_lists.items():
        if isinstance(ips, list) and len(ips) > 1:
            export_df.at[idx, "Host IP"] = ips[0]
            member_map[export_df.at[idx, "Indicator"]] = ips
        elif isinstance(ips, list) and len(ips) == 1:
            export_df.at[idx, "Host IP"] = ips[0]
        else:
            export_df.at[idx, "Host IP"] = ""

    return export_df, member_map


def _write_subnet_members_sheet(workbook, member_map):
    range_names = {}
    if not member_map:
        return range_names

    ws = workbook.add_worksheet("Subnet_Members")
    ws.hide()

    for col, (subnet, ips) in enumerate(member_map.items()):
        ws.write(0, col, subnet)
        for row, ip in enumerate(ips, start=1):
            ws.write(row, col, ip)

        start = xl_rowcol_to_cell(1, col, row_abs=True, col_abs=True)
        end = xl_rowcol_to_cell(len(ips), col, row_abs=True, col_abs=True)
        name = _subnet_range_name(subnet)
        workbook.define_name(name, f"='Subnet_Members'!{start}:{end}")
        range_names[subnet] = name

    return range_names


def _apply_member_dropdowns(worksheet, sheet_df, member_map, range_names, member_col_name="Host IP"):
    if member_col_name not in sheet_df.columns:
        return

    member_col_idx = sheet_df.columns.get_loc(member_col_name)
    for row_idx, row in enumerate(sheet_df.itertuples(index=False), start=1):
        indicator = getattr(row, "Indicator")
        if indicator not in member_map:
            continue

        ips = member_map[indicator]
        worksheet.data_validation(
            row_idx,
            member_col_idx,
            row_idx,
            member_col_idx,
            {
                "validate": "list",
                "source": f"={range_names[indicator]}",
                "input_title": "Host IP",
                "input_message": f"Select one of {len(ips)} hosts in {indicator}",
            },
        )


export_df, member_map = _prepare_export_df(final_indicators)
final_iw_no = export_df[export_df[iw_col] == "No"].copy()
final_iw_yes = export_df[export_df[iw_col] == "Yes"].copy()

# Write to one workbook with two named sheets
with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:
    final_iw_no.to_excel(writer, index=False, sheet_name="I&W_No")
    final_iw_yes.to_excel(writer, index=False, sheet_name="I&W_Yes")

    workbook = writer.book
    range_names = _write_subnet_members_sheet(workbook, member_map)
    wrap_fmt = workbook.add_format({"text_wrap": True, "valign": "top"})

    # Set defaults first, then tune long text columns for each sheet
    for sheet_name, sheet_df in [("I&W_No", final_iw_no), ("I&W_Yes", final_iw_yes)]:
        worksheet = writer.sheets[sheet_name]
        worksheet.set_column(0, len(export_df.columns) - 1, 18)

        if "Explanation" in export_df.columns:
            _exp_idx = export_df.columns.get_loc("Explanation")
            worksheet.set_column(_exp_idx, _exp_idx, 100, wrap_fmt)

        if "Associated Groups" in export_df.columns:
            _ag_idx = export_df.columns.get_loc("Associated Groups")
            worksheet.set_column(_ag_idx, _ag_idx, 45, wrap_fmt)

        if "Host IP" in export_df.columns:
            _member_idx = export_df.columns.get_loc("Host IP")
            worksheet.set_column(_member_idx, _member_idx, 22)

        _apply_member_dropdowns(worksheet, sheet_df, member_map, range_names)

output_path

if not os.path.exists(output_path):
    print(f'FATAL: Expected output missing after write: {output_path}')
    sys.exit(4)
print('PIPELINE_OK')
sys.exit(0)
