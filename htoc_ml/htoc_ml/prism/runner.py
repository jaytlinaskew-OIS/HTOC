"""PRISM indicator scoring. Daily (first-seen today) or weekly (7-day lastObserved).

Walkthrough (start at run_prism_indicator_scoring):
  1. intake_indicators_from_threatconnect
  2. enrich_with_local_and_partner_context
  3. score_prism_indicators
  4. write_prism_workbook
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

from htoc_ml.core.pipeline import PipelineError, PipelineNoWork
from htoc_ml.core.threatconnect import ThreatConnectClient
from htoc_ml.prism.client import connect_threatconnect
from htoc_ml.prism.config import PrismConfig
from htoc_ml.prism.engine import score_frame
from htoc_ml.prism.local import (
    annotate_incidents,
    attach_partners,
    attach_tag_lists,
    attach_yearly_obs,
    load_opdiv_observations,
    mass_scanner_flags,
    merge_threat_actors,
)
from htoc_ml.prism.workbook import merge_into_workbook


def run_prism_indicator_scoring(config: PrismConfig | None = None) -> list[Path]:
    """Score indicators and write the workbook. Returns paths written."""
    config = config or PrismConfig.from_env()
    client = connect_threatconnect(config)
    observed_src = intake_indicators_from_threatconnect(client, config)
    if observed_src.empty:
        if config.mode == "daily":
            raise PipelineNoWork("No indicators first-seen today — nothing to score.")
        raise PipelineError("ThreatConnect returned no HTOC Org rows.", exit_code=3)
    enriched = enrich_with_local_and_partner_context(client, observed_src, config)
    scored = score_prism_indicators(enriched, config)
    return write_prism_workbook(scored, config)


def intake_indicators_from_threatconnect(client: ThreatConnectClient, config: PrismConfig) -> pd.DataFrame:
    if config.mode == "weekly":
        return client.query_indicators_by_last_observed(
            owner_names=config.owner_names,
            indicator_types=config.indicator_types,
            lookback_days=config.query_lookback_days,
            prefer_owner="HTOC Org",
        )
    observed = pd.read_csv(config.observed_indicators_csv)
    observed["ioc_current_period_firstseen"] = pd.to_datetime(observed["ioc_current_period_firstseen"])
    today = pd.Timestamp(date.today())
    today_rows = observed[observed["ioc_current_period_firstseen"].dt.normalize() == today]
    summaries = today_rows["indicator"].dropna().unique().tolist()
    if not summaries:
        return pd.DataFrame()
    frame = client.query_indicators_by_summaries(
        summaries=summaries,
        owner_names=config.owner_names,
        indicator_types=config.indicator_types,
        prefer_owner="HTOC Org",
    )
    if frame.empty:
        raise PipelineError(
            "ThreatConnect returned no HTOC Org rows for today's first-seen indicators.",
            exit_code=3,
        )
    return frame


def enrich_with_local_and_partner_context(client: ThreatConnectClient, observed_src: pd.DataFrame, config: PrismConfig) -> pd.DataFrame:
    observed_src = merge_threat_actors(observed_src, config)
    observed_src = attach_firstseen_window(observed_src, config)
    observed_src = annotate_incidents(observed_src)
    observed_src = attach_tag_lists(observed_src)

    opdiv = load_opdiv_observations(config)
    scanners = mass_scanner_flags(opdiv)
    agg_df, _ = attach_partners(observed_src, opdiv)
    if not scanners.empty:
        agg_df = agg_df.merge(
            scanners[["indicator", "total_obs_7d", "unique_opdivs_7d", "mass_scanner_tier1", "mass_scanner_tier2"]],
            on="indicator",
            how="left",
        )
        agg_df["mass_scanner_tier1"] = agg_df["mass_scanner_tier1"].fillna(False).astype(bool)
        agg_df["mass_scanner_tier2"] = agg_df["mass_scanner_tier2"].fillna(False).astype(bool)
        agg_df["total_obs_7d"] = agg_df["total_obs_7d"].fillna(0).astype(int)
        agg_df["unique_opdivs_7d"] = agg_df["unique_opdivs_7d"].fillna(0).astype(int)
    else:
        agg_df["mass_scanner_tier1"] = False
        agg_df["mass_scanner_tier2"] = False
        agg_df["total_obs_7d"] = 0
        agg_df["unique_opdivs_7d"] = 0

    recent = client.enrich_indicators(agg_df)
    recent.drop(
        columns=[
            "tag_id", "tag_lastUsed", "tag_lastModified", "tag_ownerId", "tag_ownerName",
            "tag_dateAdded", "tag_description", "tag_tactics.count", "tag_platform.data",
            "tag_platform.count", "data.id", "data.dateAdded", "data.ownerId", "data.webLink",
            "data.ownerName", "data.lastModified", "data.summary", "data.ip", "data.legacyLink",
            "data.source", "enrich_cloudProvider", "enrich_cloudRegion", "enrich_type", "id",
        ],
        inplace=True,
        errors="ignore",
    )
    return attach_yearly_obs(recent, opdiv)


def score_prism_indicators(recent: pd.DataFrame, config: PrismConfig) -> pd.DataFrame:
    scored = score_frame(recent, extra_standalone_tags=config.extra_standalone_tags)
    if scored.empty:
        raise PipelineError(
            "df_scored is empty after scoring — refusing to rewrite workbook.",
            exit_code=3,
        )
    return scored


def write_prism_workbook(scored: pd.DataFrame, config: PrismConfig) -> list[Path]:
    path = merge_into_workbook(scored, config.excel_path)
    if not path.is_file():
        raise PipelineError(f"Expected Excel output missing after write: {path}", exit_code=4)
    return [path]


def attach_firstseen_window(observed_src: pd.DataFrame, config: PrismConfig) -> pd.DataFrame:
    observed = pd.read_csv(config.observed_indicators_csv)
    observed["firstseen_dt"] = pd.to_datetime(observed["firstseen_dt"], errors="coerce")
    today = pd.Timestamp(date.today())
    cutoff = today - pd.Timedelta(days=config.firstseen_lookback_days)
    window = observed[
        (observed["firstseen_dt"] >= cutoff) & (observed["firstseen_dt"] <= today)
    ][["indicator", "firstseen_dt"]].rename(columns={"firstseen_dt": "firstseen_date"})
    return observed_src.merge(window, on="indicator", how="left")
