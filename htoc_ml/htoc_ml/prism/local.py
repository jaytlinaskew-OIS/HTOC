"""Local CSVs: OpDiv observations, threat-actor tags, partners, incidents."""
from __future__ import annotations

import glob
import os
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta

import pandas as pd

from htoc_ml.prism.config import PrismConfig
from htoc_ml.prism.tags import PB_START_LOWER_TAGS

KNOWN_PARTNERS = {"DHA", "OS", "FDA", "CMS", "VA", "HRSA", "NIH", "IHS", "HHS", "CDC"}
OPDIV_USE_COLS = ["indicator", "observations", "OpDiv", "obs_date"]
OPDIV_DTYPES = {"indicator": "str", "observations": "int32", "OpDiv": "category", "obs_date": "str"}
BOTNET_TAGS = {
    "scanning", "ddos", "spam", "phishing", "cryptojacking",
    "credential stuffing", "ransomware", "data theft",
    "cross site scripting attacks", "sql injections",
}
MASS_SCANNER_TIER1_OBS = 10_000
MASS_SCANNER_TIER2_OBS = 100_000
MASS_SCANNER_OPDIV_MIN = 5
GROUP_TYPES = {"incident", "event"}
INCIDENT_ID_REGEX = re.compile(r"\bINC\d+\b", re.IGNORECASE)
INCIDENT_COLUMN = "incidents/events"


def load_opdiv_observations(config: PrismConfig) -> pd.DataFrame:
    template = config.opdiv_template
    directory = os.path.normpath(os.path.dirname(template))
    available = {os.path.normpath(p) for p in glob.glob(os.path.join(directory, "htoc_opdiv_obs_d*.csv"))}
    today = datetime.now(UTC).replace(tzinfo=None)
    paths = []
    for i in range(config.opdiv_lookback_days):
        path = os.path.normpath(template.format(date=(today - timedelta(days=i)).strftime("%Y%m%d")))
        if path in available:
            paths.append(path)
    print(f"Found {len(paths)} of {config.opdiv_lookback_days} OpDiv files to load")

    def _read(path):
        try:
            return pd.read_csv(path, usecols=OPDIV_USE_COLS, dtype=OPDIV_DTYPES)
        except (OSError, ValueError, pd.errors.ParserError) as exc:
            print(f"Error reading {os.path.basename(path)}: {exc}")
            return None

    with ThreadPoolExecutor(max_workers=16) as pool:
        frames = [f for f in pool.map(_read, paths) if f is not None]
    if not frames:
        return pd.DataFrame()
    frame = pd.concat(frames, ignore_index=True)
    print(f"Loaded {len(frame):,} rows from {len(frames)} files")
    return frame


def mass_scanner_flags(observed: pd.DataFrame) -> pd.DataFrame:
    empty = pd.DataFrame(columns=[
        "indicator", "total_obs_7d", "unique_opdivs_7d", "unique_days_7d",
        "mass_scanner_tier1", "mass_scanner_tier2",
    ])
    if observed.empty or "obs_date" not in observed.columns:
        print("Mass scanner detection skipped — observed data is empty or missing obs_date.")
        return empty
    cutoff_7d = (pd.Timestamp.utcnow() - pd.Timedelta(days=7)).strftime("%Y-%m-%d")
    obs_7d = observed[observed["obs_date"] >= cutoff_7d].copy()
    agg = (
        obs_7d.groupby("indicator")
        .agg(
            total_obs_7d=("observations", "sum"),
            unique_opdivs_7d=("OpDiv", "nunique"),
            unique_days_7d=("obs_date", "nunique"),
        )
        .reset_index()
    )
    broad = agg["unique_opdivs_7d"] >= MASS_SCANNER_OPDIV_MIN
    agg["mass_scanner_tier1"] = (agg["total_obs_7d"] >= MASS_SCANNER_TIER1_OBS) & (agg["total_obs_7d"] < MASS_SCANNER_TIER2_OBS) & broad
    agg["mass_scanner_tier2"] = (agg["total_obs_7d"] >= MASS_SCANNER_TIER2_OBS) & broad
    print(f"Mass scanner — Tier 1: {int(agg['mass_scanner_tier1'].sum())} | Tier 2: {int(agg['mass_scanner_tier2'].sum())}")
    return agg


def merge_threat_actors(observed_src: pd.DataFrame, config: PrismConfig) -> pd.DataFrame:
    tags = pd.read_csv(config.tags_csv)
    records = tags[tags["threat_category"] == config.threat_category]
    condensed = records.groupby("indicator").agg({
        "type": "first",
        "orig_tag": lambda x: ", ".join(sorted(set(x.dropna()))),
        "tag": lambda x: ", ".join(sorted(set(x.dropna()))),
        "threat_category": lambda x: ", ".join(sorted(set(x.dropna()))),
        "NATION STATE": lambda x: ", ".join(sorted(set(x.dropna()))) if x.notna().any() else None,
        "SECURITY ORGANIZATION": lambda x: ", ".join(sorted(set(x.dropna()))) if x.notna().any() else None,
        "MALWARE CLASS": lambda x: ", ".join(sorted(set(x.dropna()))) if x.notna().any() else None,
        "CVE_NBR": lambda x: ", ".join(sorted(set(x.dropna()))) if x.notna().any() else None,
    }).reset_index()
    print(f"Loaded {len(records)} {config.threat_category} rows, condensed to {len(condensed)} unique indicators")
    actor_tags = condensed[[
        "indicator", "tag", "orig_tag", "threat_category",
        "NATION STATE", "SECURITY ORGANIZATION", "MALWARE CLASS", "CVE_NBR",
    ]].rename(columns={
        "tag": "threat_actor",
        "orig_tag": "threat_actor_orig_tag",
        "threat_category": "threat_actor_category",
        "NATION STATE": "threat_nation_state",
        "SECURITY ORGANIZATION": "threat_security_org",
        "MALWARE CLASS": "threat_malware_class",
        "CVE_NBR": "threat_cve_nbr",
    })
    merged = observed_src.merge(actor_tags, on="indicator", how="left")
    print(f"Threat actor matches: {merged['threat_actor'].notna().sum():,} indicators")
    return merged


def annotate_incidents(observed_src: pd.DataFrame) -> pd.DataFrame:
    frame = observed_src.copy()
    if frame.empty:
        frame[INCIDENT_COLUMN] = []
        return frame
    if "associatedGroups.data" not in frame.columns:
        frame[INCIDENT_COLUMN] = "None"
        return frame

    def _groups(val):
        if isinstance(val, list):
            return [i for i in val if isinstance(i, dict) and str(i.get("type", "")).lower() in GROUP_TYPES]
        if isinstance(val, dict):
            return [val] if str(val.get("type", "")).lower() in GROUP_TYPES else []
        return []

    def _label(item):
        if not isinstance(item, dict):
            return str(item)
        typ = str(item.get("type", "")).title()
        number = item.get("id") or item.get("xid") or item.get("name")
        return f"{typ}:{number}" if number is not None else typ

    def _from_description(text):
        if not isinstance(text, str):
            return []
        ids = list(dict.fromkeys(m.upper() for m in INCIDENT_ID_REGEX.findall(text)))
        return [{"type": "incident", "id": inc_id} for inc_id in ids]

    groups = frame["associatedGroups.data"].apply(_groups)
    desc = (
        frame["description"].apply(_from_description)
        if "description" in frame.columns
        else pd.Series([[] for _ in range(len(frame))], index=frame.index)
    )
    combined = groups.combine(desc, lambda a, b: (a or []) + (b or []))
    frame[INCIDENT_COLUMN] = combined.apply(
        lambda lst: ";".join(_label(it) for it in lst) if isinstance(lst, list) and lst else "None"
    )
    print(f"Annotated incidents/events for {len(frame)} indicators.")
    return frame


def attach_tag_lists(observed_src: pd.DataFrame) -> pd.DataFrame:
    frame = observed_src.copy()
    exploded = frame[["indicator", "tags.data"]].explode("tags.data").dropna(subset=["tags.data"])
    exploded["tag_name"] = exploded["tags.data"].apply(lambda x: x.get("name") if isinstance(x, dict) else None)
    indicator_to_tags = exploded.groupby("indicator")["tag_name"].apply(lambda x: [t for t in x if t]).to_dict()
    frame["tag_list"] = frame["indicator"].map(lambda ind: indicator_to_tags.get(ind, []))
    frame["pb_lower_tags"] = frame["indicator"].map(
        lambda ind: [t for t in indicator_to_tags.get(ind, []) if isinstance(t, str) and t.strip().lower() in PB_START_LOWER_TAGS]
    )
    frame["pb_lower_flag"] = frame["pb_lower_tags"].apply(lambda x: isinstance(x, list) and len(x) > 0)
    frame["pb_lower_reason"] = frame["pb_lower_tags"].apply(
        lambda tags: f"pb_tag:{tags[0].strip()}" if isinstance(tags, list) and tags else None
    )
    frame["Botnet"] = frame["indicator"].map(
        lambda ind: [t for t in indicator_to_tags.get(ind, []) if isinstance(t, str) and t.strip().lower() in BOTNET_TAGS]
    )
    return frame


def attach_partners(observed_src: pd.DataFrame, observed_data: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    cutoff_naive = pd.Timestamp.utcnow().tz_convert(None)
    partner_from_obs = _partners_from_obs(observed_data, cutoff_naive)
    tag_agg, tag_fields = _partners_from_tags(observed_src)
    first_cols = [
        "id", "dateAdded", "ownerId", "ownerName", "webLink", "type", "lastModified", "falsePositives",
        "rating", "confidence", "description", "summary", "observations",
        "lastObserved", "privateFlag", "active", "activeLocked", "ip",
        "legacyLink", "source", "address", "url", "threatAssessScore", "calScore",
        "incidents/events", "sources", "threat_actor", "firstseen_date",
        "tag_list", "pb_lower_tags", "pb_lower_flag", "pb_lower_reason",
    ]
    df = observed_src.copy()
    if "Botnet" in df.columns:
        first_cols.append("Botnet")
    base_agg = (
        df.drop(columns=[
            "createdBy.id", "createdBy.userName", "createdBy.firstName", "createdBy.lastName",
            "createdBy.pseudonym", "createdBy.owner", "xid", "eventType", "documentDateAdded",
            "documentType", "fileSize", "fileName", "downVoteCount", "upVoteCount", "type_group",
            "webLink_group", "ownerName_group", "ownerId_group", "dateAdded_group", "id_group",
            "platforms.count", "tactics.count",
        ], errors="ignore")
        .groupby("indicator", as_index=False)[[c for c in first_cols if c in df.columns]]
        .first()
    )
    agg = _combine_partners(base_agg, tag_agg, partner_from_obs)
    for col in ["group_ids", "group_names"] + tag_fields:
        if col in agg.columns:
            agg[col] = agg[col].apply(_clean_list).apply(lambda lst: ", ".join(str(v) for v in lst) if lst else "")
    return agg, tag_fields


def attach_yearly_obs(recent_tags: pd.DataFrame, observed_data: pd.DataFrame) -> pd.DataFrame:
    if observed_data.empty:
        recent_tags["obs_count"] = 0
        return recent_tags
    counts = (
        observed_data.groupby("indicator", as_index=False)["obs_date"]
        .nunique()
        .rename(columns={"obs_date": "obs_count"})
    )
    counts = counts[counts["indicator"].isin(recent_tags["indicator"])]
    merged = recent_tags.merge(counts, on="indicator", how="left")
    print(f"obs_count merged: {len(counts):,} indicators")
    return merged


def _partners_from_obs(observed_data_df: pd.DataFrame, cutoff_naive) -> pd.DataFrame:
    if observed_data_df.empty or "OpDiv" not in observed_data_df.columns:
        return pd.DataFrame()
    observed_data_df = observed_data_df.copy()
    observed_data_df["obs_date"] = pd.to_datetime(observed_data_df["obs_date"], errors="coerce")
    recent = observed_data_df[observed_data_df["obs_date"] >= cutoff_naive - timedelta(days=60)].copy()
    if recent.empty:
        return pd.DataFrame()
    counts = (
        recent.groupby("indicator")["OpDiv"]
        .agg(["nunique", lambda s: ", ".join(sorted(set(s.dropna())))])
        .reset_index()
        .rename(columns={"nunique": "partner_count_obs", "<lambda_0>": "partners_from_obs"})
    )
    return counts[counts["partner_count_obs"] >= 1].copy()


def _partners_from_tags(observed_src: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    exploded = observed_src[["indicator", "tags.data"]].explode("tags.data").dropna(subset=["tags.data"])
    tags_norm = pd.json_normalize(exploded["tags.data"])
    tags_norm.columns = [f"tag_{c}" for c in tags_norm.columns]
    tags_norm["tag_name"] = tags_norm["tag_name"].str.replace("VA CSOC CTS Splunk", "VA Splunk API", regex=False)
    expanded = exploded.reset_index(drop=True).join(tags_norm)
    expanded["partner"] = expanded["tag_name"].map(
        lambda n: n[: -len(" Splunk API")] if isinstance(n, str) and n.endswith(" Splunk API") else None
    )
    tag_fields = list(tags_norm.columns)
    tag_agg = (
        expanded.groupby("indicator", as_index=False)
        .agg({**{f: list for f in tag_fields}, "partner": lambda x: [p for p in dict.fromkeys(x) if p]})
        .rename(columns={"partner": "partners_from_tags"})
    )
    if "tag_name" in tag_agg.columns:
        def extract_standalone(tag_list):
            if not isinstance(tag_list, list):
                return []
            return [t.strip() for t in tag_list if isinstance(t, str) and t.strip() in KNOWN_PARTNERS]

        tag_agg["standalone_partners"] = tag_agg["tag_name"].apply(extract_standalone)

        def combine_tag_partners(row):
            from_tags = row.get("partners_from_tags", [])
            standalone = row.get("standalone_partners", [])
            if isinstance(from_tags, str):
                from_tags = [p.strip() for p in from_tags.split(",") if p.strip()]
            if not isinstance(from_tags, list):
                from_tags = []
            return list(dict.fromkeys(list(from_tags) + list(standalone)))

        tag_agg["partners_from_tags"] = tag_agg.apply(combine_tag_partners, axis=1)
        tag_agg = tag_agg.drop(columns=["standalone_partners"], errors="ignore")
    return tag_agg, tag_fields


def _combine_partners(base_agg, tag_agg, all_partner_indicators) -> pd.DataFrame:
    agg_df = base_agg.merge(tag_agg, on="indicator", how="left")
    if not all_partner_indicators.empty:
        agg_df = agg_df.merge(
            all_partner_indicators[["indicator", "partners_from_obs", "partner_count_obs"]],
            on="indicator",
            how="left",
        )
    else:
        agg_df["partners_from_obs"] = ""
        agg_df["partner_count_obs"] = 0

    def combine_all(row):
        obs = row.get("partners_from_obs", "")
        tag = row.get("partners_from_tags", [])
        combined = set()
        if pd.notna(obs) and obs:
            for part in str(obs).split(", "):
                if part.strip():
                    combined.add(part.strip())
        if isinstance(tag, list):
            for part in tag:
                if part and str(part).strip():
                    combined.add(str(part).strip())
        elif pd.notna(tag) and tag:
            for part in str(tag).split(","):
                if part.strip():
                    combined.add(part.strip())
        return ", ".join(sorted(combined)) if combined else ""

    agg_df["partners"] = agg_df.apply(combine_all, axis=1)
    agg_df["partner_count"] = agg_df["partners"].apply(
        lambda x: len([p for p in str(x).split(", ") if p.strip()]) if pd.notna(x) and x else 0
    )
    agg_df = agg_df.drop(
        columns=[c for c in ["partners_from_obs", "partner_count_obs", "partners_from_tags"] if c in agg_df.columns],
        errors="ignore",
    )
    return agg_df


def _clean_list(lst):
    if not isinstance(lst, list):
        return []
    cleaned = []
    for val in lst:
        try:
            if pd.isna(val):
                continue
        except (TypeError, ValueError):
            pass
        if isinstance(val, str) and val == "":
            continue
        cleaned.append(val)
    return cleaned
