"""Scheduled Next Observed Indicator forecast runner."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from htoc_ml.core.day import to_day_index, to_timestamp
from htoc_ml.core.observations import ObservationPanel
from htoc_ml.core.pipeline import Pipeline, PipelineError
from htoc_ml.noi.bands import BandPolicy
from htoc_ml.noi.config import DATE_FMT, ForecastConfig
from htoc_ml.noi.dataset import TrainingSet
from htoc_ml.noi.features import FeatureBuilder
from htoc_ml.noi.feed_health import FeedHealth
from htoc_ml.noi.model import HorizonModel
from htoc_ml.noi.outage import OutageImputer, format_findings, format_report
from htoc_ml.noi.report import ProductionReport
from htoc_ml.noi.schedule import CutoffSchedule


class ForecastRunner(Pipeline):
    def __init__(self, config: ForecastConfig | None = None) -> None:
        self.config = config or ForecastConfig.from_env()
        self._written: list[Path] = []

    def expected_outputs(self) -> list[Path]:
        return list(self._written)

    def execute(self) -> None:
        config = self.config
        if config.as_of:
            print(f"AS-OF REPLAY: rebuilding {config.as_of} using only data available then", flush=True)

        panel = ObservationPanel.load(
            obs_template=config.obs_template,
            train_days=config.train_days,
            end_date=config.as_of,
            min_file_coverage=config.min_file_coverage,
            max_lag_days=config.max_lag_days,
        )
        print(panel.describe())

        health = FeedHealth.from_panel(panel.frame, today=config.as_of)
        summary = health.summarize(
            sorted(panel.frame["opdiv"].unique()),
            to_timestamp(panel.day_max - 30).date(),
            to_timestamp(panel.day_max).date(),
        )
        unhealthy = summary[
            (summary["outage"] > 0) | (summary["missing"] > 0) | (summary["degraded"] > 0)
        ]
        if unhealthy.empty:
            print("feed health: all OpDivs nominal over the last 30 days")
        else:
            print("feed health: issues over the last 30 days")
            for _, row in unhealthy.iterrows():
                print(
                    f"  {row['OpDiv']}: outage={row['outage']} degraded={row['degraded']} "
                    f"missing={row['missing']} | {row['unusable_days']}"
                )

        imputer = OutageImputer(panel.frame, health)
        feature_lookup, impute_report = imputer.build(panel.labels.as_dict())
        panel.set_features(feature_lookup)
        if impute_report:
            print("outage imputation:")
            for line in format_report(impute_report):
                print(line)
        else:
            print("outage imputation: no outages in the panel window")

        findings = imputer.verify_recovery()
        if findings:
            print("WARNING: feed composition changed across an outage")
            for line in format_findings(findings):
                print(line)

        features = FeatureBuilder(config.lookback_days)
        training = TrainingSet(
            config=config,
            feature_builder=features,
            labels=panel.labels,
            features=panel.features,
            health=health,
        )
        schedule = CutoffSchedule.build(panel.day_min, panel.day_max, config)
        train_df = training.build_rows(schedule.cutoffs, need_label=True)
        if train_df.empty:
            raise PipelineError("Training frame is empty after feature build.")
        print(f"training rows: {len(train_df):,} from {schedule.describe()}")

        model = HorizonModel(config, training).fit(train_df, schedule)

        if config.as_of is None:
            infer_t = panel.day_max
        else:
            infer_t = int(to_day_index(np.datetime64(pd.Timestamp(config.as_of).date())))
        infer_df = training.build_rows([infer_t], need_label=False)
        print(f"scoring {len(infer_df):,} indicators as-of {to_timestamp(infer_t).date()}")
        if infer_df.empty:
            raise PipelineError(
                f"No candidate indicators to score as-of {to_timestamp(infer_t).date()}.",
                exit_code=3,
            )

        probabilities = model.predict(infer_df)
        bands = BandPolicy()
        out = infer_df[["opdiv", "indicator", "last_seen", "freq_7", "freq_30"]].copy()
        for j, horizon_days in enumerate(config.horizons):
            out[f"prob_{horizon_days}"] = probabilities[:, j]
            out[f"band_{horizon_days}"] = [
                bands.label(p, horizon_days, opdiv)
                for p, opdiv in zip(probabilities[:, j], out["opdiv"])
            ]

        imputed_pairs = imputer.imputed_indicators(panel.labels.as_dict(), upto_di=infer_t)
        out["observed_today"] = [
            panel.labels.really_seen(opdiv, indicator, infer_t)
            for opdiv, indicator in zip(out["opdiv"], out["indicator"])
        ]
        out["basis"] = [
            "est" if (opdiv, indicator) in imputed_pairs else ""
            for opdiv, indicator in zip(out["opdiv"], out["indicator"])
        ]
        if imputed_pairs:
            print(
                f"forecast rests on imputed days for {int((out['basis'] == 'est').sum()):,} "
                f"indicators (marked 'est' in the Basis column)"
            )

        report = ProductionReport(config.horizons)
        opdiv_outputs = {
            opdiv: report.format_opdiv(group).reset_index(drop=True)
            for opdiv, group in out.groupby("opdiv")
        }
        print("OpDivs:", list(opdiv_outputs.keys()))
        if opdiv_outputs:
            print(opdiv_outputs[list(opdiv_outputs)[0]].head(10))

        if not config.save_output:
            raise PipelineError("SAVE_OUTPUT is False in scheduled runner")
        if not opdiv_outputs:
            raise PipelineError("no OpDiv outputs produced", exit_code=3)

        stamp = to_timestamp(infer_t).strftime(DATE_FMT)
        self._written = report.write(opdiv_outputs, config.save_dir, stamp)
        print(f"Wrote {len(opdiv_outputs)} OpDiv files under {config.save_dir}")
        self._record_backfill(stamp)
        self._run_eval(stamp, consolidate_only=bool(config.as_of))

    def _record_backfill(self, stamp: str) -> None:
        if not self.config.as_of:
            return
        marker = Path(self.config.save_dir) / "backfilled_forecasts.txt"
        try:
            seen: set[str] = set()
            if marker.exists():
                seen = {ln.strip() for ln in marker.read_text(encoding="utf-8").splitlines() if ln.strip()}
            if stamp not in seen:
                with marker.open("a", encoding="utf-8") as fh:
                    fh.write(f"{stamp}\n")
            print(f"AS-OF REPLAY: recorded {stamp} in {marker}")
        except OSError as exc:
            print(f"WARN: could not record backfill marker: {exc}")

    def _run_eval(self, stamp: str, consolidate_only: bool) -> None:
        if not self.config.run_eval:
            return
        from htoc_ml.noi.eval import run_eval_after_forecast

        if not run_eval_after_forecast(
            stamp,
            self.config.save_dir,
            self.config.htoc_share_root,
            consolidate_only=consolidate_only,
        ):
            print("PERF: evaluation completed with errors (see Performance/Logs on share)")
