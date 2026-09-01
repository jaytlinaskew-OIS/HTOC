"""ThreatScoreIW — one-file datapipeline wiring ThreatConnect + PRISM scores + OpDiv into an I&W workbook.

Uses shared code from ``htoc_ml.core`` (paths, ThreatConnect, CLI exit). Run:

  py -3.13 -m htoc_ml.datapipelines.threat_score_iw
  py -3.13 -m htoc_ml.datapipelines threat-score-iw

Walkthrough (start at run_threat_score_iw):
  1. intake_recent_indicators_from_threatconnect
  2. filter_threat_assess_bands
  3. join_prism_scores
  4. attach_opdiv_multi_partners
  5. filter_vt_and_severity
  6. attach_tags_and_iw_flag
  7. condense_and_write
"""
from __future__ import annotations

import ast
import ipaddress
import os
import re
import sys
import warnings
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import pytz

from htoc_ml.core import paths as htoc_paths
from htoc_ml.core.cli_exit import run_and_return_exit_code
from htoc_ml.core.pipeline import PipelineError, PipelineNoWork
from htoc_ml.core.threatconnect import ThreatConnectClient

INDICATOR_TYPES = (
    "Address", "EmailAddress", "File", "Host", "URL", "ASN", "CIDR",
    "Email Subject", "Hashtag", "Mutex", "Registry Key", "User Agent", "Stripped URL",
)
OWNER_NAMES = (
    "HTOC Org",
    "CISA Federal Feed",
    "CMS_CTI",
    "Crowdstrike Falcon Intelligence",
    "DHS CISCP",
    "Intel471",
    "Mandiant Advantage Threat Intelligence",
    "VA_TIP Data",
)


@dataclass(frozen=True)
class ThreatScoreIwConfig:
    htoc_share_root: str = htoc_paths.DEFAULT_SHARE_ROOT
    tc_project_root: str = htoc_paths.DEFAULT_TC_PROJECT_ROOT
    config_path: str = ""
    tc_sdk_path: str = ""
    scores_xlsx: str = ""
    tags_csv: str = ""
    opdiv_template: str = ""
    save_dir: str = ""
    query_lookback_hours: int = 48
    opdiv_lookback_days: int = 2
    min_opdiv_partners: int = 2
    min_vt_score: int = 2
    min_hosts_per_subnet: int = 5
    result_page_size: int = 500
    indicator_types: tuple[str, ...] = INDICATOR_TYPES
    owner_names: tuple[str, ...] = OWNER_NAMES
    prefer_owner: str = "HTOC Org"
    severities: tuple[str, ...] = ("high", "critical")

    def __post_init__(self) -> None:
        share = self.htoc_share_root.strip() or htoc_paths.DEFAULT_SHARE_ROOT
        object.__setattr__(self, "htoc_share_root", share)
        tc_root = self.tc_project_root.strip() or htoc_paths.DEFAULT_TC_PROJECT_ROOT
        object.__setattr__(self, "tc_project_root", tc_root)
        if not self.config_path:
            object.__setattr__(self, "config_path", str(htoc_paths.tc_config_json(tc_root)))
        if not self.tc_sdk_path:
            object.__setattr__(self, "tc_sdk_path", str(htoc_paths.threatconnect_sdk_dir(share)))
        if not self.scores_xlsx:
            object.__setattr__(self, "scores_xlsx", str(htoc_paths.threat_assessment_scores_xlsx(share)))
        if not self.tags_csv:
            object.__setattr__(self, "tags_csv", str(htoc_paths.observed_tags_csv(share)))
        if not self.opdiv_template:
            object.__setattr__(self, "opdiv_template", htoc_paths.opdiv_obs_template(share))
        if not self.save_dir:
            object.__setattr__(self, "save_dir", str(htoc_paths.threat_score_iw_save_dir(share)))

    def output_path(self, as_of: str | None = None) -> Path:
        stamp = as_of or date.today().strftime("%Y%m%d")
        return Path(self.save_dir) / f"ThreatAssessI_W_{stamp}.xlsx"

    @classmethod
    def from_env(cls) -> "ThreatScoreIwConfig":
        try:
            hours = int(os.environ.get("THREAT_SCORE_IW_LOOKBACK_HOURS", "48") or "48")
            return cls(
                htoc_share_root=str(htoc_paths.share_root()),
                tc_project_root=str(htoc_paths.tc_project_root()),
                config_path=os.environ.get("PRISM_CONFIG_PATH", "") or os.environ.get("THREAT_SCORE_IW_CONFIG_PATH", ""),
                scores_xlsx=os.environ.get("THREAT_SCORE_IW_SCORES_XLSX", ""),
                save_dir=os.environ.get("THREAT_SCORE_IW_SAVE_DIR", ""),
                query_lookback_hours=hours,
            )
        except PipelineError:
            raise
        except (ValueError, TypeError) as exc:
            raise PipelineError(f"invalid ThreatScoreIW env config: {exc}") from exc


def run_threat_score_iw(config: ThreatScoreIwConfig | None = None) -> list[Path]:
    """Build the daily ThreatAssessI_W workbook. Returns paths written."""
    config = config or ThreatScoreIwConfig.from_env()
    client = ThreatConnectClient(
        config_path=config.config_path,
        tc_sdk_path=config.tc_sdk_path,
        tc_project_root=config.tc_project_root,
        result_page_size=config.result_page_size,
    )
    cutoff = datetime.now(pytz.UTC) - timedelta(hours=config.query_lookback_hours)
    observed = intake_recent_indicators_from_threatconnect(client, config, cutoff)
    observed = filter_threat_assess_bands(observed)
    scored = join_prism_scores(observed, config, cutoff)
    multi = attach_opdiv_multi_partners(scored, config)
    filtered = filter_vt_and_severity(multi, config)
    labeled = attach_tags_and_iw_flag(filtered, observed, config)
    return condense_and_write(labeled, config)


def intake_recent_indicators_from_threatconnect(
    client: ThreatConnectClient,
    config: ThreatScoreIwConfig,
    cutoff: datetime,
) -> pd.DataFrame:
    start = cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")
    frame = client.query_indicators(
        owner_names=config.owner_names,
        indicator_types=config.indicator_types,
        last_observed_on_or_after=start,
        page_size=config.result_page_size,
    )
    if frame.empty:
        raise PipelineError("ThreatConnect returned no indicator rows.", exit_code=3)
    frame["lastObserved"] = pd.to_datetime(frame["lastObserved"], utc=True, errors="coerce")
    frame = frame[frame["lastObserved"] >= pd.Timestamp(cutoff)].copy()
    if config.prefer_owner:
        frame = frame[frame["ownerName"] == config.prefer_owner].copy()
    if frame.empty:
        raise PipelineError("No HTOC Org indicators in the lookback window.", exit_code=3)
    return frame


def _first_non_null_numeric(df: pd.DataFrame, ordered_cols: tuple[str, ...]) -> pd.Series | None:
    present = [c for c in ordered_cols if c in df.columns]
    if not present:
        return None
    out = pd.to_numeric(df[present[0]], errors="coerce")
    for col in present[1:]:
        series = pd.to_numeric(df[col], errors="coerce")
        out = out.mask(out.isna(), series)
    return out


def filter_threat_assess_bands(observed_src: pd.DataFrame) -> pd.DataFrame:
    rating_cols = ("threatAssessRating", "threatAssess.threatAssessRating", "rating")
    confidence_cols = ("threatAssessConfidence", "threatAssess.threatAssessConfidence")
    tar = _first_non_null_numeric(observed_src, rating_cols)
    tc = _first_non_null_numeric(observed_src, confidence_cols)
    if tar is None or tc is None:
        raise PipelineError(
            f"Could not resolve Threat Assess columns. Tried rating={rating_cols}, "
            f"confidence={confidence_cols}. Columns: {list(observed_src.columns)}"
        )
    top_rating = (
        pd.to_numeric(observed_src["rating"], errors="coerce")
        if "rating" in observed_src.columns
        else pd.Series(float("nan"), index=observed_src.index, dtype=float)
    )
    top_confidence = (
        pd.to_numeric(observed_src["confidence"], errors="coerce")
        if "confidence" in observed_src.columns
        else pd.Series(float("nan"), index=observed_src.index, dtype=float)
    )
    pass_rating = (tar >= 3) | (top_rating >= 3)
    pass_confidence = (tc >= 50) | (top_confidence >= 50)
    filtered = observed_src[pass_rating & pass_confidence].copy()
    if filtered.empty:
        raise PipelineError("No indicators passed threat-assess rating/confidence bands.", exit_code=3)
    return filtered


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


def join_prism_scores(observed_src: pd.DataFrame, config: ThreatScoreIwConfig, cutoff: datetime) -> pd.DataFrame:
    path = Path(config.scores_xlsx)
    if not path.is_file():
        raise PipelineError(f"PRISM scores workbook not found: {path}")
    try:
        df = pd.read_excel(path)
    except OSError as exc:
        raise PipelineError(f"Failed to read PRISM scores workbook: {exc}") from exc

    indicator_col = next((c for c in ["indicator", "Indicator", "INDICATOR"] if c in df.columns), None)
    if indicator_col is None:
        raise PipelineError(f"Could not find indicator column in scores workbook. Columns: {list(df.columns)}")
    last_observed_col = next(
        (
            c
            for c in ["Last Observed", "lastObserved", "LastObserved", "last_observed", "LAST OBSERVED"]
            if c in df.columns
        ),
        None,
    )
    if last_observed_col is None:
        raise PipelineError(f"Could not find 'Last Observed' column in scores workbook. Columns: {list(df.columns)}")
    if "associatedGroups.data" not in observed_src.columns:
        raise PipelineError(
            f"Could not find 'associatedGroups.data' in ThreatConnect frame. Columns: {list(observed_src.columns)}"
        )

    observed_indicators = set(observed_src["indicator"].dropna().astype(str))
    df = df[df[indicator_col].astype(str).isin(observed_indicators)].copy()
    if df.empty:
        raise PipelineNoWork("No PRISM-scored indicators overlap the ThreatConnect lookback window.")

    observed_latest = (
        observed_src.dropna(subset=["indicator"])
        .assign(
            indicator=lambda d: d["indicator"].astype(str),
            lastObserved=lambda d: pd.to_datetime(d["lastObserved"], utc=True, errors="coerce"),
        )
        .sort_values("lastObserved")
        .drop_duplicates(subset=["indicator"], keep="last")
    )
    last_obs_by_indicator = observed_latest.set_index("indicator")["lastObserved"]
    assoc_by_indicator = observed_latest.set_index("indicator")["associatedGroups.data"].map(_extract_group_ids)

    df_ind = df[indicator_col].astype(str)
    df[last_observed_col] = pd.to_datetime(df_ind.map(last_obs_by_indicator), utc=True, errors="coerce")
    cutoff_ts = pd.Timestamp(cutoff)
    df = df[df[last_observed_col].notna() & (df[last_observed_col] >= cutoff_ts)].copy()
    if df.empty:
        raise PipelineNoWork("No overlapping indicators remain after Last Observed filter.")

    df_ind = df[indicator_col].astype(str)
    if "Associated Groups" in df.columns:
        df["Associated Groups"] = df_ind.map(assoc_by_indicator).combine_first(df["Associated Groups"])
    else:
        df["Associated Groups"] = df_ind.map(assoc_by_indicator)
    return df


def _load_opdiv_observations(config: ThreatScoreIwConfig) -> pd.DataFrame:
    today = datetime.utcnow()
    paths = [
        config.opdiv_template.format(date=(today - timedelta(days=i)).strftime("%Y%m%d"))
        for i in range(config.opdiv_lookback_days)
    ]
    existing = [p for p in paths if Path(p).is_file()]
    if not existing:
        raise PipelineError("No OpDiv observation files found for the lookback window.", exit_code=3)
    frames = []
    for path in existing:
        try:
            frames.append(pd.read_csv(path))
        except OSError as exc:
            print(f"WARN: Error reading OpDiv file {path}: {exc}")
    if not frames:
        raise PipelineError("Failed to load any OpDiv observation files.", exit_code=3)
    return pd.concat(frames, ignore_index=True)


def attach_opdiv_multi_partners(df: pd.DataFrame, config: ThreatScoreIwConfig) -> pd.DataFrame:
    observed_data = _load_opdiv_observations(config)
    indicator_col_df = next((c for c in ["indicator", "Indicator", "INDICATOR"] if c in df.columns), None)
    indicator_col_obs = next(
        (c for c in ["indicator", "Indicator", "INDICATOR"] if c in observed_data.columns), None
    )
    opdiv_col = next((c for c in ["OpDiv", "opdiv", "OPDIV"] if c in observed_data.columns), None)
    if indicator_col_df is None:
        raise PipelineError(f"Could not find indicator column in scores frame. Columns: {list(df.columns)}")
    if indicator_col_obs is None:
        raise PipelineError(f"Could not find indicator column in OpDiv data. Columns: {list(observed_data.columns)}")
    if opdiv_col is None:
        raise PipelineError(f"Could not find OpDiv column in OpDiv data. Columns: {list(observed_data.columns)}")

    obs = observed_data.dropna(subset=[indicator_col_obs, opdiv_col]).copy()
    obs[indicator_col_obs] = obs[indicator_col_obs].astype(str).str.strip()
    obs[opdiv_col] = obs[opdiv_col].astype(str).str.strip()
    partners_by_indicator = obs.groupby(indicator_col_obs)[opdiv_col].apply(
        lambda s: sorted(set(x for x in s if x))
    )
    eligible = partners_by_indicator[partners_by_indicator.str.len() >= config.min_opdiv_partners]
    if eligible.empty:
        raise PipelineNoWork("No indicators seen by 2+ OpDiv partners in the OpDiv lookback.")
    opdiv_map = eligible.apply(lambda vals: ", ".join(vals))
    out = df[df[indicator_col_df].astype(str).str.strip().isin(eligible.index)].copy()
    if out.empty:
        raise PipelineNoWork("No PRISM rows remain after multi-partner OpDiv filter.")
    out["OpDiv"] = out[indicator_col_df].astype(str).str.strip().map(opdiv_map)
    out["Partners"] = out["OpDiv"]
    return out


def filter_vt_and_severity(frame: pd.DataFrame, config: ThreatScoreIwConfig) -> pd.DataFrame:
    if "Explanation" not in frame.columns:
        raise PipelineError("Scores frame missing Explanation column for VT filter.")
    if "Severity" not in frame.columns:
        raise PipelineError("Scores frame missing Severity column.")
    vt_scores = pd.to_numeric(
        frame["Explanation"].str.extract(r"VT score:\s*(\d+)", expand=False),
        errors="coerce",
    )
    out = frame[vt_scores >= config.min_vt_score].copy()
    out = out[out["Severity"].astype(str).str.lower().isin(config.severities)].copy()
    if out.empty:
        raise PipelineNoWork("No indicators remain after VT score and severity filters.")
    return out


def has_iw_tag(tags_value) -> bool:
    if tags_value is None or (isinstance(tags_value, float) and pd.isna(tags_value)):
        return False
    if not isinstance(tags_value, (list, tuple)):
        return False
    for tag in tags_value:
        try:
            name = str(tag.get("name", "") if isinstance(tag, dict) else tag).strip().lower()
            if name in {"i&w", "i & w", "iw"}:
                return True
        except Exception:
            continue
    return False


def attach_tags_and_iw_flag(
    final_indicators: pd.DataFrame,
    observed_src: pd.DataFrame,
    config: ThreatScoreIwConfig,
) -> pd.DataFrame:
    tags_path = Path(config.tags_csv)
    if not tags_path.is_file():
        raise PipelineError(f"Observed tags CSV not found: {tags_path}")
    try:
        tags_df = pd.read_csv(tags_path)
    except OSError as exc:
        raise PipelineError(f"Failed to read tags CSV: {exc}") from exc

    tags_indicator_col = next((c for c in tags_df.columns if str(c).lower() == "indicator"), None)
    tags_value_col = next((c for c in tags_df.columns if str(c).lower() in {"tags", "tag"}), None)
    if tags_indicator_col is None:
        raise PipelineError("Could not find an Indicator column in the tags CSV.")
    if tags_value_col is None:
        raise PipelineError(f"Could not find a Tag/Tags column in the tags CSV. Columns: {list(tags_df.columns)}")

    out = final_indicators.copy()
    if "Indicator" not in out.columns:
        ind_col = next((c for c in ["indicator", "INDICATOR"] if c in out.columns), None)
        if ind_col is None:
            raise PipelineError(f"Could not find Indicator column. Columns: {list(out.columns)}")
        out = out.rename(columns={ind_col: "Indicator"})

    indicator_to_tags = tags_df.set_index(tags_indicator_col)[tags_value_col].to_dict()
    out["Tags"] = out["Indicator"].map(indicator_to_tags)
    cols = [c for c in out.columns if c != "Tags"]
    out = out[cols[:-1] + ["Tags"] + cols[-1:]] if cols else out

    observed = observed_src.copy()
    if "tags.data" in observed.columns:
        observed["has_iw"] = observed["tags.data"].apply(has_iw_tag)
    else:
        observed["has_iw"] = False
    iw_per_indicator = (
        observed.groupby("indicator", dropna=False)["has_iw"]
        .max()
        .reset_index()
        .rename(columns={"indicator": "Indicator", "has_iw": "Reported I&W?_raw"})
    )
    out = out.drop(columns=[c for c in out.columns if c.startswith("Reported I&W?")], errors="ignore")
    out = out.merge(iw_per_indicator, on="Indicator", how="left")
    out["Reported I&W?"] = out["Reported I&W?_raw"].fillna(False).map({True: "Yes", False: "No"})
    out = out.drop(columns=["Reported I&W?_raw"])
    if "HTOC Threat Score" in out.columns:
        out = out.rename(columns={"HTOC Threat Score": "PRISM Score"})
    return out


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


def _has_threat_actor(value) -> bool:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return False
    return bool(str(value).strip())


def condense_final_indicators(frame: pd.DataFrame, *, min_hosts: int = 5) -> pd.DataFrame:
    """Roll dense /24 Address clusters into CIDR rows; keep singles and threat-actor IPs."""
    df = frame.copy()
    type_col = "Indicator Type" if "Indicator Type" in df.columns else "Type"

    df["_ip"] = df["Indicator"].map(_to_ip)
    df["_subnet24"] = df["_ip"].map(_subnet24)

    ta_col = "Threat Actor" if "Threat Actor" in df.columns else None
    df["_has_ta"] = df[ta_col].map(_has_threat_actor) if ta_col else False

    condensable_mask = df[type_col].eq("Address") & df["_ip"].notna() & ~df["_has_ta"]
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
        c
        for c in [
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
    optional_aggs = {
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
    }
    agg.update({col: fn for col, fn in optional_aggs.items() if col in dense_df.columns})
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
    ordered: list[str] = []
    for col in base_cols:
        ordered.append(col)
        if col == "Indicator" and "_member_ips" in out.columns:
            ordered.append("_member_ips")
    ordered.extend([c for c in out.columns if c not in ordered])
    return out[[c for c in ordered if c in out.columns]]


def _subnet_range_name(subnet: str) -> str:
    return "MBR_" + re.sub(r"[^A-Za-z0-9]", "_", str(subnet))[:200]


def _prepare_export_df(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    export_df = df.copy()
    member_ip_lists = (
        export_df.pop("_member_ips")
        if "_member_ips" in export_df.columns
        else pd.Series([None] * len(export_df), index=export_df.index)
    )
    indicator_idx = export_df.columns.get_loc("Indicator") + 1
    export_df.insert(indicator_idx, "Host IP", "")

    member_map: dict = {}
    for idx, ips in member_ip_lists.items():
        if isinstance(ips, list) and len(ips) > 1:
            export_df.at[idx, "Host IP"] = ips[0]
            member_map[export_df.at[idx, "Indicator"]] = ips
        elif isinstance(ips, list) and len(ips) == 1:
            export_df.at[idx, "Host IP"] = ips[0]
        else:
            export_df.at[idx, "Host IP"] = ""
    return export_df, member_map


def _write_subnet_members_sheet(workbook, member_map: dict) -> dict[str, str]:
    from xlsxwriter.utility import xl_rowcol_to_cell

    range_names: dict[str, str] = {}
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


def _apply_member_dropdowns(
    worksheet,
    sheet_df: pd.DataFrame,
    member_map: dict,
    range_names: dict,
    member_col_name: str = "Host IP",
) -> None:
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


def write_iw_workbook(final_indicators: pd.DataFrame, output_path: Path) -> Path:
    """Write I&W_No / I&W_Yes sheets with optional Host IP dropdowns."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    frame = final_indicators.copy()
    for col in frame.select_dtypes(include=["datetimetz"]).columns:
        frame[col] = frame[col].dt.tz_convert(None)

    iw_col = "Reported I&W?"
    if iw_col not in frame.columns:
        raise PipelineError(f"Missing required column '{iw_col}' for sheet split.")

    export_df, member_map = _prepare_export_df(frame)
    final_iw_no = export_df[export_df[iw_col] == "No"].copy()
    final_iw_yes = export_df[export_df[iw_col] == "Yes"].copy()

    try:
        with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:
            final_iw_no.to_excel(writer, index=False, sheet_name="I&W_No")
            final_iw_yes.to_excel(writer, index=False, sheet_name="I&W_Yes")
            workbook = writer.book
            range_names = _write_subnet_members_sheet(workbook, member_map)
            wrap_fmt = workbook.add_format({"text_wrap": True, "valign": "top"})
            for sheet_name, sheet_df in [("I&W_No", final_iw_no), ("I&W_Yes", final_iw_yes)]:
                worksheet = writer.sheets[sheet_name]
                worksheet.set_column(0, len(export_df.columns) - 1, 18)
                if "Explanation" in export_df.columns:
                    exp_idx = export_df.columns.get_loc("Explanation")
                    worksheet.set_column(exp_idx, exp_idx, 100, wrap_fmt)
                if "Associated Groups" in export_df.columns:
                    ag_idx = export_df.columns.get_loc("Associated Groups")
                    worksheet.set_column(ag_idx, ag_idx, 45, wrap_fmt)
                if "Host IP" in export_df.columns:
                    member_idx = export_df.columns.get_loc("Host IP")
                    worksheet.set_column(member_idx, member_idx, 22)
                _apply_member_dropdowns(worksheet, sheet_df, member_map, range_names)
    except OSError as exc:
        raise PipelineError(f"Failed to write ThreatScoreIW workbook: {exc}", exit_code=4) from exc

    if not output_path.is_file():
        raise PipelineError(f"Expected output missing after write: {output_path}", exit_code=4)
    return output_path


def condense_and_write(final_indicators: pd.DataFrame, config: ThreatScoreIwConfig) -> list[Path]:
    condensed = condense_final_indicators(final_indicators, min_hosts=config.min_hosts_per_subnet)
    path = write_iw_workbook(condensed, config.output_path())
    return [path]


def main(argv: list[str] | None = None) -> int:
    # argv unused; kept so the datapipelines dispatcher can call main(rest) uniformly.
    _ = argv
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass
    warnings.filterwarnings("ignore")
    return run_and_return_exit_code(lambda: run_threat_score_iw(ThreatScoreIwConfig.from_env()))


if __name__ == "__main__":
    raise SystemExit(main())
