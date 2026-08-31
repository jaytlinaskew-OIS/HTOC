"""PRISM scheduled runner. Daily (first-seen today) or weekly (7-day lastObserved)."""
from __future__ import annotations

from datetime import date

import pandas as pd

from htoc_ml.core.pipeline import Pipeline, PipelineError, PipelineNoWork
from htoc_ml.prism.client import ThreatConnectClient
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


class PrismRunner(Pipeline):
    def __init__(self, config: PrismConfig | None = None) -> None:
        self.config = config or PrismConfig.from_env()
        self._written = []

    def expected_outputs(self):
        return list(self._written)

    def execute(self) -> None:
        client = ThreatConnectClient(self.config)
        observed_src = self._intake(client)
        if observed_src.empty:
            if self.config.mode == "daily":
                raise PipelineNoWork("No indicators first-seen today — nothing to score.")
            raise PipelineError("ThreatConnect returned no HTOC Org rows.", exit_code=3)

        observed_src = merge_threat_actors(observed_src, self.config)
        observed_src = self._attach_firstseen(observed_src)
        observed_src = annotate_incidents(observed_src)
        observed_src = attach_tag_lists(observed_src)

        opdiv = load_opdiv_observations(self.config)
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

        recent = client.enrich(agg_df)
        recent.drop(columns=[
            "tag_id", "tag_lastUsed", "tag_lastModified", "tag_ownerId", "tag_ownerName",
            "tag_dateAdded", "tag_description", "tag_tactics.count", "tag_platform.data",
            "tag_platform.count", "data.id", "data.dateAdded", "data.ownerId", "data.webLink",
            "data.ownerName", "data.lastModified", "data.summary", "data.ip", "data.legacyLink",
            "data.source", "enrich_cloudProvider", "enrich_cloudRegion", "enrich_type", "id",
        ], inplace=True, errors="ignore")
        recent = attach_yearly_obs(recent, opdiv)
        scored = score_frame(recent, extra_standalone_tags=self.config.extra_standalone_tags)
        print(f"Scoring complete — {len(scored)} indicators scored")
        if scored.empty:
            raise PipelineError("df_scored is empty after scoring — refusing to rewrite workbook.", exit_code=3)
        path = merge_into_workbook(scored, self.config.excel_path)
        self._written = [path]
        if not path.is_file():
            raise PipelineError(f"Expected Excel output missing after write: {path}", exit_code=4)

    def _intake(self, client: ThreatConnectClient) -> pd.DataFrame:
        if self.config.mode == "weekly":
            frame = client.query_weekly()
            print(f"observed_src: {len(frame):,} rows")
            return frame
        observed = pd.read_csv(self.config.observed_indicators_csv)
        print(f"Loaded {len(observed):,} rows from observed indicators")
        observed["ioc_current_period_firstseen"] = pd.to_datetime(observed["ioc_current_period_firstseen"])
        today = pd.Timestamp(date.today())
        today_rows = observed[observed["ioc_current_period_firstseen"].dt.normalize() == today]
        print(f"Records first seen today ({today.date()}): {len(today_rows):,}")
        summaries = today_rows["indicator"].dropna().unique().tolist()
        print(f"Distinct indicators from today's observed data: {len(summaries)}")
        if not summaries:
            return pd.DataFrame()
        frame = client.query_summaries(summaries)
        print(f"observed_src: {len(frame):,} rows")
        if frame.empty:
            raise PipelineError(
                "ThreatConnect returned no HTOC Org rows for today's first-seen indicators.",
                exit_code=3,
            )
        return frame

    def _attach_firstseen(self, observed_src: pd.DataFrame) -> pd.DataFrame:
        observed = pd.read_csv(self.config.observed_indicators_csv)
        observed["firstseen_dt"] = pd.to_datetime(observed["firstseen_dt"], errors="coerce")
        today = pd.Timestamp(date.today())
        cutoff = today - pd.Timedelta(days=self.config.firstseen_lookback_days)
        window = observed[
            (observed["firstseen_dt"] >= cutoff) & (observed["firstseen_dt"] <= today)
        ][["indicator", "firstseen_dt"]].rename(columns={"firstseen_dt": "firstseen_date"})
        return observed_src.merge(window, on="indicator", how="left")
